"""
Regularidad mensual (BTC-longs, entrada corregida + salida agotamiento).

Una estrategia puede tener poco retorno pero ser MUY regular (preferible) o dar el retorno
a saltos (peor). Aquí sacamos la rentabilidad mes a mes y estadísticas de consistencia.

Nota: la REGULARIDAD (qué meses ganan/pierden/están planos) no depende del tamaño de
posición; el tamaño solo escala las magnitudes. Usamos 10% de margen para que se lea bien.

Uso:  python -m trading_latino.research.monthly
"""

from __future__ import annotations

import sys

import numpy as np

from trading_latino.backtest.engine import correr, preparar
from trading_latino.research.experiments import _BASE, _hacer_cerebro

_MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    pct = 0.10
    d = preparar("BTC")
    cer = _hacer_cerebro({**_BASE, "usar_adx": True, "adx_signo": "pos", "salida": "agotamiento_impulso"})
    r = correr("BTC", "btc_longs", 10000, 1.0, datos=d, cerebro=cer, pct_posicion=pct)
    c = r["curva"]

    g = c.groupby([c.index.year, c.index.month])
    retm = g.apply(lambda s: s.iloc[-1] / s.iloc[0] - 1)  # MultiIndex (año, mes) -> rentab.

    anios = sorted({y for (y, _) in retm.index})
    print(f"== Rentabilidad mensual (margen {pct*100:.0f}%/trade; la regularidad no cambia con el tamaño) ==")
    print("  año  | " + " | ".join(f"{m:>6}" for m in _MESES))
    print("  " + "-" * 92)
    for y in anios:
        celdas = []
        for mes in range(1, 13):
            if (y, mes) in retm.index:
                v = retm.loc[(y, mes)] * 100
                celdas.append("   ·  " if abs(v) < 0.01 else f"{v:>6.2f}")
            else:
                celdas.append("      ")
        print(f"  {y} | " + " | ".join(celdas))

    vals = retm.to_numpy() * 100
    pos = int((vals > 0.01).sum())
    neg = int((vals < -0.01).sum())
    plano = len(vals) - pos - neg

    # racha de meses negativos consecutivos
    racha = maxr = 0
    for v in vals:
        racha = racha + 1 if v < -0.01 else 0
        maxr = max(maxr, racha)

    activos = pos + neg
    print("\n-- Regularidad --")
    print(f"  Meses totales:            {len(vals)}")
    print(f"  Meses con operativa:      {activos}  (el resto, {plano}, en liquidez = 0%)")
    print(f"  Meses positivos:          {pos}  ({pos/len(vals)*100:.0f}% del total; {pos/activos*100:.0f}% de los activos)")
    print(f"  Meses negativos:          {neg}  ({neg/len(vals)*100:.0f}% del total)")
    print(f"  Media mensual:            {vals.mean():+.2f}%")
    print(f"  Desviación (volatilidad): {vals.std():.2f}%")
    print(f"  Mejor mes / peor mes:     {vals.max():+.2f}% / {vals.min():+.2f}%")
    print(f"  Peor racha negativa:      {maxr} meses seguidos")


if __name__ == "__main__":
    main()
