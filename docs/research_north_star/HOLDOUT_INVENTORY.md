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
