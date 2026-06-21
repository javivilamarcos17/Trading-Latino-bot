"""
Carry PROFESIONAL y realista (delta-neutral) sobre un CESTO de perpetuos.
Depura el carry "idealizado" de la v2 añadiendo lo que el backtest naive no veía:
  1) DIVERSIFICACIÓN en varias monedas (reparte riesgo de funding y de contraparte).
  2) Regla ANTI-FUNDING-NEGATIVO: solo mantienes el carry de una moneda cuando su
     funding reciente es positivo; si se gira (pagarías tú) -> fuera de esa moneda.
  3) COSTES explícitos: comisiones de entrada/salida + drag de rebalanceo (no el
     "haircut 0.5" arbitrario). Bruto vs neto.
  4) APALANCAMIENTO PRUDENTE: barrido 1x/2x/3x (no el ~6x peligroso del vol-target).
  5) ESTRÉS: peor día, peor mes, % de tiempo en funding negativo, racha negativa.
  6) HOLD-OUT 2026 separado.

Uso:  python -m trading_latino.research.carry_pro
"""

from __future__ import annotations

import sys
import time

import ccxt
import numpy as np
import pandas as pd

SIMBOLOS = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "LINK",
            "DOGE", "DOT", "LTC", "BCH", "ATOM", "NEAR", "UNI", "FIL", "AAVE", "INJ"]
# costes (por LADO): taker Binance ~0.045%. Una entrada+salida del carry = 2 patas x 2 lados.
COSTE_LADO = 0.00045
DRAG_DIARIO = 0.00003  # ~0.3 bps/día de rebalanceo para mantener delta-neutral (~1.1%/año)


def _funding(ex, simbolo):
    sym = f"{simbolo}/USDT:USDT"
    since = ex.parse8601("2021-01-01T00:00:00Z")
    hasta = ex.parse8601("2026-06-21T00:00:00Z")
    filas = []
    while since < hasta:
        lote = ex.fetch_funding_rate_history(sym, since=since, limit=1000)
        if not lote:
            break
        filas += lote
        since = lote[-1]["timestamp"] + 1
        if len(lote) < 1000:
            break
        time.sleep(ex.rateLimit / 1000)
    s = pd.Series({pd.to_datetime(x["timestamp"], unit="ms").tz_localize(None): x["fundingRate"] for x in filas})
    s = s[~s.index.duplicated()].sort_index().astype(float)
    return s.groupby(s.index.normalize()).sum()  # funding diario (suma de los pagos del día)


def _met(eq, nombre):
    ins = eq[eq.index.year <= 2025]
    out = eq[eq.index.year == 2026]
    cagr = (ins.iloc[-1] / ins.iloc[0]) ** (1 / 4.99) - 1
    dd = (eq / eq.cummax() - 1).min()
    rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
    print(f"  {nombre:<26}| CAGR {cagr*100:+6.1f}% | 2026 {rout*100:+6.2f}% | DD {dd*100:6.2f}% | C/DD {abs(cagr/dd) if dd<0 else 0:5.2f}")
    return cagr, dd


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    ex = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})
    series = {}
    print("Funding diario por moneda (bruto anualizado, %tiempo positivo):")
    for s in SIMBOLOS:
        try:
            r = _funding(ex, s)
        except Exception as e:
            print(f"  {s}: sin datos ({e})"); continue
        if len(r) < 200:
            continue
        series[s] = r
        print(f"  {s:<5} | {r.mean()*365*100:+6.2f}%/año | positivo {(r>0).mean()*100:4.1f}% | {len(r)} días")

    df = pd.DataFrame(series).sort_index()
    df = df[df.index >= "2021-01-01"]

    # Selección ESTÁTICA: fuera monedas con funding medio negativo (BNB) -> no aportan rent.
    buenas = [c for c in df.columns if df[c].mean() > 0.00005]   # > ~+1.8%/año bruto
    print(f"\nMonedas con funding estructuralmente positivo: {buenas}")
    df = df[buenas]

    def cesta_neto(activo, etiqueta):
        """activo: DataFrame bool (qué monedas tienes ese día). Calcula bruto y neto.
        Solo cuentan monedas que YA existen ese día (df.notna())."""
        act = (activo & df.notna()).shift(1).fillna(False)
        n = act.sum(axis=1).replace(0, np.nan)
        bruto = (df.where(act, 0)).sum(axis=1) / n
        # coste de rotación: cada ENTRADA o SALIDA = 2 patas x 1 lado = 2*COSTE_LADO
        cambios = act.astype(int).diff().abs().fillna(0)
        coste = (cambios.sum(axis=1) / n.fillna(1)) * (2 * COSTE_LADO)
        neto = (bruto - coste).fillna(0) - DRAG_DIARIO
        return bruto.fillna(0), neto

    # A) Siempre dentro de todas las buenas que existan ese día (rotación casi nula).
    siempre = df.notna()
    b_siempre, n_siempre = cesta_neto(siempre, "siempre")
    # B) Regla LENTA con histéresis: sales si el funding de 14 días < 0; vuelves cuando 14d > 0.
    lento = (df.rolling(14).mean() > 0)
    b_lento, n_lento = cesta_neto(lento, "lento")

    print(f"\nCesta diversificada ({df.shape[1]} buenas monedas) — bruto vs neto realista:")
    _met((1 + b_siempre).cumprod(), "siempre-dentro BRUTO")
    _met((1 + n_siempre).cumprod(), "siempre-dentro NETO")
    _met((1 + b_lento).cumprod(), "regla 14d BRUTO")
    _met((1 + n_lento).cumprod(), "regla 14d NETO")

    neto_cesta = n_siempre  # el robusto (poca rotación) para apalancar y estresar
    print("\nApalancamiento PRUDENTE (cesta siempre-dentro NETA):")
    for lev in (1, 2, 3):
        _met((1 + neto_cesta * lev).cumprod(), f"carry neto {lev}x")

    print("\nRendimiento NETO por año (cesta 1x) — cuánto varía el 'alquiler':")
    por_anio = (1 + neto_cesta).groupby(neto_cesta.index.year).prod() - 1
    print("  " + "  ".join(f"{y}:{r*100:+5.1f}%" for y, r in por_anio.items()))

    print("\n== ESTRÉS (cesta neta 1x) ==")
    diario = neto_cesta
    mensual = (1 + diario).groupby([diario.index.year, diario.index.month]).prod() - 1
    neg = b_siempre < 0
    racha = (neg != neg.shift()).cumsum()
    max_racha = neg.groupby(racha).sum().max()
    print(f"  peor día        : {diario.min()*100:+.2f}%")
    print(f"  peor mes        : {mensual.min()*100:+.2f}%")
    print(f"  meses negativos : {(mensual<0).mean()*100:.0f}% de los meses")
    print(f"  %tiempo funding cesta negativo: {neg.mean()*100:.1f}%  | racha negativa máx: {int(max_racha)} días")
    print("\nNota: el DD aquí es solo del flujo de funding. El riesgo REAL es de cola")
    print("(quiebra de exchange, liquidación de la pata corta en un flash-crash), que")
    print("NO está en estos números -> por eso apalancamiento bajo y reparto entre exchanges.")


if __name__ == "__main__":
    main()
