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

