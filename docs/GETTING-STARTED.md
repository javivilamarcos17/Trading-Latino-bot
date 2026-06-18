# Getting Started — Cómo arrancar un proyecto nuevo

> Guía paso a paso para empezar desde cero con esta plantilla.
> Diseñada para alguien que no tiene experiencia técnica previa.

---

## Antes de empezar: lo que necesitas

- [ ] **Claude Code** instalado ([descarga aquí](https://claude.ai/download))
- [ ] **Git** instalado ([descarga aquí](https://git-scm.com/downloads)) — el instalador por defecto está bien
- [ ] **Una cuenta en GitHub** (gratis en [github.com](https://github.com))
- [ ] **Node.js** si tu proyecto es web ([descarga aquí](https://nodejs.org)) — la versión LTS
- [ ] Tu proyecto ya tiene nombre y sabes aproximadamente qué vas a construir

---

## Paso 1 — Copiar la plantilla

1. Descarga o copia la carpeta `claude-project-template`
2. Renómbrala con el nombre de tu proyecto (ej: `mi-app-de-partes`)
3. Muévela a donde quieras trabajar (escritorio, documentos, etc.)

---

## Paso 2 — Rellenar la visión del proyecto

Abre el archivo `SYSTEM_VISION.md` con cualquier editor de texto (el Bloc de notas vale).

Rellena al menos estas secciones:
- ¿Qué es este proyecto?
- ¿Para quién es?
- ¿Cuál es el objetivo central?

No hace falta rellenarlo todo ahora. Lo irás completando con Claude.

---

## Paso 3 — Conectar a GitHub

1. Ve a [github.com/new](https://github.com/new) y crea un repositorio nuevo
   - Nombre: el mismo que tu carpeta (ej: `mi-app-de-partes`)
   - Visibilidad: Privado si los datos son sensibles
   - NO marques "Add a README" ni nada más — la plantilla ya lo trae todo

2. Abre la carpeta del proyecto en Claude Code

3. Dile a Claude:
   > *"Inicializa git y conecta este proyecto al repositorio de GitHub que acabo
   > de crear. La URL es: [pega aquí la URL de tu repo]"*

Claude hará el resto.

---

## Paso 4 — Primera sesión de trabajo

Abre Claude Code en la carpeta del proyecto y dile:

> *"Lee el SYSTEM_VISION.md y el CLAUDE.md y cuéntame qué entiendes del proyecto
> hasta ahora. Luego hazme las preguntas que necesites para poder empezar."*

Claude leerá los documentos, te resumirá lo que entendió y te hará las preguntas
necesarias. A partir de ahí, empieza el trabajo real.

---

## Paso 5 — Flujo de trabajo diario

Una vez el proyecto está en marcha, cada sesión de trabajo es así:

1. **Abrís Claude Code** → Claude lee el estado del proyecto automáticamente
2. **Describes lo que quieres** en lenguaje natural
3. **Claude trabaja** — te va informando de lo que hace
4. **Revisas y apruebas** los cambios
5. **Al cerrar**, Claude recuerda anotar las lecciones de la sesión

No hay más complejidad que esa.

---

## Preguntas frecuentes

### ¿Tengo que aprender a programar?
No. Para usar esta plantilla y trabajar con Claude, no necesitas saber código.
Lo que sí necesitas es saber describir claramente qué quieres que haga tu aplicación.

### ¿Qué hago si algo no funciona?
Descríbeselo a Claude en lenguaje normal: "Cuando hago X, pasa Y, pero esperaba Z".
Claude investigará y te dirá qué pasó.

### ¿Puedo compartir el proyecto con mi equipo?
Sí. Una vez conectado a GitHub, invita a tu equipo al repositorio desde
la configuración de GitHub. Cada persona trabajará en su propia sesión de Claude Code.

### ¿Se puede perder trabajo?
Git guarda todo el historial. Mientras hagas commits regularmente (Claude lo hace
por ti), no se pierde nada. En el peor caso, se puede volver a cualquier versión anterior.

### ¿Cuánto cuesta Claude Code?
Consulta los planes en [claude.ai](https://claude.ai). Hay planes para individuos
y para equipos.

---

## Necesito ayuda

Si algo no funciona o no entiendes algo, el mejor recurso es preguntarle
directamente a Claude en lenguaje natural. Claude está diseñado para este proyecto
y conoce su estructura.
