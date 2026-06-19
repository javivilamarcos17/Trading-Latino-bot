"""Métricas del backtest, todas en NETO (después de comisiones + funding + slippage)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def resumen(resultado: dict) -> dict:
    """Calcula las métricas clave a partir del resultado de backtest.engine.correr()."""
    ops = resultado["operaciones"]
    curva: pd.Series = resultado["curva"]
    capital = resultado["capital_inicial"]
    eq_final = float(curva.iloc[-1]) if len(curva) else capital

    pnls = np.array([o.pnl_neto for o in ops], dtype=float)
    n = len(pnls)
    ganadoras = pnls[pnls > 0]
    perdedoras = pnls[pnls <= 0]
    ganado = float(ganadoras.sum())
    perdido = float(-perdedoras.sum())

    # drawdown máximo sobre la curva marcada a mercado
    pico = curva.cummax()
    dd = (curva - pico) / pico
    max_dd = float(dd.min()) if len(curva) else 0.0

    # racha máxima de pérdidas consecutivas
    racha = max_racha = 0
    for p in pnls:
        racha = racha + 1 if p <= 0 else 0
        max_racha = max(max_racha, racha)

    return {
        "operaciones": n,
        "ganadoras": int(len(ganadoras)),
        "perdedoras": int(len(perdedoras)),
        "win_rate": (len(ganadoras) / n) if n else 0.0,
        "rentabilidad": (eq_final - capital) / capital,
        "equity_final": eq_final,
        "profit_factor": (ganado / perdido) if perdido > 0 else float("inf"),
        "ganancia_media": float(ganadoras.mean()) if len(ganadoras) else 0.0,
        "perdida_media": float(perdedoras.mean()) if len(perdedoras) else 0.0,
        "max_drawdown": max_dd,
        "racha_perdedora_max": max_racha,
        "comisiones_total": float(sum(o.comisiones for o in ops)),
        "funding_total": float(sum(o.funding for o in ops)),
    }


def formatear(resultado: dict, r: dict) -> str:
    """Devuelve el resumen en texto legible."""
    pct = lambda x: f"{x*100:.2f}%"
    return (
        f"  Operaciones:        {r['operaciones']}  ({r['ganadoras']} ganadoras / {r['perdedoras']} perdedoras)\n"
        f"  Win rate:           {pct(r['win_rate'])}\n"
        f"  Rentabilidad NETA:  {pct(r['rentabilidad'])}   (capital {resultado['capital_inicial']:.0f} -> {r['equity_final']:.0f})\n"
        f"  Profit factor:      {r['profit_factor']:.2f}\n"
        f"  Drawdown máximo:    {pct(r['max_drawdown'])}\n"
        f"  Racha perdedora:    {r['racha_perdedora_max']} seguidas\n"
        f"  Ganancia media:     {r['ganancia_media']:.2f}   Pérdida media: {r['perdida_media']:.2f}\n"
        f"  Costes pagados:     comisiones {r['comisiones_total']:.2f} + funding {r['funding_total']:.2f}"
    )
