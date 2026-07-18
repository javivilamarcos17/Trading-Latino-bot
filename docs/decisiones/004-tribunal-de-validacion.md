# ADR-004 — Tribunal de 6 leyes para validar cualquier hallazgo

**Fecha:** 2026-07-18 (consolidada; leyes acumuladas en rondas 1-6 de auditoría) · **Estado:** cerrada

## Contexto
Seis rondas de auditoría adversarial cazaron los mismos errores una y otra vez: overfit de celda
única, significancia inflada por ops correlacionadas, dependencia de 2023, lookahead en filtros,
episodios sueltos narrados como leyes, y números irreproducibles.

## Decisión
Ningún hallazgo entra al sistema sin pasar las 6 leyes:
1. FAMILIA de configuraciones (no celda única). 2. Bootstrap con p<0.10. 3. n≥100 (o etiqueta
honesta). 4. Bootstrap por EPISODIO cuando las ops comparten días. 5. Test sin-2023. 6. Chequeo de
causalidad en filtros (ventanas ± = lookahead). Además: todo número de cabecera nace de un script
GUARDADO, y las narrativas sobre <5 episodios son decoración, no hallazgo.

## Alternativas consideradas
- Validar con backtest simple + criterio propio — descartada: así nacieron todos los falsos
  positivos que el auditor tumbó.

## Consecuencias
- (+) Tasa de falsos positivos drásticamente reducida; el cementerio de descartes es conocimiento.
- (−) Ritmo de "hallazgos" mucho menor y menos vistoso. Es el precio de que lo que quede sea real.
