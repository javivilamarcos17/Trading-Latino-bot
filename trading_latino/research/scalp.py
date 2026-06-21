"""
Idea: operar rápido (1h, lo más cercano a scalping con hold-out 2026) usando SOLO
Squeeze Momentum + divergencia RSI. Largo cuando el Squeeze gira (rojo oscuro) y hay
divergencia alcista de RSI; salir cuando el Squeeze gira a verde oscuro. Bruto vs neto.

Uso:  python -m trading_latino.research.scalp
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from trading_latino.data.download import cargar
from trading_latino.indicators import squeeze
from trading_latino.domain.types import ColorSqueeze


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    d = cargar("binance", "BTC", "1h")
    d.index = pd.DatetimeIndex(d["timestamp"]).tz_localize(None)
    d = d[d.index >= "2021-01-01"]
    sq = squeeze(d)
    color = sq["color"].to_numpy()
    c = d["cierre"]
    delta = c.diff(); ag = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean(); al = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rsi = (100 - 100 / (1 + ag / al.replace(0, np.nan)))
    N = 14
    div = ((c < c.shift(N)) & (rsi > rsi.shift(N)) & (rsi < 50)).rolling(7).max().fillna(0).astype(bool).to_numpy()
    cl = c.to_numpy()
    idx = d.index

    def bt(coste):
        equity = 1.0; en = None; entrada = 0.0; eq = np.ones(len(cl)); ntr = 0
        for i in range(len(cl)):
            if en is None and color[i] == ColorSqueeze.ROJO_OSCURO.value and div[i]:
                en = i; entrada = cl[i] * (1 + coste); ntr += 1
            elif en is not None and (color[i] == ColorSqueeze.VERDE_OSCURO.value or i - en >= 24):
                equity *= (cl[i] * (1 - coste)) / entrada; en = None
            eq[i] = equity * ((cl[i] / entrada) if en is not None else 1.0)
        return pd.Series(eq, index=idx), ntr

    for nombre, coste in [("BRUTO (sin costes)", 0.0), ("NETO (taker+slip ~0.07%/lado)", 0.0007)]:
        s, ntr = bt(coste)
        dd = (s / s.cummax() - 1).min()
        ins = s[s.index.year <= 2025]; out = s[s.index.year == 2026]
        rin = ins.iloc[-1] / ins.iloc[0] - 1
        rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
        print(f"  {nombre:<32}| in-sample {rin*100:+7.1f}% | 2026 {rout*100:+6.2f}% | DD {dd*100:.1f}% | trades {ntr}")


if __name__ == "__main__":
    main()
