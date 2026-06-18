# Prompts base — Copia, pega y adapta

> Una colección de instrucciones listas para darle a Claude Code.
> No tienes que escribirlas de memoria: copia la que necesites, cambia lo que está
> [entre corchetes] y pégala.
>
> Consejo: di siempre el **porqué de negocio** y, si importa, si algo es
> **demo o producción**. Cuanto mejor el contexto, mejor el resultado.

---

## 🟢 Cada vez que abres una sesión

```
Lee SYSTEM_VISION.md, PROJECT_STATUS.md y el log de lecciones aprendidas.
Cuéntame en qué estado está el proyecto, qué funciona hoy, qué no, y cuál es
la próxima decisión pendiente. No empieces a cambiar nada todavía.
```

---

## 🚀 Iniciar un proyecto desde cero

```
Quiero arrancar este proyecto. Voy a contarte la idea y quiero que me ayudes a
rellenar SYSTEM_VISION.md haciéndome preguntas, una a una, en lenguaje normal.
La idea es: [describe en 3-4 frases qué quieres construir y para quién].
Cuando tengamos la visión clara, actualiza PROJECT_STATUS.md al estado real.
```

---

## 🔍 Auditar el estado del proyecto

```
Audita el estado real de este proyecto. Quiero saber, sin optimismo:
- ¿En qué etapa estamos de verdad? (idea / documentación / demo / prototipo / MVP / producción)
- ¿Qué funciona HOY que hayas comprobado, y qué solo está empezado o escrito?
- ¿Coincide PROJECT_STATUS.md con la realidad? Si no, dime las diferencias.
- ¿Qué riesgos abiertos hay?
Sé honesto aunque el resultado sea incómodo. Prefiero la verdad a la motivación.
```

---

## 📝 Mejorar la documentación

```
Revisa la documentación del proyecto (README, PROJECT_STATUS, ARQUITECTURA,
SYSTEM_VISION) y dime qué está desactualizado, qué es genérico todavía sin rellenar,
y qué le faltaría a alguien nuevo para entender el proyecto. Luego propón los cambios
antes de hacerlos.
```

---

## 📋 Crear o actualizar el backlog (lista de trabajo)

```
A partir de SYSTEM_VISION.md y de lo que ya está construido, propón un backlog
ordenado por prioridad en docs/ROADMAP.md: qué construir primero para llegar al MVP
más rápido. Para cada cosa, dime en una frase qué valor de negocio aporta y, a grandes
rasgos, cuánto esfuerzo lleva (poco / medio / mucho). Pregúntame antes de fijar el orden.
```

---

## 🤝 Preparar el proyecto para compartir

```
Voy a enseñar este proyecto a [un inversor / un cliente / un técnico externo / un
nuevo trabajador]. Audita el repo siguiendo docs/ANTES_DE_COMPARTIR.md punto por punto.
Dime: si hay secretos o datos sensibles, si el README y PROJECT_STATUS son honestos y
están personalizados, qué es demo y qué es real, y qué riesgos debería conocer antes
de enseñarlo. Dame un informe claro con semáforo (🔴/🟡/🟢) por cada punto.
```

---

## 🔐 Revisar seguridad y datos sensibles

```
Haz una revisión de seguridad de este repositorio pensada para una persona no técnica:
- ¿Hay algún secreto, contraseña, clave de API o token dentro del código o subido por error?
- ¿Hay datos personales o reales de clientes/empleados que no deberían estar aquí?
- ¿El .gitignore protege bien los archivos sensibles?
- ¿Algún secreto se subió alguna vez al historial y habría que rotar (cambiar)?
Explícame cada hallazgo en lenguaje normal y qué debo hacer con él, por orden de gravedad.
```

---

## ✅ Revisar un cambio antes de aprobarlo

```
Antes de dar esto por bueno: explícame en lenguaje normal qué has cambiado y por qué,
dame los pasos exactos para probarlo yo mismo, dime si esto puede romper algo que ya
funcionaba, y si cambia el estado del proyecto actualiza PROJECT_STATUS.md.
```

---

## 🛑 Cuando Claude está asumiendo cosas de tu negocio

```
Para. Eso es una decisión de negocio, no técnica, y la tomo yo. No asumas reglas de
mi negocio sin preguntarme. Dime qué necesitas saber y te lo aclaro.
```

---

## 📌 Registrar una decisión importante

```
Acabamos de decidir: [describe la decisión y el porqué]. Regístrala donde corresponda
(SYSTEM_VISION.md si es una decisión cerrada, docs/decisiones/ si es técnica relevante)
y actualiza PROJECT_STATUS.md con la última decisión tomada.
```

---

## 🧹 Cerrar la sesión

```
Vamos a cerrar. Resume qué hemos hecho hoy, actualiza PROJECT_STATUS.md y el CHANGELOG
si corresponde, y si he corregido algo tuyo durante la sesión, anótalo como lección
aprendida. Dime qué queda pendiente para la próxima vez.
```
