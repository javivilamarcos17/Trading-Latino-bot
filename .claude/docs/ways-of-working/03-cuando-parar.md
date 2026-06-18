# 03 — Cuándo Claude debe parar y consultarte

> Claude no es un robot que ejecuta ciegamente. Hay momentos en que debe parar,
> explicarte lo que va a hacer, y esperar tu confirmación.

---

## Claude siempre para antes de...

### Operaciones irreversibles
Borrar datos, eliminar tablas de base de datos, sobrescribir archivos importantes.
Si algo no tiene marcha atrás, Claude te lo dice primero.

### Cambios con impacto en producción
Cualquier cosa que afecte a la versión que están usando los usuarios reales.

### Cuando la petición es ambigua
Si lo que pides tiene dos interpretaciones posibles, Claude pregunta cuál es
la correcta en lugar de adivinar.

### Cuando detecta un riesgo técnico
Si lo que pides puede funcionar ahora pero crear problemas en el futuro,
Claude te lo explica en lenguaje normal antes de proceder.

### Cuando hay decisiones abiertas bloqueantes
Si hay una pregunta sin respuesta en `SYSTEM_VISION.md` que afecta a lo que
estás construyendo, Claude no avanza hasta que esté resuelta.

---

## Señales de que Claude va bien

- Te pregunta antes de hacer algo grande
- Cuando no entiende algo, pide clarificación en lugar de suponer
- Cuando detecta un problema potencial, te avisa antes de que te afecte
- Explica en lenguaje normal lo que acaba de hacer

## Señales de alerta

Si Claude hace cambios grandes sin consultarte, o no puede explicar en
lenguaje normal qué hizo y por qué, para la sesión y díselo explícitamente:
*"Para. Explícame qué has hecho hasta ahora en lenguaje normal."*
