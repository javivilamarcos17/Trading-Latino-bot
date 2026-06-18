---
name: nueva-leccion
description: Registra una nueva lección aprendida en el log de lessons-learned. Usar inmediatamente tras una corrección.
---

# Comando: /nueva-leccion

Cuando el usuario invoca este comando:

1. Pregunta: *"¿Qué pasó? Descríbeme el error o la corrección en tus propias palabras."*
2. Entiende la causa raíz
3. Redacta una lección clara en el formato estándar
4. La añade a `.claude/skills/lessons-learned/log.md`
5. Confirma: *"Lección registrada. ¿Continuamos?"*

## Formato a usar

```markdown
## YYYY-MM-DD HH:MM — [Título corto descriptivo]

**Error o aprendizaje:** [Qué pasó exactamente]
**Causa raíz:** [Por qué ocurrió — no la consecuencia, sino el origen]
**Lección:** [Qué hacer diferente a partir de ahora — concreto y accionable]
**Contexto:** [Dónde aplica esta lección]
```

## Reglas al redactar

- El título debe poder leerse de un vistazo y entenderse
- La lección debe ser accionable — que Claude sepa exactamente qué hacer diferente
- Si la lección contradice el comportamiento por defecto, especificarlo
- No usar tecnicismos si el error fue de comunicación con el usuario
