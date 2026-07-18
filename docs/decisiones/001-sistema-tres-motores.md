# ADR-001 — Sistema de 3 motores por régimen

**Fecha:** 2026-07-18 · **Estado:** cerrada

## Contexto
La búsqueda exhaustiva (~30 familias juzgadas) demostró que ninguna estrategia única funciona en
todos los climas: lo que gana en oso muere en toro y viceversa. El intradía es inoperable a costes
reales en todas las temporalidades probadas (1m-30min).

## Decisión
El sistema final son TRES motores complementarios por régimen:
1. **Núcleo 1D** (trend_rider + atr_break_trend, todo-clima) — el motor de base.
2. **Armas de ciclo** (planbtc, turtle_ciclo) — solo disparan en oso maduro (>200d de ATH o dd>50%).
3. **Carry de funding** (cesta delta-neutral) — paga en toro/lateral, duerme en oso (régimen OPUESTO al 2).
El semáforo (4 luces + diales contextuales) decide qué motor está habilitado cada día.

## Alternativas consideradas
- Una sola estrategia robusta — descartada: no existe fuera de muestra con nuestros datos.
- Muchas estrategias siempre encendidas — descartada: es concentración disfrazada (aviso 2026-06)
  y muere al girar el régimen.

## Consecuencias
- (+) Cada motor tiene su clima; el sistema nunca depende de un solo régimen.
- (−) Complejidad de orquestación (semáforo) y periodos con motores dormidos (paciencia obligada).
