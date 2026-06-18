---
name: nuevo-sprint
description: Inicia un nuevo sprint de trabajo. Crea la estructura de seguimiento y define los objetivos con el dueño del proyecto.
---

# Comando: /nuevo-sprint

Cuando el usuario invoca este comando:

1. Pregunta: *"¿Cuál es el objetivo principal de este sprint? ¿Qué tiene que funcionar al final?"*
2. Pregunta: *"¿Cuánto tiempo tenemos? (días o semanas)"*
3. Revisa las decisiones abiertas en SYSTEM_VISION.md — si alguna bloquea el sprint, avisar
4. Crea el archivo `docs/sprints/sprint-NNN.md` con la estructura
5. Confirma el plan con el usuario antes de empezar

## Estructura del archivo de sprint

```markdown
# Sprint NNN — [Objetivo principal]

**Fecha inicio:** YYYY-MM-DD
**Fecha objetivo:** YYYY-MM-DD
**Objetivo:** [Una frase del qué tiene que funcionar]

## Tareas

- [ ] [Tarea 1]
- [ ] [Tarea 2]
- [ ] [Tarea 3]

## Decisiones abiertas que bloquean

- [Si las hay]

## Notas y contexto

[Lo relevante para este sprint]

## Resultado final

[Se rellena al cerrar el sprint]
```
