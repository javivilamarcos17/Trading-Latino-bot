# MICRO-01B — PRE-REGISTRO (Positioning Information Test: ¿ΔOI añade info sobre price-only?)

**Fecha:** 2026-07-19 · **hypothesis_id:** HYP-MICRO-01B · **Estado:** PREREGISTERED (NO ejecutar sin RUN_APPROVED)
**Origen:** Mr GON / positioning. Primera incursión en información que el PRECIO por sí solo no contiene.

## Naturaleza
INFORMATION TEST, no estrategia. Pregunta binaria previa ya respondida: SÍ hay OI sistemático
multi-año gratis (data.binance.vision, 5min, BTC 2021+, ETH/SOL 2022+). Ver DATA MANIFEST adjunto.

## Estimando PRIMARIO (el correcto, no "qué cuadrante gana")
**¿Añadir ΔOI mejora la diferenciación de la distribución futura respecto a usar SOLO el retorno de
precio?** Operacionalización sin binarizar ingenuamente:
1. Lectura CONTINUA primero: distribución conjunta (price_return_reciente, ΔOI_reciente) → forward_ret.
2. Dentro de cada BIN de price_return (quintiles del movimiento reciente, definidos ex-ante), medir
   la diferencia de forward_ret entre ΔOI alto y ΔOI bajo (quintiles de ΔOI dentro del bin).
3. PRIMARIO = ¿esa diferencia intra-bin (el efecto de OI CONTROLANDO por precio) es materialmente
   distinta de cero y coherente entre bins? Si ≈0 → OI NO añade información sobre price-only → KILL.
Los 4 cuadrantes (price↑/↓ × OI↑/↓) son solo INTERPRETACIÓN simple al final, no el test.

## Definiciones causales (congeladas; available_at = cierre de vela)
- price_return_reciente: retorno de las últimas M velas hasta el cierre de t (M pre-registrado por TF).
- ΔOI_reciente: cambio de sum_open_interest en las mismas M velas hasta t (dato disponible en t).
- forward_ret: retorno normalizado por ATR en las próximas K velas desde el cierre de t.
- NO optimizar thresholds de OI. Quintiles/bins fijos. ε y M/K fijos por TF.

## Outcomes
forward_ret (primario), MFE, MAE, holding-time decay del edge informacional. MFE/MAE = outcomes, nunca features.

## Temporalidades (familia pequeña, buscar coherencia, no mejor celda)
5m, 15m, 1H. Se busca una REGIÓN temporal coherente (mismo signo en TFs adyacentes).

## Datos e inferencia
DEVELOPMENT: BTC/ETH/SOL, OI 5min + precio, desde 2021/2022 a 2026 (VISTO). Alinear OI (5min) con
precio por timestamp. Inferencia: **market-time block bootstrap** (BTC/ETH/SOL del mismo bloque
temporal juntos). NO tratar millones de velas como observaciones independientes; buscar si el efecto
existe a través de semanas/meses/regímenes, no un p diminuto por N enorme.

## Research budget (cerrado)
- 1 definición primaria de price_return y ΔOI (misma ventana M). Máximo 2 alternativas exploratorias
  de M (declaradas exploratorias). Bins fijos (quintiles). Máximo ~3 TFs × 1 definición = universo registrado.

## Criterios de MUERTE
1. El efecto intra-bin de OI ≈ 0 (OI no añade sobre price-only).
2. Incoherente entre bins / entre monedas / entre subperiodos.
3. Solo aparece en un TF aislado sin región coherente.
Si muere → CEMENTERIO. Si SÍ hay información → FREEZE + decidir evidencia externa (NO se convierte en
estrategia automáticamente; INFORMATION EDGE ≠ TRADABLE EDGE ≠ PORTFOLIO EDGE).

## Calidad de datos (recordatorio)
OI reportado puede tener inconsistencias entre venues (arXiv 2310.14973). Aquí una sola fuente
(Binance perp USDT), coherente internamente. Conserva venue/contract/quote/granularity en el manifest.
