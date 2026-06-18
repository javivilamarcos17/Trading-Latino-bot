# 01 — Cómo pedir cosas a Claude

> Cómo comunicarte para obtener mejores resultados.

---

## Lo que funciona bien

### Habla de negocio, no de código
❌ "Haz un endpoint REST con autenticación JWT que devuelva un array de objetos"
✅ "Necesito que cuando un conductor entre a la app, vea solo sus propios partes"

Claude traduce el negocio a código. Tú no necesitas saber cómo se llama lo que necesitas.

### Sé específico en el resultado esperado
❌ "Mejora la pantalla de facturas"
✅ "En la pantalla de facturas, cuando una factura está vencida hace más de 30 días,
   quiero que aparezca en rojo y con un aviso visible. Ahora mismo no se distingue"

### Cuando algo no funciona, describe lo que pasa, no lo que crees que falla
❌ "El código está roto"
✅ "Cuando hago clic en 'Guardar', la pantalla se queda en blanco y no pasa nada.
   Antes sí funcionaba, creo que desde que añadimos el campo de fecha"

### Comparte contexto de negocio relevante
✅ "Esto lo usan conductores en ruta, con el móvil y mala conexión. Tiene que
   funcionar aunque se pierda la señal un momento"

---

## Lo que no funciona (y por qué)

### Pedir varias cosas a la vez sin prioridad
❌ "Añade el login, la pantalla de facturas, el filtro por fecha, el PDF y la
   integración con el ERP"

Claude puede hacer todo eso, pero no todo a la vez sin un orden claro.
Mejor ir de uno en uno o indicar claramente qué es lo más urgente.

### Dar instrucciones técnicas si no estás seguro
❌ "Usa Redux con middleware Thunk y normaliza el estado con Normalizr"
Si no sabes exactamente por qué necesitas eso, no lo pidas.
Deja que Claude elija la herramienta correcta.

---

## Frases útiles

- *"Explícame qué has hecho en lenguaje normal"* → Claude te cuenta el cambio sin tecnicismos
- *"¿Qué opciones tengo para hacer X?"* → Claude te da 2-3 alternativas con pros y contras
- *"¿Eso es arriesgado?"* → Claude te dice si el cambio es reversible o no
- *"Para, esto no es lo que quería"* → Claude para y pregunta antes de continuar
- *"¿Cuánto esfuerzo es esto?"* → Claude te da una estimación aproximada
