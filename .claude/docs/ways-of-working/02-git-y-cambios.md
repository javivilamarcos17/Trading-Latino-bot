# 02 — Git y cómo se gestionan los cambios

> En lenguaje normal: cómo se guarda y protege el trabajo.

---

## ¿Qué es Git?

Git es el sistema que guarda el historial completo de cambios del proyecto.
Piénsalo como un "control de versiones" que permite:
- Ver qué cambió y cuándo
- Volver a una versión anterior si algo sale mal
- Que varias personas trabajen a la vez sin pisarse

---

## Las reglas básicas

### La rama `main` es sagrada
`main` es la versión "oficial" del proyecto — la que está en producción o
la que se enseña al cliente. **Claude nunca toca `main` directamente.**

Todo cambio nuevo se hace en una rama separada (como una copia de trabajo),
se revisa, y solo entonces se fusiona con `main`.

### Un cambio = un commit
Un commit es como un "punto de guardado" con una descripción de qué cambió.
Los buenos commits tienen mensajes claros:
- ✅ `"añadir filtro por fecha en pantalla de partes"`
- ❌ `"fix"` o `"cambios"`

### El flujo estándar

```
1. Nueva tarea → Claude crea una rama nueva
2. Claude hace los cambios en esa rama
3. Claude hace un Pull Request (PR) para revisión
4. Tú revisas y apruebas (o pides cambios)
5. Se fusiona con main
6. Se elimina la rama temporal
```

---

## ¿Qué es un Pull Request (PR)?

Es una "solicitud de fusión" — Claude dice "tengo estos cambios listos,
¿los aprobamos?". Es el momento de revisión antes de que los cambios
lleguen a `main`.

No tienes que entender el código para aprobar un PR. Puedes:
- Probar la funcionalidad en local
- Leer la descripción que Claude escribe en lenguaje normal
- Preguntar si algo no queda claro

---

## ¿Qué NO hace Claude sin tu permiso?

- Fusionar ramas con `main`
- Hacer push forzado (sobrescribir historial)
- Borrar ramas que tienen trabajo
- Publicar o desplegar a producción
