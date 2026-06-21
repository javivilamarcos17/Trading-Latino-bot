"""
Squeeze Momentum Indicator (LazyBear) — réplica exacta del script de TradingView.

Devuelve:
- valor: el histograma de momento (linreg de la des-media del precio).
- color: uno de los 4 estados (verde_claro/oscuro, rojo_claro/oscuro) — la lectura de Merino.
- squeeze_on / squeeze_off: si las Bollinger están dentro de las Keltner (compresión).

Lógica de color (idéntica al Pine de LazyBear):
- valor > 0:  sube respecto a la barra previa -> verde_claro ; baja -> verde_oscuro
- valor <= 0: baja respecto a la barra previa -> rojo_claro  ; sube/igual -> rojo_oscuro
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_latino.config import CONFIG
from trading_latino.domain.types import ColorSqueeze


def _linreg_endpoint(serie: pd.Series, periodo: int) -> pd.Series:
    """Valor de la recta de regresión lineal en la barra actual (ta.linreg(src, periodo, 0)).

    Para una ventana de longitud L con x = 0..L-1, el valor predicho en x = L-1 es una
    combinación lineal fija de los valores de la ventana: lo precalculamos como pesos.
    """
    L = periodo
    x = np.arange(L, dtype=float)
    xbar = x.mean()
    sxx = ((x - xbar) ** 2).sum()
    x_end = L - 1
    pesos = 1.0 / L + (x - xbar) * (x_end - xbar) / sxx
    return serie.rolling(L).apply(lambda w: float(np.dot(pesos, w)), raw=True)


def squeeze(
    df: pd.DataFrame,
    length: int | None = None,
    mult: float | None = None,
    length_kc: int | None = None,
    mult_kc: float | None = None,
) -> pd.DataFrame:
    """Calcula el Squeeze Momentum (LazyBear). Columnas: valor, color, squeeze_on, squeeze_off."""
    ind = CONFIG.indicadores
    length = length or ind.BB_LONGITUD
    mult = mult or ind.BB_MULT
    length_kc = length_kc or ind.KC_LONGITUD
    mult_kc = mult_kc or ind.KC_MULT

    src, h, l = df["cierre"], df["maximo"], df["minimo"]

    # --- Histograma de momento ---
    maximo_n = h.rolling(length_kc).max()
    minimo_n = l.rolling(length_kc).min()
    sma_close = src.rolling(length_kc).mean()
    media = ((maximo_n + minimo_n) / 2 + sma_close) / 2     # avg(avg(highest,lowest), sma(close))
    valor = _linreg_endpoint(src - media, length_kc)

    # --- Color (4 estados) ---
    prev = valor.shift(1)
    color = np.where(
        valor > 0,
        np.where(valor > prev, ColorSqueeze.VERDE_CLARO.value, ColorSqueeze.VERDE_OSCURO.value),
        np.where(valor < prev, ColorSqueeze.ROJO_CLARO.value, ColorSqueeze.ROJO_OSCURO.value),
    )
    color = pd.Series(color, index=df.index, dtype=object)
    color[valor.isna()] = None   # sin color durante el calentamiento

    # --- Estado de compresión: Bollinger dentro/fuera de Keltner ---
    basis = src.rolling(length).mean()
    dev = mult * src.rolling(length).std(ddof=0)            # Pine usa desviación poblacional
    upper_bb, lower_bb = basis + dev, basis - dev

    ma = src.rolling(length_kc).mean()
    prev_c = src.shift(1)
    tr = pd.concat([(h - l), (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    rangema = tr.rolling(length_kc).mean()
    upper_kc, lower_kc = ma + rangema * mult_kc, ma - rangema * mult_kc

    sqz_on = (lower_bb > lower_kc) & (upper_bb < upper_kc)
    sqz_off = (lower_bb < lower_kc) & (upper_bb > upper_kc)

    return pd.DataFrame(
        {"valor": valor, "color": color, "squeeze_on": sqz_on, "squeeze_off": sqz_off},
        index=df.index,
    )
