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
