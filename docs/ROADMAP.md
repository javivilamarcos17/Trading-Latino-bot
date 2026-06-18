# 🗺️ ROADMAP — Plan de construcción del bot

> Cómo vamos a construir el bot de Trading Latino, paso a paso, **orientado a poder
> hacer un backtesting honesto lo antes posible**. Cada fase tiene un entregable claro
> y comprobable. El dueño valida al final de cada fase.

**Principio rector:** fidelidad al método de Merino (🟦 núcleo). Ver
[ESTRATEGIA_TRADING_LATINO.md](ESTRATEGIA_TRADING_LATINO.md).
**Métrica que manda:** rentabilidad **NETA** después de comisiones, funding y slippage.

**Leyenda:** ✅ Completado · 🔄 En progreso · ⬜ Pendiente

---

## La idea central: un solo cerebro, tres mundos

Escribimos la lógica de la estrategia **una sola vez** ("el cerebro") y la separamos del
"mundo" donde vive. El cerebro solo pide *"dame la siguiente vela"* y dice *"abre/cierra
esto"*. Le enchufamos tres mundos:

| Mundo | Datos | Dinero | Para qué |
|-------|-------|--------|----------|
| **A — Backtesting** | histórico (años) | ficticio | probar la estrategia en el pasado |
| **B — Paper / Testnet** | real, en directo | ficticio | verla operar en vivo sin arriesgar |
| **C — Real** | real, en directo | real | producción |

Esto garantiza que **el código que probamos en el pasado es el mismo que opera en real.**

---

## Fases

| Fase | Descripción | Entregable | Estado |
|------|-------------|-----------|--------|
| **0** | **Diseño y cimientos** | Proyecto montado, parámetros escritos, todo documentado | 🔄 En progreso |
| **1** | **Capa de datos** | Comando que baja el histórico (BTC+20 alts, 1H, años) y lo deja listo | ⬜ |
| **2** | **Indicadores** | EMA/ADX/Squeeze/POC validados contra TradingView, con tests | ⬜ |
| **3** | **Cerebro + riesgo** | La estrategia pura + gestión de riesgo (5%, SL, BE neto, guillotina) | ⬜ |
| **4** | **Motor de backtest** | Motor event-driven con modelo de costes (comisiones+funding+slippage) | ⬜ |
| **5** | **Primer backtest + informe** | Respuesta honesta a "¿esto es rentable?" en neto; calibrar topes | ⬜ |
| **6** | **Paper trading (Testnet)** | El mismo cerebro en vivo, dinero ficticio, semanas | ⬜ |
| **7** | **Real** | Capital muy pequeño, VPS Linux 24/7 | ⬜ |

### Detalle de cada fase

**Fase 0 — Diseño y cimientos** 🔄
Cerrar parámetros (la biblia → `trading_latino/config/parameters.py`), montar estructura
del proyecto, entorno (venv) y dependencias.

**Fase 1 — Capa de datos**
Descargar velas de **1H** de varios años para BTC + 20 alts y guardarlas (formato parquet).
Resamplear a 4H/1D/1W **sin mirar el futuro** (alineación temporal correcta).

**Fase 2 — Indicadores**
Implementar EMA 10/55, ADX(23), Squeeze Momentum (LazyBear) y Perfil de Volumen (POC) con
las **fórmulas exactas** y validarlos contra TradingView en fechas concretas.

**Fase 3 — El cerebro + el riesgo**
La estrategia pura (estado multi-temporal → decisión) sin I/O. Módulo de riesgo con las
leyes 🟦 (5% por trade, SL estructural, break-even neto, guillotina del tiempo).

**Fase 4 — Motor de backtest**
Motor event-driven (vela a vela, sin lookahead) + **modelo de costes** (comisiones, funding
cada hora, slippage, apalancamiento). Registra cada operación.

**Fase 5 — Primer backtest + informe** *(por módulos separados, decisión del dueño)*
Probamos los dos motores **por separado** y siempre **en neto** (con comisiones+funding+slippage):
- **5a · BTC solo Longs** — cuando el diario de BTC está alcista. Es el primero: datos más
  largos (BTC tiene años de histórico) y la lógica más simple. A Bitcoin nunca se le hace short.
- **5b · Altcoins solo Shorts** — solo en momentos bajistas de BTC, sobre alts débiles. Menos
  operaciones y periodo más corto (las alts son recientes).
- **5c · Combinado** — una vez validados los dos por su cuenta.

Métricas en neto: curva de capital, drawdown, win rate, profit factor, rachas de pérdidas.
**Calibrar los topes de pérdida con estos datos** (no a ojo). Saber qué módulo aporta la ventaja.

**Fase 6 — Paper trading** · **Fase 7 — Real** (detalle cuando lleguemos).

---

## Lo que NO vamos a hacer en la v1 (y por qué)

- **Wyckoff completo, ondas de Elliott, RSI/MACD, Fibonacci, mapas de liquidaciones** —
  demasiado visuales/subjetivos para automatizar fiable; ensuciarían el backtest. (Posible v2.)
- **Dominancia (USDT.D/BTC.D/TOTAL3) y Área de Valor (VAH/VAL)** — mejoras que Merino sí
  usa; las dejamos para v2 una vez validado el núcleo.
- **Optimizaciones de quant que se desvíen del método** (riesgo fijo, etc.) salvo como
  experimento 🟥 aprobado tras el backtest.

---

## Dónde estamos

Fase 0 en curso. El hito que de verdad importa es la **Fase 5** (backtest honesto). Todo
lo anterior existe para llegar ahí con rigor.
