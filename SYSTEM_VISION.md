

# DOCUMENTO DE VISIÓN DEL SISTEMA (SYSTEM VISION)

## Algoritmo Operativo: "Trading Latino Purista"

## 1. Propósito Central y Filosofía (Core Vision)

El objetivo fundamental de este sistema es automatizar la estrategia visual de acción del precio y volumen popularizada por Jaime Merino. El bot debe operar de manera mecánica, eliminando por completo sesgos emocionales como la codicia o el miedo. Su filosofía principal se basa en **comprar el pánico** (en soportes importantes de volumen) y **vender o shortear la euforia** (en resistencias de volumen), manteniendo como prioridad absoluta la preservación estricta del capital.

## 2. El Arsenal Técnico (Indicadores Visuales Puros)

El sistema tomará decisiones basándose única y exclusivamente en las herramientas técnicas que se analizan en la operativa diaria de Trading Latino:

* **Media Móvil Exponencial de 55 periodos (EMA 55):** Actúa como la línea de tendencia principal y el imán del precio. Funciona como soporte o resistencia dinámica según la posición del mercado.
* **Media Móvil Exponencial de 10 periodos (EMA 10):** Mide la fuerza o inercia del movimiento inmediato a corto plazo.
* **Squeeze Momentum Indicator (LazyBear):** El monitor del ciclo. Mide el impulso a través de valles:
* *Valle Rojo Claro:* Impulso bajista con fuerza.
* *Valle Rojo Oscuro:* Pérdida de fuerza bajista (zona de compra).
* *Valle Verde Claro:* Impulso alcista con fuerza.
* *Valle Verde Oscuro:* Pérdida de fuerza alcista (zona de venta/short).


* **ADX (Average Directional Index):** Mide la fuerza de la tendencia. Cuenta con una línea horizontal fija en el nivel 23. Pendiente positiva (hacia arriba) significa que el movimiento lleva fuerza institucional; pendiente negativa (hacia abajo) significa debilidad y absorción.
* **Perfil de Volumen (VPVR):** Identifica el **POC (Point of Control)**, la línea horizontal donde se ha negociado el mayor volumen de contratos. Sirve para detectar los muros reales de soporte y resistencia del mercado.

## 3. La Jerarquía Multi-Temporal Estricta (MTF)

El bot opera bajo una estructura jerárquica en cascada. Una temporalidad menor nunca puede contradecir los límites establecidos por la temporalidad superior. El flujo de decisión es el siguiente:

1. **Filtro Macro Semanal (1W BTC):** Dicta el APALANCAMIENTO y el RIESGO de la semana. Se ejecuta una vez a la semana (cada lunes automáticamente tras el cierre de vela del domingo). Si Bitcoin cotiza por debajo de su EMA 55 semanal, el bot asume un mercado bajista estructural (*Bear Market*) y reduce a la mitad el capital expuesto en trades de tipo Long.
2. **Semáforo Diario (1D BTC):** Actúa como SEMÁFORO para dar permiso a Longs o Shorts. Se evalúa al cierre de cada vela diaria.
* *Diario Alcista* (Monitor con direccionalidad alcista o precio sobre la EMA 55): El bot tiene permitido buscar Longs en 4H. Quedan bloqueados los Shorts.
* *Diario Bajista* (Monitor con direccionalidad bajista o precio bajo la EMA 55): El bot tiene permitido buscar Shorts en Altcoins. Quedan bloqueados los Longs.


3. **Gráfico Operativo (4H Moneda):** Encuentra el PATRÓN exacto de Jaime (Squeeze + ADX + Choque en la EMA 55 o volumen).
4. **Gráfico de Gatillo (1H Moneda):** Caza el micro-retroceso final para afinar el precio exacto de entrada y evitar comprar en la punta de la vela.

## 4. Operativa de COMPRAS / LONGS (BTC y Altcoins Fuertes)

Se ejecuta únicamente cuando el Semáforo Diario de Bitcoin da luz verde alcista:

1. **Identificación en 4H:** El precio debe corregir hasta una zona de soporte importante identificada por el VPVR (cerca de un POC previo).
2. **Confirmación del Patrón:** El monitor de 4H debe pasar de rojo claro a **rojo oscuro** (giro alcista) y el ADX debe mostrar **pendiente negativa**, confirmando que los vendedores se quedaron sin fuerza.
3. **El Gatillo en 1H:** El bot baja al gráfico de 1 hora y espera a que el monitor de esta temporalidad complete su propia corrección menor (valle rojo oscuro). En ese instante se ejecuta la orden de compra a mercado.

## 5. Operativa Estricta de SHORTS en Altcoins Débiles

Este módulo se activa únicamente en los momentos bajistas de Bitcoin y funciona bajo una secuencia cronológica obligatoria que el bot debe validar paso a paso:

1. **Confirmación de Bitcoin (El Permiso):** Al cierre Diario, el bot verifica el gráfico 1D de Bitcoin. Solo si BTC tiene direccionalidad bajista (monitor con valle verde oscuro o rojo claro cayendo) o el precio está por debajo de su EMA 55 diaria, el bot activa el interruptor global de cortos.
2. **Filtrado del Activo (Buscar la Moneda Débil):** De forma continua en 4H, con el permiso de BTC activo, el bot escanea su lista cerrada de las 20 altcoins principales. Descarta cualquier moneda que muestre fuerza y solo selecciona aquellas cuyo precio cotice por debajo de su propia EMA 55 Diaria.
3. **Identificación del Setup (El Rebote a la Media):** En el gráfico de 4H, el bot monitoriza la altcoin débil elegida y espera a que el precio haga un rebote alcista que lo lleve a chocar contra su propia EMA 55 de 4H o contra un nodo de alto volumen (POC) del VPVR. El precio debe encontrar resistencia geográfica ahí.
4. **Confirmación Matemática del Patrón:** Mientras el precio choca contra la resistencia en 4H, el bot comprueba que se cumplan simultáneamente dos condiciones en los indicadores propios de la altcoin: El monitor cambia de verde claro a verde oscuro (pérdida de impulso alcista) y el ADX muestra pendiente negativa (debilidad de los compradores).
5. **El Gatillo Quirúrgico:** El bot baja al gráfico de 1H de la altcoin. Monitorea su desarrollo y ejecuta la orden de Short a mercado en el instante exacto en que el monitor de 1H se gira a la baja (pasa de verde claro a verde oscuro, o cruza el punto cero a valle rojo).

## 6. Gestión de Riesgo y Leyes de Supervivencia (Inflexible)

Este módulo actúa como el escudo de protección del algoritmo y no puede ser omitido bajo ninguna circunstancia de mercado:

* **Apalancamiento Militar:** Todas las posiciones en el mercado de futuros se ejecutarán estrictamente utilizando entre **3x y 5x en Margen Aislado**. Queda prohibido el uso de margen cruzado.
* **Prohibición Absoluta de Promediar (No DCA):** Queda estrictamente prohibido por código realizar compras o cortos adicionales a la baja para promediar el precio de una posición de futuros perdedora. Si el precio toca el Stop Loss, se asume la pérdida.
* **Stop Loss Estructural con Holgura:** El *Stop Loss* se colocará manualmente por encima del último máximo anterior (para Shorts) o por debajo del último mínimo anterior (para Longs), dándole una pequeña holgura visual colocándolo justo detrás del nodo de volumen (POC) donde el precio rebotó.
* **Protección Dinámica (Break-Even Rápido):** En el momento en que el precio se mueva a nuestro favor y la operación complete una vela de 4H con ganancias sólidas, el bot cancelará el Stop Loss original y lo moverá al **precio exacto de entrada (0% de riesgo residual)**.
* **La Guillotina del Tiempo:** Si tras abrir una operación transcurren entre **6 y 8 velas de 4 horas (24 a 32 horas de tiempo real)**, el monitor se desarrolla por completo cruzando el punto cero, pero el precio se mantiene atrapado en un rango plano sin avanzar, el bot **ejecutará un cierre inmediato a precio de mercado**. Si el patrón es alcista/bajista y el tiempo se le pasa y no se mueve, es que irá en nuestra contra.

## 7. Arquitectura e Infraestructura de Software

* **Lenguaje de Programación:** Python 3.10+.
* **Entorno de Ejecución:** Servidor Privado Virtual (VPS) Linux (Oracle Cloud o DigitalOcean) operando 24/7 de forma ininterrumpida.
* **Conexión al Mercado:** Hyperliquid Python SDK.
* **Flujo de Datos:** El bot no usará peticiones REST constantes para evitar bloqueos por límites de API. Se conectará mediante **WebSockets** permanentes al flujo de datos de Hyperliquid para recibir el precio tic a tic, procesando los indicadores del Squeeze, ADX y volumen de manera local e instantánea.
* **Filtro Horario de Bloqueo:** El bot suspenderá la apertura de cualquier nueva posición entre las 15:15 y las 15:45 (hora de Madrid) para protegerse de los falsos rompimientos y la manipulación institucional de la apertura de Nueva York.
