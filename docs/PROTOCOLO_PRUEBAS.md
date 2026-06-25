# PROTOCOLO DE PRUEBAS Y MODIFICACIONES

> El pipeline profesional para evaluar CUALQUIER estrategia de la misma forma, de modo que
> los resultados sean **comparables** y las decisiones (mantener / modificar / quitar) se tomen
> con criterio, no a ojo. Esto es lo que convierte "tests sueltos" en investigación cuantitativa.

## Las dos fuentes de datos (y para qué sirve cada una)

| Fuente | Qué es | Para qué |
|--------|--------|----------|
| **VIVO** (arena, Hyperliquid) | Datos forward, 24/7, contexto rico (funding/OI/F&G), salidas 1m | El juez **sin sesgo** del régimen ACTUAL. Genera hipótesis. Es lo más real. |
| **HISTÓRICO** (Binance, años) | 2021→hoy, todas las TF | El juez **multi-régimen**: ¿sobrevive a toro/lateral/oso? Valida hipótesis. |

> **Regla de oro:** el VIVO manda sobre el histórico cuando se contradicen (es lo más real),
> pero el histórico es el único que ve regímenes que el vivo aún no ha vivido.

## El pipeline — toda estrategia pasa por las MISMAS etapas

**ETAPA 1 — MULTI-TEMPORALIDAD.** Probar en 5m / 15m / 1h / 4h. ¿Cuál es SU mejor temporalidad?
(Lección: Merino brilla en 4h, no en 15m. Una estrategia mal medida en la TF equivocada parece muerta.)

**ETAPA 2 — MULTI-RÉGIMEN.** En su mejor TF, desglosar por clima: **alcista / lateral / bajista**
(retorno de 90 días, sin lookahead). ¿Gana en varios climas o solo en uno?

**ETAPA 3 — DIRECCIÓN.** Separar largos vs cortos. En oso los cortos mandan; no confundir
"estrategia mala" con "régimen en contra de su lado largo".

**ETAPA 4 — COSTES REALES.** Restar comisión (0.08% ida+vuelta) + slippage medido del spread
en vivo (~0.006R). Un edge que no sobrevive a costes no existe.

**ETAPA 5 — VEREDICTO** (comparable entre todas):
- **ROBUSTA** = NETO positivo en ≥2 climas → sirve en varios mercados (núcleo).
- **DE RÉGIMEN** = NETO positivo en 1 clima → herramienta de banquillo para ese clima (router).
- **DESCARTAR** = no es positivo neto en ningún clima.

**ETAPA 6 — FORWARD EN VIVO.** La que pasa entra en la arena a recoger datos forward sin sesgo.
Si el vivo confirma → sube de categoría. Si lo contradice → manda el vivo.

## Guardas anti-autoengaño (innegociables)

1. **n mínimo** (≥30 para veredicto, ≥20 por celda). Pocos datos = ruido, no edge.
2. **Consistencia** entre 3 monedas y 3 climas > un slice aislado espectacular.
3. **Hipótesis con lógica económica** antes de probar (no parámetros al azar = data-mining).
4. **Los números del vivo se de-inflan** vs out-of-sample (medido: ×6-8 en la familia OB).

## Herramientas que implementan el protocolo

- `research/protocolo.py` — el pipeline completo (etapas 1-5) → SCORECARD comparable.
- `research/estudio.py` — análisis del vivo por condiciones (pockets/leaks/exits/riesgo/simular).
- `research/backtest_largo.py` — multi-año 15m con desglose por régimen.
- `research/merino_mtf.py` / `scalp_lab.py` — focos puntuales (Merino multi-TF, scalping 5m).

## Cómo se usa para CREAR y PODAR estrategias

1. Llega una idea (hipótesis con lógica). Se implementa como detector.
2. Se pasa por `protocolo.py` → scorecard (mejor TF, régimen, neto, veredicto).
3. ROBUSTA o DE RÉGIMEN → a la arena (forward-test). DESCARTAR → fuera, documentado.
4. Periódicamente se re-corre el protocolo sobre TODO → se poda lo que dejó de funcionar.
