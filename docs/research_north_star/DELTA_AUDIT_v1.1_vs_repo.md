# DELTA AUDIT — North Star v1.1 vs repositorio real (2026-07-19)

Regla permanente: **`NO_REBUILD_IF_EQUIVALENT_EXISTS`**. Flujo: NEED → AUDIT EXISTING → REUSE →
EXTEND MINIMALLY → BUILD NEW ONLY IF NECESSARY. No sobrearquitectura. Este proyecto es de trading
cuantitativo, no de arquitectura de software por elegancia.

Corrección clave (dueño 2026-07-19): NO marcar "DONE" una capacidad solo porque exista EMBEBIDA en
una estrategia concreta. Capacidad económica ≠ componente arquitectónico genérico reutilizable.

| Componente del North Star | Estado | Nota (qué existe / qué falta / si se necesita) |
|---|---|---|
| Portfolio simulator (swing) | **EXISTS** | `portfolio_sim.py`: Test 0, causal, order-independent, 4 capas de tope |
| Compounding causal | **EXISTS** | realizado a la salida; sizing sobre equity de entrada |
| Order-independent batching | **PARTIAL** | desempate determinista por contenido ✓; pro-rata batch real = NOT_NEEDED_YET |
| Cost model fees+slippage | **EXISTS** | cR=COSTE/(D/entry) + slip; slip bps/dist medido |
| **Funding direccional** | **MISSING** | ← Entregable 2 de esta tanda |
| Data lineage / manifests | **EXISTS (manual)** | freezes + manifest 2018 con hash; proceso manual, no automático |
| **Holdout inventory global** | **MISSING** | ← Entregable 4 |
| Tribunal de validación (11 leyes) | **EXISTS** | documentado en research_north_star + memoria |
| Experiment ledger | **PARTIAL** | PROJECT_STATUS §5 es un ledger MANUAL cronológico; registro estructurado = gap |
| Strategy registry | **PARTIAL** | freezes (OB_ASIA, PORTFOLIO_v1) existen; registro unificado con estado = gap |
| **RUN_APPROVED gate** | **MISSING** | ← Entregable 5 (disciplina existe, mecanismo no) |
| Arena 24/7 + contexto | **EXISTS** | 17k ops, OI/funding/liquidez en vivo |
| Semáforo / regime read | **PARTIAL** | 4 luces + 2 diales; NO es un "regime engine" que enrute estrategias |
| Generic `TrendState` feature layer | **NOT_NEEDED_YET** | tenemos CAPACIDAD (núcleo/ichimoku) embebida; capa genérica solo si una hipótesis la pide |
| `StructureState` primitives (sweep/BOS/FVG causales) | **MISSING** | terreno nuevo real (AdriG) — ← Entregable 6 (S3-A spec) |
| `CycleState` (impulse/correction) | **MISSING** | Plan BTC; posible solape con trend, sin construir |
| `PositioningState` (OI/funding/liq sistemáticos) | **MISSING (datos)** | Mr GON; frontera más nueva, bloqueada por datos — ← Entregable 7 |
| Event-driven micro execution engine | **NOT_NEEDED_YET** | prerequisito de scalping 1m/5m; futuro, no ahora |
| 50-feature library / 8 motores / router / L2 | **NOT_NEEDED_YET** | queda en North Star, NO en sprint |

## Qué se DECIDE explícitamente NO construir ahora
Feature library genérica completa, `TrendState`/`CycleState` genéricos, los 8 motores S1-S8, router de
régimen, motor event-driven de microestructura, dashboard, L2. Todo eso permanece como mapa futuro.

## Gaps reales a rellenar en esta tanda (mínimos)
1. Funding direccional (MISSING) → cerrar. 2. Holdout inventory (MISSING) → construir. 3. Ledger/
registry/RUN_APPROVED (PARTIAL/MISSING) → mínimo, extendiendo lo que ya hay, sin plataforma. 4. S3-A
spec (StructureState primitives MISSING) → especificar, NO ejecutar. 5. OI memo (PositioningState
data MISSING) → decidir viabilidad.
