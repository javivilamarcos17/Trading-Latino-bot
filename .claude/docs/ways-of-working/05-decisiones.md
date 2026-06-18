# 05 — Cómo se toman y documentan las decisiones

> Las decisiones bien documentadas evitan debates que ya se tuvieron.

---

## El problema

En proyectos con IA, es fácil que Claude reabra decisiones que ya están tomadas.
O que el equipo olvide por qué se decidió algo hace 3 meses.

## La solución: SYSTEM_VISION.md con decisiones cerradas y abiertas

### Decisiones cerradas (D1, D2...)
Son decisiones que YA están tomadas. No se reabren.

Claude NO puede cuestionarlas a menos que:
- Aparezca información nueva relevante
- El dueño del proyecto lo pida explícitamente

Ejemplo:
> **D3 — Usamos PostgreSQL como base de datos**
> Ya tenemos experiencia, infraestructura montada y el equipo lo conoce.
> Aunque SQLite fuera más sencillo para el MVP, hemos decidido no cambiar.

### Decisiones abiertas (O1, O2...)
Son preguntas sin responder que bloquean avance.

Claude debe avisar cuando una decisión abierta bloquea una tarea.
El dueño del proyecto es responsable de resolverlas.

Ejemplo:
> **O2 — ¿Los supervisores ven los partes de otros equipos?**
> Bloquea: pantalla de supervisores (Sprint 2)
> Decide: Javier antes del 20/06

---

## Cómo documentar una decisión nueva

Cuando tomes una decisión importante durante el proyecto:
1. Díselo a Claude: *"Anota esto como decisión cerrada"*
2. Claude añade la fila a SYSTEM_VISION.md con el contexto

Si surge una duda que no puedes responder ahora:
1. Díselo a Claude: *"Esto es una decisión abierta, anótala"*
2. Claude añade la fila a SYSTEM_VISION.md con el bloqueo que genera

---

## ADRs (para decisiones técnicas importantes)

Para decisiones técnicas de peso (cambiar la base de datos, cambiar el framework,
cambiar la arquitectura), Claude puede crear un ADR (Architecture Decision Record)
en `docs/decisiones/`.

Es un documento que explica:
- Qué se decidió
- Por qué
- Qué alternativas se consideraron
- Cuáles son las consecuencias

No es obligatorio para cada decisión, solo para las que pueden ser difíciles
de entender en el futuro.
