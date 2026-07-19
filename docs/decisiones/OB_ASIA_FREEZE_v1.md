# OB_ASIA_FREEZE_v1 — Pre-registro del holdout de la familia OB/Asia (Ley 7)

**Fecha de congelación:** 2026-07-19 · **Commit congelado:** `6400d9a` · **Estado:** CONGELADO

> Regla absoluta: desde esta congelación, NINGÚN parámetro, filtro o regla de la familia OB/Asia
> se modifica antes de abrir el holdout. Si abrimos 2022, cambiamos algo y volvemos a mirar 2022,
> el holdout queda QUEMADO. Esto es pre-registro científico, no burocracia.

## Contexto (por qué se congela)
La familia OB/Asia es la evidencia VIVA más prometedora de un posible edge intradía condicionado a
régimen (NO un edge validado todavía). Live 2026 (63 días, Hyperliquid, 15m): ob_regime +0.545R
(n=137), ob +0.348R (n=179), ob_asia_close +0.327R (n=279), fvg_ob_asia +0.323R (n=315),
ob_plus_asia_r3 +0.231R (n=489), ob_trend_r3 +0.188R (n=519), ob_regime_asia +0.127R (n=871),
ob_asia +0.106R (n=901). ⚠️ Todo de UN régimen (miedo/oso 2026), misma apuesta subyacente
(short + order block + sesión asiática + bajista), y varias variantes se diseñaron VIENDO estos
datos. Por eso empieza ahora el experimento de verdad. Estos números quedan REGISTRADOS aquí para
que no podamos fingir después que no los habíamos visto.

## Detectores congelados (arena.py @ 6400d9a)
det_ob (369), det_ob_trend (446), det_ob_plus (460), det_ob_regime_asia (489), det_ob_asia (499),
det_ob_regime (509), det_fvg_ob (908), det_ob_plus_asia (1047), det_fvg_ob_asia (1219),
det_ob_trend_r3 (1244), det_ob_asia_close (1271), det_ob_asia_close_L (1283), det_ob_plus_asia_r3 (1323).

## Pre-registro de la hipótesis (elegido ANTES de abrir el holdout)

**H15-01 (PRIMARIA):** `ob_asia` — la variante más simple que captura la hipótesis económica
(order block en sesión asiática) — tiene expectancy neta positiva ESPECÍFICAMENTE durante un
estado BEAR causal y pre-registrado, y ese efecto se replica en episodios bajistas independientes.

- **Definición de BEAR (congelada, elegida EX ANTE, externa a OB):** cierre diario D-1 < EMA200
  diaria D-1 (siempre la última vela COMPLETADA → sin look-ahead). Corrección (auditoría IA): NO es
  "la definición correcta de bear" ni "cero tuning porque es estándar" — es una regla elegida ex
  ante y congelada PARA ESTE experimento. Que sea popular no la hace correcta; solo la hace no-tuneada
  por nosotros. La hipótesis es "¿hay comportamiento diferencial de OB/Asia bajo la EMA200?", no
  "hemos descubierto el verdadero régimen bear".
- **Estimando PRIMARIO ÚNICO:** ΔR = E[R | BEAR] − E[R | NON-BEAR], con criterio obligatorio
  E[R | BEAR] > 0 neto. Un solo estadístico primario (la tesis es "edge condicionado a régimen",
  no "OB funciona"). Todo lo demás es exploratorio.
- **Unidad estadística (corrección IA): NO usar "cada cruce EMA200 = episodio"** (fabrica
  pseudo-independencia: un rebote de 2 días parte un mismo fenómeno económico en 2). Y NO poner
  duración mínima (retrospectivo). En su lugar: **block bootstrap por SEMANA**, manteniendo
  BTC/ETH/SOL de la misma semana juntos en el resampling (un crash en 3 monedas ≈ 1 evento, no 3).
- **Representante PRIMARIA:** `ob_asia`. ⚠️ HONESTIDAD (auditoría IA): elegirla "por ser la más
  simple" SIGUE siendo selección — conocíamos los números de 2026 (ob_asia +0.106R, ob_regime
  +0.545R...) ANTES de elegir. El freeze NO borra esa selección previa sobre datos de desarrollo;
  por eso el holdout virgen vale tanto. **Familia de robustez:** `ob_regime_asia`, `fvg_ob_asia`.
  NO se juzgan las 13 como 13 hipótesis.

## AUDITORÍA DE GENEALOGÍA DE DATOS (hecha ANTES de abrir — hallazgo que cambia el diseño)
Toda la familia OB/Asia (ob_asia, ob_regime_asia, fvg_ob_asia incluidas) está DEFINIDA en
`backtest_ganadoras.py`, que corre sobre la caché de 15m que empieza en 2021-01-01 e INCLUYE 2022.
→ **2022 NO es holdout virgen: es dato de desarrollo** (estos detectores ya corrieron sobre él).
Usarlo como validación sería circular. Etiquetas honestas de cada dataset:

- **2018 (BTC/ETH):** ✅ HOLDOUT VIRGEN temporal — ese dato NUNCA estuvo en la caché durante el
  desarrollo (verificado: descargable gratis de Binance, 15m desde 2018-01-01). Es la ÚNICA prueba
  temporal genuinamente limpia que tenemos. ⚠️ Auditar antes: exchange, spot vs perp, timezone,
  huecos — si 2018 es spot y el live es perp, valida la ESTRUCTURA DE SEÑAL OHLC, no la ejecución.
- **2022 (BTC/ETH/SOL):** ⚠️ PARCIALMENTE INFORMADO / desarrollo (la caché con 2022 estuvo
  disponible y los detectores corrieron sobre ella). Evidencia DÉBIL, no confirmatoria limpia.
- **CONTROL NEGATIVO:** NON-BEAR (cierre > EMA200). Si OB/Asia también gana ahí = no es edge de régimen.
- **post-freeze 2026 (>6400d9a):** ✅ TRUE FORWARD — la única evidencia verdaderamente nueva del
  live. Todo lo anterior a este commit es DEVELOPMENT.

Jerarquía de evidencia resultante: 2018 BTC/ETH (virgen temporal) > post-freeze forward (nuevo) >
2022 (parcialmente informado, solo coherencia) > 2026 pre-freeze (desarrollo, NO validación).

## Criterios de MUERTE (pre-registrados)
La hipótesis H15-01 MUERE si en el holdout:
1. La representante primaria NO es positiva en 2022 (BTC/ETH/SOL).
2. Depende de una sola moneda.
3. Depende de los top-3 episodios (top-K episode deletion).
4. Cambia de signo materialmente entre episodios bajistas.
5. Es TAMBIÉN positiva en el control NON-BEAR (no sería específica de régimen).
Si sobrevive: candidata a primer motor intradía por régimen (aún pendiente forward prospectivo).

## Correcciones de lenguaje asociadas (auditoría IA externa 2026-07-19)
- "El oso está terminando / firma de suelo" era STORYTELLING. Lo correcto: "el semáforo clasifica
  el mercado como posible transición según sus reglas". Las pérdidas actuales del núcleo NO validan
  ese cambio de régimen (un trend-follower sufre whipsaws normales; hay que comparar con la
  distribución histórica de episodios equivalentes antes de hablar de cambio estructural).
- "2018 imposible" era falso: NO estaba en la caché local, pero es descargable gratis.
