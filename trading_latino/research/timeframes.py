"""
Barrido de MARCOS TEMPORALES (BTC-longs, estrategia de producción, costes maker).

Misma lógica de Merino, pero desplazando las temporalidades (roles) para operar más rápido.
Walk-forward año a año. Uso:  python -m trading_latino.research.timeframes
"""

from __future__ import annotations

import sys

import pandas as pd

from trading_latino.backtest.engine import correr, preparar
from trading_latino.reports.metrics import resumen

ANIOS = [2021, 2022, 2023, 2024, 2025]

MARCOS = {
    "M0 swing 1w/1d/4h/1h":  {"semanal": "1w", "diario": "1d", "h4": "4h", "h1": "1h"},
    "M1 intra 1d/4h/1h/15m": {"semanal": "1d", "diario": "4h", "h4": "1h", "h1": "15m"},
    "M2 intra 1d/4h/30m/15m":{"semanal": "1d", "diario": "4h", "h4": "30m", "h1": "15m"},
    "M3 scalp 4h/1h/15m/5m": {"semanal": "4h", "diario": "1h", "h4": "15m", "h1": "5m"},
}


def _rpa(curva: pd.Series) -> dict:
    out, idx = {}, curva.index.year
    for y in ANIOS:
        s = curva[idx == y]
        out[y] = (s.iloc[-1] / s.iloc[0] - 1) if len(s) > 1 else float("nan")
    return out


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    print("Estrategia de producción (entrada corregida + agotamiento), costes MAKER, por año:")
    print(f"  {'marco':<24} | " + " | ".join(f"{y:>7}" for y in ANIOS) + f" | {'TOTAL':>7} | {'ops':>5} | {'maxDD':>6}")
    print("  " + "-" * 104)
    for nombre, tfs in MARCOS.items():
        d = preparar("BTC", tfs=tfs)
        r = correr("BTC", "btc_longs", capital=10000, datos=d, maker_entrada=True)
        rpa = _rpa(r["curva"])
        rr = resumen(r)
        cells = " | ".join(f"{rpa[y]*100:>6.2f}%" for y in ANIOS)
        pos = sum(1 for y in ANIOS if rpa[y] > 0)
        marca = "  <-- robusto" if pos >= 4 else ""
        print(f"  {nombre:<24} | {cells} | {rr['rentabilidad']*100:>6.2f}% | {len(r['operaciones']):>5} | {rr['max_drawdown']*100:>5.1f}%{marca}")


if __name__ == "__main__":
    main()
