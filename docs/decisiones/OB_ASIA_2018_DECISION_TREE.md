# OB_ASIA_2018_DECISION_TREE — Pre-registro del holdout virgen (firmar ANTES de abrir 2018)

**Fecha:** 2026-07-19 · **Estrategia congelada:** `6400d9a` (OB_ASIA_FREEZE_v1) · **Estado:** FIRMADO

> Este documento se escribe y commitea ANTES de ejecutar el backtest de 2018. El commit prueba que
> los criterios se fijaron sin ver el resultado. Nada se cambia después de abrir.

## Estimando PRIMARIO
`ΔR = E[R | BEAR] − E[R | NON-BEAR]` para la config primaria `ob_asia`, sobre 2018 **BTC + ETH**.

## Requisito SECUNDARIO obligatorio
`E[R | BEAR] > 0` NETO de costes estándar (fees 0.08% ida-vuelta + slippage bps/dist).

## Definiciones (congeladas, sin tuning)
- **BEAR:** cierre diario D-1 < EMA200 diaria D-1 (última vela COMPLETADA; sin look-ahead).
  EMA200 con warmup desde 2017 (datos diarios previos a 2018).
- **NON-BEAR:** cierre diario D-1 ≥ EMA200 diaria D-1.
- **Sesión Asia, OB, stop, target, costes:** exactamente el código congelado @6400d9a. Cambia SOLO
  el fichero de datos. Prohibido `if year==2018`.
- **Inferencia:** block bootstrap por SEMANA (BTC+ETH de la misma semana viajan juntos). Sensibilidad
  de dependencia 3d/7d/14d — SOLO para ver si la significancia depende de asumir independencia, NO
  para elegir el bloque con mejor p.
- **Robustez (coherencia, no primaria):** ob_regime_asia, fvg_ob_asia.

## Naturaleza de la evidencia (honesta)
2018 BTC+ETH es UNA gran replicación macro con dos expresiones cross-asset (mismo fenómeno macro),
NO dos bear markets independientes. Valida principalmente la ESTRUCTURA DE SEÑAL OHLC (2018 será
spot Binance), no la ejecución/economics de Hyperliquid.

## Árbol de decisión (definido ANTES de abrir)
- **PASS:** `E[R|BEAR] > 0` neto Y `ΔR > 0` (BEAR>NON-BEAR) en BTC **y** en ETH, con familia de
  robustez coherente y sin colapsar al quitar las top-3 semanas. → candidata a motor intradía por
  régimen (pendiente aún de confirmación FORWARD post-freeze; PASS en 2018 no es despliegue).
- **MIXED:** signos mayormente correctos pero un activo ≈0, o `ΔR>0` con `E[R|BEAR]` marginal/≤0.
  → ni validada ni muerta; requiere forward. No se toca.
- **FAIL:** `E[R|BEAR] ≤ 0` neto, O `NON-BEAR ≥ BEAR` de forma consistente, O ambos activos negativos.
  → la tesis "motor OB/Asia condicionado a bear" recibe un golpe serio.
- **HETEROGENEIDAD (BTC fuerte + / ETH claramente −, o viceversa):** se registra "FAILED UNIVERSAL
  REPLICATION / heterogeneidad descubierta". NO se proclama "es X-only" (eso sería re-seleccionar
  mirando el holdout). La siguiente hipótesis necesitaría datos nuevos.

## Regla absoluta post-apertura
Si tras ver 2018 se nos ocurre una mejora (p.ej. añadir ADX), NO salva el holdout: 2018 queda
quemado. Se crea OB_ASIA_v2 y se confirma con FORWARD futuro, nunca con 2018 de nuevo.

---

## RESULTADO (abierto UNA vez, 2026-07-19, tras firmar) — ❌ FAIL

`ob_asia` PRIMARIA, 2018 BTC+ETH (spot Binance, manifiesto en data_store/holdout_2018/):
- E[R|BEAR] pooled = **-0.238R** (n=7087) → viola el requisito obligatorio E[R|BEAR]>0.
  block-bootstrap semanal p(≤0)=1.000. Sin top-3 semanas: -0.272R (no mejora).
- ΔR pooled = -0.038 (BEAR NO > NON-BEAR). BTC ΔR=-0.157, ETH ΔR=+0.085.
- Ambos activos NEGATIVOS en BEAR: BTC -0.268R, ETH -0.194R.
- Robustez: ob_regime_asia E[R|BEAR]=-0.243, fvg_ob_asia=-0.279 (coherente, todas negativas).

**VEREDICTO: FAIL.** Cumple 3 condiciones de muerte (E[R|BEAR]≤0, ambos activos negativos, NON-BEAR≥BEAR).
La tesis "motor OB/Asia condicionado a bear" queda FALSIFICADA en el holdout virgen. El edge vivo de
2026 (+0.1 a +0.5R) es muy probablemente específico del régimen/periodo de 2026 o sesgo de diseño,
NO un edge general de oso. Caveat: 2018 es SPOT = valida estructura de SEÑAL; pero la señal es
net-negativa, así que no es un problema de ejecución.

**Consecuencias:** (1) OB/Asia NO es un motor intradía validado. Las variantes vivas en la arena
siguen siendo un EXPERIMENTO forward, sin etiqueta de validado. (2) NO se reoptimiza sobre 2018
(quemado). Cualquier OB_ASIA_v2 exigiría forward futuro. (3) 15M-BEAR-01 cerrado como falsificado.
(4) La disciplina (congelar + holdout virgen) funcionó: mató una narrativa antes de creerla.
