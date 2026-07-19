# HOLDOUT INVENTORY — capital estadístico del proyecto (2026-07-19)

Los holdouts son CAPITAL ESTADÍSTICO. Este inventario clasifica cada dato sin abrir resultados
nuevos. "Virgen" es POR HIPÓTESIS: requiere que ni el dato ni el CONCEPTO se hayan desarrollado
mirando ese periodo.

## Lo que YA tenemos en disco
- `research_cache/`: BTC/ETH/SOL 15m (2021-01→2026-07), 5m (2024-01→2026-07).
- `data_store/binance/`: **21 monedas** (AAVE, ADA, APT, ARB, AVAX, BCH, BNB, BTC, DOGE, DOT, ETH,
  LINK, LTC, NEAR, OP, POL, SOL, SUI, TIA, UNI, XRP) en 1h/4h/1d/1w, 2021-01→2026-06.
- `holdout_2018/`: BTC/ETH 15m 2018 (descargado para OB/Asia) + diario 2017-18.
- Arena viva: 2026 (~63 días), Hyperliquid.

## Clasificación

### 🟢 VIRGEN TEMPORAL (nunca en caché; descargable; la munición más fuerte)
- **2019 + 2020, 15m BTC/ETH**: NUNCA descargado, NUNCA analizado. Virgen para CUALQUIER hipótesis.
  ~2 años de intradía limpio. (SOL solo desde ~2020-08.)
- **2018, 15m BTC/ETH**: descargable, pero ⚠️ ya SEEN/BURNED para estructura OB (lo abrimos). Para
  una hipótesis radicalmente distinta podría servir como "seen supportive", no virgen fuerte.
- Pre-2021 en general = fuera de todo lo que hemos mirado.

### 🟡 CROSS-ASSET (ya en disco; replicación entre monedas; supportive)
- **18 monedas NO usadas para desarrollo direccional** (todas menos BTC/ETH/SOL), 1h/4h/1d 2021-26.
  Sirven para: ¿un edge desarrollado en BTC/ETH/SOL generaliza a otras monedas? ⚠️ PARCIALMENTE
  INFORMADO: mismo PERIODO/regímenes que vimos (2021-26), así que es replicación cross-asset, NO
  out-of-sample temporal. Evidencia de coherencia, no confirmatoria fuerte.
  (Excepción: algunas de estas monedas se usaron en la CESTA CARRY — para hipótesis direccionales
  siguen sin tocar, pero anotarlo por moneda antes de usarla.)

### 🟠 SEEN / DEVELOPMENT (usado a fondo; NO es holdout)
- BTC/ETH/SOL todas las TFs 2021-2026 (15m, 5m, 1h, 4h, 1d): matriz, barridos, todo el desarrollo.
- Arena viva 2026 PRE-freeze: usada para diseñar variantes (sesgo de diseño).

### 🔴 BURNED (holdout ya consumido)
- 2018 15m BTC/ETH para OB_ASIA_v1 (abierto una vez → FALSIFICADO). No reutilizar para OB/Asia.

### 🔵 FORWARD (genuinamente nuevo, se acumula solo)
- Arena viva POST-freeze (desde 2026-07-19): evidencia forward real para PORTFOLIO_v1, ichimoku,
  y cualquier estrategia congelada. Es virgen-que-crece: la más valiosa a medio plazo.

## Conclusión (corrige el "solo 1-2 disparos")
Munición confirmatoria disponible, en orden de fuerza:
1. **Forward post-freeze** (crece cada día; el estándar de oro).
2. **2019-2020 15m BTC/ETH** (virgen temporal; descargar cuando una hipótesis lo pida — UNA vez cada una).
3. **18 monedas cross-asset** (replicación, supportive; ya en disco).
No es escasez extrema, pero tampoco infinito: cada periodo virgen se gasta UNA vez por hipótesis.
Regla: no descargar 2019-2020 hasta tener una hipótesis congelada que lo vaya a usar como holdout.

---

# VALIDATION CUBE (2026-07-19 — corrección tras auditoría de genealogía)

No todo OOS prueba lo mismo. Tres dimensiones DISTINTAS, cada dataset con VIRGINITY + SUITABILITY + ROLE:

## A. TEMPORAL (¿el edge existía en otro periodo?)
- **2019 BTC/ETH, 2020 BTC/ETH** (15m, descargables, NUNCA en caché): potencialmente VIRGIN.
  ROLE = TEMPORAL_OOS. SUITABLE: estructura OHLC de señal SÍ; ejecución Hyperliquid moderna NO
  (mercado antiguo, derivados inmaduros). ⚠️ SIGNAL generalization ≠ DEPLOYMENT generalization.
  ➡️ NO fusionar 2019 y 2020 por defecto: mantener 2019=OOS-A, 2020=OOS-B como piezas separadas
  si el N del fenómeno lo permite (más valioso que pooled).
- 2018 BTC/ETH: BURNED (OB/Asia).

## B. CROSS-ASSET (¿generaliza a otras monedas?) — CORRECCIÓN IMPORTANTE
- Las **18 altcoins NO son vírgenes**: todas aparecen en scripts de research (carry_pro, btc_lidera,
  confluencia, estructura_mtf, estudio_smc, cartera_edges...). Etiqueta = **PARTIALLY INFORMED**.
- ❌ NO se fabrica una "partición sellada OOS A/B/reserve" con ellas — sería fingir independencia
  que no existe (misma lección que 2022). ROLE = **CROSS-ASSET ROBUSTNESS / heterogeneidad /
  falsificación / stress**, NO evidencia confirmatoria fuerte.
- Sí se pueden AGRUPAR por metadata ex-ante (listing age, history length, liquidez/madurez) como
  "PARTIALLY-INFORMED ROBUSTNESS GROUPS" — pero etiquetados como tales, nunca como "sealed OOS".
- ⚠️ 18 monedas ≠ 18 observaciones independientes (factor cripto común → market-time block bootstrap).

## C. FORWARD (¿sigue existiendo tras descubrirlo?)
- Arena post-freeze (desde 2026-07-19): la evidencia más limpia a largo plazo. Se acumula sola.

## Estructura de validación para toda candidata futura
DEVELOPMENT (BTC/ETH/SOL 2021-26, visto, uso intensivo) → si sobrevive → EXTERNAL VALIDATION A
(temporal virgin 2019/2020 O cross-asset robustness) → si sobrevive → EXTERNAL VALIDATION B (otra
dimensión) → TRUE FORWARD. Objetivo: sobrevivir a DOS EJES de generalización distintos, no dos
tests del mismo periodo.
