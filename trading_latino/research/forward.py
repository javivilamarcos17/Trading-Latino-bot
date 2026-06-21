"""
Construcción incremental ("poco a poco") del LONG en BTC (4H/1H).

Empezamos con el NÚCLEO (solo Squeeze multi-temporal) y añadimos una pieza cada vez
(ADX, EMA, POC) para ver QUÉ aporta cada una. Walk-forward año a año, costes maker.

Uso:  python -m trading_latino.research.forward
"""

from __future__ import annotations

import sys

from trading_latino.backtest.engine import correr, preparar
from trading_latino.reports.metrics import resumen
from trading_latino.research.experiments import _hacer_cerebro

ANIOS = [2021, 2022, 2023, 2024, 2025]


def _rpa(c) -> dict:
    out = {}
    for y in ANIOS:
        s = c[c.index.year == y]
        out[y] = (s.iloc[-1] / s.iloc[0] - 1) if len(s) > 1 else float("nan")
    return out


# Núcleo: solo Squeeze 4H + gatillo 1H (sin EMA, sin ADX, sin POC).
NUCLEO = dict(semaforo="ninguno", usar_poc=False, usar_squeeze4h=True, usar_gatillo1h=True)

PASOS = [
    ("S0  solo Squeeze 4H+1H",      {**NUCLEO}),
    ("S1  +ADX pos",                {**NUCLEO, "usar_adx": True, "adx_signo": "pos"}),
    ("S1  +ADX neg",                {**NUCLEO, "usar_adx": True, "adx_signo": "neg"}),
    ("S2  +EMA (semáforo)",         {**NUCLEO, "semaforo": "ema_cross"}),
    ("S3  +EMA +ADX pos",           {**NUCLEO, "semaforo": "ema_cross", "usar_adx": True, "adx_signo": "pos"}),
    ("S4  +EMA +ADX +POC (full)",   {**NUCLEO, "semaforo": "ema_cross", "usar_adx": True, "adx_signo": "pos", "usar_poc": True, "proximidad": 0.015}),
]


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    d = preparar("BTC")
    print("LONG en BTC (4H/1H), construcción incremental, costes maker, por año:")
    print(f"  {'paso':<26} | " + " | ".join(f"{y:>7}" for y in ANIOS) + f" | {'TOTAL':>7} | {'ops':>5} | {'maxDD':>6}")
    print("  " + "-" * 104)
    for nombre, p in PASOS:
        r = correr("BTC", "btc_longs", capital=10000, datos=d, cerebro=_hacer_cerebro(p), maker_entrada=True)
        rr = resumen(r)
        rpa = _rpa(r["curva"])
        cells = " | ".join(f"{rpa[y]*100:>6.2f}%" for y in ANIOS)
        pos = sum(1 for y in ANIOS if rpa[y] > 0)
        marca = "  <-- robusto" if pos >= 4 else ""
        print(f"  {nombre:<26} | {cells} | {rr['rentabilidad']*100:>6.2f}% | {len(r['operaciones']):>5} | {rr['max_drawdown']*100:>5.1f}%{marca}")


if __name__ == "__main__":
    main()
