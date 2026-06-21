# Catálogo de estrategias de la ARENA (paper-trading en vivo)

> La arena pone a competir EN DIRECTO varias estrategias x monedas x temporalidades, en papel.
> Cada operación se mide en % neto de coste, así que todas son comparables en una tabla (el board).
> Filosofía: no nos creemos un backtest; dejamos que cada herramienta se demuestre o se hunda con
> datos reales. Añadir una estrategia = una función `det_*` más. Es flexible a propósito.

## Cómo se ejecuta
- `python -m trading_latino.live.arena`  → un "tick": detecta setups nuevos, actualiza abiertas, registra.
- `python -m trading_latino.live.board`  → vista instantánea (solo lectura) del ranking acumulado.
- Recolección 24/7: GitHub Actions (`.github/workflows/arena.yml`) cada 15 min en la nube.

## Las 11 estrategias (a 2026-06-21)

| # | Clave | Herramienta / teoría | Lógica de entrada (resumen) | Temporalidades |
|---|-------|----------------------|------------------------------|----------------|
| 1 | `smc` | SMC multi-timeframe | FVG del marco mayor + BOS/CHoCH en el menor, a favor de tendencia | 15m, 1h |
| 2 | `merino` | Trading Latino | EMA10/55 + ADX>23 + giro de Squeeze momentum | 15m, 1h |
| 3 | `sweep` | Liquidez | Barrido de máx/mín + pico de volumen + mecha de rechazo → reversión | 15m, 1h |
| 4 | `fvg` | Fair Value Gap | Retest de un FVG reciente en la propia TF | 15m, 1h |
| 5 | `ob` | Order Block | Retest de la zona del último bloque opuesto antes del impulso | 15m, 1h |
| 6 | `rsi` | RSI | Salida de sobreventa (<30) / sobrecompra (>70) | 15m, 1h |
| 7 | `volumen` | Volumen | Clímax de volumen (pico ×3) + mecha de rechazo → reversión | 15m, 1h |
| 8 | `adx` | ADX | Tendencia fuerte y creciente (>25) a favor de EMA20 → continuación | 15m, 1h |
| 9 | `rsidiv` | Divergencia RSI | Precio nuevo extremo pero RSI no lo confirma → reversión | 15m, 1h, 4h |
| 10 | `scalp_sqz` | Scalp Squeeze+RSI | Giro de momentum + RSI, stop ajustado, 1.5R | 1m, 5m |
| 11 | `scalp_rev` | Scalp reversión | Mecha fuera de banda Bollinger 2σ + cierre dentro | 1m, 5m |

Total: 69 competidores (estrategia × moneda × TF). Monedas: BTC, ETH, SOL.

## Reglas comunes
- **Sin lookahead:** se decide sobre la última vela CERRADA; el resultado se mide hacia delante.
- **Bracket uniforme:** entrada + stop + objetivo (R). Salida cuando toca stop u objetivo.
- **Coste:** 0,05% por operación (estimación Hyperliquid taker+slippage). El scalping parte en desventaja.
- **Honestidad:** muestra pequeña al principio = sin conclusiones. Hay que dejar acumular días/semanas.

## Ideas en cola para añadir (cuando haya datos de las actuales)
- VWAP (rebote en VWAP diario/semanal), EMA rápida de scalping, patrones de velas, OI/liquidaciones
  en vivo (Hyperliquid), confluencias (2+ herramientas a la vez), y variantes multi-TF de cada una.

## Cómo se evalúa y mejora (el bucle)
1. Recoger datos en vivo (cloud, 24/7).
2. Mirar el board: qué estrategia/moneda/TF acumula retorno positivo con muestra suficiente.
3. Subir las que ganan, quitar las que mueren, ajustar parámetros, añadir variantes. Repetir.
