"""
Perfil de Volumen — POC (Point of Control) aproximado.

El POC es el precio donde más volumen se ha negociado en una ventana: el "muro" real de
soporte/resistencia. El perfil exacto necesitaría datos intra-vela que no tenemos, así que
APROXIMAMOS repartiendo el volumen de cada vela por el rango [mínimo, máximo] que cubrió.

⚠️ Aproximación (🔎): la validaremos contra el VPVR de TradingView en su momento. Para el
backtest sirve como zona de referencia; no pretende ser idéntica al tick.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_latino.config import CONFIG


def poc(df: pd.DataFrame, ventana: int | None = None, bins: int = 50) -> pd.Series:
    """POC móvil: para cada vela, precio de mayor volumen en las últimas `ventana` velas.

    Reparte el volumen de cada vela uniformemente entre los `bins` de precio que cubre su
    rango [mínimo, máximo]. Devuelve una Series con el precio del bin más votado.
    """
    ventana = ventana or CONFIG.indicadores.POC_VENTANA_VELAS
    lo = df["minimo"].to_numpy(dtype=float)
    hi = df["maximo"].to_numpy(dtype=float)
    vol = df["volumen"].to_numpy(dtype=float)
    n = len(df)
    out = np.full(n, np.nan)

    for t in range(ventana - 1, n):
        ini = t - ventana + 1
        w_lo, w_hi, w_vol = lo[ini : t + 1], hi[ini : t + 1], vol[ini : t + 1]
        precio_min, precio_max = w_lo.min(), w_hi.max()
        if precio_max <= precio_min:
            out[t] = precio_min
            continue
        bordes = np.linspace(precio_min, precio_max, bins + 1)
        centros = (bordes[:-1] + bordes[1:]) / 2
        acumulado = np.zeros(bins)
        for vlo, vhi, vv in zip(w_lo, w_hi, w_vol):
            # bins que toca esta vela; reparte su volumen entre ellos
            i0 = np.searchsorted(bordes, vlo, side="right") - 1
            i1 = np.searchsorted(bordes, vhi, side="right") - 1
            i0 = max(i0, 0)
            i1 = min(i1, bins - 1)
            if i1 < i0:
                continue
            acumulado[i0 : i1 + 1] += vv / (i1 - i0 + 1)
        out[t] = centros[int(acumulado.argmax())]

    return pd.Series(out, index=df.index, name="poc")
