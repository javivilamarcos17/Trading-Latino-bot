"""
Media Móvil Exponencial (EMA).

Replica `ta.ema` de TradingView: factor alpha = 2/(periodo+1), sembrada con el primer
valor de la serie (equivalente a pandas .ewm(span=periodo, adjust=False)).
"""

from __future__ import annotations

import pandas as pd

from trading_latino.config import CONFIG


def ema(serie: pd.Series, periodo: int) -> pd.Series:
    """EMA de una serie. Coincide con ta.ema de TradingView."""
    return serie.ewm(span=periodo, adjust=False).mean()


def anadir_emas(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una copia del df con las columnas ema_rapida (10) y ema_lenta (55)."""
    out = df.copy()
    out["ema_rapida"] = ema(df["cierre"], CONFIG.indicadores.EMA_RAPIDA)
    out["ema_lenta"] = ema(df["cierre"], CONFIG.indicadores.EMA_LENTA)
    return out
