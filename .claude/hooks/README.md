# Hooks — ¿Qué son y para qué sirven?

> **En lenguaje normal:** Los hooks son pequeños programas que se ejecutan
> automáticamente en momentos concretos — como alarmas que se activan solas.
> Tú no tienes que hacer nada para que funcionen.

---

## Los hooks de este proyecto

### SessionStart.sh
**Cuándo se ejecuta:** Al abrir Claude Code
**Qué hace:** Muestra un resumen del estado del proyecto — rama actual, últimos
cambios, lecciones aprendidas. Como el "buenos días" del proyecto.

### PreToolUse.sh
**Cuándo se ejecuta:** Antes de que Claude ejecute cualquier comando
**Qué hace:** Bloquea operaciones peligrosas. Es el "guardián" que impide que
Claude borre la base de datos o haga un push forzado por accidente.

### PostToolUse.sh
**Cuándo se ejecuta:** Después de que Claude edite o cree archivos
**Qué hace:** Registra un log de auditoría. Sirve para saber qué cambió y cuándo.

### Stop.sh
**Cuándo se ejecuta:** Al cerrar la sesión de Claude Code
**Qué hace:** Recuerda verificar que no quedan cambios sin guardar y que se
han registrado las lecciones aprendidas de la sesión.

### block-subagent-external.py
**Cuándo se ejecuta:** Cuando Claude usa un agente especialista
**Qué hace:** Los agentes especialistas no pueden hacer push ni deploy solos.
Solo Claude en conversación directa contigo puede hacer operaciones externas.

### log-subagent-spawn.py
**Cuándo se ejecuta:** Cuando Claude activa un agente especialista
**Qué hace:** Registra en un log cuándo y qué agente se activó. Trazabilidad.

---

## ¿Puedo modificarlos?

Sí, pero con cuidado. Pídele a Claude que lo haga y que te explique qué cambia.
