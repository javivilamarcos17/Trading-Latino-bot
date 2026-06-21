"""Tests del módulo de riesgo (Fase 3)."""

from datetime import datetime, timezone

import pytest

from trading_latino.config import CONFIG
from trading_latino.domain.types import Lado
from trading_latino.risk import manager as r


def test_semaforo_diario():
    assert r.semaforo_diario(ema_rapida_diaria=100, ema_lenta_diaria=90) == "alcista"
    assert r.semaforo_diario(ema_rapida_diaria=80, ema_lenta_diaria=90) == "bajista"


def test_apalancamiento_segun_semanal():
    assert r.apalancamiento_semana(precio_btc_semanal=100, ema_lenta_semanal=90) == CONFIG.riesgo.APALANCAMIENTO_MAX
    assert r.apalancamiento_semana(precio_btc_semanal=80, ema_lenta_semanal=90) == CONFIG.riesgo.APALANCAMIENTO_MIN


def test_tamano_posicion():
    # 10.000 de capital, 5%, 5x, precio 100 -> margen 500 -> nocional 2500 -> 25 unidades
    cantidad = r.tamano_posicion(equity=10_000, precio=100, apalancamiento=5, pct=0.05)
    assert cantidad == pytest.approx(25.0)


def test_coste_ida_vuelta_taker():
    # 2 x 0.045% + 0.05% de slippage = 0.0014
    assert r.coste_ida_vuelta(maker=False, incluir_slippage=True) == pytest.approx(0.0014)
    # maker sin slippage = 2 x 0.015% = 0.0003
    assert r.coste_ida_vuelta(maker=True, incluir_slippage=False) == pytest.approx(0.0003)


def test_break_even_neto_cubre_costes():
    be_largo = r.break_even_neto(100.0, Lado.LARGO, coste_total=0.001)
    be_corto = r.break_even_neto(100.0, Lado.CORTO, coste_total=0.001)
    assert be_largo == pytest.approx(100.1)   # un poco por ENCIMA de la entrada
    assert be_corto == pytest.approx(99.9)     # un poco por DEBAJO de la entrada


def test_stop_estructural():
    minimos = [98, 97, 99, 96, 100]
    maximos = [102, 103, 101, 104, 100]
    sl_largo = r.stop_estructural(minimos, maximos, Lado.LARGO, holgura=0.01)
    sl_corto = r.stop_estructural(minimos, maximos, Lado.CORTO, holgura=0.01)
    assert sl_largo == pytest.approx(96 * 0.99)    # bajo el mínimo
    assert sl_corto == pytest.approx(104 * 1.01)   # sobre el máximo


def test_bloqueo_horario_madrid():
    # 1 julio 2025: Madrid es UTC+2 (verano). 13:30 UTC = 15:30 Madrid -> bloqueado.
    bloqueado = datetime(2025, 7, 1, 13, 30, tzinfo=timezone.utc)
    libre = datetime(2025, 7, 1, 10, 0, tzinfo=timezone.utc)        # 12:00 Madrid
    assert r.en_bloqueo_horario(bloqueado) is True
    assert r.en_bloqueo_horario(libre) is False
