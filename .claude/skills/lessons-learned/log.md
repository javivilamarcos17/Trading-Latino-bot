# Lessons Learned — Log de lecciones aprendidas

> Este archivo es la memoria persistente del proyecto.
> Claude lo lee al inicio de cada sesión para no repetir errores.
> **No borrar entradas antiguas** — son el historial de aprendizaje.

---

## Cómo añadir una lección

Di a Claude: `/nueva-leccion`
O directamente: *"Anota esto como lección aprendida: [descripción]"*

## Formato estándar

```markdown
## YYYY-MM-DD HH:MM — [Título corto]

**Error o aprendizaje:** [Qué pasó]
**Causa raíz:** [Por qué ocurrió]
**Lección:** [Qué hacer diferente en el futuro]
**Contexto:** [Dónde aplica — siempre, en ciertos módulos, etc.]
```

---

<!-- Las lecciones se añaden debajo de esta línea -->

## 2026-06-18 — Fidelidad al método de Jaime Merino (no "irse de la pinza")

**Error o aprendizaje:** Al analizar la estrategia empecé a proponer mejoras de quant
(riesgo fijo por trade en vez del 5% de Merino, filtros de entrada por "ventaja",
órdenes límite/maker, topes de pérdida inventados). Eso empezaba a desviarse del método
real de Merino.
**Causa raíz:** Sesgo de ingeniero a "optimizar" en lugar de **clonar fielmente**. El
proyecto es "Trading Latino **Purista**": el valor está en reproducir SU método, no en
inventar uno nuevo.
**Lección:** Toda regla del bot se clasifica y se respeta esa clasificación:
- 🟦 **NÚCLEO MERINO** — su método. Sagrado. No se toca ni se "mejora".
- 🟨 **REALIDAD TÉCNICA** — neutral y obligatorio (modelar comisiones/funding/slippage,
  conexión, datos). No cambia ninguna decisión suya; solo refleja el mundo real.
- 🟥 **AÑADIDO NUESTRO** — propuesta opcional. NUNCA contamina el núcleo. Solo se activa
  si el dueño lo aprueba explícitamente y el backtest lo justifica.
Ante la duda → se hace lo que hace Merino, no lo que yo creo "mejor".
**Contexto:** Siempre, en todo el diseño y código del bot.

## 2026-06-19 — Confundimos el papel del ADX en la entrada

**Error o aprendizaje:** La entrada de BTC-longs exigía ADX con pendiente NEGATIVA
("vendedores agotados"). La ablación + walk-forward mostraron que esa condición era el
fallo: rompía la robustez fuera de muestra (única variante que perdía en 2024). Invertirla
a pendiente POSITIVA (o quitarla) da una estrategia robusta: positiva en 4 de 5 años.
**Causa raíz:** Traducción mecánica errónea del método discrecional (el riesgo nº1 que ya
habíamos marcado). El ADX mide fuerza sin dirección; en un retroceso dentro de tendencia
alcista, que el ADX SUBA capta que el impulso de fondo se reactiva.
**Lección:** Validar cada condición de entrada por ABLACIÓN (quitar/invertir una a una) y
con WALK-FORWARD (varios años), nunca asumir que nuestra lectura del método es correcta.
Separar la operativa en partes y aislar el fallo es el método de trabajo.
**Contexto:** Entrada del cerebro; y método general para validar cualquier regla nueva.

## 2026-06-21 — El sniping muy apalancado está condenado por los costes (ley coste-en-R)

**Error o aprendizaje:** Probamos "sniping": arriesgar 1% pero MUY apalancado (stop ajustado),
entrando en barridos de liquidez / stop-hunts (la "manipulación"), con y sin filtro de tendencia
+ confirmación. Incluso en BRUTO el edge es microscópico (~+0,02R/op) e inconsistente entre años;
en NETO es destrucción total (−100%).

**Causa raíz (matemática, general):** El coste de una operación medido en unidades de riesgo (R)
es **coste% ÷ distancia-del-stop%**. Con sniping el stop es ajustado (es lo que permite el alto
apalancamiento), p. ej. 0,3%; con coste ida+vuelta ~0,15% pagas ~0,5R EN CADA OPERACIÓN. El mejor
edge de entrada documentado (~0,02R) es ~25x menor. Apalancar MÁS ajusta el stop y EMPEORA la
proporción coste/riesgo. Además el order-book real (dónde está la liquidez) no está en OHLCV: los
swings solo son un proxy pobre de la manipulación.

**Lección:** Antes de backtestear cualquier idea de alta frecuencia/alto apalancamiento, calcular
coste-en-R = coste% / stop%. Si es comparable o mayor que el edge de entrada plausible, está muerta
de salida. El apalancamiento NUNCA crea edge; solo escala (y el coste escala con él vía el stop ajustado).

**Matiz (probado después):** DETECTAR mejor la liquidez SÍ sube el edge de entrada: barrido de
niveles IGUALES + pico de volumen + mecha de rechazo subió el edge ×5-8 (de +0,02R a +0,165R). Y el
arreglo al muro es **stop ANCHO (menos apalancado)**, no más: baja el muro de ~0,2R a ~0,1R. Aun así,
con proxy OHLCV el edge es fino/frágil (2 de 8 configs, neto marginal). La versión potente requiere
el MAPA DE LIQUIDEZ real (order-book on-chain del DEX Hyperliquid + heatmap de liquidaciones por OI),
que NO es backtesteable con histórico gratis -> es una estrategia de datos EN VIVO, no de backtest.

**Contexto:** Scalping, sniping, cualquier estrategia de stop ajustado / alta rotación.

## 2026-06-21 — Lookahead MTF: un FVG del marco mayor no "existe" hasta que su vela CIERRA

**Error o aprendizaje:** La operativa SMC multi-timeframe (FVG diario + BOS 1H) daba un resultado
espectacular: +0,208R/op neto, POSITIVO todos los años incl. 2026 (+536R). Al revisar integridad
encontré el fallo: usaba la hora de APERTURA de la vela diaria como momento en que el FVG existe, y
permitía entradas en 1H DURANTE esa vela diaria aún sin cerrar -> lookahead. Corregido (la zona solo
se conoce en t_apertura + duración), el edge SE DESVANECE: −0,016R/op, win 33,3% = exactamente el
azar a 2R. TODO el edge era el bug.

**Causa raíz:** En multi-timeframe, un patrón del marco mayor (FVG, swing, vela) NO está confirmado
hasta que su vela CIERRA. El timestamp de las velas (ccxt/Binance) es la APERTURA; usarlo como
"momento conocido" adelanta la señal una vela entera del marco mayor — enorme en HTF (1 día).

**Lección:** En cualquier estrategia multi-timeframe, el dato del marco mayor solo es utilizable a
partir de `t_apertura + duración_de_la_vela`. Antes de creerse CUALQUIER resultado bueno, re-test con
retraso explícito y comprobar que apenas cambia (como hicimos con el carry). Un resultado que pasa de
+0,2R a 0 con el fix de timing era 100% lookahead. La regla del proyecto sigue: ante un edge bonito,
buscar PRIMERO el lookahead. Cazarlo aquí evitó desplegar una estrategia falsa con dinero real.

**Contexto:** Toda estrategia multi-timeframe; validación de cualquier edge nuevo.

## 2026-06-22 — La confluencia de indicadores de PRECIO es ilusoria (son redundantes)

**Error o aprendizaje:** Probamos si combinar indicadores (confluencia) y alinear con el marco mayor
mejora el acierto. Sobre 34.042 señales (1h, 12 monedas), el acierto se queda PLANO ~33% (= azar a 2R)
tengas 1 o 5 indicadores coincidiendo; el alineamiento HTF tampoco ayuda (34% vs 34%); y decae en 2026.

**Causa raíz:** La matriz de correlación lo destapa: trend y RSI correlan 0,69; trend/RSI vs ADX −0,33.
Los indicadores técnicos son TRANSFORMACIONES REDUNDANTES del mismo precio. "5 confirmaciones" son ~2
piezas de info independiente — y ni esas predicen dirección (mercado eficiente). La confluencia FEELS
como más evidencia pero es la MISMA evidencia contada varias veces.

**Lección:** No apilar indicadores de precio esperando que la "confluencia" cree edge — está demostrado
que no. La información INDEPENDIENTE (la que podría tener edge) NO está en el precio: está en datos de
otra naturaleza —funding, Open Interest, liquidaciones, order-book— que reflejan POSICIONAMIENTO, no
patrón de precio. Ahí hay que mirar. Y la dimensión de SALIDA (trailing/BE/parcial/tiempo) sigue sin probar.

**Contexto:** Diseño de estrategias; gestión de expectativas; por qué pivotamos a datos no-precio.

## 2026-06-21 — "Detectable ≠ explotable": las micro-ineficiencias direccionales son SUB-COSTE

**Error o aprendizaje:** La estadística del precio mostró efectos REALES y persistentes: autocorrelación
diaria negativa todos los años (incl. 2026, −0,06) y rebote tras caídas fuertes (+0,32% en BTC). Pero
al convertirlo en estrategia: la reversión dólar-neutral PIERDE (−12 a −38%, la rotación se come el
edge de −0,04); comprar-la-caída es beta disfrazado (pierde en 2026); y con filtro de tendencia queda
en +4%/año de preservación (DD −14%), por debajo del listón. Intradía (1h) es directamente aleatorio
(autocorr ~−0,01, ratio de varianza ~1, edge 0,007% << coste 0,07%).

**Causa raíz:** Un efecto estadísticamente DETECTABLE (autocorr ≠ 0) no es un edge TRADEABLE si es
más pequeño que los costes de explotarlo. Y ese hueco sub-coste es JUSTO la definición de mercado
eficiente: la ineficiencia persiste precisamente porque nadie puede arbitrarla con beneficio.

**Lección:** Ante cualquier patrón direccional, comparar el edge/op estimado (|autocorr|·σ, o la media
condicional) contra el coste ANTES de ilusionarse. "Es pura estadística" corta en ambos sentidos: la
estadística también DEMUESTRA cuándo no hay nada explotable. Lo tradeable de verdad son las PRIMAS
ESTRUCTURALES (carry/basis/funding-arb) — positivas por encima del coste porque compensan un riesgo
real, no porque predigan la dirección. La dirección, en cripto líquido, es esencialmente eficiente.

**Contexto:** Cualquier estrategia direccional / de patrón de precio; gestión de expectativas del dueño.

## 2026-06-21 — La reversión tras barrido de liquidez NO existe en velas (41k casos); las "señales SMC" empeoran

**Error o aprendizaje:** Estudio diagnóstico sobre 41.344 barridos de pool (BTC 5m/15m/30m/1h + 21
monedas 1h, sin lookahead): la tasa de reversión a 1,5R es 37,7%, POR DEBAJO del umbral de
rentabilidad (40% = valor de un paseo aleatorio). MFE≈MAE (1,87R≈1,90R) = sin edge direccional;
si acaso, ligera CONTINUACIÓN. Y las condiciones "smart money" (más toques, más volumen, mecha
grande) EMPEORAN la reversión; combinarlas da 29,8% (lo peor).

**Causa raíz:** Un barrido obvio (nivel claro + volumen) suele ser un movimiento REAL, no una
manipulación. El mercado ya descontó la lógica de la "trampa obvia". Con datos OHLCV no se puede
distinguir un stop-hunt de una ruptura genuina; justo lo que más parece trampa es lo que más continúa.

**Lección:** La "caza de liquidez / reversión SMC" detectable con velas no tiene edge — verificado
a gran escala. Cualquier edge real de sniping tendría que venir de datos que las velas NO ven
(order-book on-chain del DEX, mapa de liquidaciones por OI en vivo), y aun así la carga de la prueba
es alta tras este resultado. Medir la reacción con objetivo REALISTA (1,5R), no "pool opuesto"
(que está a ~7R y casi nunca se alcanza), y comparar SIEMPRE contra el umbral de paseo aleatorio
1/(1+R). 

**Contexto:** Sniping/SMC/barridos de liquidez; cualquier estrategia de reversión en niveles.

## 2026-06-21 — Los cortos/long-short tampoco son robustos; los edges DECAYERON en 2024-2026

**Error o aprendizaje:** Reabrimos los cortos quitando el beta de mercado (long-short
dólar-neutral, estilo Merino) para ver si así aguantaban. Probado a fondo: momentum
transversal L/S, largo-BTC/corto-alts-débiles, corto-solo, y reversión a corto plazo.
NINGUNO es robusto: drawdowns −40% a −96% y/o pierden en 2026. El momentum L/S fue el
"menos malo" (+11-13% CAGR en 2021-2023) pero lleva 3 años seguidos perdiendo (−5, −10, −9).

**Causa raíz:** El régimen de mercado cambió. Tanto el carry como el momentum transversal
RINDIERON en 2021-2023 y se COMPRIMIERON/DECAYERON en 2024-2026: el cripto maduró, se volvió
más eficiente y más correlacionado, y los edges sistemáticos clásicos se erosionaron. No es un
fallo de implementación; es que la ventaja estadística de esas familias se ha estrechado.

**Lección:** (1) Quitar el beta no convierte un edge muerto en vivo: si la dispersión/momentum
no persiste, el L/S tampoco rinde. (2) SIEMPRE mirar los últimos 2-3 años por separado: un CAGR
bonito puede esconder un edge ya decaído. (3) Ser honesto con el dueño: un ≥10%/año robusto a
apalancamiento seguro NO está respaldado por nuestros tests en el régimen actual. (4) El sesgo de
supervivencia es conservador para shorts (las delistadas fueron a cero), así que el corto medido
es un suelo — y aun así no compensa el riesgo de los rebotes violentos de los perdedores.

**Contexto:** Cualquier estrategia direccional/transversal; comunicación honesta del listón de rentabilidad.

## 2026-06-21 — La estrategia "estrella" era carry apalancado, y su DD bajo es engañoso

**Error o aprendizaje:** La v2 ("3 edges diversificados con risk-parity") era en realidad
**carry apalancado**: el risk-parity (1/volatilidad) daba ~97% del peso al carry (vol diaria
0,03%) y solo ~9% al sleeve fundamental (vol 2,1%). Forzar más peso al fundamental EMPEORABA
(añade drawdown direccional). Además, al medir el carry **realista** (cesta diversificada,
neto de costes), su +12%/año está **inflado por 2021 (+45%)**: 2025-2026 rinden ~+1%/año a 1x.
Y meter MÁS monedas (de 6 a 15) NO mejora: las alts de cola tienen funding ruidoso/negativo.

**Causa raíz:** (1) Confiar en una narrativa de "diversificación" sin auditar los PESOS reales
que produce el risk-parity. (2) Mirar el CAGR medio sin desglose por año (oculta que un solo año
de euforia domina). (3) Confundir el drawdown del *flujo de funding* (−1,6%) con el riesgo real
del carry, que es de **COLA** (quiebra de exchange, liquidación de la pata corta, pico de funding)
y NO aparece en el backtest.

**Lección:** (a) Auditar siempre los PESOS efectivos de cualquier asignación, no la intención.
(b) Desglosar por año/régimen antes de creerse un CAGR. (c) Para estrategias market-neutral, el
riesgo que importa es la COLA, no la volatilidad del backtest: documentarlo explícitamente y
limitar apalancamiento. (d) "Más diversificación" debe demostrarse, no asumirse.

**Contexto:** Carry y cualquier estrategia de cartera/asignación; comunicación honesta de riesgo.

## 2026-06-20 — Bug de NaN: abríamos operaciones con datos de calentamiento

**Error o aprendizaje:** En la revisión de realidad detecté que producción daba más
operaciones que el experimento. Causa: los filtros usaban `x <= 0` y `x is None`, que
NO atrapan NaN (`NaN <= 0` es False; un NaN de numpy no es None). Así, durante el
calentamiento de los indicadores, se colaban entradas con POC/ADX/stop = NaN → ¡operaciones
con stop NaN que nunca saltan bien!
**Causa raíz:** Confiar en comparaciones ingenuas con datos que pueden ser NaN.
**Lección:** Todo filtro numérico sobre indicadores debe usar un guard NaN-safe
(`x is not None and not isnan(x)`). Y reconciliar SIEMPRE producción vs experimento: si
no dan el mismo número de operaciones, hay un bug.
**Contexto:** Cualquier condición numérica del cerebro/estrategia.


## 2026-07-18 — Procesos largos SIEMPRE con seguimiento del harness
**Qué pasó:** el barrido de la matriz (8 TFs, horas de cálculo) se lanzó con `&` suelto y murió
en silencio a mitad de la 2ª temporalidad al cerrarse una sesión; se perdieron horas y nadie avisó.
**Causa raíz:** un proceso en background de shell no sobrevive al ciclo de vida de la sesión y no
notifica su muerte.
**Lección:** todo cómputo >10 min se lanza con run_in_background del harness (notifica al
terminar y su muerte es visible), nunca con `&` suelto. Verificar procesos vivos al retomar sesión.

## 2026-07-18 — No convertir episodios en leyes ni ruido de quincena en regimen
**Qué pasó:** en la misma sesión narré "el 2º disparo caza el suelo" (n=2 pares, P(azar)=0.25) y
"relevo de régimen observado en vivo" (una ventana de 14d que ocurre el 60-71% del tiempo bajo el
mismo régimen). El auditor tumbó ambas: datos válidos, narrativa inventada encima.
**Causa raíz:** tendencia a rematar hallazgos válidos con una historia más fuerte que los datos.
**Lección:** toda afirmación sobre <5 episodios es decoración, no hallazgo; antes de narrar un
"cambio de régimen" en vivo, calcular el percentil histórico de esa misma ventana bajo la misma
condición — si no es extremo (<10 o >90), es un martes cualquiera.
