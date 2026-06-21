# 🎯 Riesgos de rentabilidad y cómo los solventamos

> Este documento convierte la "autopsia anticipada" (¿dónde fallará?) en un **plan de
> soluciones**. Guía qué debe medir el backtest y qué decidiremos según los resultados.
> Filosofía: **no adivinamos si gana; lo medimos, en neto, sin autoengaños.**

**Dónde se juega la rentabilidad, en una frase:** que la **ventaja neta supere los costes**,
y eso depende sobre todo de la **regla de salida**; el mayor riesgo de fondo es la **brecha
entre el Merino discrecional y el bot mecánico**.

---

## Costes reales (confirmados) — Hyperliquid

| Coste | Valor | Nota |
|-------|-------|------|
| Comisión taker | **0,045%** por lado | órdenes a mercado (lo que usa Merino) |
| Comisión maker | **0,015%** por lado | órdenes límite |
| Funding | **cada hora** (1/8 del ritmo de 8h), tope 4%/h | en shorts suele ir a favor si el funding es positivo |
| Slippage | estimado 0,05% | a someter a sensibilidad |

Ida y vuelta a mercado ≈ **0,09%** + slippage + funding (×24-32 cobros). Lo modelamos exacto.

---

## Riesgo 1 — El muro de los costes *(el punto crítico)*
**Solución:**
- Modelo de costes exacto (arriba) en cada operación; **todas las métricas en neto**.
- **Barrido de sensibilidad a costes** (`BARRIDO_COSTES = 0 / 0.5x / 1x / 2x`): vemos a partir
  de qué nivel de coste deja de ganar → cuánto **margen** real tenemos.
- Palancas si hace falta: filtro de entrada por ventaja (objetivo ≥ N× coste) 🟥 y órdenes maker 🟥.
- **Gate:** si solo gana con costes < 1× los reales → no es viable.

## Riesgo 2 — La regla de salida *(la palanca nº1 del beneficio)*
**Solución:** la salida será un **módulo configurable** y compararemos variantes en el backtest:
1. Giro del Squeeze (purista de Merino) · 2. Siguiente muralla de volumen (POC) ·
3. Trailing stop · 4. Múltiplo de R fijo · 5. Toma parcial + dejar correr el resto.
Medimos cuál da mejor resultado **neto**; el dueño fija el "default purista".

## Riesgo 3 — Brecha discrecional → mecánico *(el más subestimado)*
**Solución (triple):**
- **Codificar los filtros objetivables** del criterio humano: ADX fuerte, "no operar en lateral",
  calidad mínima del setup → menos operaciones marginales que él se saltaría.
- **Validar contra sus operaciones reales:** tú me das fechas/setups de sus directos y
  comprobamos que el bot habría señalado lo mismo (o por qué no).
- **Humildad:** la versión mecánica es la BASE; aceptamos que quizá necesite filtros
  inspirados en su criterio. Si la ventaja vivía solo en su discreción, hay que saberlo.

## Riesgo 4 — Sobreajuste (curva ajustada al pasado)
**Solución:**
- **Validación fuera de muestra:** ajustamos en 2021-2023 (`FECHA_FIN_ENTRENAMIENTO`) y
  validamos en 2024-2025, que el bot NO vio al calibrar.
- Pocos parámetros tuneables; preferir **robustez** (mesetas de resultados) a picos.

## Riesgo 5 — Dependencia del régimen (gana en tendencia, sangra en lateral)
**Solución:**
- El **ADX > 23 ya es un filtro de régimen** (fuerza de tendencia) — nos apoyamos en él.
- Filtro extra de "no operar en lateral" 🟥 a probar.
- **Informe desglosado por régimen** (tendencia vs lateral) para verlo, no intuirlo.

## Riesgo 6 — Módulo de alt-shorts (pocas operaciones, short squeeze)
**Solución:** probar por separado (ya decidido); reportar **nº de operaciones y significancia**;
ampliar universo/periodo si hacen falta más muestras; topes de riesgo duros por colas de squeeze.

## Riesgo 7 — Fills y slippage optimistas
**Solución:** slippage conservador + **barrido de sensibilidad**; universo de alts líquidas;
en operativa real, preferir órdenes límite.

---

## Qué DEBE medir el backtest (instrumentación obligatoria)
- Métricas **en neto**, separadas **por módulo** (BTC-long / alt-short) y **por régimen**.
- **Barrido de costes** y de slippage (margen sobre el muro de costes).
- Distribución de **R** (payoff), **rachas** de pérdidas, **drawdown**, **nº de operaciones**.
- Resultados **dentro vs fuera de muestra** (entrenamiento vs test).

## Gates de decisión (honestidad antes que ilusión)
- 🟢 **Verde:** gana neto **fuera de muestra**, con costes ≥1× y aguantando slippage → pasar a paper.
- 🟡 **Ámbar:** gana solo en muestra o solo con costes irreales → iterar salida/filtros, **no** arriesgar.
- 🔴 **Rojo:** no gana ni ajustando razonablemente → **no operar con dinero real**; documentar el aprendizaje.

---

## Info que aún conviene conseguir
- Funding **histórico** real (para el coste exacto en backtest; de momento se puede estimar).
- Definición fina de las reglas discrecionales de Merino (de sus directos, con ayuda del dueño).
- Comprobar que los resultados con datos de Binance **transfieren** a Hyperliquid (precios casi iguales).

---

*Mantiene: Claude (con validación del dueño). Este documento manda sobre qué mide la Fase 5.*
