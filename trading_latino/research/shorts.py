"""
Ablación del módulo SHORT sobre las altcoins (solo cortos), año a año.
Objetivo: encontrar qué condiciones capturan los OSOS (2022/2023). El short espejo no lo hacía.

Uso:  python -m trading_latino.research.shorts
"""

from __future__ import annotations

import sys

from trading_latino.config import CONFIG
from trading_latino.research.experiments import _hacer_cerebro_corto
from trading_latino.research.portfolio import correr_cartera

ANIOS = [2021, 2022, 2023, 2024, 2025]
_SBASE = dict(semaforo="ema_cross", usar_poc=True, proximidad=0.015, usar_squeeze4h=True, usar_gatillo1h=True)

VARIANTES = [
    ("base espejo (ADX pos)",   {**_SBASE, "usar_adx": True, "adx_signo": "pos"}),
    ("sin ADX",                 {**_SBASE, "usar_adx": False}),
    ("ADX neg",                 {**_SBASE, "usar_adx": True, "adx_signo": "neg"}),
    ("sin POC",                 {**_SBASE, "usar_poc": False, "usar_adx": False}),
    ("sin squeeze4h",           {**_SBASE, "usar_squeeze4h": False, "usar_adx": False}),
    ("sin gatillo 1H",          {**_SBASE, "usar_gatillo1h": False, "usar_adx": False}),
    ("POC 3% sin ADX",          {**_SBASE, "proximidad": 0.03, "usar_adx": False}),
]


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    alts = list(CONFIG.altcoins)
    print("Ablación SHORT sobre 20 alts (solo cortos), costes maker, por año:")
    print(f"  {'variante':<22} | " + " | ".join(f"{y:>7}" for y in ANIOS) + f" | {'TOTAL':>7} | {'ops':>4} | {'maxDD':>6}")
    print("  " + "-" * 100)
    for nombre, p in VARIANTES:
        r = correr_cartera(alts, maker_entrada=True, max_posiciones=8, cerebro=_hacer_cerebro_corto(p))
        c = r["curva"]
        tot = c.iloc[-1] / r["capital"] - 1
        dd = ((c - c.cummax()) / c.cummax()).min()
        cells = []
        for y in ANIOS:
            s = c[c.index.year == y]
            cells.append(f"{(s.iloc[-1]/s.iloc[0]-1)*100:>6.2f}%" if len(s) > 1 else "   -   ")
        print(f"  {nombre:<22} | " + " | ".join(cells) + f" | {tot*100:>6.2f}% | {len(r['operaciones']):>4} | {dd*100:>5.1f}%")


if __name__ == "__main__":
    main()
