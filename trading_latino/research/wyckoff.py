"""
Wyckoff mecanizado: el SPRING (sacudida / falsa ruptura del soporte que se recupera = caza de
liquidez institucional). Entrada larga tras el Spring. Variante con volumen (esfuerzo). BTC diario.
Validado en 2026.  Uso:  python -m trading_latino.research.wyckoff
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from trading_latino.data.download import cargar

VENTANA = 20   # rango de soporte/resistencia
HOLD = 10      # días de mantenimiento tras el Spring


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    for activo in ["BTC", "ETH", "SOL"]:
        d = cargar("binance", activo, "1d")
        d.index = pd.DatetimeIndex(d["timestamp"]).tz_localize(None)
        d = d[d.index >= "2021-01-01"]
        lo, hi, cl, vol = d["minimo"], d["maximo"], d["cierre"], d["volumen"]
        soporte = lo.rolling(VENTANA).min().shift(1)
        volmedia = vol.rolling(VENTANA).mean()

        # Spring: el mínimo perfora el soporte pero el cierre lo recupera (falsa ruptura).
        spring = (lo < soporte) & (cl > soporte)
        spring_vol = spring & (vol > volmedia)   # con esfuerzo (volumen alto)

        def backtest(senal, nombre):
            cap = 10000.0
            eq_list = []
            i = 0
            n = len(d)
            idx = d.index
            cierre = cl.to_numpy()
            sig = senal.to_numpy()
            equity = cap
            curva = np.full(n, cap)
            en = -1   # índice de salida pendiente
            entrada = 0.0
            for i in range(n):
                if en == -1 and sig[i]:
                    en = min(i + HOLD, n - 1)
                    entrada = cierre[i]
                if en != -1 and i == en:
                    equity *= cierre[i] / entrada
                    en = -1
                curva[i] = equity * (cierre[i] / entrada if en != -1 else 1.0)
            s = pd.Series(curva, index=idx)
            dd = (s / s.cummax() - 1).min()
            ins = s[s.index.year <= 2025]; out = s[s.index.year == 2026]
            rin = ins.iloc[-1] / ins.iloc[0] - 1
            rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
            cagr = (1 + rin) ** (1 / 4.99) - 1
            print(f"  [{activo}] {nombre:<20}| señales {int(senal.sum()):3d} | CAGR {cagr*100:+6.1f}%/a | 2026 {rout*100:+6.2f}% | DD {dd*100:.1f}%")

        backtest(spring, "Spring")
        backtest(spring_vol, "Spring + volumen")


if __name__ == "__main__":
    main()
