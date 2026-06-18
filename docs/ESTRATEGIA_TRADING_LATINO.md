# 📖 La Biblia de la Estrategia — Trading Latino (Jaime Merino)

> **Qué es este documento:** el conocimiento consolidado sobre el método de Jaime
> Merino (Trading Latino) que sirve de referencia para programar el bot. Todo lo que
> el código haga debe poder justificarse desde aquí.
>
> **Fuente de la verdad:** sus propios directos y clases en YouTube/X. Las fuentes de
> terceros son interpretaciones útiles, pero NO oficiales. Por eso cada regla está
> marcada con su nivel de fiabilidad.
>
> **Estado:** 🟡 Borrador de investigación (sesión de 2026-06-18). Se irá afinando
> validando contra sus directos.

**Leyenda de fiabilidad:**
- ✅ **Confirmado** — coincide con el `SYSTEM_VISION.md` del dueño y/o con varias fuentes.
- ⚠️ **Interpretación** — de terceros (community), razonable pero no oficial.
- 🔎 **A validar** — hay que comprobarlo en un directo concreto antes de codificarlo en firme.

---

## 1. Quién es (y por qué su método encaja con un bot)

Trader salvadoreño, fundador de **TradingLatino**. Formación de base **informática**
(redes, sistemas, programación orientada a objetos). Enseña gratis en YouTube y
**opera en directo en streaming**, que es donde se ve su método real. Su análisis se
apoya en **Teoría de Dow** y **método Wyckoff** (acumulación/distribución) traducidos
a indicadores. Es **trader intradía** (entradas típicas de 1 a 4 horas) con algo de swing corto.

Su operativa es muy **sistematizable** (reglas claras, mecánicas), por eso tiene
sentido automatizarla. La gran ventaja del bot: ejecuta la disciplina que a un humano
le cuesta mantener.

## 2. Filosofía central ✅

- *"El trading es 90% emocional y 10% inteligencia."* → el bot elimina miedo y avaricia.
- **Comprar el pánico** en soportes de volumen; **vender/shortear la euforia** en resistencias.
- **Teoría de la opinión contraria:** el ~90% pierde; hay que operar contra la masa, con las "ballenas".
- **Operar impulsos, no retrocesos.** Entrar cuando el impulso arranca, no intentar cazar cuchillos cayendo.
- Prioridad nº1: **no perder** (preservar capital) por encima de ganar.

## 3. El arsenal técnico (ajustes exactos) ✅

| Herramienta | Ajuste | Para qué |
|---|---|---|
| **EMA 10** | longitud 10, sobre cierre | inercia a corto plazo |
| **EMA 55** | longitud 55, sobre cierre | tendencia principal / "imán" del precio; soporte-resistencia dinámica |
| **Squeeze Momentum (LazyBear)** | Bollinger 20 × 2.0 · Keltner 20 × 1.5 | el ciclo de impulso (los "valles") |
| **ADX** | suavizado 14 · DI 14 · **nivel clave 23** | FUERZA de la tendencia (no dirección) |
| **Perfil de Volumen (VPVR/VPOC)** | POC = precio de mayor volumen negociado | muros reales de soporte/resistencia |

> Estos ajustes **coinciden exactamente** con los del `SYSTEM_VISION.md`. ✅

**Regla del ADX:** mide fuerza, no dirección. Por encima de 23 con **pendiente positiva**
= movimiento con fuerza institucional. **Pendiente negativa** = debilidad/absorción
(señal de que el movimiento se agota). ⚠️ La estrategia community "Ruckard" mide la
pendiente sobre **3 barras** con una inclinación mínima exigida.

## 4. Cómo se lee el Squeeze Momentum (los 4 colores) ✅

Regla matemática exacta del LazyBear (valor de la barra vs la anterior):

| Color | Posición | Movimiento | Significado | Acción |
|---|---|---|---|---|
| 🟩 Verde claro | sobre 0 | subiendo | impulso alcista fuerte | — |
| 🟢 Verde oscuro | sobre 0 | bajando | se agota la subida | **zona de venta/short** |
| 🟥 Rojo claro | bajo 0 | cayendo | impulso bajista fuerte | — |
| 🟫 Rojo oscuro | bajo 0 | recuperando | se agota la bajada | **zona de compra** |

> Coincide **al 100%** con la lectura de tu `SYSTEM_VISION.md`. ✅
> Esto define "direccionalidad": **el color comparando barra actual vs anterior** (no
> solo encima/debajo de cero). Algunas versiones lo afinan con "4 cuadrantes"
> (pendiente + posición respecto al 0). 🔎 A validar cuál usa él en directo.

## 5. La jerarquía multi-temporal — el "semáforo" ✅

Una temporalidad menor **nunca** contradice a la mayor:

1. **Semanal BTC (1W):** dicta apalancamiento/riesgo de la semana. Bajo EMA55 semanal = bear estructural → reducir Longs a la mitad.
2. **Diario BTC (1D):** el **semáforo**. Alcista → solo Longs. Bajista → solo Shorts (en altcoins).
3. **4H de la moneda:** encuentra el patrón (choque en EMA55/POC + Squeeze girando + ADX con pendiente a la baja).
4. **1H de la moneda:** el gatillo fino, para no comprar/vender en la punta de la vela.

## 6. ⭐ POR QUÉ SOLO SHORTS EN ALTCOINS (y NUNCA en Bitcoin)

Esta es la pregunta clave. Hay **dos razones**, una defensiva y otra ofensiva:

### A) Por qué NO se shortea Bitcoin (defensa) ✅
- BTC es el **activo rey / índice** de todo el mercado. Una noticia macro, una compra
  institucional o un tuit pueden generar **"velas asesinas"**: subidas verticales de
  miles de dólares en minutos.
- Esas subidas provocan **short squeezes** brutales: liquidan en masa a quien apuesta
  en contra. Es habitual ver **150-200 millones de dólares en cortos liquidados en una
  sola hora** cuando BTC rompe una resistencia. Shortear BTC es ponerse delante de un tren.
- BTC tiene **sesgo alcista estructural** a largo plazo y compradores institucionales
  que lo defienden. → Si BTC cae o entra en pánico, el bot **no shortea**: se queda en
  liquidez esperando comprar barato el rebote sobre un POC.

### B) Por qué SÍ se shortean las altcoins débiles (ataque) ✅
- En mercado bajista, **BTC cae 60-70%** desde máximos, pero **las altcoins caen 80-95%**:
  caen más y más rápido.
- Cuando hay miedo, sube la **dominancia de BTC**: el capital huye de las altcoins hacia
  BTC y stablecoins (*risk-off*). Las altcoins **sangran doble**: pierden valor frente al
  dólar **y** frente a BTC. (Ej.: a principios de 2026, el 83% de las altcoins rindieron
  peor que BTC.)
- Las altcoins tienen **libros de órdenes finos** (poca liquidez): una venta moderada
  empuja el precio mucho más abajo → movimientos amplios, ideales para un short.

### C) Cómo elige a la altcoin "enferma" ✅
Solo cuando el **diario de BTC** está bajista, el bot escanea su lista cerrada (~20
altcoins) y selecciona **solo** las que ya cotizan **por debajo de su propia EMA55
diaria** (las más débiles), esperando un **rebote a la EMA55/POC en 4H** que falle, con
el Squeeze girando a verde oscuro y el ADX con pendiente negativa. Se caza a los débiles
en su rebote ilusorio.

> **Conclusión:** se ataca donde el riesgo de "vela asesina" es bajo y la debilidad es
> estructural (alts), y se respeta donde el riesgo de squeeze es alto (BTC). Esto encaja
> perfectamente con la Regla nº1 de tu manual: *"A Bitcoin jamás se le hace un Short."* ✅

## 7. Operativa de LONGS ✅
(Solo con semáforo diario de BTC en verde)
1. **4H:** el precio corrige hasta soporte de volumen (POC previo).
2. **Patrón:** Squeeze pasa de rojo claro a **rojo oscuro** (giro) + ADX con **pendiente negativa** (vendedores sin fuerza).
3. **Gatillo 1H:** esperar a que el monitor de 1H complete su corrección menor (rojo oscuro) → compra a mercado.

## 8. Operativa de SHORTS en altcoins ✅
(Solo con semáforo diario de BTC en rojo)
1. **Permiso BTC:** 1D de BTC bajista o bajo su EMA55 → interruptor global de cortos ON.
2. **Filtrado:** escanear ~20 alts, quedarse con las que estén **bajo su EMA55 diaria**.
3. **Setup 4H:** rebote que choca contra su EMA55 de 4H o un POC y encuentra resistencia.
4. **Confirmación:** Squeeze de verde claro a **verde oscuro** + ADX con **pendiente negativa**.
5. **Gatillo 1H:** short a mercado cuando el monitor de 1H se gira a la baja.

## 9. Gestión de riesgo — las leyes de supervivencia ✅

| Ley | Detalle |
|---|---|
| **Tamaño fijo** | Capital en 20 partes → **5% por operación**, siempre igual. ⚠️ (a veces dice 10 partes; 20 es lo conservador) |
| **Interés simple** | Nunca compuesto. No se reinvierten ganancias para arriesgar más. *"Tú controlas tu cuenta, no el mercado."* |
| **Apalancamiento** | **3x-5x en margen aislado**. Cruzado prohibido. (Algún vídeo antiguo dice ≤10x; usamos 3-5x del SYSTEM_VISION.) |
| **Stop Loss siempre** | Puesto en el exchange en el mismo instante de abrir. Nunca una operación sin SL. |
| **SL estructural** | Detrás del último mínimo (Long) / máximo (Short), pegado al POC. NO un % fijo arbitrario. ⚠️ Ruckard tope ~2,4% de distancia. |
| **No promediar (no DCA)** | Si toca SL, se asume la pérdida. Jamás meter capital para salvar una posición perdedora. |
| **Break-even (NETO, con costes)** | Tras una vela 4H ganadora, mover el SL al **break-even real con costes** = entrada + comisiones ida/vuelta + funding + slippage (Long) / − lo mismo (Short). **NUNCA a la entrada cruda** (eso deja pérdida oculta por comisiones). Ver §13. |
| **Guillotina del tiempo** | 6-8 velas de 4H (24-32h): si el ciclo se completa y el precio sigue plano → cierre inmediato a mercado. |
| **Filtro horario** | No abrir nada entre **15:15 y 15:45 (Madrid)** (apertura de Nueva York). |

## 10. Comparación con lo que mandó el dueño

- **`SYSTEM_VISION.md`** → ✅ coincide con todo lo investigado (indicadores, semáforo, leyes).
- **Resumen Ejecutivo del dueño** → ✅ fiel; buena traducción a lenguaje de negocio.
- **Manual Operativo Detallado del dueño** → ✅ coherente y **añade explícito** lo más
  importante: *"a Bitcoin jamás se le hace Short"* y *"SL puesto en el servidor del
  exchange en el mismo milisegundo"*. Lo adoptamos como norma cerrada.

## 11. ⚠️ Avisos importantes (protección al dueño)

1. **Contenido antiguo peligroso (época BitMex):** parte de su material viejo enseñaba
   *recomprar sin stop loss* y *aguantar pérdidas para recuperar margen*. Eso
   **contradice frontalmente** las leyes de tu `SYSTEM_VISION` (siempre stop, nunca
   promediar). **NO se mete en el bot.** Tu visión refleja su método moderno y disciplinado.
2. **Más indicadores fuera de alcance:** en su día a día usa también RSI, MACD y ondas
   de Elliott. El proyecto se queda con el **núcleo purista** (EMA/Squeeze/ADX/Volumen).
   Menos piezas = bot más fiable y backtest más limpio.
3. **Toma parcial de beneficios:** a veces vende la mitad de la posición al entrar en
   ganancias. No está en el SYSTEM_VISION → decisión pendiente del dueño.
4. **Cifras de marketing:** se citan efectividades altas ("~86% en 4,5 años"). Tomar con
   pinzas; lo demostrará nuestro propio backtest, no las promesas.

## 12. 🔎 Cosas a validar contra sus directos (cuando tengamos transcripciones)

- Definición exacta de "direccionalidad" del monitor (¿color barra-vs-barra, o pendiente + cuadrante?).
- Qué cuenta exactamente como "mecha/swing" válido para colocar el SL estructural.
- Ventana exacta del Perfil de Volumen para calcular el POC.
- La lista cerrada concreta de altcoins que vigila.
- Si aplica toma parcial de beneficios y en qué %.

## 13. ⭐ Principio rector: RENTABILIDAD NETA después de costes

> **Regla de diseño nº1:** la única métrica que importa es el beneficio **NETO**, después
> de comisiones, funding y slippage. Una estrategia que gana en bruto puede perder en
> neto. Todo —entradas, break-even, objetivos, backtest— se mide en neto.

**Costes de cada operación (perpetuos en Hyperliquid):**
- **Comisiones:** al abrir y al cerrar (ida y vuelta), sobre el *nocional* (= margen ×
  apalancamiento). Bajas (~0,02-0,045% por lado según maker/taker). 🔎 Confirmar esquema vigente.
- **Funding:** pago periódico por mantener la posición; en Hyperliquid es **cada hora** →
  en 24-32h son 24-32 cobros/pagos. Pequeños, pero suman (y en mercados "cargados", grandes).
- **Slippage:** las órdenes a mercado no entran al precio exacto.

**El break-even real NO es el precio de entrada:**
- **Long:**  `BE = entrada × (1 + comisiones_ida_vuelta + funding + slippage)` → un pelín *por encima*.
- **Short:** `BE = entrada × (1 − comisiones_ida_vuelta − funding − slippage)` → un pelín *por debajo*.

Si te sacan en el BE real, sales **a cero de verdad**, no con pérdida oculta.

> Matiz: el BE en *precio* (~0,09% por comisiones) es igual a 3x o 5x; el apalancamiento no
> cambia ese precio, pero amplifica el impacto en la cuenta y acerca la liquidación → backtestear 3x y 5x.

**Consecuencias de diseño (obligatorias):**
1. **Filtro de entrada por ventaja real:** no abrir si la distancia al objetivo no supera
   holgadamente el coste ida/vuelta (p. ej. objetivo ≥ 2-3× los costes).
2. **Break-even ajustado a costes** (fórmula de arriba), nunca a la entrada cruda.
3. **Take-profit neto:** el objetivo deja beneficio *después* de costes.
4. **Backtest 100% en neto:** todas las métricas restan comisiones + funding + slippage.

**Palanca de rentabilidad:** órdenes **límite (maker)** en el gatillo abaratan comisiones
frente a ir a mercado (taker), a cambio de arriesgar no entrar. El backtest medirá la mejora.

## 14. 🔍 Huecos del método detectados (pendientes de cerrar)

**🔴 Críticos (sin esto no se puede backtestear bien):**
- **Salida en beneficio** (¿dónde se toman ganancias?): agotamiento del impulso (Squeeze se
  gira), siguiente muralla de volumen, o toma parcial. *Propuesta:* agotamiento + BE neto +
  guillotina; toma parcial a probar.
- **Cortacircuitos de pérdida** (kill-switch diario/semanal/mensual). 🔎 A derivar del backtest, no a ojo.
- **Máx. posiciones simultáneas y exposición total** (las alts están correlacionadas → tope conjunto).
- **Qué hacer con posiciones abiertas al cambiar el semáforo.**

**🟡 Mejoras que él usa (valorar v2):**
- Dominancia (USDT.D / BTC.D / TOTAL3) como contexto risk-on/off para shorts de alts.
- Perfil de Volumen completo: Área de Valor (VAH/VAL) y POC virgen, además del POC.

**⚪ Fuera de la v1 (demasiado subjetivo para automatizar fiable):** Wyckoff completo,
ondas de Elliott, RSI/MACD, Fibonacci, mapas de liquidaciones.

## 15. 🪙 Universo de altcoins (lista de vigilancia)

Elegidas por criterio profesional: cotizan en Hyperliquid, alta liquidez, alts establecidas
que Merino sigue, y variedad de sectores.

| Sector | Monedas |
|--------|---------|
| Majors / L1 grandes | ETH, SOL, BNB, XRP, ADA |
| L1 alternativas | AVAX, NEAR, APT, SUI |
| L2 / escalado | ARB, OP, POL |
| DeFi / oráculos | LINK, UNI, AAVE |
| Veteranas líquidas | LTC, BCH |
| Interoperabilidad | DOT |
| Infra / modular | TIA |
| Meme líquida | DOGE |

Es la **lista de vigilancia**, NO se shortean todas a la vez: el filtro (bajo EMA55 diaria +
BTC bajista) elige solo las "enfermas". 🔎 Verificar disponibilidad real en Hyperliquid.

## Fuentes
- invertirenbolsa.wiki — Jaime Merino: ¿cómo invierte?
- criptotendencias.com — Recomendaciones de Jaime Merino (capital en 20 partes, interés simple)
- es.tradingview.com/scripts/tradinglatino — indicadores oficiales community
- es.tradingview.com/script/2qapmnO6 — estrategia "Ruckard TradingLatino" (codificación, NO oficial)
- es.tradingview.com/script/PjaGa5pl — SQZMOM + ADX (lectura por cuadrantes)
- jaimesensei.blogspot.com — apuntes de estudio del método
- coindesk.com / news.bitcoin.com — datos de short squeezes en BTC
- atozmarkets.com / coinmarketcap.com — datos de caídas de altcoins y dominancia BTC en bear market

---

*Mantiene: Claude (con validación del dueño). Actualizar al validar reglas contra directos o al cerrar parámetros de la Fase 0.*
