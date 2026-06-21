"""
Long-short MARKET-NEUTRAL estilo Merino: largo lo fuerte / corto lo débil, sin exposición
neta al mercado (dólar-neutral). Reabrimos los CORTOS, pero quitando el beta de mercado
(que es lo que hacía fallar los cortos direccionales puros) y quedándonos con la DISPERSIÓN
relativa entre monedas.

Dos cosas juegan a favor del lado corto:
  - Al shortear un perpetuo COBRAS el funding (viento de cola cuando el funding es positivo).
  - El sesgo de supervivencia es CONSERVADOR para shorts: las monedas que desaparecieron se
    fueron a cero; shortearlas habría sido muy rentable. Medir solo con supervivientes
    INFRAVALORA el edge corto -> lo que salga aquí es un suelo, no un techo.

Variantes (todas dólar-neutral, neto de funding y costes, con hold-out 2026):
  A) Momentum transversal: largo tercil fuerte / corto tercil débil.
  B) Merino: largo BTC / corto el tercil de alts más débil.

Uso:  python -m trading_latino.research.longshort
"""

from __future__ import annotations

import sys
import time

import ccxt
import pandas as pd

SIMBOLOS = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "LINK",
            "DOGE", "DOT", "LTC", "BCH", "ATOM", "NEAR", "UNI", "FIL", "AAVE"]
COSTE_LADO = 0.00045
INICIO = "2021-01-01T00:00:00Z"
FIN = "2026-06-21T00:00:00Z"
ANIOS = [2021, 2022, 2023, 2024, 2025, 2026]


def _ohlcv(ex, sym):
    since = ex.parse8601(INICIO); hasta = ex.parse8601(FIN); rows = []
    while since < hasta:
        lote = ex.fetch_ohlcv(f"{sym}/USDT:USDT", "1d", since=since, limit=1000)
        if not lote:
            break
        rows += lote; since = lote[-1][0] + 86_400_000
        if len(lote) < 1000:
            break
        time.sleep(ex.rateLimit / 1000)
    s = pd.Series({pd.to_datetime(r[0], unit="ms").tz_localize(None): r[4] for r in rows})
    return s[~s.index.duplicated()].sort_index()


def _funding(ex, sym):
    since = ex.parse8601(INICIO); hasta = ex.parse8601(FIN); rows = []
    while since < hasta:
        lote = ex.fetch_funding_rate_history(f"{sym}/USDT:USDT", since=since, limit=1000)
        if not lote:
            break
        rows += lote; since = lote[-1]["timestamp"] + 1
        if len(lote) < 1000:
            break
        time.sleep(ex.rateLimit / 1000)
    s = pd.Series({pd.to_datetime(x["timestamp"], unit="ms").tz_localize(None): x["fundingRate"] for x in rows})
    s = s[~s.index.duplicated()].sort_index().astype(float)
    return s.groupby(s.index.normalize()).sum()


def _stats(nombre, r):
    eq = (1 + r.fillna(0)).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    ins = eq[eq.index.year <= 2025]
    cagr = (ins.iloc[-1] / ins.iloc[0]) ** (1 / 4.99) - 1
    aa = " ".join(f"{(eq[eq.index.year==y].iloc[-1]/eq[eq.index.year==y].iloc[0]-1)*100:+4.0f}" if len(eq[eq.index.year == y]) > 1 else "  -" for y in ANIOS)
    print(f"  {nombre:<30}| CAGR {cagr*100:+6.1f}% | DD {dd*100:6.1f}% | C/DD {abs(cagr/dd) if dd<0 else 0:5.2f} | {aa}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    ex = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})
    print(f"Descargando precio+funding de {len(SIMBOLOS)} monedas...")
    px, fund = {}, {}
    for s in SIMBOLOS:
        try:
            p = _ohlcv(ex, s); f = _funding(ex, s)
        except Exception as e:
            print(f"  {s}: sin datos ({e})"); continue
        if len(p) > 200:
            px[s] = p; fund[s] = f
    P = pd.DataFrame(px).sort_index()
    F = pd.DataFrame(fund).reindex(P.index).fillna(0)
    P = P[P.index >= "2021-01-01"]; F = F.reindex(P.index).fillna(0)
    R = P.pct_change()                      # retorno de precio diario
    neto = R - F                            # un LARGO gana R y PAGA F; un corto gana -R y COBRA F

    def backtest(pesos, rebal=7):
        """pesos(fila) -> Serie de pesos objetivo dólar-neutral. Rebalancea cada `rebal` días."""
        W = pesos.copy()
        mask = pd.Series(False, index=W.index)
        mask.iloc[::rebal] = True
        W = W.where(mask).ffill().fillna(0.0)          # mantener pesos entre rebalanceos
        ret = (W.shift(1) * neto).sum(axis=1)          # retorno con pesos del día anterior
        turn = (W - W.shift(1)).abs().sum(axis=1)       # rotación
        return ret - turn * COSTE_LADO

    def neutral(rank_score, lado="ambos"):
        """Construye pesos dólar-neutral por terciles del score (alto=fuerte)."""
        W = pd.DataFrame(0.0, index=P.index, columns=P.columns)
        for dia in P.index:
            sc = rank_score.loc[dia].dropna()
            if len(sc) < 6:
                continue
            n = max(1, len(sc) // 3)
            fuertes = sc.nlargest(n).index; debiles = sc.nsmallest(n).index
            if lado in ("ambos", "largo"):
                W.loc[dia, fuertes] = 0.5 / len(fuertes)
            if lado in ("ambos", "corto"):
                W.loc[dia, debiles] = -0.5 / len(debiles)
        return W

    print("\nA) Momentum transversal dólar-neutral (largo fuerte / corto débil):")
    for lb in (20, 30, 60, 90):
        mom = P / P.shift(lb) - 1
        _stats(f"momentum {lb}d (L/S)", backtest(neutral(mom), rebal=7))

    print("\nB) Merino: largo BTC / corto el tercil de alts más débil (momentum 30d):")
    mom = P / P.shift(30) - 1
    alts = [c for c in P.columns if c != "BTC"]
    Wm = pd.DataFrame(0.0, index=P.index, columns=P.columns)
    for dia in P.index:
        sc = mom.loc[dia, alts].dropna()
        if len(sc) < 6:
            continue
        n = max(1, len(sc) // 3)
        Wm.loc[dia, sc.nsmallest(n).index] = -0.5 / n
        Wm.loc[dia, "BTC"] = 0.5
    _stats("BTC largo / alts débiles corto", backtest(Wm, rebal=7))

    print("\nC) Solo cortar alts débiles (sin pata larga, captura decaimiento+funding):")
    Wc = pd.DataFrame(0.0, index=P.index, columns=P.columns)
    for dia in P.index:
        sc = mom.loc[dia, alts].dropna()
        if len(sc) < 6:
            continue
        n = max(1, len(sc) // 3)
        Wc.loc[dia, sc.nsmallest(n).index] = -1.0 / n
    _stats("corto alts débiles (1x)", backtest(Wc, rebal=7))

    print("\nD) REVERSIÓN a corto plazo dólar-neutral (largo los que cayeron / corto los que subieron):")
    for lb, rb in ((3, 1), (5, 2), (7, 3), (14, 7)):
        rev = -(P / P.shift(lb) - 1)            # score alto = cayó mucho -> largo
        _stats(f"reversión {lb}d (rebal {rb}d)", backtest(neutral(rev), rebal=rb))

    print("\n(años: 21·22·23·24·25·26. 2026 = prueba ciega)")


if __name__ == "__main__":
    main()
