# ADR-002 — Tope de riesgo abierto agregado del 5%

**Fecha:** 2026-07-18 · **Estado:** cerrada

## Contexto
La conciliación del portfolio demostró que sin tope, la simulación apilaba 21+ posiciones
simultáneas (25% del capital en riesgo) y el resultado (+114% en 2023) era inoperable e inflado.

## Decisión
Tope duro de **5% de riesgo abierto agregado** en todo momento (0.25%/op el núcleo, 0.5% armas de
ciclo). Señal que llega con el tope lleno = se salta. Números oficiales bajo esta regla:
+44.5%/5.5a, DD −12.4% (script: concilia_portfolio.py).

## Alternativas consideradas
- Sin tope (maximizar señales) — descartada: riesgo simultáneo inasumible, DD −19.6%.
- Tope por estrategia solamente — descartada: no protege del apilamiento entre estrategias
  correlacionadas (todas disparan en las mismas rachas).

## Consecuencias
- (+) DD contenida (−12% vs −20%), riesgo conocido y escalable linealmente con el presupuesto.
- (−) Se renuncia a ~40% del resultado bruto de los mejores episodios (240 señales saltadas).
