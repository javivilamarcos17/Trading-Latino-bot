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


@dataclass(frozen=True)
class EstadoTF:
    """Foto de una temporalidad en un instante: indicadores ya calculados de velas cerradas."""
    cierre: float
    ema_rapida: float
    ema_lenta: float
    adx: float
    adx_pendiente: float            # cambio del ADX en las últimas N barras (signo = dirección)
    di_pos: float
    di_neg: float
    sqz_valor: float
    sqz_color: ColorSqueeze | None
    poc: float | None = None
    swing_min: float | None = None   # mínimo estructural reciente (para el SL en Largos)
    swing_max: float | None = None   # máximo estructural reciente (para el SL en Cortos)


@dataclass(frozen=True)
class EstadoMercado:
    """Lo que 've' el cerebro en un instante: el precio y las 4 temporalidades alineadas.

    Regla anti-'mirar el futuro': cada EstadoTF refleja solo velas YA CERRADAS hasta `timestamp`.
    """
    simbolo: str
    timestamp: datetime
    precio: float
    semanal: EstadoTF
    diario: EstadoTF
    h4: EstadoTF
    h1: EstadoTF


class Accion(str, Enum):
    NADA = "nada"
    ABRIR_LARGO = "abrir_largo"
    ABRIR_CORTO = "abrir_corto"
    CERRAR = "cerrar"
    MOVER_BREAKEVEN = "mover_breakeven"


@dataclass(frozen=True)
class Decision:
    """La salida del cerebro: qué hacer y por qué."""
    accion: Accion
    motivo: str
    stop_loss: float | None = None   # solo al abrir o al mover a break-even
