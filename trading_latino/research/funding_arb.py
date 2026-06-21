"""
ARBITRAJE DE FUNDING ENTRE EXCHANGES (market-neutral y, en teoría, regime-independiente).
El mismo perpetuo (p. ej. BTC) tiene funding DISTINTO en cada exchange a la vez. La jugada:
  - LARGO el perpetuo donde el funding es más BAJO (o negativo) -> pagas poco / cobras.
  - CORTO el perpetuo donde el funding es más ALTO -> cobras mucho.
  - El precio se cancela (mismo activo, lados opuestos) -> exposición neta = 0.
  - Cobras el DIFERENCIAL de funding entre los dos exchanges.
No necesita que el funding sea alto: solo que haya DIFERENCIA. Por eso podría pagar en calma.

Honestidad: medimos sin mirar el futuro (la dirección se fija con el funding de AYER y se cobra
el diferencial de HOY) y neto de costes de cambiar de pareja de exchanges. Riesgos reales NO
modelados: contraparte en DOS exchanges a la vez, capital partido, transferencias entre venues.

Uso:  python -m trading_latino.research.funding_arb
"""

from __future__ import annotations

import sys
import time

import ccxt
import pandas as pd

MONEDAS = ["BTC", "ETH", "SOL"]
# (id ccxt, plantilla de símbolo) — la mayoría USDT; Hyperliquid usa USDC.
EXCHANGES = [
    ("binance", "{}/USDT:USDT"),
    ("bybit", "{}/USDT:USDT"),
    ("okx", "{}/USDT:USDT"),
    ("gate", "{}/USDT:USDT"),
    ("hyperliquid", "{}/USDC:USDC"),
]
COSTE_LADO = 0.00045
# Drag diario de mantener la pareja fija (rebalanceo delta-neutral, comisiones periódicas).
# ~0.005%/día ≈ ~1.8%/año. Conservador para una posición casi estática.
DRAG_ARB = 0.00005
INICIO = "2022-01-01T00:00:00Z"   # antes hay pocos venues con histórico
FIN = "2026-06-21T00:00:00Z"
ANIOS = [2022, 2023, 2024, 2025, 2026]


def _funding_diario(ex, sym):
    since = ex.parse8601(INICIO); hasta = ex.parse8601(FIN); rows = []
    while since < hasta:
        try:
            lote = ex.fetch_funding_rate_history(sym, since=since, limit=1000)
        except Exception:
            break
        if not lote:
            break
        rows += lote; since = lote[-1]["timestamp"] + 1
        if len(lote) < 100:
            break
        time.sleep(ex.rateLimit / 1000)
    if not rows:
        return pd.Series(dtype=float)
    s = pd.Series({pd.to_datetime(x["timestamp"], unit="ms").tz_localize(None): x["fundingRate"] for x in rows})
    s = s[~s.index.duplicated()].sort_index().astype(float)
    return s.groupby(s.index.normalize()).sum()   # funding diario (suma de pagos del día)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    for moneda in MONEDAS:
        print(f"\n===== {moneda} =====")
        series = {}
        for ex_id, plantilla in EXCHANGES:
            try:
                ex = getattr(ccxt, ex_id)({"enableRateLimit": True, "options": {"defaultType": "swap"}})
                s = _funding_diario(ex, plantilla.format(moneda))
            except Exception as e:
                print(f"  {ex_id:<12} sin datos ({type(e).__name__})"); continue
            if len(s) > 100:
                series[ex_id] = s
                print(f"  {ex_id:<12} {s.mean()*365*100:+6.2f}%/año | {len(s)} días")
            else:
                print(f"  {ex_id:<12} histórico insuficiente")

        if len(series) < 2:
            print("  -> menos de 2 exchanges con datos: no se puede arbitrar."); continue

        df = pd.DataFrame(series).sort_index()
        df = df[df.index >= INICIO[:10]]

        # PAREJA FIJA ESTRUCTURAL: para cada par de venues con solape, mantener corto el de
        # funding medio más ALTO / largo el más BAJO. Capturas el diferencial persistente, sin
        # latigazos. Net = (f_alto - f_bajo) cada día - drag de mantenimiento.
        nombres = list(df.columns)
        mejores = []
        for i in range(len(nombres)):
            for j in range(i + 1, len(nombres)):
                a, b = nombres[i], nombres[j]
                par = df[[a, b]].dropna()
                if len(par) < 300:
                    continue
                alto, bajo = (a, b) if par[a].mean() >= par[b].mean() else (b, a)
                spread = (par[alto] - par[bajo])          # >= 0 en media por construcción
                neto = spread - DRAG_ARB                  # drag de rebalanceo/mantenimiento
                eq = (1 + neto).cumprod()
                dd = (eq / eq.cummax() - 1).min()
                cagr = (eq.iloc[-1] / eq.iloc[0]) ** (365 / len(eq)) - 1
                pos = (spread > 0).mean()
                mejores.append((cagr, dd, pos, alto, bajo, eq, len(eq)))

        if not mejores:
            print("  -> ningún par con solape suficiente."); continue
        mejores.sort(reverse=True)
        print(f"  Parejas FIJAS (corto el de funding alto / largo el bajo), neto de drag {DRAG_ARB*365*100:.0f}%/año:")
        for cagr, dd, pos, alto, bajo, eq, n in mejores:
            aa = " ".join(f"{(eq[eq.index.year==y].iloc[-1]/eq[eq.index.year==y].iloc[0]-1)*100:+5.1f}" if len(eq[eq.index.year == y]) > 1 else "   -" for y in ANIOS)
            print(f"    corto {alto:<11} / largo {bajo:<11}| CAGR {cagr*100:+5.1f}% | DD {dd*100:5.1f}% | spread+ {pos*100:3.0f}% días | {n}d | {aa}")


if __name__ == "__main__":
    main()
