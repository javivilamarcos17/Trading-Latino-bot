# Estados del proyecto — Qué significa cada etapa

> El error más común y más caro de un proyecto es **creer que está más avanzado de lo que está.**
> "Esto ya está hecho" cuando solo hay una demo bonita ha hundido más proyectos
> (y relaciones con socios e inversores) que cualquier fallo técnico.
>
> Este documento define, sin ambigüedad, qué significa cada etapa.
> Úsalo junto a [PROJECT_STATUS.md](../PROJECT_STATUS.md) para no engañarte a ti mismo.

---

## La regla que lo resume todo

> **Documentación ≠ Demo ≠ Producto que funciona.**
>
> - Que esté **escrito** no significa que esté **construido**.
> - Que se pueda **enseñar** no significa que se pueda **usar**.
> - Que **funcione en tu ordenador** no significa que funcione **para tus usuarios**.

---

## Las 6 etapas

### 💡 1. Idea
**Qué es:** la idea existe en tu cabeza, en notas o en una conversación. Nada más.

**Qué hay:** nada construido, nada escrito de forma estructurada.

**Lo que NO puedes decir todavía:** "estamos construyendo X". Todavía estás *pensando* X.

**Cómo se sale de aquí:** rellenando `SYSTEM_VISION.md`.

---

### 📄 2. Documentación
**Qué es:** está escrito qué se quiere hacer, para quién y por qué. Hay un plan.

**Qué hay:** `SYSTEM_VISION.md` relleno, quizá un roadmap. **Cero código que funcione.**

**El peligro:** sentir que "ya casi está" porque hay muchos documentos bonitos.
Documentar es el 5% del trabajo, no el 80%. Un documento no atiende a un cliente.

**Lo que NO puedes decir:** "tenemos un producto". Tienes un *plan*.

**Cómo se sale de aquí:** construyendo la primera pieza que se pueda enseñar.

---

### 🎬 3. Demo
**Qué es:** algo que se puede **enseñar** en una pantalla. Sirve para explicar la idea.

**Qué hay:** pantallas, botones, quizá datos de mentira ("de pega"). Se ve bonito.

**El peligro — EL MÁS GRANDE DE TODOS:** una demo engaña al ojo. Parece terminada.
Pero por dentro: los datos no se guardan de verdad, no hay usuarios, no hay seguridad,
si pulsas el botón equivocado se rompe. **Una demo es teatro, no producto.**

**Lo que NO puedes decir:** "ya funciona". Funciona *para enseñarlo*, no *para usarlo*.

**Cómo se sale de aquí:** haciendo que las cosas funcionen de verdad por dentro, una a una.

---

### 🛠️ 4. Prototipo funcional
**Qué es:** funciona de verdad en algunas partes. Los datos se guardan, algo real ocurre.

**Qué hay:** flujos reales que funcionan, pero incompletos, frágiles o sin pulir.
Se cae con facilidad. No está listo para gente ajena al proyecto.

**Lo que NO puedes decir:** "lo pueden usar mis clientes". Aún no es fiable.

**Cómo se sale de aquí:** completando el flujo mínimo que aporta valor y haciéndolo fiable.

---

### 🚀 5. MVP (Producto Mínimo Viable)
**Qué es:** la versión más pequeña que un usuario real puede usar y obtener valor.

**Qué hay:** el flujo principal funciona de extremo a extremo, de forma fiable,
con datos reales. Le faltan funciones, pero lo que hay **funciona y aporta valor**.

**Lo que SÍ puedes decir:** "ya se puede usar para X". Con honestidad sobre los límites.

**Cómo se sale de aquí:** uso real continuado, estabilidad, soporte, escala.

---

### 🏭 6. Producción
**Qué es:** está en uso real. Hay gente que depende de ello para su trabajo o negocio.

**Qué hay:** datos reales, usuarios reales, copias de seguridad, seguridad,
plan para cuando algo falle. Romperlo tiene consecuencias reales.

**Responsabilidad:** a partir de aquí, cada cambio puede afectar a gente real.
Todo cambio se prueba antes. Nada se toca a la ligera.

---

## Tabla rápida

| Etapa | ¿Hay código que funciona? | ¿Se puede enseñar? | ¿Lo puede USAR un tercero? | ¿Datos reales? |
|-------|:---:|:---:|:---:|:---:|
| 💡 Idea | No | No | No | No |
| 📄 Documentación | No | Solo el plan | No | No |
| 🎬 Demo | Por fuera sí, por dentro no | Sí | **No** | No (de pega) |
| 🛠️ Prototipo | A medias | Sí | Con cuidado | A veces |
| 🚀 MVP | Sí (lo esencial) | Sí | Sí | Sí |
| 🏭 Producción | Sí (completo y fiable) | Sí | Sí, depende de ello | Sí |

---

## Cómo usar esto en el día a día

1. Cada vez que dudes en qué punto estás, vuelve aquí y sé **conservador**: elige la etapa menor.
2. Refleja siempre la etapa real en [PROJECT_STATUS.md](../PROJECT_STATUS.md).
3. Antes de enseñar el proyecto a alguien, di SIEMPRE en qué etapa está.
   Decir "es una demo" no resta: genera confianza. Vender una demo como producto, la destruye.
4. Si Claude construye algo, pregúntale: *"¿esto en qué etapa nos deja?"*.
