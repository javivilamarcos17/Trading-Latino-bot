"""
Bake-off de estrategias (dentro y fuera del método Merino). Todas validadas en hold-out 2026.
Eficiente: una pasada, tabla compacta. Uso:  python -m trading_latino.research.bakeoff
"""

from __future__ import annotations

import math
import sys

from trading_latino.backtest.engine import correr, preparar
from trading_latino.domain.types import Accion, Decision
from trading_latino.research.experiments import _hacer_cerebro


def _n(x):
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def _hold(estado, pos):
    return Decision(Accion.NADA, "") if pos else Decision(Accion.ABRIR_LARGO, "hold", stop_loss=estado.precio * 0.5)


def _trend(cond):
    def cer(estado, pos):
        ok = cond(estado)
        if pos is None:
            return Decision(Accion.ABRIR_LARGO, "t", stop_loss=estado.precio * 0.7) if ok else Decision(Accion.NADA, "")
        return Decision(Accion.NADA, "") if ok else Decision(Accion.CERRAR, "fin")
    return cer


def _rsi_mr(estado, pos):
    r = estado.h4.rsi
    if pos is None:
        return Decision(Accion.ABRIR_LARGO, "mr", stop_loss=estado.precio * 0.85) if (_n(r) and r < 30) else Decision(Accion.NADA, "")
    return Decision(Accion.CERRAR, "mr-exit") if (_n(r) and r > 55) else Decision(Accion.NADA, "")


_MERINO = _hacer_cerebro(dict(semaforo="ema_cross", usar_squeeze4h=True, usar_gatillo1h=True, usar_poc=True, proximidad=0.015, usar_vwap=True))

ESTR = {
    "buy & hold":          _hold,
    "EMA55 diaria":        _trend(lambda e: _n(e.diario.cierre) and _n(e.diario.ema_lenta) and e.diario.cierre > e.diario.ema_lenta),
    "EMA55 SEMANAL":       _trend(lambda e: _n(e.semanal.cierre) and _n(e.semanal.ema_lenta) and e.semanal.cierre > e.semanal.ema_lenta),
    "cruce EMA10>55 d":    _trend(lambda e: _n(e.diario.ema_rapida) and _n(e.diario.ema_lenta) and e.diario.ema_rapida > e.diario.ema_lenta),
    "RSI mean-rev":        _rsi_mr,
    "EMA d + semanal":     _trend(lambda e: _n(e.diario.cierre) and _n(e.diario.ema_lenta) and _n(e.semanal.cierre) and _n(e.semanal.ema_lenta) and e.diario.cierre > e.diario.ema_lenta and e.semanal.cierre > e.semanal.ema_lenta),
    "Merino long":         _MERINO,
}

_TREND_D = _trend(lambda e: _n(e.diario.cierre) and _n(e.diario.ema_lenta) and e.diario.cierre > e.diario.ema_lenta)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    d = preparar("BTC")
    print("BTC, costes maker | in-sample 2021-25 (CAGR) | hold-out 2026 | maxDD | ops")
    for n, cer in ESTR.items():
        r = correr("BTC", "btc_longs", capital=10000, datos=d, cerebro=cer, maker_entrada=True)
        c = r["curva"]
        ins = c[c.index.year <= 2025]; out = c[c.index.year == 2026]
        rin = ins.iloc[-1] / ins.iloc[0] - 1
        rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
        dd = ((c - c.cummax()) / c.cummax()).min()
        print(f"  {n:<18}| {rin*100:+7.1f}% (CAGR {(((1+rin)**(1/4.99))-1)*100:+5.1f}%/a) | 2026 {rout*100:+6.2f}% | DD {dd*100:5.1f}% | {len(r['operaciones'])}")

    print("\nEMA55-diaria con APALANCAMIENTO escalado (techo de retorno y su coste en DD):")
    for pct in [0.05, 0.10, 0.20, 0.30]:
        r = correr("BTC", "btc_longs", capital=10000, datos=d, cerebro=_TREND_D, maker_entrada=True, pct_posicion=pct)
        c = r["curva"]
        ins = c[c.index.year <= 2025]; out = c[c.index.year == 2026]
        rin = ins.iloc[-1] / ins.iloc[0] - 1
        rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
        dd = ((c - c.cummax()) / c.cummax()).min()
        print(f"  margen {pct*100:>2.0f}% | CAGR {(((1+rin)**(1/4.99))-1)*100:+5.1f}%/a | 2026 {rout*100:+6.2f}% | maxDD {dd*100:5.1f}%")


if __name__ == "__main__":
    main()
