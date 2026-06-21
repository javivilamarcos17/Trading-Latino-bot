"""
Diagnóstico del embudo de entrada (BTC-longs).

¿Por qué solo 42 operaciones en 5 años? Esto cuenta, vela a vela, cuántas pasan cada
condición de entrada (de forma acumulada), para ver QUÉ filtro es el cuello de botella.
No es exactamente nº de trades (no se puede entrar estando ya dentro), pero muestra con
qué frecuencia APARECE el setup.

Uso:  python -m trading_latino.backtest.diagnose_entry
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from trading_latino.config import CONFIG
from trading_latino.backtest.engine import preparar
from trading_latino.domain.types import ColorSqueeze


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    e = CONFIG.estrategia
    d = preparar("BTC")
    h1, master, al = d["h1"], d["master"], d["al"]

    precio = h1["apertura"].to_numpy()
    ema_r_d = al["1d"]["ema_rapida"].to_numpy()
    ema_l_d = al["1d"]["ema_lenta"].to_numpy()
    poc4 = al["4h"]["poc"].to_numpy()
    color4 = al["4h"]["sqz_color"].to_numpy()
    pend4 = al["4h"]["adx_pendiente"].to_numpy()
    color1 = al["1h"]["sqz_color"].to_numpy()

    lt = master.tz_convert("Europe/Madrid")
    minutos = lt.hour * 60 + lt.minute
    bloqueo = (minutos >= 15 * 60 + 15) & (minutos <= 15 * 60 + 45)

    n = len(master)
    ro = ColorSqueeze.ROJO_OSCURO.value

    with np.errstate(invalid="ignore"):
        c1 = ema_r_d > ema_l_d                                   # semáforo diario alcista
        c2 = np.abs(precio - poc4) / poc4 <= e.PROXIMIDAD_POC    # cerca del POC 4H
        c3 = color4 == ro                                        # Squeeze 4H rojo oscuro
        c4 = pend4 < 0                                           # ADX 4H pendiente negativa
        c5 = color1 == ro                                        # gatillo 1H rojo oscuro
        c6 = ~np.asarray(bloqueo)                                # fuera de bloqueo horario

    etapas = [
        ("Total de velas 1h", np.ones(n, dtype=bool)),
        ("1) semáforo diario alcista", c1),
        ("2) + cerca del POC 4H (<=1.5%)", c1 & c2),
        ("3) + Squeeze 4H rojo oscuro", c1 & c2 & c3),
        ("4) + ADX 4H pendiente negativa", c1 & c2 & c3 & c4),
        ("5) + gatillo 1H rojo oscuro", c1 & c2 & c3 & c4 & c5),
        ("6) + fuera de bloqueo horario", c1 & c2 & c3 & c4 & c5 & c6),
    ]

    print("== Embudo de entrada BTC-longs (velas que pasan cada filtro, acumulado) ==")
    for nombre, mask in etapas:
        cuenta = int(np.nansum(mask))
        print(f"  {nombre:<38} {cuenta:>7}  ({cuenta/n*100:5.1f}% del total)")

    # ¿Cuál es el filtro más restrictivo por sí solo?
    print("\n-- Cada filtro por separado (sobre el total) --")
    for nombre, mask in [("semáforo diario alcista", c1), ("cerca del POC 4H", c2),
                         ("Squeeze 4H rojo oscuro", c3), ("ADX 4H pendiente neg.", c4),
                         ("gatillo 1H rojo oscuro", c5)]:
        cuenta = int(np.nansum(mask))
        print(f"  {nombre:<28} {cuenta/n*100:5.1f}% de las velas")


if __name__ == "__main__":
    main()
