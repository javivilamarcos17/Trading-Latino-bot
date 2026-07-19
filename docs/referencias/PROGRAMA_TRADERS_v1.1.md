# Programa de investigación de traders v1.1 — REFERENCIA (menú opcional, NO mandato)

**Origen:** documentos v1.1 aportados por el asesor externo (otra IA), 2026-07-19.
**Estado:** REFERENCIA / menú de direcciones futuras. NO reemplaza nada de lo ya construido.

> Principio del dueño (2026-07-19): "no tenemos que olvidar todo lo que tenemos y hemos trabajado
> ya". Este programa se enchufa ENCIMA del sistema existente; no lo sustituye. ~70% de lo que
> describe YA está hecho (ver tabla). Lo nuevo son las capas Estructura/Ciclo/Positioning, y dos de
> ellas están bloqueadas por datos que no tenemos (OI/CVD/liquidaciones sistemáticos).

## Lo que YA tenemos (la base, no se toca)
- **Trend layer:** núcleo 1D + ichimoku 4h (validados; ichimoku con OOS temporal 2017-20).
- **Portfolio engine:** portfolio_sim.py (Test 0 reproduce baseline, causal, order-independent).
- **Tribunal V2 (Leyes 1-11)** — ver abajo, ya en uso.
- **Arena 24/7** (17k ops), cost model neto (falta funding direccional), data-manifest/lineage
  (hecho en el holdout 2018), armas de ciclo, carry.
- **Freezes vivos:** OB_ASIA_FREEZE_v1 (FALSIFICADO en 2018), PORTFOLIO_v1 (forward desde 2026-07-19).

## Lo genuinamente nuevo (opcional, por régimen y por datos)
- **Estructura (AdriG/SMC):** S2 OB_STRUCTURE_v2 (hipótesis NUEVA, no rescate de OB/Asia), S3
  Sweep+Acceptance/Rejection. Solo necesitan OHLC → EJECUTABLES (con cuidado del holdout virgen).
- **Ciclo (Plan BTC):** S4 Impulse-Correction-Reacceleration. OHLC → ejecutable, alto riesgo hindsight.
- **Positioning (Mr GON):** S5 Positioning State, S6 Leverage Reset, S7 Spot/Futures, S8 Scalper.
  ⛔ BLOQUEADAS por datos: necesitan OI/funding/liquidaciones/CVD sistemáticos que NO tenemos
  (30 días gratis Binance). Decisión de compra de datos pendiente del dueño.

## Tribunal V2 — las 11 leyes (consolidado)
1. Familia, no celda ganadora. 2. Bootstrap por unidad económica/temporal (episodio/bloque).
3. N efectiva (trades ≠ observaciones independientes). 4. LOYO (no "sin 2023" ad-hoc).
5. Causalidad estricta (ninguna feature conoce el futuro; MFE/MAE son outcomes, nunca features).
6. Neto realista (fees + slippage + FUNDING + ejecución). 7. Data-snooping (Research Ledger +
DSR/PBO/SPA). 8. Valor incremental de portfolio (standalone rentable no basta). 9. Una teoría de
heterogeneidad debe predecir dónde falla (mata la TEORÍA, no el despliegue acotado revalidado).
10. Freeze-before-holdout (se abre una vez; cambio posterior = versión nueva). 11. Integridad del
resultado negativo (una hipótesis falsificada queda falsificada; no se reoptimiza con el holdout
quemado ni se renombra para salvarla; una hipótesis nueva del fracaso exige nuevo ID + evidencia).

## Reglas de gobernanza adoptadas
- Una sola hipótesis primaria por experimento. Un holdout se abre una vez.
- Confirmatorio (holdout virgen / forward) requiere aprobación explícita del dueño (RUN_APPROVED).
  Exploratorio/descriptivo sobre datos YA vistos es libre (no puede quemar un holdout).
- Toda feature: value/observed_at/available_at/source/venue/market_type/version. available_at ≤ decisión.
- Toda fuente de datos: manifest (venue, market_type, símbolo, UTC, gaps, hash, fecha).
- Trader = fuente de HIPÓTESIS, no de bot. Etiquetar reglas EXPLICIT/INFERRED/UNKNOWN/MARKETING.

## Prioridad recomendada (camino LEAN, no la catedral)
- **P0 consolidar (datos en mano, no es alpha nueva):** funding en núcleo/turtle/ichimoku; forward
  de PORTFOLIO_v1; registrar OB_ASIA_v1=FALSIFIED en el ledger.
- **P1 un piloto nuevo end-to-end:** S3 Sweep+Acceptance/Rejection (OHLC, genuinamente distinto de
  lo ya muerto; gasta 2018 con cuidado). Construir gobernanza/features SOLO lo que ese piloto pida.
- **P2+ (data-dependent):** Positioning/MICRO-01B solo tras decidir compra de OI histórico.
- **Muro del scalping:** 1m/5m NO se puede validar solo en papel; exige piloto de ejecución real a
  tamaño mínimo (medir fill esperado vs real). Es una decisión del dueño, no técnica.

## Documentos fuente completos
El texto íntegro del Manual Maestro v1.1 y la Directiva de Implementación v1.1 fue aportado por el
asesor externo el 2026-07-19 (en el historial de la conversación). Este fichero extrae lo adoptable
y lo ancla a lo existente; si se necesita el verbatim, está en el registro de la sesión.
