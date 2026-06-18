# CLAUDE.md

> Este archivo le dice a Claude Code dónde encontrar sus instrucciones completas.

Lee `.claude/CLAUDE.md` para la constitución completa del agente.

El orden de lectura al iniciar una sesión es:
1. Este archivo (puntero)
2. `.claude/CLAUDE.md` — constitución completa
3. `SYSTEM_VISION.md` — visión y contexto del proyecto
4. `PROJECT_STATUS.md` — estado real del proyecto (qué funciona hoy, qué no)
5. `.claude/skills/lessons-learned/log.md` — lecciones de sesiones anteriores
6. `docs/ARQUITECTURA.md` — estado técnico actual

> Guías para humanos no técnicos (Claude las usa al orientar al dueño, aunque no
> las lea entero al arrancar): `docs/ONBOARDING_NO_TECNICO.md`,
> `docs/ESTADOS_DEL_PROYECTO.md`, `docs/ANTES_DE_COMPARTIR.md`, `docs/PROMPTS_BASE.md`.
