# Diccionario — Términos técnicos en lenguaje normal

> Si escuchas una palabra técnica que no entiendes, búscala aquí.
> Están ordenadas de más frecuentes a menos frecuentes.

---

## Los más importantes

### Repositorio (repo)
La carpeta del proyecto, pero en versión controlada. Guarda no solo los archivos
actuales, sino TODO el historial de cambios. Es como un Google Drive que recuerda
cada versión de cada archivo desde el principio.

### Git
El sistema que gestiona el repositorio. Permite guardar versiones, trabajar
en paralelo y volver atrás si algo sale mal. **Tú no necesitas usar Git
directamente — Claude lo hace por ti.**

### Commit
Un "punto de guardado" del proyecto con un mensaje que describe qué cambió.
Como guardar una partida de videojuego con una nota de dónde estás.
Ejemplo: *"feat: añadir pantalla de login"*

### Rama (branch)
Una copia de trabajo paralela del proyecto donde se hacen cambios sin afectar
a la versión principal. Cuando los cambios están listos, se fusionan con `main`.
Como trabajar en un borrador antes de enviarlo.

### Main
La rama principal — la versión "oficial" del proyecto. Es la que está en
producción o la que se enseña al cliente. Claude nunca toca `main` directamente.

### Pull Request (PR)
Una "solicitud de revisión" — Claude dice "tengo estos cambios listos, ¿los aprobamos?"
Es el momento de revisar antes de que los cambios lleguen a `main`.

### Deploy / Despliegue
Publicar el proyecto para que los usuarios reales puedan usarlo. Como "subir"
la app a internet. Solo se hace cuando todo está revisado y aprobado.

---

## Sobre la arquitectura

### Frontend
La parte visual de la aplicación — lo que ve y toca el usuario. Pantallas,
botones, formularios, gráficos.

### Backend
La parte invisible que hace funcionar todo — el servidor, la base de datos,
la lógica de negocio. El usuario no lo ve pero lo usa constantemente.

### Base de datos
Donde se guardan los datos de forma organizada y permanente. Como un Excel
muy potente y seguro al que accede la aplicación automáticamente.

### API
La "puerta" por la que el frontend habla con el backend. Cuando el usuario
hace clic en "Guardar", el frontend envía una petición al backend a través
de la API.
Ejemplo: *"Cuando el conductor guarda un parte, el frontend envía los datos
al backend a través de la API, y el backend los guarda en la base de datos."*

### Endpoint
Un "punto de acceso" concreto de la API. Es como una dirección específica
para cada operación.
Ejemplo: `/api/partes/crear` para crear un parte, `/api/partes/lista` para ver todos.

---

## Sobre Claude Code

### Hook
Un pequeño programa que se ejecuta automáticamente en momentos concretos
(al abrir sesión, antes de un comando, al cerrar). Como una alarma automática.

### Skill
Un paquete de conocimiento que Claude carga cuando lo necesita. Como un
"módulo de formación" específico — uno para Git, otro para el negocio, etc.

### Agent / Subagente
Una versión especializada de Claude para una tarea concreta (diseño, backend,
seguridad...). Claude principal los convoca cuando necesita expertise específico.

### Command (slash command)
Un atajo que empieza por `/` para decirle a Claude que haga algo específico.
Ejemplo: `/nueva-leccion` para registrar lo que aprendió.

### CLAUDE.md
El archivo de instrucciones que le dice a Claude cómo comportarse en este proyecto.
Es la "constitución" del agente.

### Lessons Learned
El log donde Claude registra los errores y correcciones para no repetirlos.
La memoria persistente del proyecto.

---

## Sobre el proceso de trabajo

### Sprint
Un período de trabajo con un objetivo concreto y una fecha límite. Normalmente
1-2 semanas. Al final del sprint, algo nuevo debe estar funcionando.

### ADR (Architecture Decision Record)
Un documento que explica una decisión técnica importante: qué se decidió,
por qué, y qué alternativas se descartaron. Para que en el futuro se entienda
por qué el sistema es como es.

### CI/CD
"Continuous Integration / Continuous Deployment". Un sistema automático que
verifica que el código funciona cada vez que hay cambios, y lo publica
automáticamente si todo está bien.

### Environment (entorno)
Las diferentes versiones del sistema en funcionamiento:
- **Local**: en tu ordenador, solo para desarrollo
- **Staging**: una copia de producción para pruebas antes de publicar
- **Producción**: la versión real que usan los usuarios

### .env
Un archivo de configuración que guarda información secreta (contraseñas,
claves de API, etc.). **NUNCA se sube a GitHub.** Claude no lo toca.

### Dependency / Dependencia
Software externo que usa el proyecto. Como ingredientes de una receta.
Hay que instalarlos antes de poder cocinar.

### Package.json / requirements.txt / pyproject.toml
El "libro de recetas" del proyecto — lista todas las dependencias que necesita
y cómo instalarlas. Varía según el lenguaje (Node.js, Python...).

---

## Sobre GitHub

### GitHub
El servicio donde se aloja el repositorio online. Es el "servidor" donde vive
el código, accesible para todo el equipo.

### Fork
Una copia de un repositorio en tu propia cuenta de GitHub. Se usa para
contribuir a proyectos ajenos.

### Issue
Un "ticket" de trabajo en GitHub — puede ser un bug, una funcionalidad nueva
o una pregunta. Se usan para hacer seguimiento del trabajo pendiente.

### Actions / CI
El sistema de automatización de GitHub. Ejecuta pruebas y verificaciones
automáticamente cada vez que hay cambios en el código.

---

*¿Falta algún término? Díselo a Claude: "Añade [término] al diccionario"*
