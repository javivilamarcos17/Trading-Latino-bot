"""Tests de los indicadores (Fase 2).

Comprueban propiedades matemáticas conocidas. La validación definitiva (que coinciden con
TradingView en fechas concretas) la hacemos aparte, con el dueño mirando su gráfico.
"""

import numpy as np
import pandas as pd

from trading_latino.indicators.ema import ema
from trading_latino.indicators.adx import adx
from trading_latino.indicators.squeeze import squeeze, _linreg_endpoint
from trading_latino.indicators.volume_profile import poc
from trading_latino.domain.types import ColorSqueeze


def _df_tendencia_alcista(n=200):
    close = pd.Series(np.linspace(100.0, 200.0, n))
    return pd.DataFrame({
        "apertura": close, "maximo": close + 1.0, "minimo": close - 1.0,
        "cierre": close, "volumen": np.ones(n),
    })


# ---------------- EMA ----------------
def test_ema_coincide_con_ewm():
    s = pd.Series(np.arange(1, 21, dtype=float))
    assert np.allclose(ema(s, 5), s.ewm(span=5, adjust=False).mean())


def test_ema_de_serie_constante_es_constante():
    s = pd.Series([7.0] * 30)
    assert np.allclose(ema(s, 10), 7.0)


# ---------------- linreg (corazón del Squeeze) ----------------
def test_linreg_sobre_recta_perfecta_devuelve_la_recta():
    # La regresión de una recta exacta devuelve el valor actual de la recta.
    s = pd.Series(np.arange(50) * 2.0 + 3.0)
    lr = _linreg_endpoint(s, 10)
    assert np.allclose(lr.iloc[9:], s.iloc[9:])


# ---------------- ADX ----------------
def test_adx_en_rango_0_100_y_direccion_correcta():
    out = adx(_df_tendencia_alcista()).dropna()
    assert (out["adx"] >= 0).all() and (out["adx"] <= 100).all()
    # en tendencia alcista, +DI debe dominar sobre -DI
    assert out["di_pos"].iloc[-1] > out["di_neg"].iloc[-1]


# ---------------- Squeeze ----------------
def test_squeeze_columnas_y_colores_validos():
    rng = np.random.default_rng(0)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, 150)))
    df = pd.DataFrame({
        "apertura": close, "maximo": close + 1, "minimo": close - 1,
        "cierre": close, "volumen": np.ones(150),
    })
    out = squeeze(df)
    assert {"valor", "color", "squeeze_on", "squeeze_off"}.issubset(out.columns)
    validos = {c.value for c in ColorSqueeze}
    assert set(out["color"].dropna().unique()).issubset(validos)


def test_squeeze_logica_de_color():
    rng = np.random.default_rng(1)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, 200)))
    df = pd.DataFrame({
        "apertura": close, "maximo": close + 1, "minimo": close - 1,
        "cierre": close, "volumen": np.ones(200),
    })
    out = squeeze(df)
    v, prev, col = out["valor"], out["valor"].shift(1), out["color"]
    # valor>0 y subiendo => verde_claro ; valor<=0 y bajando => rojo_claro
    m_vc = (v > 0) & (v > prev)
    m_rc = (v <= 0) & (v < prev)
    assert (col[m_vc] == ColorSqueeze.VERDE_CLARO.value).all()
    assert (col[m_rc] == ColorSqueeze.ROJO_CLARO.value).all()


# ---------------- POC ----------------
def test_poc_detecta_concentracion_de_volumen():
    n = 60
    close = pd.Series([100.0] * n)
    df = pd.DataFrame({
        "apertura": close, "maximo": close + 0.5, "minimo": close - 0.5,
        "cierre": close, "volumen": np.ones(n),
    })
    p = poc(df, ventana=30, bins=20).dropna()
    assert np.allclose(p, 100.0, atol=0.5)
