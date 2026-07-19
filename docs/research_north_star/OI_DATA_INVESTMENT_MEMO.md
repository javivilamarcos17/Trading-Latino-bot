# OI DATA INVESTMENT MEMO — desbloquear MICRO-01B (Price × OI State)

**Fecha:** 2026-07-19 · **Objetivo:** decidir si podemos acceder razonablemente a Open Interest
SISTEMÁTICO multi-año (BTC/ETH/SOL, 5m o mejor) para el primer estudio de la frontera de positioning.
**Regla:** no comprar por "suena interesante". Se compra solo lo que desbloquea un experimento
definido (MICRO-01B) y solo si pasa el investment gate. NO L2 todavía.

## Qué necesita MICRO-01B (mínimo viable)
- OI por marca temporal para BTC/ETH/SOL, idealmente ≤5m, 2021-2026 (para cubrir varios regímenes).
- Secundario (fases posteriores, NO ahora): funding (ya lo tenemos vía Binance), liquidaciones, CVD spot/perp.
- Pregunta única de MICRO-01B: ¿OI añade información incremental sobre price-only? (4 cuadrantes
  price↑/↓ × OI↑/↓, forward return/MFE/MAE/decay). Si NO → paramos la escalera. No hace falta L2.

## Opciones de fuente (verificar cobertura/coste antes de contratar — no asumir)
| Fuente | OI histórico | Granularidad | Coste | Notas / caveats |
|---|---|---|---|---|
| **Binance API pública** (`openInterestHist`) | ~30 días (limitación conocida) | 5m/15m/1h/4h | gratis | Insuficiente para multi-año. Sirve para prototipo forward, no para el estudio histórico. |
| **Binance public data (data.binance.vision)** | verificar si publica OI en los dumps (klines sí; metrics/OI = COMPROBAR) | diaria/horaria | gratis | ⚠️ acción: auditar si los dumps incluyen `metrics`/OI histórico. Si sí → gratis y suficiente. PRIMERA opción a verificar. |
| **Coin Metrics** | OI a nivel de mercado, histórico desde ~2020 (community limitado; pro completo) | market-level | pago (pedir muestra) | Permite OI por venue + agregado (distinguir deleveraging real vs migración entre venues). Pedir rango exacto y precio. |
| **Kaiko** | derivados (OI, funding) desde ~2020 | por exchange | pago | Pedir data dictionary: cobertura BTC/ETH/SOL, desde qué fecha, contratos inversos, migraciones. |
| **CoinGlass API** | OI + liquidaciones OHLC histórico por par/agregado | OHLC | freemium/pago | Útil como cross-check, NO como única verdad (calidad entre venues dudosa — arXiv 2310.14973). |

## Riesgo de calidad (documentado)
Estudio académico (arXiv 2310.14973) encontró inconsistencias graves en cómo algunos venues
reportan OI (cifras implausibles). → NO tratar "OI cayó 15% = deleveraging real" sin normalizar
definiciones. Cada serie conserva: venue, contract_type, quote, methodology, timestamp granularity.

## Investment gate (comprar solo si TODO se cumple)
1. La fuente cubre BTC/ETH/SOL con granularidad ≤5m y desde ≥2021.
2. Coste razonable para el valor esperado (MICRO-01B es UN experimento; no comprar "por si acaso").
3. Calidad auditada (sin cifras implausibles; metodología documentada).
4. Solo entonces: adquirir OI (+ funding donde falte). NO liquidaciones/CVD/L2 hasta que OI demuestre
   información incremental.

## Recomendación / secuencia
1. **GRATIS PRIMERO:** auditar si `data.binance.vision` publica OI/metrics histórico. Si sí → MICRO-01B
   sin gastar un euro. (Acción de verificación, no de compra.)
2. Si no: pedir MUESTRA + precio a Coin Metrics y Kaiko para BTC/ETH/SOL OI 2021-26 ≤5m.
3. Decidir con el investment gate. Prioridad de MICRO-01B alta EN CUANTO el dato sea viable — puede
   competir con (o adelantar a) S1/S4, porque introduce información NUEVA que el cementerio OHLC
   nunca tuvo.
