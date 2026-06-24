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
- [X] 🛠️ **Prototipo de investigación** — El laboratorio de backtest corre end-to-end y es honesto
      (sin lookahead, con costes). NO hay bot operando todavía.
- [ ] 🚀 **MVP**
- [ ] 🏭 **Producción**

**Estado: 🛠️ Prototipo de investigación.** Tenemos un **laboratorio de backtest serio** (alineado por
hora de cierre, sin mirar el futuro, con comisiones/funding/slippage, y con **2026 como año de prueba
ciega**). Con él hemos hecho una **búsqueda exhaustiva** de estrategias. **Conclusión honesta:**

- **Casi todo lo direccional/técnico/ML/scalping FALLA fuera de muestra** (overfitting): se ve bonito
  en el pasado y se cae en 2026. Esto incluye la estrategia mecánica de Merino, divergencias RSI,
  Squeeze, etc. probadas en muchas temporalidades.
- **El ÚNICO edge robusto que hemos encontrado es el CARRY de funding** (delta-neutral: cobrar el
  "alquiler" del funding con el precio cubierto, sin apostar dirección). Es real y muy estable.
- **PERO el carry depende del régimen y se ha comprimido:** cesta diversificada de 6-15 monedas,
  NETO de costes, a 1x → **+11-12%/año de media… pero inflado por 2021 (+45%)**. Quitando 2021,
  los años recientes (2025-2026) rinden **~+1%/año a 1x**. Drawdown del flujo de funding ~−1,6%.
- ⚠️ **Ese drawdown bajo es engañoso:** solo mide la volatilidad del funding. **NO** incluye el
  riesgo de COLA real (quiebra de exchange tipo FTX, liquidación de la pata corta en un flash-crash,
  pico de funding). Apalancar el carry para llegar al 10%+/año mete ese riesgo de cola en juego.

---

## 2. ✅ Qué funciona HOY

> Solo lo comprobado de verdad.

- La **documentación** (visión, biblia de Merino, roadmap, arquitectura) y el **esqueleto** del proyecto.
- **Descarga de datos** (Binance perp: BTC y altcoins, 1h/4h/1d/1w) verificada sin huecos/duplicados.
- **Motor de backtest event-driven** con no-lookahead verificado, costes reales (comisiones, funding,
  slippage) y hold-out de 2026 separado.
- **Laboratorio de research** (`trading_latino/research/*.py`): decenas de experimentos reproducibles
  (técnico, ML, carry, on-chain, sentimiento, momentum transversal, macro, Wyckoff, scalping).
- **Análisis del carry profesional** (`research/carry_pro.py`): cesta diversificada, regla
  anti-funding-negativo, costes explícitos, barrido de apalancamiento, estrés y desglose por año.
- **Lectura EN VIVO de Hyperliquid (solo lectura, sin órdenes, sin dinero):**
  - `live/mapa_liquidez.py`: mapa de liquidez en tiempo real (pools de stops + muros del order-book
    + OI + funding). **Verificado contra la API pública en vivo.**
  - `live/sniper.py` y `live/agente_smc.py`: detectores + paper-trading de SMC/barridos.
  - **`live/arena.py`: ARENA en vivo — 32 estrategias × BTC/ETH/SOL × varias TF (1m→4h) en PAPEL.**
    Incluye familia OB depurada, FVG+OB, RSI/divergencias, Merino y `merinox`, `atr_break` (Keltner
    adaptativo, validada), `donchian`, smart-money+price-action (`adrig`), multi-temporalidad real (`mtf`),
    OB reforzado (`ob_plus`),
    filtros de sesión Asia, sub-sesión (aperturas reales de bolsa) y estrategias ICT de ventana de
    mercado (`silver_bullet`, `judas_swing_ob`, `ny_london_sweep`). Cada operación registra **contexto
    rico** (funding, OI, ΔOI, Fear&Greed, régimen/ADX, sesión/sub-sesión, premium/discount, liquidez,
    volumen, dirección sesión anterior) y mide **5 políticas de salida** sobre el recorrido real de 1m.
    Registro CONTINUO de contexto (`_ctx_<coin>.jsonl`). **Funcionando — 1.737 ops cerradas al 2026-06-23.**
  - ⚠️ **AVISO CRÍTICO (anti-autoengaño):** las 1.737 ops son de **UN SOLO RÉGIMEN** (1.736 de 1.737 con
    Fear&Greed <30 = miedo; mercado bajista: cortos +0.42R vs largos −0.06R; Asia +0.75R vs NY −0.48R).
    Las "ganadoras" (familia OB-Asia) son **la misma apuesta medida muchas veces**: *corto + OB + Asia +
    bajista*. NO es diversificación, es concentración disfrazada. Cuando el régimen gire (euforia/alcista)
    podrían caer todas a la vez. **Varias estrategias nuevas se diseñaron VIENDO estos datos** (sesgo de
    diseño) → su buen resultado es eco, no predicción. **Metodología correcta:** los datos EN VIVO son la
    verdad (van hacia adelante, sin sesgo); los **50 días de Binance** (`research/backtest_ganadoras.py`)
    sirven para VALIDAR fuera de muestra cada conclusión antes de fiarse.
  - **Recolección automática EN LA NUBE (GitHub Actions, patrón bucle-en-job, cada ~3 min, 24/7
    auto-encadenado) — VERIFICADA.** Ya NO depende del portátil. Datos en la rama `arena-data`.
    Herramientas de análisis read-only: `_inventario.py`, `_analisis.py`, `_mtf.py`, `board.py`, `salidas.py`.

---

## 3. ❌ Qué NO funciona / NO existe todavía

- **No hay bot operando** — ni en papel (testnet) ni en real. Solo backtest/research.
- **El riesgo de cola del carry NO está modelado** (contraparte/exchange, liquidación, pico funding).
- **No hay gestión de riesgo en vivo** (colchones de liquidación, reparto multi-exchange, monitor de funding).
- **No hemos demostrado ≥10%/año robusto a apalancamiento seguro.** El carry a 1x reciente está por
  debajo de ese listón; llegar exige 2-3x (con su riesgo de cola) o esperar regímenes de euforia.
- Conexión a exchange en vivo, paper trading y operativa real (fases finales).

---

## 4. 🧪 Cómo probarlo

```bash
# (1) que el esqueleto y la configuración cargan:
.venv/Scripts/python.exe -c "from trading_latino.config import CONFIG; print('Altcoins:', len(CONFIG.altcoins))"

# (2) el análisis del carry profesional (cesta diversificada, neto, estrés, por año):
.venv/Scripts/python.exe -m trading_latino.research.carry_pro

# (3) auditoría de la estrategia "estrella" v2 (atribución, lookahead, asignación):
.venv/Scripts/python.exe -m trading_latino.research.audit_v2

# (4) MAPA DE LIQUIDEZ EN VIVO de Hyperliquid (solo lectura):
.venv/Scripts/python.exe -m trading_latino.live.mapa_liquidez BTC ETH

# (5) PAPER-SNIPER en vivo (ejecutar cada ~15 min para acumular track record):
.venv/Scripts/python.exe -m trading_latino.live.sniper BTC
```

---

## 5. 🔚 Última decisión / hallazgo

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
