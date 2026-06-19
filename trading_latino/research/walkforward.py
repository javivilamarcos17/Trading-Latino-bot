"""
Validación walk-forward (BTC-longs).

En vez de mirar un único tramo de test (que se "gasta" si lo miramos muchas veces),
evaluamos la rentabilidad neta AÑO A AÑO. Una estrategia robusta debe ser positiva (o al
menos no perder) en VARIOS años distintos, no solo en uno. Así detectamos el sobreajuste.

Uso:  python -m trading_latino.research.walkforward
"""

from __future__ import annotations

import sys

import pandas as pd

from trading_latino.backtest.engine import correr, preparar
from trading_latino.research.experiments import _BASE, _hacer_cerebro

ANIOS = [2021, 2022, 2023, 2024, 2025]


def _rent_por_anio(curva: pd.Series) -> dict[int, float]:
    out = {}
    idx_year = curva.index.year
    for y in ANIOS:
        seg = curva[idx_year == y]
        out[y] = (seg.iloc[-1] / seg.iloc[0] - 1) if len(seg) > 1 else float("nan")
    return out


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    datos = preparar("BTC")
    h1 = datos["h1"]
    bh = _rent_por_anio(pd.Series(h1["cierre"].to_numpy(), index=pd.DatetimeIndex(h1["timestamp"])))

    variantes = [
        ("ADX pend.NEG (viejo)",       {**_BASE, "usar_adx": True, "adx_signo": "neg"}),
        ("sin filtro ADX",             {**_BASE, "usar_adx": False}),
        ("ADX pend.POSITIVA (nuevo)",  {**_BASE, "usar_adx": True, "adx_signo": "pos"}),
    ]

    cab = " | ".join(f"{y:>7}" for y in ANIOS)
    print(f"  {'variante':<26} | {cab} | {'TOTAL':>7} | {'ops':>4}")
    print("  " + "-" * 92)
    # referencia comprar-y-mantener
    bh_total = h1["cierre"].iloc[-1] / h1["cierre"].iloc[0] - 1
    cells = " | ".join(f"{bh[y]*100:>6.1f}%" for y in ANIOS)
    print(f"  {'comprar y mantener':<26} | {cells} | {bh_total*100:>6.1f}% |    -")
    print("  " + "-" * 92)

    for nombre, p in variantes:
        r = correr("BTC", "btc_longs", 10000, 1.0, datos=datos, cerebro=_hacer_cerebro(p))
        rpa = _rent_por_anio(r["curva"])
        total = r["curva"].iloc[-1] / r["curva"].iloc[0] - 1
        cells = " | ".join(f"{rpa[y]*100:>6.2f}%" for y in ANIOS)
        positivos = sum(1 for y in ANIOS if rpa[y] > 0)
        marca = "  <-- robusto" if positivos >= 4 else ""
        print(f"  {nombre:<26} | {cells} | {total*100:>6.2f}% | {len(r['operaciones']):>4}{marca}")


if __name__ == "__main__":
    main()
