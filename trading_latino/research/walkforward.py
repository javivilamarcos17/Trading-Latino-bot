"""
Validación walk-forward (BTC-longs): rentabilidad neta AÑO A AÑO + operaciones + drawdown.
Una estrategia robusta debe ser positiva en VARIOS años, no solo en uno.

Uso:  python -m trading_latino.research.walkforward
"""

from __future__ import annotations

import sys

import pandas as pd

from trading_latino.backtest.engine import correr, preparar
from trading_latino.reports.metrics import resumen
from trading_latino.research.experiments import _BASE, _hacer_cerebro

ANIOS = [2021, 2022, 2023, 2024, 2025]
CORREGIDA = {**_BASE, "usar_adx": True, "adx_signo": "pos"}


def _rent_por_anio(curva: pd.Series) -> dict:
    out, idx = {}, curva.index.year
    for y in ANIOS:
        seg = curva[idx == y]
        out[y] = (seg.iloc[-1] / seg.iloc[0] - 1) if len(seg) > 1 else float("nan")
    return out


def _tabla(titulo: str, datos: dict, variantes: list, mult: float = 1.0, maker: bool = False) -> None:
    coste = "MAKER (límite)" if maker else f"{mult:.2f}x (taker)"
    print(f"\n== {titulo}  [costes: {coste}] ==")
    print(f"  {'variante':<26} | " + " | ".join(f"{y:>7}" for y in ANIOS) + f" | {'TOTAL':>7} | {'ops':>5} | {'maxDD':>6}")
    print("  " + "-" * 104)
    for nombre, p in variantes:
        r = correr("BTC", "btc_longs", capital=10000, datos=datos,
                   cerebro=_hacer_cerebro(p), multiplicador_costes=mult, maker_entrada=maker)
        rpa = _rent_por_anio(r["curva"])
        rr = resumen(r)
        cells = " | ".join(f"{rpa[y]*100:>6.2f}%" for y in ANIOS)
        pos = sum(1 for y in ANIOS if rpa[y] > 0)
        marca = "  <-- robusto" if pos >= 4 else ""
        print(f"  {nombre:<26} | {cells} | {rr['rentabilidad']*100:>6.2f}% | {len(r['operaciones']):>5} | {rr['max_drawdown']*100:>5.1f}%{marca}")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    datos = preparar("BTC")
    h1 = datos["h1"]
    bh = _rent_por_anio(pd.Series(h1["cierre"].to_numpy(), index=pd.DatetimeIndex(h1["timestamp"])))
    print("Referencia comprar-y-mantener: " + " | ".join(f"{bh[y]*100:>6.1f}%" for y in ANIOS))

    # Operativa de CICLO de 1H (entra cada giro de 1H, sale en cada techo de 1H) a costes maker.
    ciclo = {**_BASE, "salida": "ciclo_1h"}
    _tabla("Operativa de ciclo 1H (varias entradas por tendencia 4H)", datos, [
        ("swing 4H+1H (agotam.)",   {**CORREGIDA, "salida": "agotamiento_impulso"}),
        ("ciclo: 1H+4H+POC+ADX",    {**ciclo, "usar_adx": True, "adx_signo": "pos"}),
        ("ciclo: 1H+POC+ADX",       {**ciclo, "usar_adx": True, "adx_signo": "pos", "usar_squeeze4h": False}),
        ("ciclo: 1H+POC",           {**ciclo, "usar_squeeze4h": False}),
        ("ciclo: 1H solo (daily)",  {**ciclo, "usar_poc": False, "usar_squeeze4h": False}),
    ], maker=True)


if __name__ == "__main__":
    main()
