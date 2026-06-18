# 04 — Aprender de errores

> El sistema que hace que Claude mejore con el tiempo en tu proyecto.

---

## El problema que resuelve

Claude no recuerda conversaciones anteriores entre sesiones. Cada vez que
abres una sesión nueva, es como si fuera la primera vez. Sin un sistema,
cometería los mismos errores una y otra vez.

## La solución: el log de lecciones

El archivo `.claude/skills/lessons-learned/log.md` es la memoria persistente
del proyecto. Cada vez que corriges a Claude, se registra la lección para
que no se repita.

---

## Cómo funciona

### Cuando corriges a Claude:
1. Claude reconoce el error sin excusas
2. Entiende por qué ocurrió
3. Escribe la lección en el log **antes de continuar**
4. Aplica lo aprendido en el resto de la sesión

### En la siguiente sesión:
Claude lee el log al arrancar y lleva todas las lecciones incorporadas.

---

## Cómo añadir una lección (tú también puedes)

Di a Claude: `/nueva-leccion`
Claude te preguntará qué pasó y redactará la lección en el formato correcto.

---

## Formato de una lección

```markdown
## 2026-01-15 — Nunca asumir el formato de fecha sin preguntar

**Error:** Claude usó formato MM/DD/YYYY en lugar de DD/MM/YYYY en los partes.
**Causa:** Asumió el formato americano por defecto.
**Lección:** En este proyecto, SIEMPRE usar DD/MM/YYYY. El cliente y los 
usuarios son españoles. Confirmado por [nombre] el 15/01/2026.
```

---

## ¿Qué tipo de cosas se registran?

- Preferencias de formato o estilo que Claude no conocía
- Reglas de negocio que Claude malinterpretó
- Formas de trabajar que el equipo prefiere
- Errores técnicos recurrentes y su solución
- Cosas que parecen obvias pero Claude tiende a olvidar
