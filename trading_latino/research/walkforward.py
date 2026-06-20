"""
Validación walk-forward (BTC-longs).

Evaluamos la rentabilidad neta AÑO A AÑO. Una estrategia robusta debe ser positiva (o al
menos no perder) en VARIOS años, no solo en uno. Así detectamos el sobreajuste.

Uso:  python -m trading_latino.research.walkforward
"""

from __future__ import annotations

import sys

import pandas as pd

from trading_latino.backtest.engine import correr, preparar
from trading_latino.research.experiments import _BASE, _hacer_cerebro

ANIOS = [2021, 2022, 2023, 2024, 2025]

# Entrada ya corregida (ADX pendiente positiva).
CORREGIDA = {**_BASE, "usar_adx": True, "adx_signo": "pos"}


def _rent_por_anio(curva: pd.Series) -> dict:
    out, idx = {}, curva.index.year
    for y in ANIOS:
        seg = curva[idx == y]
        out[y] = (seg.iloc[-1] / seg.iloc[0] - 1) if len(seg) > 1 else float("nan")
    return out


def _tabla(titulo: str, datos: dict, variantes: list) -> None:
    print(f"\n== {titulo} ==")
    cab = " | ".join(f"{y:>7}" for y in ANIOS)
    print(f"  {'variante':<26} | {cab} | {'TOTAL':>7} | {'ops':>4}")
    print("  " + "-" * 92)
    for nombre, p in variantes:
        r = correr("BTC", "btc_longs", 10000, 1.0, datos=datos, cerebro=_hacer_cerebro(p))
        rpa = _rent_por_anio(r["curva"])
        total = r["curva"].iloc[-1] / r["curva"].iloc[0] - 1
        cells = " | ".join(f"{rpa[y]*100:>6.2f}%" for y in ANIOS)
        pos = sum(1 for y in ANIOS if rpa[y] > 0)
        marca = "  <-- robusto (4+/5)" if pos >= 4 else ""
        print(f"  {nombre:<26} | {cells} | {total*100:>6.2f}% | {len(r['operaciones']):>4}{marca}")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    datos = preparar("BTC")
    h1 = datos["h1"]
    bh = _rent_por_anio(pd.Series(h1["cierre"].to_numpy(), index=pd.DatetimeIndex(h1["timestamp"])))
    cells = " | ".join(f"{bh[y]*100:>6.1f}%" for y in ANIOS)
    bh_total = h1["cierre"].iloc[-1] / h1["cierre"].iloc[0] - 1
    print(f"Referencia comprar-y-mantener: {cells} | total {bh_total*100:.1f}%")

    _tabla("Reglas de salida sobre la ENTRADA CORREGIDA (ADX pendiente positiva)", datos, [
        ("salida: agotamiento",   {**CORREGIDA, "salida": "agotamiento_impulso"}),
        ("salida: trailing",      {**CORREGIDA, "salida": "trailing"}),
        ("salida: multiplo_r",    {**CORREGIDA, "salida": "multiplo_r"}),
        ("salida: siguiente_poc", {**CORREGIDA, "salida": "siguiente_poc"}),
    ])


if __name__ == "__main__":
    main()
