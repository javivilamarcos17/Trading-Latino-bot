# REAL EXECUTION LAB v1 — validar ejecución real de Ichimoku 4H ETH/SOL (spec, SIN órdenes)

**Fecha:** 2026-07-19 · **Estado:** SPEC (v1 = SHADOW, cero órdenes, cero dinero, cero claves de trading).
**Objetivo:** NO ganar dinero. Medir la única incertidumbre que ningún backtest resuelve: fills
reales, slippage, latencia, fees reales y funding real. Estrategia: Ichimoku 4H ETH/SOL CONGELADA
(no se optimiza, no se cambian señales, no se añade sizing sofisticado).

> ⚠️ GATE DE DINERO REAL (decisión del DUEÑO, separada e informada): el "sí a todo" de la
> investigación NO autoriza arriesgar capital real ni manejar claves de trading. Ninguna orden real
> se envía sin un go explícito del dueño PARA ESO. v1 no toca dinero.

## Fases (progresión prudente)
- **v1 SHADOW (ahora, sin riesgo):** genera la señal ichimoku en vivo (4h ETH/SOL, mismo código
  congelado), registra la ORDEN QUE ENVIARÍA (entry/stop/target/size) y la compara contra precios
  reales de Hyperliquid (mid/best bid-ask del momento). Mide slippage esperado, fees teóricos,
  funding real acumulado. NO envía nada. Aprende la mecánica y el logging sin arriesgar un céntimo.
- **v2 MIN-SIZE REAL (solo con go explícito del dueño):** las mismas señales, tamaño mínimo técnico,
  con envío real de órdenes y reconciliación fill esperado vs real.

## 1. Arquitectura mínima (separación estricta)
`SIGNAL ENGINE` (ichimoku 4h, read-only, congelado) → `INTENDED ORDER` (entry/stop/target/size,
LOGGED) → [v1: STOP aquí, comparación con precio real] → [v2: `EXECUTION` con aprobación manual por
orden] → `RECONCILIATION` (esperado vs real). Cada capa aislada; la señal nunca "sabe" del fill.

## 2. Logging obligatorio por operación
signal_ts · intended_entry · intended_stop · intended_target · intended_size · actual_fill_price ·
actual_fill_ts · slippage_bps · fee_real · funding_accrued · exit_intended · exit_actual ·
execution_delay_ms · expected_R (modelo) · realized_R · **execution_gap = realized_R − expected_R** ·
venue · fee_tier. Todo a un log append-only con timestamp UTC.

## 3. Kill-switch (obligatorio antes de cualquier orden real en v2)
- Pérdida diaria máxima → HALT. Máx posiciones abiertas → HALT. Slippage por orden > tolerancia → cancelar.
- Pérdida de conexión / datos rancios → HALT (no operar a ciegas). Parada de emergencia manual.
- Cualquier anomalía inesperada → HALT y avisar, no "seguir a ver".

## 4. Reconciliación esperado vs real (API oficial Hyperliquid)
Usar los endpoints oficiales de FILLS del usuario y de FUNDING histórico de Hyperliquid (no coste
fijo supuesto): expected_entry vs actual_fill, expected_exit vs actual, expected_fees vs actual,
expected_funding (proxy) vs actual (Hyperliquid horario). Reconciliación exacta por operación.

## 5. Criterio de "hemos aprendido suficiente"
Ichimoku holdea ~4 días → produce fills razonablemente rápido. Objetivo: **execution_gap estable
sobre ≥20-30 operaciones reales** (o un gap sistemático claro antes). Pregunta a responder: ¿el
backtest sobreestima lo capturable, y en cuánto? Con eso se ajusta el modelo de costes y se decide
si el edge sobrevive a ejecución real.

## 6. Tamaño mínimo técnico y exposición (verificar en cuenta antes de v2)
Hyperliquid tiene un notional mínimo por orden (histórico ~$10). El tamaño exacto y el fee tier
REAL de la cuenta deben leerse de la API/meta del mercado, NO suponerse. Exposición monetaria de v2
= (min_notional) × (nº posiciones simultáneas ETH/SOL). Objetivo: exposición trivial, "coste de
comprar información de ejecución", no de ganar.

## 7. Checklist EXACTO antes de la primera orden real (v2) — todos obligatorios
1. ⬜ Go explícito e informado del DUEÑO para arriesgar dinero real (esta decisión, no el sí-general).
2. ⬜ Probado antes en TESTNET de Hyperliquid.
3. ⬜ Clave de API dedicada SOLO trading, **retiros DESHABILITADOS**, IP allowlist si posible.
4. ⬜ Clave en `.env` (NUNCA commiteada — ya protegido por los deny locks del proyecto).
5. ⬜ Tamaño = mínimo técnico. Exposición monetaria confirmada y aceptada por el dueño.
6. ⬜ Kill-switch implementado Y probado (forzar cada condición de HALT).
7. ⬜ Aprobación MANUAL por orden en las primeras N (no automático).
8. ⬜ Fee tier real leído de la cuenta; funding real reconciliado.

## Fuera de alcance de v1/v2 (no ahora)
Capital significativo, escalado, sizing dinámico, más estrategias (núcleo/turtle vendrían después —
turtle holdea ~78 días, tarda meses en dar señal real → shadow prolongado). Optimizar ichimoku. NADA.
