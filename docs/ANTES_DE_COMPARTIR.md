# Antes de compartir — Checklist obligatorio

> Antes de enseñar este repositorio a **un socio, cliente, inversor, técnico externo
> o un nuevo trabajador**, repasa esta lista. Entera.
>
> Compartir un repo es como abrir las puertas de tu casa: una vez alguien ha entrado,
> ha visto lo que hay dentro. Si dejaste una contraseña en la mesa o vendiste una
> maqueta como si fuera la casa terminada, el daño ya está hecho.
>
> **Cómo usarla:** pídele a Claude *"Audita el repo siguiendo docs/ANTES_DE_COMPARTIR.md
> y dame un informe punto por punto"*. Luego revisa tú las casillas críticas.

---

## 🔴 Críticas — si fallan, NO compartas

### 1. Sin secretos ni claves
- [ ] No hay ningún archivo `.env` subido al repositorio (solo `.env.example` sin valores reales).
- [ ] No hay contraseñas, claves de API, tokens ni datos de acceso escritos dentro del código.
- [ ] No hay claves ni certificados (`.pem`, `.key`, `.p12`) subidos.
- [ ] Si en algún momento se subió un secreto por error: **se ha rotado** (cambiado por uno nuevo).

> ⚠️ Borrar un secreto en un commit nuevo **no lo elimina del historial**. Si se filtró,
> hay que **cambiar esa clave** en el servicio donde vive. Pídele ayuda a Claude con esto.

### 2. Sin datos sensibles ni personales reales
- [ ] No hay datos reales de clientes, empleados o terceros (nombres, emails, teléfonos, DNIs...).
- [ ] Las demos usan datos inventados ("de pega"), no reales.
- [ ] No hay documentos internos confidenciales subidos por descuido.

---

## 🟡 Importantes — para no dar mala imagen ni falsas expectativas

### 3. README personalizado
- [ ] El `README.md` habla de **tu proyecto**, no es el genérico de la plantilla.
- [ ] Explica qué es, para quién y en qué estado está.

### 4. PROJECT_STATUS actualizado y honesto
- [ ] [PROJECT_STATUS.md](../PROJECT_STATUS.md) refleja el estado **real** de hoy.
- [ ] La etapa marcada (idea/demo/MVP/...) es honesta — ante la duda, la menor.
- [ ] "Qué funciona" lista solo cosas probadas de verdad.

### 5. Qué es demo y qué es producción — DEJADO CLARO
- [ ] Está escrito, donde la otra persona lo verá, qué partes son demo y cuáles funcionan de verdad.
- [ ] No se está enseñando una demo dando a entender que es un producto terminado.

> Decir "esto es una demo para enseñar la idea" genera confianza.
> Que el otro lo descubra solo, la destruye. Ver [ESTADOS_DEL_PROYECTO.md](ESTADOS_DEL_PROYECTO.md).

### 6. Demo reproducible
- [ ] Hay instrucciones para que la otra persona (o tú) arranque y vea el estado actual.
- [ ] Esas instrucciones se han probado y funcionan (no solo "deberían funcionar").
- [ ] Están en `PROJECT_STATUS.md` (sección "Cómo probarlo") o en el README.

### 7. CI: estado claro (sin falsa seguridad)
- [ ] Si NO hay tests reales todavía, está claro que el CI solo comprueba documentación.
- [ ] No se está enseñando un "✅ CI passing" dando a entender que el producto está testeado cuando no lo está.

> Un check verde que solo valida documentos no significa "el producto funciona".
> Sé honesto sobre qué comprueba realmente tu CI.

### 8. Decisiones actualizadas
- [ ] Las decisiones cerradas y abiertas en `SYSTEM_VISION.md` están al día.
- [ ] No hay decisiones importantes tomadas "de palabra" pero sin registrar.

---

## 🟢 Recomendables — según con quién compartas

### 9. Riesgos legales y de datos
- [ ] Si manejas datos personales, sabes si te aplica el RGPD u otra normativa.
- [ ] No estás compartiendo algo que infrinja contratos, NDAs o propiedad de terceros.
- [ ] Si hay dudas legales serias, lo consultas con un profesional antes de compartir.

### 10. Acceso adecuado
- [ ] Si el repo es privado, das acceso solo a quien debe tenerlo.
- [ ] Si lo haces público, has repasado DOS VECES los puntos 1 y 2 (secretos y datos).

---

## Según a quién se lo enseñas

| Le enseñas a... | Lo más importante |
|-----------------|-------------------|
| **Inversor** | PROJECT_STATUS honesto, qué es demo vs. real, riesgos claros |
| **Cliente** | Demo reproducible, expectativas claras, datos de pega (no reales) |
| **Técnico externo** | README, ARQUITECTURA, sin secretos, decisiones al día |
| **Nuevo trabajador** | ONBOARDING, GETTING-STARTED, acceso adecuado |
| **Público (open source)** | TODO lo crítico revisado dos veces, especialmente secretos |

---

## Resumen en una frase

> **No compartas nada hasta que: (1) no haya secretos ni datos reales, y
> (2) lo que la otra persona vea coincida con lo que el proyecto es de verdad.**
