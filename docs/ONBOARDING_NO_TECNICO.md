# Onboarding para personas no técnicas — Cómo trabajar con Claude Code

> Esta guía es para **trabajar con Claude día a día** una vez tienes el proyecto montado.
> Si todavía no has instalado nada ni conectado GitHub, empieza por
> [GETTING-STARTED.md](GETTING-STARTED.md) y vuelve aquí después.
>
> No necesitas saber programar. Necesitas saber **describir lo que quieres** y
> **revisar lo que recibes**. Esta guía te enseña a hacer ambas cosas bien.

---

## La idea de fondo

Trabajas con Claude como trabajarías con un buen desarrollador de confianza:
- **Tú** aportas el negocio, las prioridades y el criterio de "esto está bien / mal".
- **Claude** aporta la parte técnica: cómo construirlo, con qué, y el rigor.

Tu trabajo no es entender el código. Tu trabajo es **dirigir y revisar.**

---

## Paso 1 — Al abrir Claude Code (cada sesión)

Lo primero, siempre, este prompt:

> *"Lee SYSTEM_VISION.md, PROJECT_STATUS.md y el log de lecciones. Cuéntame en qué
> estado está el proyecto, qué funciona hoy y cuál es la próxima decisión pendiente."*

Esto pone a Claude en contexto y te recuerda a ti dónde lo dejaste.
Si Claude empieza a trabajar sin haber leído esto, párale y pídeselo.

---

## Paso 2 — Cómo pedir cambios (bien)

**Pide el QUÉ y el PORQUÉ, no el CÓMO.** Tú describes el resultado de negocio;
Claude decide la solución técnica.

✅ **Bien:**
> *"Quiero que los supervisores puedan ver solo los partes de su propio equipo,
> no los de toda la empresa. Es por privacidad entre departamentos."*

❌ **Mal (te metes en su terreno técnico sin necesidad):**
> *"Añade un filtro SQL con un WHERE por department_id en la tabla de partes."*

**Reglas para pedir bien:**
- Una cosa a la vez. Peticiones pequeñas se revisan mejor y se rompen menos.
- Di siempre el *porqué de negocio* — ayuda a Claude a tomar mejores decisiones.
- Si es importante, di explícitamente: *"esto es para producción"* o *"esto es solo una demo"*.

---

## Paso 3 — Cómo evitar romper cosas

- **No tengas prisa por fusionar (mergear).** Pide siempre ver y probar antes.
- **Un cambio a la vez.** Si pides 5 cosas juntas y una falla, es difícil saber cuál.
- **Si algo funciona, no lo toques "por mejorar"** salvo que haya una razón clara.
- **Ante la duda, pregunta antes de aprobar:** *"¿Esto puede romper algo que ya funcionaba?"*
- **Nunca apruebes algo que no entiendes qué hace.** Pide que te lo expliquen en cristiano.

> Git guarda todo el historial. Aunque algo salga mal, casi siempre se puede volver
> atrás. Pero prevenir es más barato que reparar: revisa antes de aprobar.

---

## Paso 4 — Cómo revisar lo que Claude ha hecho

No necesitas leer código. Necesitas comprobar el **resultado**. Pide siempre esto:

> *"Antes de dar esto por bueno: explícame en lenguaje normal qué has cambiado,
> cómo lo pruebo yo mismo paso a paso, y si esto cambia el estado del PROJECT_STATUS."*

Luego **pruébalo tú**. Si Claude dice "ya funciona", tu trabajo es verificarlo
con tus propios ojos siguiendo sus pasos. "Funciona en mi máquina" no basta.

Checklist mental al revisar:
- [ ] ¿Hace lo que pedí?
- [ ] ¿Lo he probado yo y lo he visto funcionar?
- [ ] ¿Entiendo, en lenguaje normal, qué se cambió?
- [ ] ¿Se actualizó `PROJECT_STATUS.md` si el estado cambió?

---

## Paso 5 — Cuándo parar y decidir

Claude debe pararse y preguntarte cuando hay una decisión de negocio. Si no lo hace
y notas que está "inventando" reglas de tu negocio, párale:

> *"Para. Eso es una decisión de negocio, no técnica. Pregúntame antes de asumir."*

---

## Paso 6 — Pedir una auditoría antes de compartir

Antes de enseñar el proyecto a un socio, cliente, inversor o técnico externo,
pide SIEMPRE una auditoría. Prompt recomendado:

> *"Voy a enseñar este proyecto a [un inversor / un cliente / un técnico]. Audita el
> repo siguiendo docs/ANTES_DE_COMPARTIR.md: comprueba que no hay secretos ni claves,
> que el README y el PROJECT_STATUS están personalizados y son honestos, qué es demo
> y qué es real, y qué riesgos debería conocer antes de enseñarlo. Dame un informe claro."*

Detalles en [ANTES_DE_COMPARTIR.md](ANTES_DE_COMPARTIR.md).

---

## Errores típicos de principiante (y cómo evitarlos)

| Error | Consecuencia | Cómo evitarlo |
|-------|--------------|---------------|
| Aprobar sin probar | Crees que funciona y no funciona | Pruébalo tú siempre |
| Pedir 10 cosas a la vez | Si algo falla, no sabes qué fue | Una cosa a la vez |
| Confundir demo con producto | Vendes humo a un tercero | Lee [ESTADOS_DEL_PROYECTO.md](ESTADOS_DEL_PROYECTO.md) |
| No decir el porqué de negocio | Claude decide a ciegas | Explica siempre el contexto |
| Enseñar el repo sin auditar | Filtras claves o datos sensibles | Usa [ANTES_DE_COMPARTIR.md](ANTES_DE_COMPARTIR.md) |

---

## Prompts listos para copiar

Tienes una colección completa en [PROMPTS_BASE.md](PROMPTS_BASE.md).
Los más usados: arrancar sesión, pedir cambios, revisar, auditar antes de compartir.
