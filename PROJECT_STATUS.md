# PROJECT_STATUS.md — Estado real del proyecto

> 🟢 **Este es el archivo más honesto del proyecto.**
> Aquí no se vende humo: dice qué funciona DE VERDAD hoy y qué no.
> Pensado para que cualquier persona —tú, un socio, un inversor— entienda
> el estado real en 30 segundos, sin saber nada de tecnología.
>
> **Regla de oro:** si algo no está aquí marcado como "funciona", asume que NO funciona.
> Una demo bonita NO es un producto. Documentación NO es código que funciona.
>
> Claude actualiza este archivo cada vez que cambia algo importante.
> Si ves que está desactualizado, pídele: *"Actualiza el PROJECT_STATUS"*.

---

## 1. Estado actual

> Marca con una **X** la casilla real. Solo una. Si dudas entre dos, elige la MENOR.

- [ ] 💡 **Idea**
- [ ] 📄 **Documentación**
- [ ] 🎬 **Demo**
- [X] 🛠️ **Prototipo de investigación** — Laboratorio honesto + arena 24/7 en PAPEL. NO hay dinero real.
- [ ] 🚀 **MVP**
- [ ] 🏭 **Producción**

**Estado: 🛠️ Prototipo de investigación con arena de papel 24/7.** (actualizado 2026-07-18)
El proyecto tiene un **sistema final de 3 motores** definido, auditado (6 rondas adversariales) y
con números oficiales reproducibles:

1. **Motor 1 — Núcleo 1D** (trend_rider + atr_break_trend, todo-clima): validado 2021-26.
2. **Motor 2 — Armas de ciclo** (planbtc, turtle_ciclo): disparan al final del oso. **ARMADAS AHORA**
   (285d desde ATH, −49%); planbtc lleva su primer largo vivo con ~+1.8R latentes.
3. **Motor 3 — Carry de funding** (cesta delta-neutral): paga en toro/lateral, duerme en oso.
   **DORMIDO por diseño** (funding del universo aún negativo); monitor construido y esperando.

**Números oficiales del portfolio (script publicado y verificado por 2 agentes):**
variante-espec (núcleo 4R 0.25%/op + turtle 3R + tope 5% riesgo abierto) = **+44.5% en 5.5 años,
caída máxima −12.4%, 2023 +35%**; variantes conservadoras +32-38%. ⚠️ Caveat estructural: los 5
mejores episodios concentran ~todo el resultado (p_episodio 0.05) — el riesgo es la concentración
episódica, no la volatilidad diaria. Escala ~linealmente con el presupuesto de riesgo.

**Descartes firmes con datos** (~30 familias juzgadas): TODO el intradía a costes reales (1m-30min),
estacionalidad horaria, ventana ETF, arma de techo, fade-del-fallo, stat-arb, y el resto del
cementerio del §5. El conocimiento negativo es el mayor activo del proyecto.

---

## 2. ✅ Qué funciona HOY

> Solo lo comprobado de verdad.

- **Arena 24/7 en papel** (Hyperliquid, costes reales): ~17.100 ops cerradas, 56 estrategias
  históricas, colector nube (rama `arena-data`, ~3 min) + tarea local. Cada op registra contexto
  rico y 5 políticas de salida (A/B de salidas gratis). ⚠️ Ops de estrategias recién desplegadas
  incluyen replay con metadata contextual falsa — excluir pre-despliegue (memoria `arena-backfill`).
- **Panel operativo**: `semaforo.py` (4 luces: ciclo, carry, dirección 7d, kill-switch 14d + 2
  diales contextuales: persistencia de funding y fase n/3) y `monitor_carry.py` (cesta candidata
  + triggers de desmontaje del manual carry). Ambos verificados en vivo.
- **Laboratorio research** con modelo de costes corregido (cR = COSTE/(D/entrada) + slip) y
  **tribunal de 6 leyes** (familia, bootstrap por episodio, sin-2023, causalidad, p<0.10, n≥100).
- **Sistema de agentes**: auditor adversarial (6 rondas — ha retirado números de ambos bandos),
  investigador externo (informes con fuentes), revisor semanal del forward.
- **Forward limpio A/B pre-registrado** (solo-largos, funding, vetos fvg_ob) acumulando desde
  2026-07-18; veredictos al llegar n≥30.
- **Lectura en vivo de Hyperliquid** (mapa de liquidez, order-book) verificada contra la API.

---

## 3. ❌ Qué NO funciona / NO existe todavía

- **No hay bot con dinero real** — ni siquiera testnet con órdenes. Todo es papel/lectura.
- **La cesta carry NO está montada** (dormida por régimen: funding del universo −1.3% APR).
  El riesgo de cola tiene manual (Ethena replicado) pero NO implementación.
- **El intradía histórico es INOPERABLE a costes reales** — confirmado por 3 vías independientes.
- **La concentración episódica** del portfolio (top-5 episodios ≈ todo el R) no tiene mitigación
  posible: es la naturaleza del edge. Solo se gestiona con el tope de riesgo abierto.
- **Matriz de temporalidades incompleta**: 30min cerrada (nada operable); 7 TFs computando.
- Los diales (fase, persistencia) son CONTEXTO, no reglas de disparo (auditoría r6).

---

## 4. 🧪 Cómo probarlo

```bash
# (1) SEMÁFORO diario — qué operar hoy, 4 luces + 2 diales:
.venv/Scripts/python.exe -m trading_latino.live.semaforo

# (2) MONITOR del motor 3 — estado de la cesta carry y su dial:
.venv/Scripts/python.exe -m trading_latino.live.monitor_carry

# (3) NÚMEROS OFICIALES del portfolio (el script de la conciliación):
.venv/Scripts/python.exe "<scratchpad>/concilia_portfolio.py"

# (4) MAPA DE LIQUIDEZ en vivo de Hyperliquid (solo lectura):
.venv/Scripts/python.exe -m trading_latino.live.mapa_liquidez BTC ETH
```

## 5. 🔚 Última decisión / hallazgo

- **2026-07-19s** — 🔥 ICHIMOKU: OUT-OF-SAMPLE TEMPORAL 2017-2020 SUPERADO con nota (Binance 4h
  BTC+ETH, datos que el hallazgo nunca vio): 9/26 n=257 +0.471R p_semanal=0.001; 12/30 n=223
  +0.378R p=0.005. Positivo en 9/10 años de 2017-2026 (unica celda roja: BTC-2018 -0.09).
  Patron de decaimiento de alfa clasico (mas fuerte antes, positivo hoy) — coherente, no
  sospechoso. Con esto: familia+significancia+n+sin-2023+causalidad+episodio+OOS temporal, la
  candidata historica mas fuerte del proyecto. Falta SOLO el veredicto del auditor (r7 en curso;
  vector critico: redundancia vs nucleo trend 4h). Si sobrevive -> arena en papel.

- **2026-07-19r** — 🌩️ CANDIDATA SERIA: ICHIMOKU 4h CON NUBE (script oficial
  research/ichimoku_test.py). Pasa las 6 leyes a la primera: familia coherente (6/6 celdas
  positivas solo el bloque 4h+nube; sin nube y 1D = ruido), mejor config 12/30 3R n=655 +0.178R,
  LOS 6 AÑOS POSITIVOS (2022 bajista +0.093 incluido), sin-2023 +0.151, largos/cortos
  equilibrados (+0.182/+0.173 — rareza en el cementerio), bootstrap por semana p=0.021,
  causalidad verificada (nube proyectada kj velas). PENDIENTE antes de desplegar: (a) veredicto
  del auditor, (b) test de redundancia vs nucleo trend (¿mismas operaciones con otro nombre?).
  Si sobrevive ambos, a la arena en papel.

- **2026-07-19q** — 🧮 RIESGO DE COLA DEL CARRY DIMENSIONADO (cierra la propuesta nº4 por
  completo): a escala retail (sin custodia off-exchange), la muerte subita de un venue cuesta
  ~0.5*manga*(1/lev + 0.3) — margen depositado + gap de la pata spot sin cobertura. Con lev=3 y
  presupuesto de cola del 3% del capital ⇒ MANGA CARRY MAXIMA ~9-10% del capital, que a +11.7%
  CAGR aporta ~1.0-1.2%/año al portfolio. Conclusion honesta: el motor 3 es MODESTO por diseño —
  paga el alquiler en toro/lateral pero no es palanca de rentabilidad; su valor es ser el motor
  del regimen OPUESTO a las armas de ciclo. Formula en el docstring de monitor_carry.py.
  ADRs 001-004 registradas (3 motores, tope 5%, taker, tribunal). Cabecera del STATUS reescrita
  al estado real. Matriz: 2h en curso (BTC+ETH hechos).

- **2026-07-19p** — 🧮 CONCILIACION CERRADA (2 cuentas pendientes, un muerto por cabeza):
  (1) PORTFOLIO 2023: causa raiz = la simulacion R4 del auditor NO tenia tope de riesgo abierto
  (apilaba 21+ posiciones, 25% de capital en riesgo → su +114% RETIRADO); mi +6.3%/5.5a y mi +49%
  de 2023 tambien RETIRADOS por irreproducibles (heredoc no guardado). NUMEROS OFICIALES (script
  publicado scratchpad/concilia_portfolio.py, verificado por ambos): variante-espec C (nucleo 4R
  0.25%/op + turtle 3R 0.5% + tope 5% riesgo abierto) = 2023 +35.0% · TOTAL +44.5%/5.5a ·
  DD -12.4%; variantes conservadoras D/E = +32-38% total. Caveat vigente: top-5 episodios = 110%
  del R total, p_episodio 0.0504 — la concentracion en pocos episodios sigue siendo el riesgo
  estructural. (2) FADE-DEL-FALLO: de watch-list a DESCARTE — rejilla completa de definiciones
  n=67-106, exp +0.011/+0.154R, p_episodio 0.27-0.46 en TODAS las celdas; mi n=139 irreproducible.
  Regla nueva derivada: numero no respaldado por script guardado = numero que no existe.

- **2026-07-19o** — ⚖️ AUDITORIA RONDA 6 (4 veredictos, todos aplicados):
  (1) Dial de fase MATIZADO: la familia de ventanas aguanta (5/10/15/20d, mismos episodios nucleo,
  +121-138% vs +33% base) pero la regla "esperar al 2o disparo" es post-hoc con n=2 pares
  (P(azar)=0.25 y ni se sostiene en 2020) → RETRACTADA; el dial queda como contexto sin regla de
  disparo. (2) Lead-lag: estadistica CONFIRMADA (sobrevive control de precio, p=0.001) pero dial
  REFUTADO por redundante — condicionar por el funding PROPIO del venue da lo mismo o mas (Q3
  propio +22.8% vs Q3 Binance +21.7%); recalificado como dial de PERSISTENCIA (autocorrelacion
  propia), semaforo y monitor_carry relabelados. (3) be05: decision CONFIRMADA (dif +0.099R/op
  p=0.003, resolucion intrabarra no sesga) pero "todos los años" era falso — son 4/6 (2021 gano
  be05); corregido. (4) Relevo de regimen REFUTADO como señal: ventanas 14d como la actual ocurren
  el 60-71% del tiempo bajo el mismo regimen (percentil 60-71 = martes cualquiera); el kill-switch
  actua igual pero NO hay "validacion en directo" de nada. Meta-leccion del auditor registrada:
  no convertir episodios sueltos en leyes ni ruido de quincena en regimenes observados.

- **2026-07-19n** — 🔄 RELEVO DE REGIMEN OBSERVADO EN VIVO (primera validacion en directo de la
  arquitectura): el cluster Asia (estrellas del oso) en deterioro sostenido 2 semanas
  (fvg_ob_asia +0.56→-0.15R, fvg_ob +0.23→-0.17R) EXACTAMENTE cuando ciclo maduro + carry
  despertando + sesgo LARGO — sus condiciones de caza se acaban y el kill-switch del semaforo las
  banquilla solo, sin mano. A/B forward apunta fuerte (solo-largos +1.113R n=14 vs todas -0.899R
  n=102) pero sin veredicto hasta n>=30 (protocolo). Matriz relanzada con seguimiento robusto
  (7 TFs restantes) tras morir el proceso anterior a mitad de 2h. Leccion operativa: procesos
  largos SIEMPRE con seguimiento del harness, no con & suelto.

- **2026-07-19m** — 🪟 VENTANA ETF (fixing 14-16h UTC) DESCARTADA: condicionada al flujo de AYER
  (causal), la deriva sale con signo contrario e insignificante (dif -10.2 bps, p=0.28); el efecto
  mismo-dia es fuerte (+50.6 bps) pero es simultaneidad no operable. Resto con pulso: momentum de
  flujos a dia completo (+37 bps/dia dif, p~0.10) — EN el liston, no debajo; reconfirma el
  descarte previo de ETF-flows standalone. Cola del informe del investigador COMPLETADA
  (estacionalidad ❌, lead-lag ✅ dial, ventana ETF ❌). Siguiente: monitor del motor 3
  (puente semaforo→cesta con triggers de desmontaje del manual carry).

- **2026-07-19l** — 📡 LEAD-LAG DE FUNDING CONFIRMADO (primer candidato virgen que sobrevive a la
  primera): Binance lidera el funding de Bybit/Gate mas alla de la inercia propia (coef +0.13 a
  +0.36, p~0.000 bootstrap por bloques 7d; placebo inverso mucho mas debil = asimetria real,
  replica MDPI 14(2):346 con datos propios 2024-26). NO es estrategia sola (decimas de bp/periodo
  vs 10-20 bps de montaje) → es DIAL DE TIMING del motor 3: condicionar apertura/rebalanceo de la
  cesta carry a Binance en cuartil alto suma +2.4 pts APR (BTC) / +11 pts (ETH) en zona media, y
  BTC 8→14.4% APR en zona alta (tabla monotona en casi todas las filas). Pendiente de integrar en
  la espec del motor 3 cuando se construya. 30min de la matriz cerrada: nada operable (mejor
  merino_fiel +0.063R, muy bajo liston) — 3a confirmacion anti-intradia.

- **2026-07-19k** — 🕐 ESTACIONALIDAD HORARIA re-testeada en era-ETF (BTC+ETH, bootstrap por dia):
  DESCARTADA. Las ventanas publicadas (22-23h UTC Quantpedia, lunes-Asia Concretum) estan muertas
  o son ruido en 2024-26 (p 0.21-0.97, ninguna significativa); los signos por hora se invierten
  entre eras = no estacionario. Unica celda estable en las 4 combinaciones: goteo +3-7 bps/h en
  21-22h UTC (cierre NYSE), inoperable en solitario (costes 8+ bps) y seleccionarla post-hoc
  seria snooping → solo observacion. Familia estacionalidad-intradia CERRADA (se suma a
  finde-edge y hour-filter ya descartadas). Siguiente de la cola: lead-lag de funding entre
  exchanges (el candidato mas virgen del informe).

- **2026-07-19j** — 📚 INFORME DEL INVESTIGADOR (con fuentes): (1) CORRECCION a 19i: la evidencia
  publicada (232k ordenes maker REALES en Binance, arXiv 2502.18625; arXiv 2407.16527; arXiv
  2607.01550) mide seleccion adversa real que mi simulacion a 15m no puede ver (cola, precio debe
  atravesar el limite): los fills se concentran en las operaciones perdedoras y en señales
  direccionales el coste dominante son los fills perdidos → regla final: TAKER en entradas de
  ruptura, maker solo en salidas pasivas. Mi sim del 19i era optimista por granularidad. (2) CARRY
  TAIL: manual Ethena replicable a retail (colateral fuera del exchange/stable-margin, cap por
  venue, desmontaje por funding<0 persistente o de-peg); OJO: carry agregado con Sharpe NEGATIVO
  en 2025 (crowding) → motor 3 exige el semaforo de funding, no es rentable siempre. (3) 5 edges
  con paper detras; mejores ratio esfuerzo/originalidad: lead-lag de funding entre exchanges
  (MDPI 14(2):346, el mas virgen) y re-test estacionalidad horaria era-ETF 2024-26 (test barato
  con cache 15m propia). Ambos a la cola de pruebas.

- **2026-07-19i** — 🧾 EJECUCION MAKER cuantificada (nucleo 1D, 545 ops 2021-26): limite al cierre
  llena ~100% historicamente (granularidad 15m), sin seleccion adversa medible, pero el ahorro es
  DESPRECIABLE en 1D (+1R total en 5.5 años, ~+0.002R/op) porque los stops anchos diluyen la
  comision en R. Veredicto: usar maker al ejecutar en real como higiene (gratis), pero NO es
  palanca de rentabilidad; lo habria sido en intradia (stops 10x mas finos) pero el intradia esta
  descartado por costes. Propuesta cerrada. Investigador externo lanzado en paralelo (maker/carry
  tail/edges 2026) — informe pendiente.

- **2026-07-19h** — 🧭 DETECTOR DE TRANSICION DE FASE backtesteado (BTC 2019-26, funding real Binance):
  triple convergencia (ciclo maduro 30d + funding 7d cruza a positivo + giro direccional 7d).
  7 episodios cerrados: media +180d +95% vs +33% base, pero 2/7 negativos → n=7 = DIAL CONTEXTUAL,
  no sistema (ley del tribunal). Patron clave: el PRIMER disparo en un oso es prematuro
  (2019-10 -12%, 2022-06 -21%, 2026-05-19 -18%); el SEGUNDO caza el suelo real (2020-04 +59%,
  2022-11 +62%). El disparo prematuro de este ciclo YA ocurrio (mayo 2026); el recruce de funding
  de julio esta armando el segundo → refuerza mantener armadas turtle_ciclo/planbtc sin añadir
  riesgo nuevo hasta que dispare. Pendiente: integrarlo como nota informativa en el semaforo.

- **2026-07-19g** — ⛏️ MINERIA DEL VIVO (17.138 ops): (1) la racha de -1R uniforme del nucleo NO es bug
  (mae>=1.0 en todas: stops reales barridos) — son cortos de tendencia barridos por rebotes en V =
  firma de SUELO, confirmacion independiente de la transicion de fase del semaforo. (2) A/B de
  politicas de salida con las 5 que registra la arena: be05 gana en vivo en el nucleo (+0.331R vs
  -0.013R, n=90) PERO el historico 1D 2021-26 la refuta TODOS los años (pareado -0.10R/op,
  p=0.999) → artefacto de regimen; se mantiene target fijo; el A/B sigue gratis en la arena
  (revisar si n>=100 vivo con ventaja sostenida en tendencia). (3) ⚠️ turtle_ciclo/planbtc tienen
  ops replay-backfill al desplegarse (funding/OI/FNG estampados al registro, no historicos): su
  metadata contextual NO vale para analisis; precios OHLC si. (4) scalp_break vivo -0.252R (n=202)
  reconfirma el veredicto anti-intradia → retirar del semaforo si sigue asi al proximo corte.

- **2026-07-19f** — 🔺 ARMA DE TECHO descartada (familia 8/9 negativa, p=0.90) + hallazgo de
  asimetría: en cripto los SUELOS son eventos operables (la V) y los TECHOS son procesos ruidosos
  (los breakdowns tras euforia se recompran). El techo se gestiona con defensas (no-largos en
  euforia, vol-targeting, carry cobrando), no con un arma corta. Semáforo con 4ª luz (carry)
  operativa: primera lectura +3.0% APR neutral — funding despertando desde negativo, coherente
  con la triple convergencia (ciclo maduro + giro a largo + funding cruzando) = posible fin de oso.
  Cola de propuestas: detector de transición de fase, ejecución maker, riesgo de cola carry, fixing-window.

- **2026-07-19e** — 🔄 EL TERCER MOTOR: carry como pata de régimen opuesto.
  1. Carry selectivo p90 (propuesta del investigador): REFUTADO con datos (pierde vs siempre-dentro:
     2024 +4.9% vs +11.9% — los picos no compensan perderse la acumulación).
  2. **HALLAZGO de arquitectura: el carry paga en TORO/LATERAL (2021 +47%, 2024 +12%) y duerme en
     oso (2025 +2.6%, 2026 −0.4%) — el régimen OPUESTO a las armas de ciclo.** Sistema final de 3
     motores complementarios: Núcleo 1D (todo tiempo) + armas de ciclo (fin de oso) + CESTA CARRY
     15 monedas (toro/lateral, +11.7% CAGR neto histórico, DD −2.3%, riesgo de cola aparte).
     El semáforo ganará una luz más: funding estructural de la cesta > 0 → carry ON.
  3. Covered calls Deribit: overlay de tenencia (Sharpe~1 pata corta) — solo si algún día se
     mantiene BTC spot; nunca puts. ETF-flows: mi test previo manda (muere a costes) sobre la cita.

- **2026-07-19d** — ⚖️ RONDA 5: breadth RETRACTADO (lookahead mío: la ventana ±5d miraba el
  futuro; la versión causal sin-2023 da +0.086R ≈ nada — era la V oct23-24 redescubierta por
  3ª vez). Fade-del-fallo: DUDOSO (12 episodios, p=0.28 — a vigilar, no hallazgo).
  **LEY NUEVA DEL TRIBUNAL (obligatoria para toda estrategia): (i) bootstrap por EPISODIO,
  (ii) test SIN-2023, (iii) chequeo de CAUSALIDAD de cada filtro.** Los dos errores sistémicos
  del proyecto quedan institucionalizados como checks: ops corales contadas como independientes
  y validación dominada por el episodio 2023-24.

- **2026-07-19c** — ⚖️ AUDITORÍA R4 del portfolio + versión CORREGIDA + 2 originales al tribunal.
  1. **Portfolio +113% → INFLADO-PERO-REAL**: el 4R era ajuste a 2023 (años recientes favorecen
     2R-3R); riesgo abierto llegaba al 25% simultáneo (¡72 posiciones!); las 3 patas disparan sobre
     el MISMO episodio (V oct23-24) → era UNA apuesta de ciclo con tres tamaños.
  2. **PORTFOLIO CORREGIDO (3R + tope de RIESGO ABIERTO 5% + book al cierre): +6.3% total,
     peor caída −3.7%** ≈ +1.1%/año ultraseguro. El retorno escala ~proporcional al presupuesto de
     riesgo elegido (tope 10% ≈ doble). LA VERDAD: el edge es real pero pequeño; los números grandes
     eran concentración. Decisión de tamaño = decisión de cuánta concentración de ciclo se acepta.
  3. **VIVO coherente con el histórico**: trend_rider 1D vivo +0.35R (n=44), atr_break_trend +0.29R
     (n=23) — la columna 1D es real en ambas lentes. planbtc/turtle en ventana, esperando señal.
  4. **2 hallazgos ORIGINALES en ronda 5 del auditor**: fade-del-fallo (9/9, p=0.000 por op) y
     breadth coral (6/6, +0.555R confirmada vs −0.129R solitaria). Retest: MUERTO (−0.015R).
     Breadth-cortos: débil. Pendiente veredicto por episodios.

- **2026-07-19b** — 💼 PORTFOLIO FINAL simulado (todo a costes reales, 2021-26, 610 ops):
  **Núcleo 1D@4R × vol-targeting (0.3%) + planbtc (1%) + turtle_ciclo (0.5%) =
  TOTAL +113.2% · peor caída −19.4%** · años: 2021 −2.0 / 2022 +16.2 / 2023 +49.0 /
  2024 +34.1 / 2025 −9.7 / 2026 +3.8. Vs núcleo solo a 2R: +51%/−17.4%. Positivo 4/6 años,
  ~+13%/año compuesto con DD<20%. PENDIENTE: auditoría adversarial del ensamblaje
  (el objetivo 4R se eligió del mismo histórico — mitigado por familia monótona 2R/3R/4R).

- **2026-07-19** — 🏛️ RESOLUCIÓN FINAL DE LA ARQUITECTURA (todo a costes reales).
  1. **RETRACTACIÓN: el "interruptor de ciclo para FVG" era artefacto del bug de costes.** Con el
     parquet regenerado: oso-maduro −0.29/−0.31/−0.37R vs fuera −0.29/−0.30/−0.36R — indistinguible.
     La familia Asia intradía NO tiene soporte histórico en NINGUNA condición a costes reales.
  2. **Maestro v3 (con clúster Asia): −23.2%** — confirmado que el clúster B histórico resta. El
     PORTFOLIO FINAL validado es el NÚCLEO 1D: trend_rider + atr_break_trend + vol-targeting =
     **+51% total 2021-26, peor caída −17.4%, positivo 5/6 años** (2021 −3%) + armas de ciclo.
     MEJORA (19-jul): salidas del núcleo — familia monótona 2R +0.255R → 3R +0.280R → **4R +0.337R**
     (n=545; el trailing empeora: +0.10R). Objetivo de DESPLIEGUE del núcleo: 4R. La arena sigue
     midiendo las 5 salidas para el juicio forward. + armas de ciclo
     (planbtc, turtle_ciclo — honestas por episodios) + FOMC simbólica.
  3. **La familia Asia queda SOLO-VIVO**: su única evidencia es el forward de la arena (costes
     limpios, 2026). Tamaño mínimo, gobernada por semáforo — que de hecho la tiene banquillada
     por decay ahora mismo. Si el forward limpio (línea base 18-jul) no la sostiene, se retira.
  4. Matriz total 13 familias × 9 TF: computando (3 barridos + 5m descargado).

- **2026-07-18 (CIERRE DEL DÍA)** — La verdad final a costes reales + turtle_ciclo desplegada.
  1. **REGEN a costes corregidos (82k ops 15m, 2021-26): el intradía histórico es INOPERABLE** —
     carteras A/B/C = −100% (ruina), rotación adaptativa −82%. El intradía SOLO se justifica por el
     VIVO (arena con costes limpios, régimen 2026, tamaño mínimo, semáforo). Caso cerrado.
  2. **TURTLE CONTRA-RÉGIMEN** (hallazgo propio auditado): familia 6/6 (+0.59/+0.86R), robusta 9/9
     umbrales, sin lookahead; verdad del auditor: n_efectivo=7 episodios (p~0.02-0.05), 80% del R de
     la V oct23-24 → ARMA DE CICLO hermana de planbtc. Desplegada como turtle_ciclo (1D, solo largos,
     ciclo profundo) — ventana ACTIVA hoy, esperando la ruptura de 55d.
  3. **El sistema final que queda en pie:** columna 1D/4h (trend_rider/atr_break_trend/turtle55 +
     vol-targeting CONFIRMADO) + armas de ciclo (planbtc, turtle_ciclo) + FOMC (hipótesis viva, riesgo
     simbólico) + Asia-15m solo-vivo gobernada por semáforo (kill-switch 14d, dirección 7d, veto spread>p90).
  4. Descartadas hoy con datos: stat-arb pares (todas TF), hash-ribbons (rota 2025+), PSAR/Heikin/TTM,
     dual momentum (universo), finde-edge (p=0.55). Permisos aceptar-todo con los 5 candados intactos.


- **2026-07-18 (cierre)** — 🐢 TURTLE CONTRA-RÉGIMEN: auditada y desplegada con etiqueta honesta.
  Hallazgo propio (breakout de 55d CONTRA el clima dominante): familia 6/6 (+0.59/+0.86R), robusta
  a umbrales 9/9, sin lookahead, exits idénticos a 15m. VERDAD del auditor: n_efectivo=7 episodios
  (p~0.02-0.05), 80% del R de la V de oct23-24 → ARMA DE CICLO hermana de planbtc (~1 ventana/2 años).
  Desplegada  (1D, SOLO largos, ciclo profundo) — ventana ACTIVA hoy, esperando ruptura.
  También: stat-arb pares DESCARTADA (todas las TF), hash-ribbons rota desde 2025, PSAR/Heikin/TTM
  descartadas, ichimoku solo 4h. Permisos: aceptar-todo configurado manteniendo los 5 candados.


- **2026-07-18 (noche-2)** — ⚖️ AUDITORÍA RONDA 2: vol-targeting CONFIRMADO (18/18 configs
  reducen caída — familia entera, no una celda); FOMC-fade degradada a HIPÓTESIS VIVA (bootstrap
  p=0.23 con n=44 — dirección plausible, riesgo simbólico solo); finde-en-tendencia REFUTADA como
  señal (p=0.55; se mantiene 1D en finde por NEUTRALIDAD, no por edge); dual momentum REFUTADO
  (sesgo de universo: HODL SOL +3331%; BTC/ETH solo +363%; signo depende del lookback; DD -36/-79%).
  META-LECCIÓN adoptada: probar FAMILIAS de configuraciones + significancia (bootstrap) ANTES de
  llamar a algo validado. Turtle-55 pendiente de ese estándar en la matriz total.

- **2026-07-18 (noche)** — 📅 FOMC-fade (ver corrección arriba) + semáforo recalibrado.
  1. **SHORT 48h post-anuncio FOMC** (hipótesis pre-registrada del investigador, calendario oficial):
     replicada con nuestras velas 15m: n=44 eventos 2021-26, win 66%, +0.44%/evento NETO, positiva
     5/6 años (~+3.5%/año, 8 ops/año). Satélite de calendario estilo planbtc. Pre-drift largo: descartada
     (muerta desde 2023). PENDIENTE: auditoría adversarial antes de desplegar.
  2. **Semáforo recalibrado con backtests del analista**: dirección 30d→7d (reacciona en 2-4 días),
     kill-switch 21d→14d (mejor R y menos falsas retiradas). Primera lectura: modo DEFENSIVO correcto
     (Asia banquillada por decay real mientras el mercado gira a largo). scalp_break reactivada
     (+0.19R forward vivo limpio, único scalp con evidencia viva positiva).


- **2026-07-18 (tarde)** — 🔬 CAMPAÑA AUTÓNOMA: investigación externa × datos propios.
  1. **Estacionalidad horaria (papers Quantpedia):** la anomalía 21-23h UTC EXISTE en nuestros datos
     pero muere a costes como estrategia. CRÍTICA ORIGINAL: para nuestro sistema corto-sesgado esas
     horas son las PEORES (vivo -0.365R) — el paper AL REVÉS es nuestra ventaja.
  2. **⭐ FILTRO NUEVO doble-validado: fvg_ob SIN entradas 18-23h UTC** → histórico +0.003→+0.019R
     (n=10k) y VIVO +0.068→+0.232R (n=916, ×3.4). Solo para fvg_ob (no mejora trend_rider ni Asia).
     Regla de despliegue del semáforo.
  3. Barrido de TEMPORALIDADES INÉDITAS 30m/2h (7 estrategias × 3 monedas × 5.5 años): computando.


- **2026-07-18** — 🏆 **PORTFOLIO MAESTRO v2: POSITIVO TODOS LOS AÑOS 2021-2026.**
  Composición: columna 4h (atr_break_trend + merino 4h, siempre) + FVG-Asia y ob_asia_close-largos
  (SOLO oso maduro: >250d desde ATH y dd>40%) + planbtc (1%). Presupuesto POR estrategia (tope
  2/día/estrategia), riesgo 0.25%, neto de costes+slippage.
  **Años: 2021 +11.5% · 2022 +19.9% · 2023 +18.0% · 2024 +11.3% · 2025 −0.0% · 2026 +9.6%
  · TOTAL +92.5% · peor caída −26.8%** (vs estáticas −48/−81% con caídas −71/−88%).
  ⚠️ Cautela: ensamblado con piezas validadas independientemente pero COMPUESTO sobre el mismo
  histórico → el juez final es el forward. Siguiente: semáforo diario sobre esta base (P2 del plan).


- **2026-07-17** — 🎯 EL INTERRUPTOR DE CICLO (Plan BTC) + veredictos a años vista.
  1. **⭐ HALLAZGO MAYOR: la métrica de ciclo de Plan BTC (>200d desde ATH o caída>50%) es el
     INTERRUPTOR de nuestra familia FVG:** fvg_ob_asia +0.106R en ciclo profundo vs −0.065R fuera
     (n=1.7k/2.7k); fvg_ob +0.053R vs −0.030R (n=5.4k/8k). Explica por qué 2026 funciona y da la regla:
     operar FVG-Asia SOLO en ciclo profundo (condición CUMPLIDA hoy: 284d, dd 50%). Se aplica al
     desplegar, no al recoger (colector queda crudo).
  2. **Plan BTC mecanizado VALIDADO** (diario, BTC-only): +0.46R n=49 (2018-26) Y **+0.36R n=104 en 14 AÑOS (Bitstamp 2012-2026, 4 ciclos, positiva en las 4 épocas)** — el edge más robusto del proyecto. ROBUSTO 27/27 en
     sensibilidad. En vivo como `planbtc` (1d). NO baja a TF menores (sniper 15m −0.02R, 4h diluye).
  3. **Los % 2021-26 de las intradía actuales: NEGATIVOS** (ob_asia_close −0.04R, carteras estáticas
     −48% a −81%). El edge Asia es un fenómeno de ERA (2026 = ciclo profundo). trend_rider única
     robusta todos los años (+0.025R). El vivo 2026 (+0.16/+0.20R forward) coincide con el backtest 2026.
  4. **Rotación adaptativa**: umbral estricto (90d, >+0.10R, n≥30) minimiza pérdidas (−8% total,
     −35% DD vs −81% naive) pero no convierte estrategias sin edge en cartera ganadora → es la RED DE
     SEGURIDAD, no el motor. Arquitectura final: CICLO (interruptor) → ROTACIÓN (red) → operativas.
  5. En vivo nuevos: `planbtc` (1d), `trend_rider_f` (funding 3/3), `ob_asia_close_L` (solo largos).
     ⚠️ PUSH PENDIENTE del dueño (~14 commits locales; la nube corre código de hace 3 semanas).


- **2026-06-25** — 🧭 PROTOCOLO SISTEMÁTICO + el edge vive en 4h + scalping cerrado.
  1. **Construido el PROTOCOLO** (`research/protocolo.py`, metodología en `docs/PROTOCOLO_PRUEBAS.md`):
     cada estrategia pasa por las MISMAS etapas — multi-TF (15m/1h/4h) × multi-régimen (toro/lateral/oso)
     × costes reales → veredicto comparable (ROBUSTA / DE RÉGIMEN / DESCARTAR). La columna vertebral.
  2. **⭐ HALLAZGO: la familia momentum/breakout es ROBUSTA en 4h, no en 15m.** El protocolo (3 años,
     3 monedas, NETO de costes): atr_break_trend **+0.229R**, merino +0.219R, atr_break +0.201R,
     merinox +0.198R — **positivas en LOS 3 CLIMAS**, 3× mejor que en 15m. En 4h los stops anchos hacen
     que la comisión no pese. El OB base sigue sin edge (−0.019R, solo lateral).
  3. **Aplicado a la arena** (pendiente de push): atr_break/donchian +4h; `atr_break_trend` y
     `trend_rider` (rellena el TORO, ROBUSTA) nuevas en 4h. merino/merinox ya en 4h.
  4. **SCALPING 5m: CERRADO, no viable.** Probado exhaustivo (5 operativas × normal/alta-vol × taker/maker
     × fija/trailing). El trailing mejora el bruto pero net@maker solo da positivo marginal en 1 moneda
     por operativa (ETH breakout +0.05R) = no robusto. La comisión se come el edge diminuto del 5m.
     El MISMO edge (momentum+trailing) rinde 4× y consistente en 4h. Retirado scalp_break (falló a escala).
  5. **Datos en vivo:** la nube nunca paró (commits cada 3-4 min); el desfase local era por el PC dormido.
     ⚠️ **PUSH pendiente del dueño** (`git push origin master`) — hasta entonces la nube corre el código viejo.


- **2026-06-24** — 🚨 GIRO ESTRATÉGICO: el multi-año (BTC 2021-2026, ~50k ops/estrategia) destapa la verdad.
  1. **La familia OB base NO tiene edge multi-año:** ob_trend/ob_plus/ob_regime = **−0.028R**, NEGATIVA en
     los 6 años Y en los 3 climas (alcista/lateral/bajista). Lo que veíamos en vivo era específico del
     filtro Asia + régimen reciente (o sesgo). El multi-año hizo su trabajo: destapar el autoengaño.
     ⚠️ MATIZ: el multi-año prueba el DETECTOR BASE; las versiones Asia-filtradas (ob_plus_asia...) NO
     se testearon aún — el filtro Asia podría añadir edge real. Pendiente de validar.
  2. **⭐ merinox = EL EDGE ROBUSTO:** +0.080R, POSITIVA en los 6 años Y en lateral (+0.10) + bajista
     (+0.15). merino base también (+0.058R). Es la estrategia de Trading Latino/Merino (EMA10/55 + ADX +
     squeeze + EMA200 + sin clímax). **Promocionada a estrategia PRINCIPAL.** Quitado su 1h (era veneno).
  3. **atr_break VINDICADA:** +0.018R multi-año (trend variant +0.023R, mejor). Su −0.47R en vivo era
     muestra pequeña (n=51). Mantenida, quitado el 1h.
  4. **Mean Reversion MUERTA:** −0.20R en TODOS los climas, incluido lateral. Hipótesis enterrada.
  5. **vwap muerta** (−0.023R), **donchian neutral** (±0.00R).
  6. **PATRÓN SISTÉMICO confirmado:** el 1h es malo en casi todas (pocas señales, peores). El 15m (y el
     4h para Merino) es el punto dulce. Retirado el 1h de 7 estrategias. El 5m es ruido salvo para orf.
  7. **HONESTIDAD:** son salidas de 15m sin slippage, solo BTC (ETH/SOL pendientes). Edges pequeños
     (+0.08R) que el slippage puede comerse. Hay que confirmar en ETH/SOL antes de fiarse del todo.

- **2026-06-23 (tarde)** — 🧹 PROFESIONALIZACIÓN + nueva familia validada + poda con evidencia.
  1. **`atr_break` (canal de Keltner adaptativo) — NUEVA estrategia VALIDADA** en Binance 50d (1m exacto):
     **+0.41R en BTC Y ETH, win 52%** (vs 36-41% de las OB), positiva en los 2 meses y las 2 monedas.
     Sesgo de diseño BAJO (de manual + concepto de un vídeo, no exprimida de los datos). **Perfil de edge
     COMPLEMENTARIO:** gana en NY (+0.53R) donde las OB pierden (−0.12R) → diversifica de verdad. Ya en la
     arena recogiendo datos en vivo. Su variante con filtro Asia/EMA200 NO mejoraba la base → entra sola.
  2. **Poda con evidencia (respetando la MEJOR de las 5 salidas, no solo 'fixed'):** retiradas 4 muertas —
     `sweep` (−0.18R), `breaker` (−0.05R, n=104), `breaker_prev_ny` (−0.58R; el +1.52R inicial era ruido de
     n pequeño), `judas_swing_ob` (−1.56R, apenas dispara). **Arena: 34 → 32 estrategias activas.** Histórico
     conservado, retiros reversibles y documentados en el código.
  3. **Mean Reversion (anti-tendencia) — PROBADA y RECHAZADA (de momento):** comprar capitulación
     (banda 2.5σ + RSI<25 + clímax de volumen). En 50d (régimen bajista) **perdió −0.32R** (atrapar cuchillos,
     confirmado). NO va a la arena. Encolada al multi-año para el test justo: ¿gana en régimen LATERAL (2023)?
  4. **6 estrategias de scalping/HFT/MEV analizadas y DESCARTADAS con razón** (market-making Avellaneda-Stoikov,
     order-book imbalance, grid trading, CEX-DEX arb, JIT liquidity, MEV sandwich, CVD order-flow): requieren
     Rust/C++, nodos propios, sub-milisegundo, capital institucional y comisiones 0% — **imposibles de construir
     y de validar** con nuestra infra (regla nº1: no fiarse de lo que no se puede backtestear). El sandwich es
     además depredador. Lo único reciclable: usar órdenes maker (límite) para bajar costes si algún día hay
     dinero real, y CEX-DEX arb coincide con el carry ya identificado (pero su versión rentable es sub-ms).
  5. **Métrica viva:** longs 803 (37%) / shorts 1390 (63%) — sesgo a corto coherente con el régimen bajista.
  6. **Salud del sistema:** tests 22/22, los detectores nuevos IDÉNTICOS entre arena y backtest (la validación
     aplica a la versión en vivo), todas las estrategias activas con dispatch verificado, board regenera sin error.

- **2026-06-23** — ⭐ PRIMERA VALIDACIÓN FUERA DE MUESTRA del edge OB-Asia (el hallazgo más sólido del proyecto).
  1. **Contexto:** la arena en vivo (1.737 ops) sugería ganadoras espectaculares (`ob_plus_asia` +1.30R,
     `ob_plus_asia_r3` +2.19R). PERO **todas las ops son de UN SOLO RÉGIMEN** (1.736/1.737 con miedo<30;
     bajista: cortos +0.42R vs largos −0.06R; Asia +0.75R vs NY −0.48R). Riesgo de autoengaño: las "34
     estrategias" son **la misma apuesta** (corto+OB+Asia+bajista) medida muchas veces, y varias se
     diseñaron VIENDO esos datos (sesgo de diseño).
  2. **Prueba (`research/backtest_ganadoras.py`):** backtest de 52 días (May 2–Jun 23 2026) con velas de
     15m de Hyperliquid para señales + **1m de Binance** para salidas exactas (~75k velas/moneda, ~1.300
     ops). Binance da meses de 1m (Hyperliquid solo 3-4 días); precio idéntico <0.1%.
  3. **RESULTADO — el edge AGUANTA:** `ob_regime_asia` +0.32R (n=1.286), `ob_asia` +0.31R (n=1.308),
     `ob_plus_asia` +0.16/+0.23R, `ob_trend_r3` +0.10/+0.16R. **Positivo en los dos meses Y en BTC+ETH.**
     Es la validación más fuerte de cualquier cosa en el proyecto.
  4. **PERO 3 avisos anti-autoengaño:**
     (a) **Los números en vivo estaban INFLADOS 6-8×.** Edge real ≈ **+0.2-0.3R/op**, no +1.3-2.2R.
     Muestra pequeña + suerte inflaban la tabla en vivo.
     (b) **Sigue siendo el MISMO régimen** (May-Jun bajista/miedo). NO sabemos qué pasa en euforia/alcista.
     (c) Las variantes apiladas por diseño (`ob_plus_asia_r3`, `ob_asia_close`) NO se validaron; las
     ganadoras robustas son las de mayor muestra (`ob_regime_asia`, `ob_asia`), no las que lideraban en vivo.
  5. **Metodología confirmada:** vivo genera hipótesis (sin sesgo, va hacia adelante) → Binance valida
     fuera de muestra → solo entonces fiarse. Funcionó.
  6. **Comprobación:** 9 estrategias casi muertas (smc=0, ob_scalp=2, mtf=2, ny_london_sweep=3,
     judas_swing_ob=4 ops): las ICT de ventana estrecha disparan demasiado poco para medir nada.
  7. **Infra:** merge a master (34 estrategias + SOL + 3 ICT) → la nube ya corre el código nuevo;
     `data_store` destrackeado de las ramas de código (datos solo en `arena-data`).

- **2026-06-22** — Reconstrucción de la ARENA en vivo como laboratorio de medición 24/7 (nube).
  1. **Decisión del dueño:** en vez de cerrar en "el direccional es eficiente", montar un laboratorio
     en vivo que mida muchas estrategias en condiciones reales y recoja la MÁXIMA información para
     descubrir si hay edge y bajo qué condiciones. Filosofía: analizar → probar → mejorar en directo.
  2. **Construido:** cobertura amplia de temporalidades, contexto rico por operación, **registro
     continuo de contexto** (simular cualquier operativa futura), estrategias compuestas multi-factor
     (`adrig`, `merinox`), multi-temporalidad real (`mtf`) y OB reforzado (`ob_plus`).
  3. **Aviso de honestidad:** la recolección EN VIVO lleva **horas/días**, no semanas. La mayoría de
     datos actuales son **backfill** de un solo tramo de mercado (miedo + funding positivo, sin variedad
     de régimen). **NO hay conclusiones todavía.**
  4. **Lead a confirmar (NO probado):** la **familia OB** es la única consistentemente positiva en el
     backfill (`ob_trend` 15m +0.77R n=68; `ob` 15m +0.18R n=151), con **objetivo fijo 2R** (el
     break-even temprano le corta ganadoras) y **mejor en 15m**. Filtro validado: **no entrar en clímax
     de volumen** (>2.5x media). Falta confirmar con datos en vivo de varios regímenes antes de fiarse.
  5. **Resto (fvg, vwap, scalps, adx, donchian, volumen):** negativas en el backfill → candidatas a
     retirar, pero **se espera a tener datos en vivo** antes de podar.

- **2026-06-21** — Depuración de la estrella (v2) + reapertura de los cortos. Hallazgos:
  1. La v2 era en realidad **carry apalancado** (risk-parity le daba ~97% al carry); el sleeve
     fundamental restaba (añadía drawdown direccional).
  2. El carry, medido **realista** (cesta diversificada, neto de costes), rinde **~+12%/año
     (inflado por 2021)**, **~+1-5%/año en años recientes**, DD −1,6% (solo del flujo; falta la cola).
  3. **Meter más monedas (6→15) NO mejora** — las alts de cola tienen funding ruidoso/negativo.
  4. **Reabrimos los cortos** (long-short market-neutral, Merino, reversión): **ninguno robusto**
     (DD −40% a −96% y/o pierden en 2026).
  5. **Hallazgo de fondo:** tanto el carry como el momentum transversal **rindieron en 2021-2023 y
     se DECAYERON en 2024-2026** — el cripto maduró y los edges sistemáticos clásicos se comprimieron.
  6. **Arbitraje de funding DEX↔CEX (corto Hyperliquid / largo Binance):** edge REAL market-neutral,
     **positivo casi todos los años** (BTC/ETH/SOL), CAGR ~+5-6% a 1x, DD −1 a −4%. PERO **se está
     comprimiendo** (BTC 2024 +10,9% → 2026 +0,2%) según madura Hyperliquid. Forward ≈ 0-2%/año.
     Dato accionable: el carry rinde casi el DOBLE shorteando en Hyperliquid (+14,4%) que en Binance
     (+6,6%), a cambio de riesgo de contraparte del DEX.
  7. **Sniping muy apalancado (barridos de liquidez):** en backtest OHLCV, edge fino y solo con
     stop ANCHO (no apalancado). Pero detectar mejor la liquidez SÍ sube el edge ×5-8.
  8. **Decisión del dueño:** construir el SNIPER DE LIQUIDEZ EN VIVO sobre Hyperliquid (DEX con
     order-book transparente). Hecho: mapa de liquidez en vivo + paper-sniper (solo lectura).
  9. **Estudio diagnóstico (41.344 barridos):** la REVERSIÓN tras barrer liquidez **NO tiene edge**
     (37,7% < 40% aleatorio). Con velas no se distingue stop-hunt de ruptura real.
  10. **FVG / Order Blocks (278k casos):** FVG sí supera el azar (45,4%, estable incl 2026) pero
     **muere en el muro de coste** (neto −0,02R). OB 42,4%, igual.
  11. **Operativa SMC multi-timeframe (FVG diario + BOS 1H):** parecía oro (+0,2R/op, +536R) pero
     era **100% LOOKAHEAD**; corregido = aleatorio (−0,016R/op, win 33% a 2R). Diagnóstico: ningún
     sub-segmento (largos/cortos/moneda/stop) tiene edge.
  12. **BTC como referencia (lead-lag):** BTC NO lidera a las alts (corr lag-1 ≈ 0; lag-0 +0,68 es
     beta contemporánea, no explotable). Seguir a BTC con retraso: ruina.
  13. **SMC/FVG en tradicional (EUR/USD, oro, S&P):** PEOR que cripto — por DEBAJO del azar
     (forex ~37%, oro/S&P ~30%). El bajo coste no salva porque el bruto ya es negativo.
  14. **CIERRE:** búsqueda direccional agotada con rigor en cripto y tradicional → eficiente.
     Lo único tradeable validado: PRIMAS ESTRUCTURALES (carry, arb DEX↔CEX).

---

## 6. ⏭️ Próxima decisión necesaria (decide: el dueño)

Elegir el camino con el carry como único edge robusto encontrado:
- **(A) Aceptarlo como motor de bajo riesgo** a apalancamiento prudente (1-2x → ~12-26% histórico,
  ~2-10% en regímenes calmos), y construir el bot con gestión de cola (multi-exchange, colchones).
- **(B) Seguir buscando** un edge COMPLEMENTARIO que pague en los años flacos del carry (calmos/bajistas):
  p. ej. arbitraje de funding entre exchanges (market-neutral, no requiere euforia).
- **(C) Profesionalizar el carry** en un paper-trade sobre testnet antes de cualquier dinero real.

---

## 7. ⚠️ Riesgos abiertos

- **El listón de ≥10%/año robusto NO está demostrado a apalancamiento seguro.** El carry a 1x reciente
  rinde poco; el 10%+ exige apalancar (riesgo de cola) o depender de euforias de mercado.
- **Riesgo de cola del carry no modelado:** quiebra de exchange (FTX), liquidación de la pata corta,
  pico de funding. Es el riesgo REAL y el backtest no lo ve.
- **Régimen:** el funding se ha comprimido; no asumir que el +12% histórico se repite.
- **Riesgo financiero:** es trading apalancado con dinero real (fases finales). Empezar con capital
  mínimo y solo tras validar en paper.
- **Dependencia de terceros:** APIs de exchanges (límites, cambios, caídas).

---

## 8. 🎯 Nivel de confianza del estado actual

- [ ] 🟢 Alto
- [X] 🟡 **Medio** — El laboratorio de backtest y los hallazgos (carry = único edge robusto, pero
      regime-dependiente) son sólidos y honestos. Pero NO hay producto operando y el ≥10%/año robusto
      a apalancamiento seguro sigue sin demostrarse.
- [ ] 🔴 Bajo

---

*Última actualización: 2026-06-23 (tarde) por Claude — atr_break validada, poda de 4, scalping/MEV descartado, 32 estrategias.*
*Mantiene: Claude (con validación del dueño del proyecto).*
