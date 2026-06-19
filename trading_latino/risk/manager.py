"""
Gestión de riesgo — las leyes de supervivencia de Merino (🟦 núcleo), en código.

Funciones puras y testeables. El cerebro y el motor de backtest las usan; no tienen estado
ni conexión a nada. Todo lo relacionado con costes va en NETO (🟨), como mandó el dueño.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, time
from zoneinfo import ZoneInfo

from trading_latino.config import CONFIG
from trading_latino.domain.types import Lado


# ───────────────────────── Semáforo (permiso de dirección) ─────────────────────────
def semaforo_diario(ema_rapida_diaria: float, ema_lenta_diaria: float) -> str:
    """Semáforo diario de BTC: 'alcista' permite Longs, 'bajista' permite Shorts (en alts).

    Regla: EMA10 por encima de EMA55 en diario = alcista (coincide con la versión Ruckard
    del método). 🟦 núcleo.
    """
    return "alcista" if ema_rapida_diaria > ema_lenta_diaria else "bajista"


def apalancamiento_semana(precio_btc_semanal: float, ema_lenta_semanal: float) -> int:
    """Apalancamiento de la semana según el filtro macro semanal de BTC.

    BTC por encima de su EMA55 semanal (bull) -> 5x; por debajo (bear estructural) -> 3x.
    🟦 núcleo (rango 3x-5x). 🔎 regla exacta a afinar.
    """
    r = CONFIG.riesgo
    return r.APALANCAMIENTO_MAX if precio_btc_semanal > ema_lenta_semanal else r.APALANCAMIENTO_MIN


# ───────────────────────── Tamaño de posición ─────────────────────────
def tamano_posicion(equity: float, precio: float, apalancamiento: int, pct: float | None = None) -> float:
    """Cantidad (en unidades del activo) a operar.

    🟦 Merino: 5% del capital por operación (capital en 20 partes). Ese 5% es el MARGEN
    comprometido; con apalancamiento, el nocional = margen × apalancamiento. 🔎 (confirmar
    si interpreta el 5% como margen o como exposición; aquí: margen).
    """
    pct = pct if pct is not None else CONFIG.riesgo.TAMANO_POSICION_PCT
    margen = equity * pct
    nocional = margen * apalancamiento
    return nocional / precio


# ───────────────────────── Costes y break-even neto ─────────────────────────
def coste_ida_vuelta(maker: bool = False, incluir_slippage: bool = True) -> float:
    """Coste de abrir + cerrar (sin funding), como fracción del precio.

    Funding NO va aquí: depende del tiempo en posición y lo añade el motor de backtest.
    """
    c = CONFIG.costes
    comision = (c.COMISION_MAKER if maker else c.COMISION_TAKER) * 2  # entrada + salida
    slippage = c.SLIPPAGE_ESTIMADO if incluir_slippage else 0.0
    return comision + slippage


def break_even_neto(entrada: float, lado: Lado, coste_total: float | None = None) -> float:
    """Precio de break-even REAL (con costes). 🟨 (lo pidió el dueño).

    Si el stop salta aquí, la operación sale a CERO de verdad (no con pérdida oculta).
    `coste_total` = comisiones ida/vuelta (+ slippage) (+ funding acumulado, si el motor lo pasa).
    """
    coste_total = coste_total if coste_total is not None else coste_ida_vuelta()
    if lado is Lado.LARGO:
        return entrada * (1 + coste_total)
    return entrada * (1 - coste_total)


# ───────────────────────── Stop Loss estructural ─────────────────────────
def stop_estructural(
    minimos: Sequence[float],
    maximos: Sequence[float],
    lado: Lado,
    holgura: float = 0.003,
) -> float:
    """SL estructural detrás del último mínimo (Long) o máximo (Short) reciente. 🟦.

    `minimos`/`maximos`: ventana de velas recientes. `holgura`: pequeño margen visual
    (por defecto 0,3%) para colocarlo justo detrás del swing/POC. 🔎 ventana y holgura a afinar.
    """
    if not minimos or not maximos:
        raise ValueError("Se necesitan velas recientes para el stop estructural.")
    if lado is Lado.LARGO:
        return min(minimos) * (1 - holgura)
    return max(maximos) * (1 + holgura)


# ───────────────────────── Filtro horario (apertura de NY) ─────────────────────────
def en_bloqueo_horario(momento: datetime) -> bool:
    """True si `momento` cae en la ventana de bloqueo (15:15-15:45 Madrid). 🟦.

    No se abren posiciones nuevas dentro de esa franja (manipulación de apertura de NY).
    """
    r = CONFIG.riesgo
    local = momento.astimezone(ZoneInfo(r.BLOQUEO_HORARIO_TZ)).time()
    inicio = time.fromisoformat(r.BLOQUEO_HORARIO_INICIO)
    fin = time.fromisoformat(r.BLOQUEO_HORARIO_FIN)
    return inicio <= local <= fin
