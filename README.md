# Claude Project Template — Sistema operativo de proyecto

> Una plantilla para construir proyectos reales con **Claude Code** de forma
> **ordenada, profesional y segura** — aunque no tengas conocimientos técnicos.
>
> **Tú aportas el negocio. Claude actúa como tu técnico.**
> La plantilla pone las reglas, la estructura y las protecciones para que esa
> colaboración salga bien y para que **siempre sepas en qué estado real está tu proyecto.**

> ℹ️ **Esto es una plantilla, no tu proyecto todavía.** Acabas de copiar el molde.
> Hasta que no lo rellenes y empieces a construir, el proyecto está en estado **💡 Idea**
> (lo verás reflejado en [PROJECT_STATUS.md](PROJECT_STATUS.md)).

---

## ¿Qué es esto?

Una carpeta preparada para que, al abrirla con Claude Code, Claude tenga todo el
contexto necesario para trabajar bien y, sobre todo, para que **tú siempre puedas
entender**, sin leer código:

- 🟢 **qué es** el proyecto → [SYSTEM_VISION.md](SYSTEM_VISION.md)
- 📊 **en qué estado está** y qué funciona de verdad hoy → [PROJECT_STATUS.md](PROJECT_STATUS.md)
- 🪜 **qué significa cada etapa** (idea, demo, MVP, producción) → [docs/ESTADOS_DEL_PROYECTO.md](docs/ESTADOS_DEL_PROYECTO.md)
- 🤝 **cómo trabajar con Claude** → [docs/ONBOARDING_NO_TECNICO.md](docs/ONBOARDING_NO_TECNICO.md)
- 🔒 **cuándo se puede compartir** con terceros → [docs/ANTES_DE_COMPARTIR.md](docs/ANTES_DE_COMPARTIR.md)

## ¿Para quién es?

Para **personas con un buen conocimiento de su negocio pero sin perfil técnico**
que quieren construir software con Claude Code sin perder el control ni hacerse
falsas ilusiones sobre el avance real.

---

## Empezar en 4 pasos

```
1. Copia esta carpeta y renómbrala con el nombre de tu proyecto.
2. Rellena SYSTEM_VISION.md (qué es, para quién, objetivo).
3. Abre la carpeta en Claude Code y dile:
   "Lee SYSTEM_VISION.md y PROJECT_STATUS.md y cuéntame qué entiendes."
4. A partir de ahí, Claude te guía.
```

¿Primera vez con esto? Sigue la guía completa en **[docs/GETTING-STARTED.md](docs/GETTING-STARTED.md)**
(instalar, conectar GitHub, primera sesión). Y para el día a día con Claude:
**[docs/ONBOARDING_NO_TECNICO.md](docs/ONBOARDING_NO_TECNICO.md)**.

---

## Los 3 archivos que TÚ rellenas

| Archivo | Qué es | Cuándo |
|---------|--------|--------|
| **[SYSTEM_VISION.md](SYSTEM_VISION.md)** | La visión: qué construyes, para quién, qué decisiones están tomadas | Al empezar, y lo vas completando |
| **[PROJECT_STATUS.md](PROJECT_STATUS.md)** | El estado real: qué funciona hoy, qué no, qué falta decidir | Lo mantiene Claude, tú lo validas |
| **[.claude/skills/project-context/SKILL.md](.claude/skills/project-context/SKILL.md)** | Contexto de negocio que Claude necesita para decidir bien | Cuando tu negocio tenga reglas que Claude deba conocer |

> El resto de archivos los **mantiene Claude por ti** (arquitectura, changelog, roadmap...).
> Tú solo los lees cuando quieras entender algo.

## Archivos que NO deberías tocar sin entenderlos

Estos definen *cómo se comporta Claude y qué protecciones tienes*. Funcionan solos.
Cámbialos solo si sabes lo que haces (o pídele a Claude que te explique antes):

- **[CLAUDE.md](CLAUDE.md)** y **[.claude/CLAUDE.md](.claude/CLAUDE.md)** — las reglas del agente (su "constitución").
- **[.claude/hooks/](.claude/hooks/README.md)** — protecciones de seguridad automáticas.
- **[.claude/settings.json](.claude/settings.json)** — configuración técnica de Claude Code.
- **[.gitignore](.gitignore)** y **[.env.example](.env.example)** — protegen tus secretos. No los vacíes.

---

## Cómo trabajar con Claude Code

El detalle está en [docs/ONBOARDING_NO_TECNICO.md](docs/ONBOARDING_NO_TECNICO.md), pero en resumen:

1. **Pide el QUÉ y el PORQUÉ**, no el CÓMO. Tú describes el resultado de negocio; Claude decide lo técnico.
2. **Una cosa a la vez.** Los cambios pequeños se revisan mejor y se rompen menos.
3. **Revisa antes de aprobar.** Pide que te expliquen el cambio en lenguaje normal y pruébalo tú.
4. **Antes de compartir con alguien**, pide una auditoría con [docs/ANTES_DE_COMPARTIR.md](docs/ANTES_DE_COMPARTIR.md).

Tienes prompts listos para copiar y pegar en **[docs/PROMPTS_BASE.md](docs/PROMPTS_BASE.md)**.

## Flujo recomendado de trabajo

```
Abrir sesión  →  "Lee SYSTEM_VISION + PROJECT_STATUS y dime el estado"
      ↓
Pedir un cambio concreto (con su porqué de negocio)
      ↓
Claude propone / construye  →  te explica qué hizo
      ↓
Tú lo pruebas y lo apruebas  →  Claude actualiza PROJECT_STATUS
      ↓
Antes de enseñarlo a alguien  →  auditoría (ANTES_DE_COMPARTIR.md)
```

---

## Mapa de la plantilla

### Raíz — lo que más usarás
- **[SYSTEM_VISION.md](SYSTEM_VISION.md)** ⭐ — la visión (tú la rellenas).
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** 📊 — el estado real y honesto, de un vistazo.
- **[CLAUDE.md](CLAUDE.md)** — puntero a las reglas del agente.

### `docs/` — para personas, no para Claude
- **[GETTING-STARTED.md](docs/GETTING-STARTED.md)** — arrancar desde cero (instalar, GitHub).
- **[ONBOARDING_NO_TECNICO.md](docs/ONBOARDING_NO_TECNICO.md)** — cómo trabajar con Claude día a día.
- **[ESTADOS_DEL_PROYECTO.md](docs/ESTADOS_DEL_PROYECTO.md)** — qué es idea / demo / MVP / producción.
- **[ANTES_DE_COMPARTIR.md](docs/ANTES_DE_COMPARTIR.md)** — checklist antes de enseñar el repo.
- **[PROMPTS_BASE.md](docs/PROMPTS_BASE.md)** — prompts listos para copiar.
- **[DICCIONARIO.md](docs/DICCIONARIO.md)** — términos técnicos en lenguaje normal.
- **[ARQUITECTURA.md](docs/ARQUITECTURA.md)** · **[ROADMAP.md](docs/ROADMAP.md)** · **[CHANGELOG.md](docs/CHANGELOG.md)** — Claude los mantiene.
- **[decisiones/](docs/decisiones/README.md)** · **[sprints/](docs/sprints/README.md)** — historial de decisiones y trabajo.

### `.claude/` — cómo se comporta Claude (funciona solo)
- **[CLAUDE.md](.claude/CLAUDE.md)** — constitución del agente.
- **[hooks/](.claude/hooks/README.md)** — automatizaciones y protecciones de seguridad.
- **[agents/](.claude/agents/README.md)** — agentes especializados (arquitectura, negocio...).
- **[skills/](.claude/skills/)** — conocimiento: lecciones aprendidas, protocolo Git, contexto de negocio.
- **[commands/](.claude/commands/)** — atajos `/nueva-leccion`, `/revisar-cambios`, `/nuevo-sprint`.
- **[memory/](.claude/memory/README.md)** — memoria persistente entre sesiones.

### `.github/` — automatización en GitHub
- **CI** — comprueba que la **documentación** está en orden (NO que el producto funcione; ver [el propio CI](.github/workflows/ci.yml)).
- **PR template** — checklist de revisión antes de aprobar cambios.

---

## ¿Es mucho? No tienes que entenderlo todo

Para empezar solo necesitas cuatro archivos:
1. [SYSTEM_VISION.md](SYSTEM_VISION.md) — rellénalo.
2. [PROJECT_STATUS.md](PROJECT_STATUS.md) — consulta el estado real (lo mantiene Claude).
3. [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) — sigue los pasos.
4. [docs/DICCIONARIO.md](docs/DICCIONARIO.md) — consúltalo cuando aparezca algo desconocido.

**El resto lo gestiona Claude.**
