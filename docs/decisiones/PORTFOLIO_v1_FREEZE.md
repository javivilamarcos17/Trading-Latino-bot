# PORTFOLIO_v1_FREEZE — Congelación de la cartera para forward test

**Fecha:** 2026-07-19 · **Commit:** `6400d9a` · **Estado:** CONGELADO

> Motivo (auditoría IA externa): el resultado núcleo+turtle+ichimoku (Calmar 0.65→1.41-1.57) NO es
> un OOS nuevo — núcleo, turtle e ichimoku ya se investigaron sobre esos datos antes de preguntar
> "¿qué pasa si los combino?". Demuestra COMPATIBILIDAD histórica y aparente complementariedad, NO
> validación independiente. Por eso se congela: desde HOY (2026-07-19), la curva forward de esta
> cartera exacta es la primera evidencia verdaderamente nueva.

## Composición congelada
- **Motor 1 — Núcleo 1D:** trend_rider + atr_break_trend, target 4R, riesgo 0.25%/op.
- **Motor 2 — Turtle ciclo:** ruptura 55d en ciclo profundo, target 3R, largos, riesgo 0.5%/op.
- **Motor 3 — Ichimoku 4h:** tenkan/kijun 12/30 + nube, stop swing-10, 3R, SOLO ETH/SOL, 0.25%/op.
- **Motor de riesgo:** tope global 5% de presupuesto asignado; contabilidad CAUSAL (PnL a la salida);
  desempate de simultaneidad determinista por contenido. Motor: `research/portfolio_sim.py` @6400d9a.

## Métricas de referencia (histórico 2021-26, contabilidad causal — NO son forward)
- Núcleo+turtle: +36.7% / DD -10.5% (realizada) / Calmar 0.68.
- +ichimoku: +63-65% / DD -7.2/-7.8% / Calmar 1.41-1.57 (robusto a política de simultaneidad).
- ⚠️ PENDIENTE antes de llamar a esto "neto final": FUNDING histórico direccional NO incluido aún.
  El PnL es neto de fees/slippage pero PRE-funding. No afirmar "rentabilidad neta final" hasta medirlo.

## Qué es evidencia nueva
Solo la curva de esta cartera desde 2026-07-19 en adelante. Todo lo anterior es desarrollo/compatibilidad.

## Reglas
- No se toca la composición ni el risk cap sin abrir una versión nueva (PORTFOLIO_v2).
- Prohibido "seguir mejorando el simulador" (overfitting del portfolio engine). Solo se añade FUNDING
  (coste real que falta), y después se deja respirar. Factor cap: APARCADO (mejora marginal + grados
  de libertad; el global 5% ya autorregula vía escasez de capital).
