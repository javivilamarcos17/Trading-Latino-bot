"""
Edge DISTINTO: seguimiento de tendencia (trend-following), no el patrón de retroceso.

Regla simple y robusta (pocos parámetros): estar LARGO mientras el precio (diario) esté por
encima de su EMA55 diaria; salir cuando la pierde. Se monta en la tendencia y la aguanta.
Probado en BTC y en cartera, in-sample (2021-25) vs hold-out 2026.

Uso:  python -m trading_latino.research.trend
"""

from __future__ import annotations

import math
import sys

from trading_latino.backtest.engine import correr, preparar
from trading_latino.config import CONFIG
from trading_latino.domain.types import Accion, Decision, EstadoMercado, Posicion
from trading_latino.research.portfolio import correr_cartera


def _num(x):
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def cerebro_trend(estado: EstadoMercado, posicion: Posicion | None) -> Decision:
    d = estado.diario
    sube = _num(d.cierre) and _num(d.ema_lenta) and d.cierre > d.ema_lenta
    if posicion is None:
        if sube:
            return Decision(Accion.ABRIR_LARGO, "tendencia: precio sobre EMA55 diaria",
                            stop_loss=estado.precio * 0.75)   # stop amplio; manda la salida por tendencia
        return Decision(Accion.NADA, "")
    if not sube:
        return Decision(Accion.CERRAR, "fin de tendencia (precio bajo EMA55 diaria)")
    return Decision(Accion.NADA, "")


def _rep(nombre, c, ops):
    ins = c[c.index.year <= 2025]; out = c[c.index.year == 2026]
    rin = ins.iloc[-1] / ins.iloc[0] - 1
    rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
    dd = ((c - c.cummax()) / c.cummax()).min()
    cagr_in = (1 + rin) ** (1 / 4.99) - 1
    print(f"{nombre:<20}| in 21-25 {rin*100:+7.1f}% (CAGR {cagr_in*100:+5.1f}%/a) | 2026 {rout*100:+6.2f}% | DD {dd*100:5.1f}% | ops {ops}")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    print("TREND-FOLLOWING (largo mientras precio>EMA55 diaria), costes maker:")
    for s in ["BTC", "ETH", "SOL"]:
        r = correr(s, "btc_longs", capital=10000, datos=preparar(s), cerebro=cerebro_trend, maker_entrada=True)
        _rep(s, r["curva"], len(r["operaciones"]))

    uni = list(CONFIG.altcoins) + ["BTC"]
    r = correr_cartera(uni, maker_entrada=True, max_posiciones=8, cerebro=cerebro_trend)
    _rep("CARTERA " + str(len(uni)), r["curva"], len(r["operaciones"]))


if __name__ == "__main__":
    main()
