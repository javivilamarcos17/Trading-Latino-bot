"""
Motor de backtest event-driven (Fase 4).

Recorre la historia **vela de 1h a vela de 1h** (sin mirar el futuro) y, en cada paso:
1. arma el EstadoMercado con los indicadores de las velas YA CERRADAS de cada temporalidad,
2. pregunta al cerebro qué hacer (precio = apertura de la vela actual),
3. ejecuta en el broker simulado (con comisiones + slippage + funding),
4. aplica funding de la hora y comprueba el stop loss dentro de la vela.

Alineación anti-lookahead: cada temporalidad se indexa por su HORA DE CIERRE, y a cada
instante de 1h se le asigna la última vela superior que ya había cerrado.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_latino.config import CONFIG
from trading_latino.data.download import cargar
from trading_latino.domain.types import (
    Accion, ColorSqueeze, EstadoMercado, EstadoTF, Lado,
)
from trading_latino.execution.broker_simulado import BrokerSimulado
from trading_latino.indicators import adx, ema, poc, squeeze
from trading_latino.risk.manager import apalancamiento_semana, tamano_posicion
from trading_latino.strategy.brain import decidir

_DURACION = {
    "5m": pd.Timedelta(minutes=5), "15m": pd.Timedelta(minutes=15), "30m": pd.Timedelta(minutes=30),
    "1h": pd.Timedelta(hours=1), "4h": pd.Timedelta(hours=4),
    "1d": pd.Timedelta(days=1), "1w": pd.Timedelta(weeks=1),
}


def _indicadores_tf(df: pd.DataFrame, tf: str, con_poc=False, con_swing=False) -> pd.DataFrame:
    """Calcula indicadores de una temporalidad e indexa por HORA DE CIERRE (open + duración)."""
    a = adx(df)
    s = squeeze(df)
    out = pd.DataFrame({
        "cierre": df["cierre"].to_numpy(),
        "ema_rapida": ema(df["cierre"], CONFIG.indicadores.EMA_RAPIDA).to_numpy(),
        "ema_lenta": ema(df["cierre"], CONFIG.indicadores.EMA_LENTA).to_numpy(),
        "adx": a["adx"].to_numpy(),
        "adx_pendiente": a["adx"].diff(CONFIG.indicadores.ADX_BARRAS_PENDIENTE).to_numpy(),
        "di_pos": a["di_pos"].to_numpy(),
        "di_neg": a["di_neg"].to_numpy(),
        "sqz_valor": s["valor"].to_numpy(),
        "sqz_color": s["color"].to_numpy(),
        "sqz_color_prev": s["color"].shift(1).to_numpy(),
        "poc": poc(df).to_numpy() if con_poc else np.full(len(df), np.nan),
    })
    n = CONFIG.estrategia.SWING_LOOKBACK_VELAS
    out["swing_min"] = df["minimo"].rolling(n).min().to_numpy() if con_swing else np.nan
    out["swing_max"] = df["maximo"].rolling(n).max().to_numpy() if con_swing else np.nan
    out["rsi"] = _rsi(df["cierre"]).to_numpy()
    out["volumen_rel"] = (df["volumen"] / df["volumen"].rolling(20).mean()).to_numpy()
    out["vwap"] = _vwap_semanal(df).to_numpy()
    out.index = pd.DatetimeIndex(df["timestamp"]) + _DURACION[tf]   # hora de cierre
    return out


def _vwap_semanal(df: pd.DataFrame) -> pd.Series:
    """VWAP anclado a la semana (se reinicia cada lunes). Precio típico ponderado por volumen."""
    ts = pd.DatetimeIndex(df["timestamp"])
    iso = ts.isocalendar()
    clave = pd.Series((iso["year"].astype(int) * 100 + iso["week"].astype(int)).to_numpy(), index=df.index)
    tp = (df["maximo"] + df["minimo"] + df["cierre"]) / 3
    pv = (tp * df["volumen"]).groupby(clave).cumsum()
    vv = df["volumen"].groupby(clave).cumsum()
    return pv / vv.replace(0, np.nan)


def _rsi(serie: pd.Series, periodo: int = 14) -> pd.Series:
    """RSI de Wilder."""
    delta = serie.diff()
    ag = delta.clip(lower=0).ewm(alpha=1 / periodo, adjust=False).mean()
    ap = (-delta.clip(upper=0)).ewm(alpha=1 / periodo, adjust=False).mean()
    rs = ag / ap.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def _color(valor) -> ColorSqueeze | None:
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return None
    try:
        return ColorSqueeze(valor)
    except ValueError:
        return None


# Asignación de roles -> temporalidad real. Por defecto = el marco swing actual.
# Se puede desplazar para probar marcos intradía, p.ej.:
#   {"semanal":"1d","diario":"4h","h4":"1h","h1":"15m"}  (4H/1H/15m)
_DEFAULT_TFS = {"semanal": "1w", "diario": "1d", "h4": "4h", "h1": "1h"}
_HORAS = {"5m": 1 / 12, "15m": 0.25, "30m": 0.5, "1h": 1.0, "4h": 4.0, "1d": 24.0, "1w": 168.0}


def preparar(simbolo: str, exchange: str = "binance", tfs: dict | None = None) -> dict:
    """Carga datos, calcula indicadores y los alinea por ROL sobre la rejilla del marco base.

    `tfs` mapea roles (semanal/diario/h4/h1) a temporalidades reales. El rol 'h1' es el marco
    base (el reloj); el rol 'h4' es el operativo (donde se calculan POC, swing y el contador).
    """
    tfs = tfs or _DEFAULT_TFS
    base = cargar(exchange, simbolo, tfs["h1"])
    ind = {rol: _indicadores_tf(cargar(exchange, simbolo, tf), tf,
                                con_poc=(rol == "h4"), con_swing=(rol == "h4"))
           for rol, tf in tfs.items()}
    master = pd.DatetimeIndex(base["timestamp"])
    alineado = {rol: ind[rol].reindex(master, method="ffill") for rol in ind}
    ct_4h = pd.Series(ind["h4"].index, index=ind["h4"].index).reindex(master, method="ffill")
    return {"h1": base, "master": master, "al": alineado, "ct_4h": ct_4h, "base_tf": tfs["h1"]}


_COLS = ["cierre", "ema_rapida", "ema_lenta", "adx", "adx_pendiente", "di_pos", "di_neg",
         "sqz_valor", "sqz_color", "sqz_color_prev", "poc", "swing_min", "swing_max",
         "rsi", "volumen_rel", "vwap"]


def _arrays(al_tf: pd.DataFrame) -> dict:
    """Extrae las columnas a arrays numpy una sola vez (el bucle por filas de pandas es lento)."""
    return {c: al_tf[c].to_numpy() for c in _COLS}


def _estado_tf_arr(A: dict, i: int) -> EstadoTF:
    return EstadoTF(
        cierre=A["cierre"][i], ema_rapida=A["ema_rapida"][i], ema_lenta=A["ema_lenta"][i],
        adx=A["adx"][i], adx_pendiente=A["adx_pendiente"][i], di_pos=A["di_pos"][i], di_neg=A["di_neg"][i],
        sqz_valor=A["sqz_valor"][i], sqz_color=_color(A["sqz_color"][i]),
        poc=A["poc"][i], swing_min=A["swing_min"][i], swing_max=A["swing_max"][i],
        sqz_color_prev=_color(A["sqz_color_prev"][i]), rsi=A["rsi"][i], volumen_rel=A["volumen_rel"][i],
        vwap=A["vwap"][i],
    )


def correr(simbolo: str = "BTC", modo: str | None = None,
           capital: float | None = None, multiplicador_costes: float = 1.0,
           datos: dict | None = None, regla_salida: str | None = None,
           cerebro=None, pct_posicion: float | None = None,
           maker_entrada: bool = False) -> dict:
    """Corre el backtest. Devuelve operaciones, curva de capital y resumen.

    `cerebro`: función opcional (estado, posicion) -> Decision para experimentar con
    lógicas alternativas. Si es None, usa el cerebro de producción (strategy.decidir).
    """
    modo = modo or CONFIG.backtest.MODO
    capital = capital or CONFIG.backtest.CAPITAL_INICIAL
    d = datos or preparar(simbolo)
    h1, master, al, ct_4h = d["h1"], d["master"], d["al"], d["ct_4h"]

    # arrays de la vela de 1h (rápido)
    ap = h1["apertura"].to_numpy()
    mx = h1["maximo"].to_numpy()
    mn = h1["minimo"].to_numpy()
    ci = h1["cierre"].to_numpy()
    # precálculo de columnas alineadas que se usan a menudo
    A = {tf: _arrays(al[tf]) for tf in al}
    ct = ct_4h.to_numpy()

    horas_barra = _HORAS.get(d.get("base_tf", "1h"), 1.0)
    broker = BrokerSimulado(capital, multiplicador_costes, maker_entrada, horas_barra)
    curva = np.full(len(master), capital, dtype=float)
    ct_prev = None

    for i in range(len(master)):
        ts = master[i].to_pydatetime()
        precio = ap[i]

        # contar velas de 4h transcurridas si hay posición y se cerró una nueva vela de 4h
        if broker.posicion is not None and ct[i] != ct_prev and ct_prev is not None:
            broker.posicion.velas_4h_transcurridas += 1
        ct_prev = ct[i]

        estado = EstadoMercado(
            simbolo=simbolo, timestamp=ts, precio=precio,
            semanal=_estado_tf_arr(A["semanal"], i), diario=_estado_tf_arr(A["diario"], i),
            h4=_estado_tf_arr(A["h4"], i), h1=_estado_tf_arr(A["h1"], i),
        )

        decision = (cerebro(estado, broker.posicion) if cerebro is not None
                    else decidir(estado, broker.posicion, modo, regla_salida))

        if decision.accion is Accion.ABRIR_LARGO and broker.posicion is None:
            apalanc = apalancamiento_semana(estado.semanal.cierre, estado.semanal.ema_lenta)
            cantidad = tamano_posicion(broker.equity, precio, apalanc, pct_posicion)
            broker.abrir("BTC" if simbolo == "BTC" else simbolo, Lado.LARGO, cantidad,
                         apalanc, decision.stop_loss, precio, ts)
        elif decision.accion is Accion.CERRAR and broker.posicion is not None:
            broker.cerrar(precio, ts, decision.motivo)
        elif decision.accion is Accion.MOVER_BREAKEVEN and broker.posicion is not None:
            broker.mover_stop(decision.stop_loss)

        # funding de la hora + comprobación del stop dentro de la vela
        if broker.posicion is not None:
            broker.aplicar_funding(ci[i])
            p = broker.posicion
            if p.lado is Lado.LARGO and mn[i] <= p.stop_loss:
                broker.cerrar(p.stop_loss, ts, "stop loss")
            elif p.lado is Lado.CORTO and mx[i] >= p.stop_loss:
                broker.cerrar(p.stop_loss, ts, "stop loss")

        # actualizar el máximo a favor (para la salida trailing), con la vela ya vista
        if broker.posicion is not None:
            p = broker.posicion
            if p.lado is Lado.LARGO:
                p.max_favorable = max(p.max_favorable, mx[i])
            else:
                p.max_favorable = min(p.max_favorable, mn[i])

        # marca a mercado de la equity (incluye P&L no realizado)
        equity_mtm = broker.equity
        if broker.posicion is not None:
            p = broker.posicion
            signo = 1 if p.lado is Lado.LARGO else -1
            equity_mtm += (ci[i] - p.precio_entrada) * p.cantidad * signo
        curva[i] = equity_mtm

    return {
        "simbolo": simbolo, "modo": modo, "multiplicador_costes": multiplicador_costes,
        "capital_inicial": capital, "equity_final": broker.equity,
        "operaciones": broker.operaciones,
        "curva": pd.Series(curva, index=master, name="equity"),
    }
