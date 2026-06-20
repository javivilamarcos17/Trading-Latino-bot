"""
Contribución de cada HERRAMIENTA sobre una base (Squeeze+EMA), long BTC, 4H/1H.
Añadimos una herramienta cada vez y medimos si mejora o empeora (retorno y drawdown).
Cada herramienta se añade con una hipótesis clara, no a ciegas.

Uso:  python -m trading_latino.research.tools
"""

from __future__ import annotations

import sys

from trading_latino.backtest.engine import correr, preparar
from trading_latino.reports.metrics import resumen
from trading_latino.research.experiments import _hacer_cerebro

ANIOS = [2021, 2022, 2023, 2024, 2025]
BASE = dict(semaforo="ema_cross", usar_poc=False, usar_squeeze4h=True, usar_gatillo1h=True)

VARIANTES = [
    ("BASE Squeeze+EMA",        {**BASE}),
    ("+ ADX pos",               {**BASE, "usar_adx": True, "adx_signo": "pos"}),
    ("+ POC 1.5%",              {**BASE, "usar_poc": True, "proximidad": 0.015}),
    ("+ Volumen>media",         {**BASE, "usar_volumen": True, "vol_factor": 1.0}),
    ("+ RSI<50 (1H)",           {**BASE, "usar_rsi": True, "rsi_umbral": 50}),
    ("+ cerca EMA55-4H",        {**BASE, "usar_ema55": True, "prox_ema55": 0.02}),
    ("+ gatillo GIRO 1H",       {**BASE, "gatillo_giro": True}),
    ("SIN bloqueo horario",     {**BASE, "usar_bloqueo": False}),
]


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    d = preparar("BTC")
    print("LONG BTC (4H/1H), base Squeeze+EMA, contribución de cada herramienta (costes maker):")
    print(f"  {'variante':<22} | " + " | ".join(f"{y:>6}" for y in ANIOS) + f" | {'TOTAL':>7} | {'ops':>4} | {'maxDD':>6} | {'ret/DD':>6}")
    print("  " + "-" * 104)
    for nombre, p in VARIANTES:
        r = correr("BTC", "btc_longs", capital=10000, datos=d, cerebro=_hacer_cerebro(p), maker_entrada=True)
        rr = resumen(r)
        c = r["curva"]
        cells = []
        for y in ANIOS:
            s = c[c.index.year == y]
            cells.append(f"{(s.iloc[-1]/s.iloc[0]-1)*100:>5.1f}%" if len(s) > 1 else "  -  ")
        dd = rr["max_drawdown"]
        ratio = abs(rr["rentabilidad"] / dd) if dd < 0 else 0
        print(f"  {nombre:<22} | " + " | ".join(cells) + f" | {rr['rentabilidad']*100:>6.2f}% | {len(r['operaciones']):>4} | {dd*100:>5.1f}% | {ratio:>5.2f}")


if __name__ == "__main__":
    main()
