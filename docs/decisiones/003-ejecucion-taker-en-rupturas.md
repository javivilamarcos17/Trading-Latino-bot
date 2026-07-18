# ADR-003 — Ejecución: taker en entradas de ruptura, maker solo en salidas pasivas

**Fecha:** 2026-07-18 · **Estado:** cerrada

## Contexto
El ahorro maker (~3 bps/lado) tentaba. Mi simulación a 15m decía "fill 100%, gratis". La evidencia
publicada (232k órdenes maker reales en Binance, arXiv 2502.18625/2407.16527/2607.01550) mide lo
que la simulación no ve: los fills de órdenes límite se concentran en las operaciones perdedoras y,
en señales direccionales, el coste dominante son las rupturas que se escapan sin llenarte.

## Decisión
Entradas de ruptura SIEMPRE taker. Maker solo en salidas sin urgencia (targets).

## Alternativas consideradas
- Límite al cierre en entradas — descartada: selección adversa documentada supera el ahorro.
- Todo taker — descartada en salidas: ahí la selección adversa es neutra y el ahorro es gratis.

## Consecuencias
- (+) No se pierden las mejores operaciones (las que corren) ni se acumulan las peores.
- (−) Se paga ~3 bps más por entrada; en 1D es despreciable (~0.002R/op).
