# Changelog — Historial de cambios

> Registro de todos los cambios significativos del proyecto.
> El más reciente siempre arriba.
> Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)

---

## [Sin publicar]

> Los cambios en desarrollo van aquí hasta que se publican.

---

## [0.2.0] — 2026-06-17 — La plantilla como sistema operativo de proyecto

> Mejora de la plantilla para convertirla en un "sistema operativo de proyecto"
> orientado a personas no técnicas, con foco en evitar la falsa sensación de avance.

### Añadido
- `PROJECT_STATUS.md` — estado real del proyecto de un vistazo (etapa, qué funciona
  hoy, qué no, cómo probarlo, decisiones, riesgos, nivel de confianza).
- `docs/ESTADOS_DEL_PROYECTO.md` — definición clara de las 6 etapas (idea, documentación,
  demo, prototipo, MVP, producción) para no confundir "enseñable" con "terminado".
- `docs/ONBOARDING_NO_TECNICO.md` — cómo trabajar con Claude día a día: pedir cambios,
  revisar, evitar romper cosas, pedir auditorías.
- `docs/ANTES_DE_COMPARTIR.md` — checklist obligatorio antes de enseñar el repo a
  socios, clientes, inversores, técnicos o trabajadores.
- `docs/PROMPTS_BASE.md` — prompts reutilizables (arrancar, auditar, documentar, backlog,
  preparar para compartir, revisar seguridad).

### Cambiado
- `README.md` — reescrito: explica qué es la plantilla, para quién, cómo usarla, qué
  archivos rellenar, cuáles no tocar y el flujo de trabajo recomendado.
- `.github/workflows/ci.yml` — CI honesto: verifica archivos obligatorios y avisa si
  README/PROJECT_STATUS siguen genéricos, sin dar falsa seguridad. El job de tests del
  producto queda desactivado y documentado hasta que exista stack técnico.
- `CLAUDE.md` y `.claude/CLAUDE.md` — añadido `PROJECT_STATUS.md` al orden de lectura,
  regla de mantenerlo honesto y obligación de distinguir documentación/demo/producción.

---

<!-- Claude añade entradas aquí siguiendo este formato:

## [1.0.0] — YYYY-MM-DD

### Añadido
- Nueva funcionalidad X que permite Y

### Cambiado
- El flujo de Z ahora funciona así en lugar de asá

### Corregido
- El error que ocurría cuando...

### Eliminado
- Se eliminó la funcionalidad X porque...

-->
