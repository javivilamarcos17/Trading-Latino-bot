"""
Tipos base del dominio (compartidos por backtest y operativa real).

Son las "palabras" con las que hablan todas las piezas del bot: una vela, una señal,
una posición... Definirlos una vez evita confusiones entre módulos.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Lado(str, Enum):
    """Dirección de una operación."""
    LARGO = "largo"    # compra (Long)
    CORTO = "corto"    # venta (Short)


class TipoOrden(str, Enum):
    MERCADO = "mercado"   # se ejecuta ya, al precio actual (taker). Lo que usa Merino.
    LIMITE = "limite"     # espera a un precio (maker). Más barato, pero puede no entrar.


class ColorSqueeze(str, Enum):
    """Los 4 estados del Squeeze Momentum (LazyBear)."""
    VERDE_CLARO = "verde_claro"    # sobre 0 y subiendo  -> impulso alcista fuerte
    VERDE_OSCURO = "verde_oscuro"  # sobre 0 y bajando   -> se agota la subida (zona venta/short)
    ROJO_CLARO = "rojo_claro"      # bajo 0 y cayendo    -> impulso bajista fuerte
    ROJO_OSCURO = "rojo_oscuro"    # bajo 0 y recuperando-> se agota la bajada (zona compra)


@dataclass(frozen=True)
class Vela:
    """Una vela OHLCV. `timestamp` es el momento de APERTURA de la vela (UTC)."""
    timestamp: datetime
    apertura: float
    maximo: float
    minimo: float
    cierre: float
    volumen: float


@dataclass(frozen=True)
class Senal:
    """Lo que decide el cerebro: una intención de operar (aún sin ejecutar)."""
    simbolo: str
    lado: Lado
    motivo: str                 # por qué, en lenguaje claro (para el log y la auditoría)
    precio_referencia: float    # precio en el momento de la señal
    stop_loss: float            # SL estructural ya calculado
    timestamp: datetime


@dataclass
class Posicion:
    """Una posición abierta en el mercado."""
    simbolo: str
    lado: Lado
    precio_entrada: float
    cantidad: float             # tamaño en unidades del activo
    apalancamiento: int
    stop_loss: float
    abierta_en: datetime
    break_even_aplicado: bool = False
    velas_4h_transcurridas: int = 0   # para la guillotina del tiempo
