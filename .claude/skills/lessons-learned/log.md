# Lessons Learned — Log de lecciones aprendidas

> Este archivo es la memoria persistente del proyecto.
> Claude lo lee al inicio de cada sesión para no repetir errores.
> **No borrar entradas antiguas** — son el historial de aprendizaje.

---

## Cómo añadir una lección

Di a Claude: `/nueva-leccion`
O directamente: *"Anota esto como lección aprendida: [descripción]"*

## Formato estándar

```markdown
## YYYY-MM-DD HH:MM — [Título corto]

**Error o aprendizaje:** [Qué pasó]
**Causa raíz:** [Por qué ocurrió]
**Lección:** [Qué hacer diferente en el futuro]
**Contexto:** [Dónde aplica — siempre, en ciertos módulos, etc.]
```

---

<!-- Las lecciones se añaden debajo de esta línea -->

## 2026-06-18 — Fidelidad al método de Jaime Merino (no "irse de la pinza")

**Error o aprendizaje:** Al analizar la estrategia empecé a proponer mejoras de quant
(riesgo fijo por trade en vez del 5% de Merino, filtros de entrada por "ventaja",
órdenes límite/maker, topes de pérdida inventados). Eso empezaba a desviarse del método
real de Merino.
**Causa raíz:** Sesgo de ingeniero a "optimizar" en lugar de **clonar fielmente**. El
proyecto es "Trading Latino **Purista**": el valor está en reproducir SU método, no en
inventar uno nuevo.
**Lección:** Toda regla del bot se clasifica y se respeta esa clasificación:
- 🟦 **NÚCLEO MERINO** — su método. Sagrado. No se toca ni se "mejora".
- 🟨 **REALIDAD TÉCNICA** — neutral y obligatorio (modelar comisiones/funding/slippage,
  conexión, datos). No cambia ninguna decisión suya; solo refleja el mundo real.
- 🟥 **AÑADIDO NUESTRO** — propuesta opcional. NUNCA contamina el núcleo. Solo se activa
  si el dueño lo aprueba explícitamente y el backtest lo justifica.
Ante la duda → se hace lo que hace Merino, no lo que yo creo "mejor".
**Contexto:** Siempre, en todo el diseño y código del bot.

## 2026-06-19 — Confundimos el papel del ADX en la entrada

**Error o aprendizaje:** La entrada de BTC-longs exigía ADX con pendiente NEGATIVA
("vendedores agotados"). La ablación + walk-forward mostraron que esa condición era el
fallo: rompía la robustez fuera de muestra (única variante que perdía en 2024). Invertirla
a pendiente POSITIVA (o quitarla) da una estrategia robusta: positiva en 4 de 5 años.
**Causa raíz:** Traducción mecánica errónea del método discrecional (el riesgo nº1 que ya
habíamos marcado). El ADX mide fuerza sin dirección; en un retroceso dentro de tendencia
alcista, que el ADX SUBA capta que el impulso de fondo se reactiva.
**Lección:** Validar cada condición de entrada por ABLACIÓN (quitar/invertir una a una) y
con WALK-FORWARD (varios años), nunca asumir que nuestra lectura del método es correcta.
Separar la operativa en partes y aislar el fallo es el método de trabajo.
**Contexto:** Entrada del cerebro; y método general para validar cualquier regla nueva.

## 2026-06-20 — Bug de NaN: abríamos operaciones con datos de calentamiento

**Error o aprendizaje:** En la revisión de realidad detecté que producción daba más
operaciones que el experimento. Causa: los filtros usaban `x <= 0` y `x is None`, que
NO atrapan NaN (`NaN <= 0` es False; un NaN de numpy no es None). Así, durante el
calentamiento de los indicadores, se colaban entradas con POC/ADX/stop = NaN → ¡operaciones
con stop NaN que nunca saltan bien!
**Causa raíz:** Confiar en comparaciones ingenuas con datos que pueden ser NaN.
**Lección:** Todo filtro numérico sobre indicadores debe usar un guard NaN-safe
(`x is not None and not isnan(x)`). Y reconciliar SIEMPRE producción vs experimento: si
no dan el mismo número de operaciones, hay un bug.
**Contexto:** Cualquier condición numérica del cerebro/estrategia.

