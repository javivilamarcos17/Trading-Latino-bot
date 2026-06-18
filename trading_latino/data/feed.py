"""
Interfaz de datos: "dame las velas".

Esta es una de las dos piezas de enchufe del diseño "un cerebro, tres mundos".
El cerebro pide velas a un Feed sin saber de dónde salen:
  - FeedHistorico  -> lee parquet del disco            (Mundo A: backtesting)
  - FeedHyperliquid-> recibe velas por WebSocket en vivo (Mundos B/C: paper y real)

Aquí solo definimos el CONTRATO (qué métodos debe tener). Las implementaciones
concretas se construyen en su fase correspondiente.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from trading_latino.domain.types import Vela


class Feed(ABC):
    """Contrato común para cualquier fuente de velas."""

    @abstractmethod
    def velas(self, simbolo: str, temporalidad: str) -> Iterator[Vela]:
        """Devuelve las velas YA CERRADAS de un símbolo y temporalidad, en orden.

        Regla de oro (anti-"mirar el futuro"): un Feed nunca entrega una vela hasta
        que está cerrada, y en backtest las entrega en estricto orden temporal.
        """
        raise NotImplementedError

    @abstractmethod
    def funding_en(self, simbolo: str, momento) -> float:
        """Tasa de funding aplicable a un símbolo en un instante dado (para el coste real)."""
        raise NotImplementedError
