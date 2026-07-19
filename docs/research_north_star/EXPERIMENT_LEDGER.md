# EXPERIMENT LEDGER — registro de hipótesis (Ley 7: cuenta TODOS los grados de libertad)

Toda hipótesis testeada queda aquí, viva o muerta. Los muertos permanecen (denominador estadístico
para DSR/PBO futuro). Cada experimento termina en un VEREDICTO explícito, nunca en "seguir estudiando".

| id | hipótesis | estado | datos | estimando primario | resultado | veredicto | follow-up permitido |
|---|---|---|---|---|---|---|---|
| HYP-OBASIA-v1 | OB/Asia = edge condicionado a bear | **FALSIFIED** | 2018 BTC/ETH virgen | E[R\|BEAR] | −0.238R, p≤0=1.0, ambos activos neg | KILL | ninguno (2018 quemado) |
| HYP-S3A-001 | sweep→acceptance/rejection añade info | **KILL** | BTC/ETH/SOL 15m 2021-26 (dev) | ΔInfo=E[acc]−E[rej] | −0.021 ATR, p=0.51, heterog. incoherente | KILL | ninguno; observación "rej>acc" logged sin acción |
| HYP-MICRO-01B | ΔOI añade info sobre price-only | **PREPARING** | OI 5min gratis 2021/22-26 (descargando) | info incremental price+OI vs price | — | pendiente RUN | data-ready en curso |

## Conclusiones PERMITIDAS vs NO permitidas (anti-sobreinterpretación)
- **S3-A**: permitido → "con la definición causal preregistrada (Donchian-20, ε=0.10ATR, 15m,
  2021-26), acceptance/rejection no aporta información incremental material sobre sweep alone".
  NO permitido → "los sweeps no sirven / SMC refutado / liquidity concepts muertos / AdriG refutado".
- **OB/Asia**: murió la tesis "OB/Asia = motor de oso generalizable", NO "los order blocks no funcionan".

## Observaciones logged (reservoir, SIN autorización de follow-up)
- S3-A: "rejection continúa algo más que acceptance" (contraintuitivo) — DENTRO DEL RUIDO (p=0.51),
  no preregistrado como tesis. Guardado. NO se abre S3-A2 para perseguirlo.

## Throughput científico (la métrica real de esta fase)
Hipótesis atacadas: 2 confirmatorias (OB/Asia, S3-A) → 2 muertas. 0 holdouts vírgenes consumidos en
S3-A. 0 estrategias construidas sobre features sin información. KILL FAST · LEARN · MOVE ON.

## Incidentes de integridad de datos (protección permanente)
- **2026-07-19 — corrupción de timestamps OI**: `create_time` (string "2024-01-01 00:00:00")
  parseado por pandas 2.x a resolución de SEGUNDOS → fechas 1970-01-19 tras la conversión a ms.
  Root cause: mismatch de resolución/unidad datetime. Fix: conversión robusta
  `datetime64[ms]`. Datos corruptos BORRADOS y regenerados DESDE SOURCE (no parche post-hoc de
  timestamps). **Datos experimentales expuestos: NO · MICRO-01B status: NOT RUN** → la virginidad
  experimental de MICRO-01B NO se vio afectada. Protección permanente añadida al DATA GATE:
  5 invariantes temporales (range sanity, monotonicidad, duplicados, cadencia 5m, UTC/boundary,
  todos FAIL duro) + ingestion unit test reutilizable (1704067200000 ↔ 2024-01-01 00:00:00 UTC).
  Política confirmada: ante corrupción estructural de ingesta → regenerar desde source, nunca parchear.
