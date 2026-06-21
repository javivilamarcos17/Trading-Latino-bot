"""
Backtest de CARTERA (la solución profesional: breadth).

El mismo edge validado (swing 4H/1H, longs) aplicado a MUCHOS activos a la vez, con un solo
capital compartido y un tope de posiciones simultáneas (control de exposición/correlación).
Por activo es frecuencia de swing; en cartera, "muchísima frecuencia" — como opera Merino.

Costes maker (entrada límite) + funding por barra + slippage en salida. Sin lookahead
(misma alineación por hora de cierre que el motor de un activo).

Uso:  python -m trading_latino.research.portfolio
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from trading_latino.backtest.engine import _DEFAULT_TFS, _HORAS, _arrays, _color, _indicadores_tf
from trading_latino.config import CONFIG
from trading_latino.data.download import cargar
from trading_latino.domain.types import Accion, EstadoMercado, EstadoTF, Lado, Posicion
from trading_latino.risk.manager import apalancamiento_semana, tamano_posicion
from trading_latino.strategy.brain import decidir

ANIOS = [2021, 2022, 2023, 2024, 2025]


def _estado_tf(A: dict, i: int) -> EstadoTF:
    return EstadoTF(
        cierre=A["cierre"][i], ema_rapida=A["ema_rapida"][i], ema_lenta=A["ema_lenta"][i],
        adx=A["adx"][i], adx_pendiente=A["adx_pendiente"][i], di_pos=A["di_pos"][i], di_neg=A["di_neg"][i],
        sqz_valor=A["sqz_valor"][i], sqz_color=_color(A["sqz_color"][i]),
        poc=A["poc"][i], swing_min=A["swing_min"][i], swing_max=A["swing_max"][i],
        sqz_color_prev=_color(A["sqz_color_prev"][i]), rsi=A["rsi"][i],
        volumen_rel=A["volumen_rel"][i], vwap=A["vwap"][i],
    )


def _alinear(simbolo: str, master: pd.DatetimeIndex, tfs: dict, exchange="binance"):
    """Indicadores por rol (ffill) + OHLC base exacto (NaN antes del listado) + contador 4h."""
    ind = {rol: _indicadores_tf(cargar(exchange, simbolo, tf), tf,
                                con_poc=(rol == "h4"), con_swing=(rol == "h4"))
           for rol, tf in tfs.items()}
    A = {rol: _arrays(ind[rol].reindex(master, method="ffill")) for rol in ind}
    b = cargar(exchange, simbolo, tfs["h1"])
    b.index = pd.DatetimeIndex(b["timestamp"])
    b = b.reindex(master)                       # exacto: NaN donde el activo aún no existía
    ohlc = {k: b[c].to_numpy() for k, c in [("a", "apertura"), ("h", "maximo"), ("l", "minimo"), ("c", "cierre")]}
    ct = pd.Series(ind["h4"].index, index=ind["h4"].index).reindex(master, method="ffill").to_numpy()
    return A, ohlc, ct


def correr_cartera(simbolos: list[str], tfs: dict | None = None, capital=10000.0,
                   maker_entrada=True, max_posiciones=8, pct=0.05, modo="combinado",
                   cerebro=None) -> dict:
    tfs = tfs or _DEFAULT_TFS
    c = CONFIG.costes
    horas = _HORAS.get(tfs["h1"], 1.0)
    # master = rejilla de 1h de BTC (referencia común)
    btc1h = cargar("binance", "BTC", tfs["h1"])
    master = pd.DatetimeIndex(btc1h["timestamp"])
    datos = {s: _alinear(s, master, tfs) for s in simbolos}

    equity = capital
    posiciones: dict[str, Posicion] = {}
    com_entrada: dict[str, float] = {}
    funding_ac: dict[str, float] = {}
    operaciones = []
    curva = np.full(len(master), capital, dtype=float)
    ct_prev: dict[str, object] = {s: None for s in simbolos}

    def _abrir(s, lado, cantidad, apalanc, sl, precio, ts):
        nonlocal equity
        if maker_entrada:
            p_eff, com = precio, cantidad * precio * c.COMISION_MAKER
        else:
            slip = c.SLIPPAGE_ESTIMADO
            p_eff = precio * (1 + slip) if lado is Lado.LARGO else precio * (1 - slip)
            com = cantidad * p_eff * c.COMISION_TAKER
        equity -= com
        com_entrada[s] = com
        funding_ac[s] = 0.0
        posiciones[s] = Posicion(simbolo=s, lado=lado, precio_entrada=p_eff, cantidad=cantidad,
                                 apalancamiento=apalanc, stop_loss=sl, abierta_en=ts,
                                 stop_inicial=sl, max_favorable=p_eff)

    def _cerrar(s, precio, ts, motivo):
        nonlocal equity
        p = posiciones[s]
        slip = c.SLIPPAGE_ESTIMADO
        p_eff = precio * (1 - slip) if p.lado is Lado.LARGO else precio * (1 + slip)
        signo = 1 if p.lado is Lado.LARGO else -1
        pnl_bruto = (p_eff - p.precio_entrada) * p.cantidad * signo
        com_sal = p.cantidad * p_eff * c.COMISION_TAKER
        equity += pnl_bruto - com_sal
        coms = com_entrada[s] + com_sal
        operaciones.append((s, p.abierta_en, ts, pnl_bruto - coms - funding_ac[s], motivo))
        del posiciones[s]

    for i in range(len(master)):
        ts = master[i].to_pydatetime()
        for s in simbolos:
            A, ohlc, ct = datos[s]
            precio = ohlc["a"][i]
            if precio is None or np.isnan(precio):     # activo aún no listado / sin vela
                continue

            pos = posiciones.get(s)
            if pos is not None and ct[i] != ct_prev[s] and ct_prev[s] is not None:
                pos.velas_4h_transcurridas += 1
            ct_prev[s] = ct[i]

            estado = EstadoMercado(simbolo=s, timestamp=ts, precio=precio,
                                   semanal=_estado_tf(A["semanal"], i), diario=_estado_tf(A["diario"], i),
                                   h4=_estado_tf(A["h4"], i), h1=_estado_tf(A["h1"], i))
            d = cerebro(estado, pos) if cerebro is not None else decidir(estado, pos, modo)

            if d.accion in (Accion.ABRIR_LARGO, Accion.ABRIR_CORTO) and pos is None and len(posiciones) < max_posiciones:
                lado = Lado.LARGO if d.accion is Accion.ABRIR_LARGO else Lado.CORTO
                apalanc = apalancamiento_semana(estado.semanal.cierre, estado.semanal.ema_lenta)
                cantidad = tamano_posicion(equity, precio, apalanc, pct)
                _abrir(s, lado, cantidad, apalanc, d.stop_loss, precio, ts)
            elif d.accion is Accion.CERRAR and pos is not None:
                _cerrar(s, precio, ts, d.motivo)
            elif d.accion is Accion.MOVER_BREAKEVEN and pos is not None:
                pos.stop_loss = d.stop_loss
                pos.break_even_aplicado = True

            pos = posiciones.get(s)
            if pos is not None:
                funding = pos.cantidad * ohlc["c"][i] * c.FUNDING_HORARIO_ESTIMADO * horas
                signo = 1 if pos.lado is Lado.LARGO else -1
                equity -= funding * signo
                funding_ac[s] += funding * signo
                if pos.lado is Lado.LARGO:
                    if ohlc["l"][i] <= pos.stop_loss:
                        _cerrar(s, pos.stop_loss, ts, "stop loss")
                    else:
                        pos.max_favorable = max(pos.max_favorable, ohlc["h"][i])
                else:
                    if ohlc["h"][i] >= pos.stop_loss:
                        _cerrar(s, pos.stop_loss, ts, "stop loss")
                    else:
                        pos.max_favorable = min(pos.max_favorable, ohlc["l"][i])

        # marca a mercado de la cartera
        mtm = equity
        for s, p in posiciones.items():
            ci = datos[s][1]["c"][i]
            if not np.isnan(ci):
                mtm += (ci - p.precio_entrada) * p.cantidad * (1 if p.lado is Lado.LARGO else -1)
        curva[i] = mtm

    return {"curva": pd.Series(curva, index=master), "operaciones": operaciones,
            "equity_final": equity, "capital": capital}


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    universo = list(CONFIG.altcoins) + ["BTC"]
    print(f"Cartera de {len(universo)} activos (longs swing 4H/1H, costes maker, máx 8 posiciones)...")
    r = correr_cartera(universo, maker_entrada=True, max_posiciones=8)
    c = r["curva"]
    total = c.iloc[-1] / r["capital"] - 1
    pico = c.cummax(); dd = ((c - pico) / pico).min()
    print(f"\nOperaciones: {len(r['operaciones'])}")
    print(f"Rentabilidad TOTAL: {total*100:+.2f}%   (CAGR ~{((1+total)**(1/4.99)-1)*100:.2f}%/año)")
    print(f"Max drawdown: {dd*100:.1f}%")
    print("\nPor año:")
    for y in ANIOS:
        s = c[c.index.year == y]
        if len(s) > 1:
            print(f"  {y}: {(s.iloc[-1]/s.iloc[0]-1)*100:+.2f}%")


if __name__ == "__main__":
    main()
