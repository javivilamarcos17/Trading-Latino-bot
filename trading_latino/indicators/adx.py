"""
ADX (Average Directional Index) — método de Wilder, como en TradingView (ta.dmi / ta.adx).

Mide la FUERZA de la tendencia (no la dirección). Devuelve también +DI y -DI.
- ADX subiendo por encima de 23 = movimiento con fuerza.
- ADX con pendiente negativa = debilidad / agotamiento.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_latino.config import CONFIG


def _rma(serie: pd.Series, periodo: int) -> pd.Series:
    """Suavizado de Wilder (RMA), idéntico a ta.rma de TradingView.

    alpha = 1/periodo, sembrado con la media simple de los primeros `periodo` valores.
    """
    arr = serie.to_numpy(dtype=float)
    out = np.full(len(arr), np.nan)
    if len(arr) < periodo:
        return pd.Series(out, index=serie.index)
    out[periodo - 1] = np.nanmean(arr[:periodo])
    alpha = 1.0 / periodo
    for i in range(periodo, len(arr)):
        prev = out[i - 1]
        out[i] = arr[i] * alpha + prev * (1 - alpha)
    return pd.Series(out, index=serie.index)


def adx(df: pd.DataFrame, periodo_di: int | None = None, periodo_adx: int | None = None) -> pd.DataFrame:
    """Calcula ADX, +DI y -DI. Devuelve un DataFrame con columnas: adx, di_pos, di_neg."""
    periodo_di = periodo_di or CONFIG.indicadores.ADX_DI_LONGITUD
    periodo_adx = periodo_adx or CONFIG.indicadores.ADX_PERIODO

    h, l, c = df["maximo"], df["minimo"], df["cierre"]
    prev_c = c.shift(1)

    # True Range
    tr = pd.concat([(h - l), (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)

    # Movimiento direccional
    up = h.diff()             # high - high previo
    down = -l.diff()          # low previo - low
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=df.index)

    # Suavizado de Wilder
    tr_s = _rma(tr, periodo_di)
    plus_di = 100.0 * _rma(plus_dm, periodo_di) / tr_s
    minus_di = 100.0 * _rma(minus_dm, periodo_di) / tr_s

    suma = (plus_di + minus_di).replace(0.0, np.nan)
    dx = 100.0 * (plus_di - minus_di).abs() / suma
    adx_serie = _rma(dx, periodo_adx)

    return pd.DataFrame({"adx": adx_serie, "di_pos": plus_di, "di_neg": minus_di})
