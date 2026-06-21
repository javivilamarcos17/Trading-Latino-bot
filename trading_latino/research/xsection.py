"""
Momentum TRANSVERSAL (cross-sectional), market-neutral: cada semana, largo en las monedas
más fuertes (mejor momentum) y corto en las más débiles, a partes iguales. Neutral al mercado
(no apuesta a que cripto suba o baje). Edge documentado en muchos mercados. Validado en 2026.

Uso:  python -m trading_latino.research.xsection
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from trading_latino.config import CONFIG
from trading_latino.data.download import cargar


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    universo = list(CONFIG.altcoins) + ["BTC"]
    cierres = {}
    for s in universo:
        try:
            d = cargar("binance", s, "1d")
            cierres[s] = pd.Series(d["cierre"].to_numpy(), index=pd.DatetimeIndex(d["timestamp"]).tz_localize(None))
        except Exception:
            pass
    px = pd.DataFrame(cierres).sort_index()
    px = px[px.index >= "2021-01-01"]
    ret = px.pct_change()

    LB = 30      # lookback de momentum (días)
    K = 4        # nº de monedas en cada pata (top K largo, bottom K corto)
    REB = 7      # rebalanceo cada 7 días
    coste = 0.0006  # ida/vuelta aprox por rebalanceo sobre el nocional que rota

    mom = px.pct_change(LB)
    fechas = px.index
    pos = pd.DataFrame(0.0, index=fechas, columns=px.columns)
    ultima = None
    for i, f in enumerate(fechas):
        if i < LB:
            continue
        if ultima is None or (f - ultima).days >= REB:
            m = mom.loc[f].dropna()
            if len(m) >= 2 * K:
                fuertes = m.nlargest(K).index
                debiles = m.nsmallest(K).index
                fila = pd.Series(0.0, index=px.columns)
                fila[fuertes] = 1.0 / K
                fila[debiles] = -1.0 / K
                pos.loc[f] = fila.values
                ultima = f
            else:
                pos.loc[f] = pos.iloc[i - 1].values
        else:
            pos.loc[f] = pos.iloc[i - 1].values

    pos_ayer = pos.shift(1).fillna(0.0)
    pnl = (pos_ayer * ret).sum(axis=1)
    turnover = (pos - pos.shift(1)).abs().sum(axis=1)
    pnl_neto = pnl - turnover * coste
    eq = (1 + pnl_neto.fillna(0)).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    ins = eq[eq.index.year <= 2025]; out = eq[eq.index.year == 2026]
    rin = ins.iloc[-1] / ins.iloc[0] - 1
    rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
    cagr = (1 + rin) ** (1 / 4.99) - 1
    print(f"Momentum transversal (long top{K}/short bottom{K}, rebal {REB}d, lookback {LB}d):")
    print(f"  in-sample 21-25: {rin*100:+7.1f}% (CAGR {cagr*100:+5.1f}%/a) | HOLD-OUT 2026: {rout*100:+6.2f}% | DD {dd*100:.1f}%")
    print("  Por año:")
    for y in [2021, 2022, 2023, 2024, 2025, 2026]:
        s = eq[eq.index.year == y]
        if len(s) > 1:
            print(f"    {y}: {(s.iloc[-1]/s.iloc[0]-1)*100:+6.2f}%")


if __name__ == "__main__":
    main()
