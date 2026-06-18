# Agentes — ¿Qué son y para qué sirven?

> **En lenguaje normal:** Los agentes son versiones especializadas de Claude,
> cada una enfocada en un área concreta. Como tener un equipo de especialistas
> en lugar de un generalista para todo.
>
> Claude principal los convoca cuando necesita ayuda especializada en una tarea.
> Tú no tienes que invocarlos manualmente.

---

## Los agentes de este proyecto

| Agente | Especialidad | Cuándo actúa |
|--------|-------------|--------------|
| `architect` | Diseño global del sistema | Cuando hay que decidir cómo estructurar algo nuevo |
| `backend-dev` | Servidor, base de datos, lógica | Cuando hay que construir la parte invisible |
| `frontend-dev` | Pantallas, interfaz, experiencia | Cuando hay que construir lo que se ve |
| `qa-engineer` | Tests y calidad | Cuando hay que verificar que todo funciona |
| `devops` | Despliegue y automatización | Cuando hay que publicar o automatizar procesos |
| `security-auditor` | Seguridad | Cuando hay que revisar que nada es vulnerable |
| `domain-analyst` | Reglas de negocio | Cuando hay que entender y documentar la lógica del dominio |

---

## Reglas importantes de los agentes

- **Los agentes no se invocan entre sí** — solo Claude principal coordina
- **Los agentes no hacen push ni deploy** — solo Claude principal puede, y con tu permiso
- **Cada agente trabaja en su área** — el backend-dev no toca el frontend, etc.
- **Todo queda registrado** — hay un log de cuándo se activó cada agente

---

## ¿Tengo que configurarlos?

En proyectos pequeños, puede que nunca necesites agentes especializados.
Claude los activa solo cuando la tarea es lo suficientemente compleja.
