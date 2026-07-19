# S3-A — PRE-REGISTRO (Sweep → Acceptance/Rejection · INFORMATION TEST)

**Fecha:** 2026-07-19 · **hypothesis_id:** HYP-S3A-001 · **Estado:** PREREGISTERED (NO ejecutar sin `RUN_APPROVED=true`)
**Origen conceptual:** AdriG/SMC (fuente de hipótesis, no validación de gurú). NO es rescate de OB_ASIA_v1 (falsificada).

## Naturaleza
NO es una estrategia. NO hay entry/stop/target/R. Es un **INFORMATION TEST**: ¿la respuesta del
mercado tras atravesar un nivel estructural conocido ex-ante contiene información incremental sobre
la distribución de retornos futura, MÁS ALLÁ de saber que hubo un sweep?

## Definiciones causales (congeladas; available_at = cierre de la vela; sin look-ahead)
- **Nivel estructural (PRIMARIO, único, sin tuning):** máximo/mínimo de las N=20 velas previas
  (Donchian-20, convención estándar). `available_at` = cierre de la vela previa.
- **ε (colchón):** 0.10 × ATR14 (fijo, no se optimiza).
- **BREAKOUT UP:** close_t > nivel_high + ε. **SWEEP/REJECTION UP:** high_t > nivel_high + ε PERO
  close_t < nivel_high (cruzó y cerró dentro). **ACCEPTANCE UP:** tras un breakout, close_{t} sigue
  > nivel_high en la vela de confirmación (declarado SOLO al cierre de esa vela). Simétrico abajo.
- Todos los estados se declaran al CIERRE. Cero confirmación futura.

## Estimando PRIMARIO (la comparación que importa)
**ΔInformación** = distribución del retorno futuro condicionada a {sweep+respuesta} MENOS la
condicionada a {sweep solo / simple break}. Formalmente, outcome primario:
`fwd_ret_K` (retorno normalizado por ATR en las próximas K=12 velas del TF de evento) comparando:
1. simple break del nivel (benchmark)
2. sweep solo (benchmark)
3. sweep + REJECTION (candidato reversión)
4. sweep + ACCEPTANCE (candidato continuación)
Pregunta primaria: **¿(3) y (4) añaden información sobre (1)/(2)?** Si el sweep solo ya explica
todo, acceptance/rejection NO aporta y S3-A muere.

## Outcomes secundarios (descriptivos)
MFE, MAE, holding-time decay del edge informacional (a qué horizonte se disipa). MFE/MAE son
OUTCOMES, jamás features.

## Temporalidades (justificadas, no "mejor celda")
Contexto estructural: 1H y 4H. Observación del evento: 15m. Se busca una REGIÓN temporal coherente
(varias TFs adyacentes con el mismo signo), no un TF espectacular aislado.

## Universo y datos
DEVELOPMENT: BTC/ETH/SOL, 2021-2026 (datos VISTOS). NO consume ningún holdout. Inferencia: block
bootstrap por SEMANA (BTC/ETH/SOL de la misma semana juntos). Neto de fees+slippage al medir
retornos operables (aunque como information test el foco es la distribución, no el PnL).

## Research budget (cerrado ANTES de ejecutar)
- 1 definición primaria de nivel (Donchian-20). Máximo 2 alternativas EXPLORATORIAS (N=10, N=50)
  declaradas como exploratorias, no confirmatorias.
- 2 definiciones de respuesta (acceptance, rejection). ε fijo. K fijo.
- Máximo teórico: ~6 celdas. Todas registradas en el ledger (para el DSR/PBO futuro).

## Criterios de MUERTE (pre-registrados)
1. sweep+respuesta NO añade información incremental sobre sweep solo/simple break.
2. El efecto depende de una sola moneda / un solo año / los top-3 episodios.
3. Cambia de signo materialmente entre subperiodos.
Si muere → CEMENTERIO. NO "probé otra definición y ahora funciona" (eso sería HYP nuevo).

## Follow-ups PROHIBIDOS
- Convertir un hallazgo de S3-A en filtro/estrategia sin FREEZE + nueva evidencia (holdout/forward).
- Tunear cualquier parámetro tras ver resultados y seguir llamándolo S3-A.
- Usar 2018 (quemado) o descargar 2019/2020 para "confirmar" sin pasar por el pipeline.

## Decisión posterior (explícita, no automática)
Tras ejecutar: KILL / CONTINUE / FREEZE / PROMOTE. Si PROMOTE a estrategia (S3-B), es un HYP nuevo
con su propio pre-registro y consume evidencia externa (temporal 2019/2020 o cross-asset robustness).
