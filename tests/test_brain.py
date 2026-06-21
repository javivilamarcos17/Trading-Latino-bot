"""Tests del cerebro (Fase 3b) — módulo BTC solo-Longs."""

from datetime import datetime, timezone

import pytest

from trading_latino.domain.types import (
    Accion,
    ColorSqueeze,
    EstadoMercado,
    EstadoTF,
    Lado,
    Posicion,
)
from trading_latino.risk.manager import break_even_neto
from trading_latino.strategy.brain import decidir

LIBRE = datetime(2025, 7, 1, 8, 0, tzinfo=timezone.utc)   # 10:00 Madrid -> fuera de bloqueo
BLOQUEO = datetime(2025, 7, 1, 13, 30, tzinfo=timezone.utc)  # 15:30 Madrid -> bloqueo NY


def _tf(sqz_color=ColorSqueeze.ROJO_OSCURO, ema_rapida=110.0, ema_lenta=100.0,
        adx_pendiente=1.0, poc=100.0, swing_min=98.0, swing_max=104.0):
    return EstadoTF(
        cierre=100.0, ema_rapida=ema_rapida, ema_lenta=ema_lenta, adx=25.0,
        adx_pendiente=adx_pendiente, di_pos=20.0, di_neg=15.0, sqz_valor=-1.0,
        sqz_color=sqz_color, poc=poc, swing_min=swing_min, swing_max=swing_max,
    )


def _estado(precio=100.0, ts=LIBRE, diario=None, h4=None, h1=None):
    return EstadoMercado(
        simbolo="BTC", timestamp=ts, precio=precio,
        semanal=_tf(),
        diario=diario or _tf(ema_rapida=110.0, ema_lenta=100.0),       # alcista
        h4=h4 or _tf(sqz_color=ColorSqueeze.ROJO_OSCURO, adx_pendiente=1.0, poc=100.0, swing_min=98.0),
        h1=h1 or _tf(sqz_color=ColorSqueeze.ROJO_OSCURO),
    )


def _pos(velas_4h=3, be=False, entrada=100.0):
    return Posicion(
        simbolo="BTC", lado=Lado.LARGO, precio_entrada=entrada, cantidad=1.0,
        apalancamiento=5, stop_loss=97.0, abierta_en=LIBRE,
        break_even_aplicado=be, velas_4h_transcurridas=velas_4h,
    )


# ───────────── Entradas ─────────────
def test_entra_largo_con_patron_completo():
    d = decidir(_estado(), None)
    assert d.accion is Accion.ABRIR_LARGO
    assert d.stop_loss == pytest.approx(98.0 * (1 - 0.003))   # bajo el swing_min, con holgura


def test_no_entra_si_semaforo_diario_bajista():
    d = decidir(_estado(diario=_tf(ema_rapida=90.0, ema_lenta=100.0)), None)
    assert d.accion is Accion.NADA


def test_no_entra_si_gatillo_1h_no_confirma():
    d = decidir(_estado(h1=_tf(sqz_color=ColorSqueeze.ROJO_CLARO)), None)
    assert d.accion is Accion.NADA


def test_no_entra_si_precio_lejos_del_poc():
    d = decidir(_estado(precio=110.0), None)   # poc=100 -> 10% de distancia
    assert d.accion is Accion.NADA


def test_no_entra_en_bloqueo_horario():
    d = decidir(_estado(ts=BLOQUEO), None)
    assert d.accion is Accion.NADA
    assert "bloqueo" in d.motivo.lower()


# ───────────── Gestión de la posición ─────────────
def test_cierra_por_agotamiento_del_impulso():
    d = decidir(_estado(h4=_tf(sqz_color=ColorSqueeze.VERDE_OSCURO)), _pos())
    assert d.accion is Accion.CERRAR
    assert "agotamiento" in d.motivo


def test_mueve_a_break_even_tras_vela_ganadora():
    d = decidir(_estado(precio=105.0, h4=_tf(sqz_color=ColorSqueeze.ROJO_OSCURO)), _pos(velas_4h=1, be=False))
    assert d.accion is Accion.MOVER_BREAKEVEN
    assert d.stop_loss == pytest.approx(break_even_neto(100.0, Lado.LARGO))


def test_guillotina_cierra_si_plano_y_tiempo_agotado():
    d = decidir(_estado(precio=100.5, h4=_tf(sqz_color=ColorSqueeze.ROJO_OSCURO)), _pos(velas_4h=8, be=True))
    assert d.accion is Accion.CERRAR
    assert "guillotina" in d.motivo
