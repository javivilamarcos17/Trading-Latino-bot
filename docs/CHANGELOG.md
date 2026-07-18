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


## 2026-07-18 — Sesión de investigación continua (propuestas + auditoría r6)

### Añadido
- Semáforo: 4ª luz (carry) + dial de persistencia de funding + dial de fase (contexto n/3).
- `monitor_carry.py`: puente semáforo→cesta del motor 3 con triggers de desmontaje.
- `barrido_5m.py`: última casilla del mapa de temporalidades (5min nativo 2024-26).

### Decidido con datos (STATUS §5, entradas 19f-19o)
- Descartes: arma de techo, estacionalidad horaria era-ETF, ventana fixing ETF, dial lead-lag
  cross-venue (redundante con persistencia propia), be05 como salida del núcleo (fixed gana 4/6 años).
- Confirmado: lead-lag estadístico de funding; dial de fase como contexto (familia de ventanas robusta).
- Retractado tras auditoría r6: regla del "2º disparo" (n=2) y "relevo de régimen en vivo" (percentil 60-71).

### Corregido
- Ejecución: taker en entradas de ruptura (la evidencia publicada mata el maker en breakouts).
- Lección operativa: procesos largos siempre con seguimiento del harness.
