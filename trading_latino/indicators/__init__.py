"""
Indicadores técnicos (Fase 2).

Replican las fórmulas EXACTAS que usa TradingView / Trading Latino, para que el bot "vea"
lo mismo que vería Jaime Merino en su gráfico. Si esto no coincide con TradingView, todo
el backtest sería mentira — por eso van acompañados de tests y de validación manual.

Convención: todas las funciones reciben un DataFrame con las columnas del proyecto
(apertura, maximo, minimo, cierre, volumen) y devuelven Series/DataFrame alineados.
"""

from trading_latino.indicators.ema import ema, anadir_emas
from trading_latino.indicators.adx import adx
from trading_latino.indicators.squeeze import squeeze
from trading_latino.indicators.volume_profile import poc

__all__ = ["ema", "anadir_emas", "adx", "squeeze", "poc"]
