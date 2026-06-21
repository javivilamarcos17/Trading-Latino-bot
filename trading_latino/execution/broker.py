"""
Interfaz de ejecución: "ejecuta esta orden".

La segunda pieza de enchufe del diseño "un cerebro, tres mundos". El cerebro ordena
abrir/cerrar/proteger sin saber si va a un simulador o al exchange real:
  - BrokerSimulado   -> aplica comisiones + funding + slippage (Mundo A: backtesting)
  - BrokerHyperliquid-> manda órdenes reales al exchange        (Mundos B/C: paper y real)

Aquí solo el CONTRATO. Las implementaciones llegan en su fase.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from trading_latino.domain.types import Lado, Posicion, TipoOrden


class Broker(ABC):
    """Contrato común para ejecutar operaciones, igual en backtest y en real."""

    @abstractmethod
    def abrir(
        self,
        simbolo: str,
        lado: Lado,
        cantidad: float,
        apalancamiento: int,
        stop_loss: float,
        tipo: TipoOrden = TipoOrden.MERCADO,
    ) -> Posicion:
        """Abre una posición. El SL DEBE quedar colocado en el mismo acto (regla 🟦)."""
        raise NotImplementedError

    @abstractmethod
    def cerrar(self, posicion: Posicion, motivo: str) -> float:
        """Cierra una posición a mercado. Devuelve el P&L NETO (tras costes)."""
        raise NotImplementedError

    @abstractmethod
    def mover_stop(self, posicion: Posicion, nuevo_stop: float) -> None:
        """Mueve el stop loss (p. ej. para el break-even neto)."""
        raise NotImplementedError

    @abstractmethod
    def equity(self) -> float:
        """Capital total actual (para sizing y métricas)."""
        raise NotImplementedError
