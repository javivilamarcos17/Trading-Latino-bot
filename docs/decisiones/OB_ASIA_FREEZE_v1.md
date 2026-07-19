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

- **Definición de BEAR (congelada, SIN tuning, externa a OB):** cierre diario < EMA200 diaria.
  Es la convención de tendencia más estándar, cero parámetros elegidos por nosotros. Causal.
- **Variable estadística:** episodio bajista (`bear_episode_id` = cada entrada/salida del estado),
  NO la operación. Bootstrap por episodio.
- **Representante PRIMARIA:** `ob_asia` (la más simple). **Familia de robustez (2 vecinas
  pre-registradas):** `ob_regime_asia` (añade filtro de régimen), `fvg_ob_asia` (añade FVG).
  NO se juzgan las 13 variantes como 13 hipótesis (eso reabriría data-snooping).

## Datasets del holdout
- **2018 (BTC/ETH):** descargable gratis de Binance public data (verificado: 15m desde 2018-01-01).
  Holdout temporal — NO participó en el diseño.
- **2022 (BTC/ETH/SOL):** en caché 15m (2021-26). Holdout — NO tocar hasta abrir.
- **CONTROL NEGATIVO:** estado NON-BEAR (cierre > EMA200). Si OB/Asia también gana ahí, NO es un
  edge de régimen, es otra cosa (probablemente sesgo).
- **2026 forward:** por FECHA REAL de despliegue de cada variante (detectar decay backtest→live).

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
