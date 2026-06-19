"""
Broker simulado (Mundo A: backtesting).

Ejecuta las órdenes del cerebro aplicando los costes REALES en neto:
- comisiones (taker) al abrir y al cerrar,
- slippage adverso en cada ejecución a mercado,
- funding cada hora mientras la posición está abierta.

Registra cada operación cerrada para el informe. `multiplicador_costes` permite el barrido
de sensibilidad (0x / 0.5x / 1x / 2x) que pide docs/RIESGOS_RENTABILIDAD.md.
"""

from __future__ import annotations

from datetime import datetime

from trading_latino.config import CONFIG
from trading_latino.domain.types import Lado, OperacionCerrada, Posicion


class BrokerSimulado:
    def __init__(self, capital_inicial: float, multiplicador_costes: float = 1.0):
        self.equity: float = capital_inicial
        self.posicion: Posicion | None = None
        self.operaciones: list[OperacionCerrada] = []
        self._mult = multiplicador_costes
        self._c = CONFIG.costes
        # acumuladores de la posición abierta
        self._comision_entrada = 0.0
        self._funding_acumulado = 0.0

    # ---- costes ----
    def _slippage(self) -> float:
        return self._c.SLIPPAGE_ESTIMADO * self._mult

    def _comision(self, nocional: float) -> float:
        return nocional * self._c.COMISION_TAKER * self._mult

    # ---- operaciones ----
    def abrir(self, simbolo: str, lado: Lado, cantidad: float, apalancamiento: int,
              stop_loss: float, precio: float, momento: datetime) -> None:
        # slippage adverso: un Long compra un poco más caro
        slip = self._slippage()
        precio_eff = precio * (1 + slip) if lado is Lado.LARGO else precio * (1 - slip)
        comision = self._comision(cantidad * precio_eff)
        self.equity -= comision
        self._comision_entrada = comision
        self._funding_acumulado = 0.0
        self.posicion = Posicion(
            simbolo=simbolo, lado=lado, precio_entrada=precio_eff, cantidad=cantidad,
            apalancamiento=apalancamiento, stop_loss=stop_loss, abierta_en=momento,
            stop_inicial=stop_loss, max_favorable=precio_eff,
        )

    def aplicar_funding(self, precio_actual: float) -> None:
        """Funding de una hora. El Long lo paga (coste); el Short lo cobra (signo contrario)."""
        if self.posicion is None:
            return
        tasa = self._c.FUNDING_HORARIO_ESTIMADO * self._mult
        coste = self.posicion.cantidad * precio_actual * tasa
        signo = 1 if self.posicion.lado is Lado.LARGO else -1
        self.equity -= coste * signo
        self._funding_acumulado += coste * signo

    def cerrar(self, precio: float, momento: datetime, motivo: str) -> None:
        p = self.posicion
        if p is None:
            return
        slip = self._slippage()
        # slippage adverso: un Long vende un poco más barato
        precio_eff = precio * (1 - slip) if p.lado is Lado.LARGO else precio * (1 + slip)
        signo = 1 if p.lado is Lado.LARGO else -1
        pnl_bruto = (precio_eff - p.precio_entrada) * p.cantidad * signo
        comision_salida = self._comision(p.cantidad * precio_eff)

        self.equity += pnl_bruto - comision_salida
        comisiones = self._comision_entrada + comision_salida
        pnl_neto = pnl_bruto - comisiones - self._funding_acumulado

        self.operaciones.append(OperacionCerrada(
            simbolo=p.simbolo, lado=p.lado, abierta_en=p.abierta_en, cerrada_en=momento,
            precio_entrada=p.precio_entrada, precio_salida=precio_eff, cantidad=p.cantidad,
            pnl_bruto=pnl_bruto, comisiones=comisiones, funding=self._funding_acumulado,
            pnl_neto=pnl_neto, motivo_cierre=motivo, velas_4h=p.velas_4h_transcurridas,
        ))
        self.posicion = None

    def mover_stop(self, nuevo_stop: float) -> None:
        if self.posicion is not None:
            self.posicion.stop_loss = nuevo_stop
            self.posicion.break_even_aplicado = True
