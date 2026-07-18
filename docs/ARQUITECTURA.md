# Arquitectura — Estado técnico del proyecto

> Documento vivo. Claude lo actualiza cuando cambia algo técnico relevante.
> Si quieres saber cómo está construido el proyecto, lee esto.

**Última actualización:** 2026-06-18 — Diseño inicial (Fase 0).
**Mantenedor:** Claude (con validación del dueño).

---

## Visión general

Bot que automatiza la estrategia de Trading Latino (Jaime Merino) sobre futuros
perpetuos de cripto. Diseño **"un solo cerebro, tres mundos"**: la lógica de la
estrategia se escribe una vez y se reutiliza idéntica en backtesting, paper trading y
real. Solo cambian las "piezas de enchufe" (de dónde vienen los datos y a dónde van las
órdenes). Así, lo que validamos en el backtest es exactamente lo que opera en real.

---

## Stack tecnológico

| Capa | Tecnología | Por qué |
|------|-----------|---------|
| Lenguaje | **Python 3.14** (en entorno aislado `.venv`) | rey de datos/finanzas. ✅ Verificado: pandas 3.0, numpy 2.4, ccxt 4.5, pyarrow 24, matplotlib 3.11 instalan y funcionan en 3.14 |
| Datos / cálculo | **pandas + numpy + pyarrow** | manejo de velas y cálculo de indicadores; parquet para guardar |
| Datos históricos | **ccxt** (descarga de velas) | acceso unificado a exchanges; histórico largo para el backtest |
| Backtesting | **motor propio event-driven** | la estrategia (multi-temporal + perpetuos + funding + SL estructural + guillotina) es muy específica; un motor propio da control total y evita errores de "mirar el futuro" |
| Exchange (paper/real) | **hyperliquid-python-sdk** (WebSocket) | el exchange elegido en la visión; datos tic a tic sin saturar la API |
| Tests | **pytest** | validar indicadores contra TradingView y la lógica del cerebro |
| Gráficas informe | **matplotlib** | curva de capital y drawdown del backtest |

> **Decisión técnica (Claude):** para el *backtest* usamos histórico largo (vía ccxt, p.
> ej. Binance) porque Hyperliquid tiene poco histórico; para *operar* usamos Hyperliquid.
> Validar estrategia ≠ operar: es estándar y aceptable.

---

## Estructura de carpetas

```
trading_latino/                 # el paquete del bot
  config/
    parameters.py               # ⭐ TODOS los parámetros (la biblia en código), etiquetados 🟦🟨🟥
  domain/
    types.py                    # tipos base: Candle, Position, Order, Signal, Side...
  indicators/                   # Fase 2 — EMA, ADX, Squeeze (LazyBear), Volume Profile (POC)
  strategy/
    brain.py                    # Fase 3 — EL CEREBRO: estado multi-temporal -> decisión (puro, sin I/O)
  risk/
    manager.py                  # Fase 3 — 5%, SL estructural, break-even NETO, guillotina, topes
  data/
    feed.py                     # interfaz "dame velas" (la implementan: histórico y Hyperliquid)
    download.py                 # Fase 1 — descargar histórico y guardarlo en parquet
  backtest/
    engine.py                   # Fase 4 — motor event-driven + modelo de costes
  execution/
    broker.py                   # interfaz "ejecuta orden" (la implementan: simulado y Hyperliquid)
  reports/
    metrics.py                  # Fase 5 — métricas en neto + curva de capital
data_store/                     # datos descargados (parquet) — NO se sube a git
tests/                          # pruebas (pytest)
requirements.txt                # dependencias
```

**Las dos "interfaces de enchufe"** (`data/feed.py` y `execution/broker.py`) son la clave
del diseño: el cerebro habla con ellas sin saber si está en backtest o en real.

---

## Flujos principales

### Backtest (Mundo A)
```
parquet histórico → Feed(histórico) → Indicadores → Cerebro → Riesgo
   → Broker(simulado: aplica comisiones+funding+slippage) → Reporte en neto
```

### Real / Paper (Mundos B/C)
```
Hyperliquid WebSocket → Feed(Hyperliquid) → Indicadores → Cerebro → Riesgo
   → Broker(Hyperliquid: órdenes reales) → registro/alertas
```
**El bloque "Indicadores → Cerebro → Riesgo" es idéntico en los tres mundos.**

---

## Decisiones técnicas

Ver `SYSTEM_VISION.md` (decisiones de negocio) y
`docs/ESTRATEGIA_TRADING_LATINO.md` (método + clasificación 🟦🟨🟥).

| # | Decisión | Tipo |
|---|----------|------|
| A1 | Diseño "un cerebro, tres mundos" (misma estrategia en backtest/paper/real) | 🟨 |
| A2 | Motor de backtest propio (no framework genérico) | 🟨 |
| A3 | Histórico largo vía ccxt/Binance para backtest; Hyperliquid para operar | 🟨 |
| A4 | Modelar comisiones + funding (cada hora) + slippage; métricas en NETO | 🟨 |
| A5 | Parámetros centralizados en `config/parameters.py`, etiquetados por origen | 🟨 |

---

## Cómo arrancar en local

```bash
# 1) crear el entorno aislado (una sola vez)
python -m venv .venv

# 2) instalar dependencias dentro del entorno
.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# (en Linux/Mac sería:  .venv/bin/python -m pip install -r requirements.txt)

# 3) comprobar que todo funciona
.venv/Scripts/python.exe -c "from trading_latino.config import CONFIG; print('alts:', len(CONFIG.altcoins))"
```
✅ Verificado el 2026-06-18 en Windows con Python 3.14.

---

## Variables de entorno necesarias

```bash
# Para operar (paper/real) — NUNCA en este archivo, van en .env
HYPERLIQUID_API_WALLET=descripcion   # cartera/clave para Hyperliquid (fase 6+)
HYPERLIQUID_TESTNET=true             # true en paper, false en real
```


---

## Panel operativo en vivo (actualizado 2026-07-18)

| Pieza | Comando | Qué hace |
|---|---|---|
| Semáforo | `python -m trading_latino.live.semaforo` | 4 luces (ciclo, carry, dirección 7d, kill-switch 14d) + 2 diales contextuales (persistencia de funding; fase con convergencia n/3 — sin regla de disparo, auditoría r6) |
| Monitor motor 3 | `python -m trading_latino.live.monitor_carry` | Cesta carry candidata (solo monedas que pagan >2% APR), dial de persistencia y triggers de desmontaje (funding<0 3d; de-peg >1%; máx 50%/exchange; colateral solo stables). Informativo, NO opera |
| Arena 24/7 | colector nube (GitHub Actions, rama `arena-data`) + tarea local `TradingArenaPaper` | Paper-trading Hyperliquid con costes reales; registra 5 políticas de salida por op (A/B de salidas gratis) |
| Barridos | `barrido_tf <tfs>` / `barrido_5m` | Matriz 13 familias × temporalidad, neto de costes (cR = COSTE/(D/entry) + slip) |

Advertencia de datos: las ops "vivas" de una estrategia recién desplegada incluyen replay
histórico con metadata contextual (funding/OI/FNG) estampada al registro — excluir pre-despliegue
en análisis contextual (ver memoria `arena-backfill-contaminacion`).
