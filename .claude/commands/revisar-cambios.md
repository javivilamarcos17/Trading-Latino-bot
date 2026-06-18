---
name: revisar-cambios
description: Revisa los cambios actuales (staged o respecto a main) antes de hacer un commit o PR. Comprueba calidad, coherencia y posibles problemas.
---

# Comando: /revisar-cambios

Cuando el usuario invoca este comando:

1. Ejecuta `git diff` para ver los cambios
2. Revisa que:
   - Los cambios son coherentes con lo que se pidió
   - No hay console.log, debuggers o código temporal olvidado
   - No hay credenciales o secrets en los archivos
   - Los archivos modificados tienen sentido juntos
   - El mensaje de commit propuesto es descriptivo
3. Reporta en lenguaje normal: qué cambió, si hay algo que revisar, si está listo para commit
4. Propone el mensaje de commit en formato Conventional Commits

## Salida esperada

```
✅ Cambios revisados:
- Se modificó [archivo] para [qué hace]
- Se añadió [archivo] que [para qué sirve]

⚠️ A revisar:
- [Algo que podría ser un problema o pregunta]

📝 Commit sugerido:
feat(scope): descripción clara
```
