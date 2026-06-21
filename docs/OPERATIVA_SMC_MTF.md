# OPERATIVA SMC MULTI-TIMEFRAME — la lógica antes de construir

> Consolidación de TODO lo que la investigación ha validado, en una sola operativa coherente.
> Esto es el plan lógico. Luego se implementa y se prueba (sin lookahead, neto de costes, con 2026
> como prueba ciega). Verde solo si es rentable Y aguanta 2026.

---

## 1. Principio rector (lo que demostró la investigación)

- **Predecir la dirección es casi siempre eficiente** (intradía = aleatorio puro). No hay bola de cristal.
- **El único edge direccional ROBUSTO y estable (incluido 2026) es la reacción en zonas de liquidez
  tipo FVG** (45% de reversión a 1,5R, estable todos los años, 121k muestras). Está **justo en el muro
  de coste** → para hacerlo rentable hay que: (a) **entrar con orden LÍMITE (maker)**, mucho más barata,
  y (b) **apilar CONFLUENCIA** para subir el acierto.
- **La confluencia que potencia el edge:** tendencia del marco mayor + zona de liquidez del marco mayor
  + confirmación de estructura (CHoCH/BOS) del marco menor. El baseline de estructura ya da +0,10R/op
  neto, pero flojea en mercados laterales/bajistas (es trend-following). La combinación busca lo mejor
  de ambos: la **estabilidad** del FVG + la **R grande** de la continuación de tendencia.

---

## 2. Entender las TEMPORALIDADES (cada marco tiene UN trabajo)

| Marco | Su trabajo | Qué miramos |
|-------|-----------|-------------|
| **Semanal / Diario (HTF)** | **SESGO + ZONA** | Tendencia (solo operamos a favor) y DÓNDE está la liquidez: el FVG/área del marco mayor donde esperamos al precio. |
| **4H (intermedio)** | **ESTRUCTURA** | El retroceso (pullback) hacia la zona y el primer cambio de carácter. |
| **1H / 15m (LTF)** | **GATILLO** | La confirmación fina (CHoCH/BOS) y la entrada con límite; el stop pegado a la estructura menor (riesgo pequeño). |

**Regla de oro:** la ZONA la manda el marco mayor; el TIMING, el menor. Nunca al revés.
Esto es lo que permite stop ajustado (entrada en LTF) con objetivo grande (recorrido del HTF) → R alto.

---

## 3. El SETUP — largo (espejo exacto para corto)

1. **Sesgo HTF (diario) alcista:** precio > EMA diaria (o secuencia de máximos/mínimos crecientes).
2. **Zona de liquidez HTF:** el impulso alcista dejó un **FVG diario** (hueco de descuento sin rellenar).
3. **Pullback:** el precio retrocede y entra a retestear ese FVG diario.
4. **Confirmación LTF (1H):** dentro de la zona, **CHoCH alcista** = deja de hacer mínimos decrecientes
   y **rompe el último máximo** (BOS al alza). [El "máximo anterior" = el que precede al mínimo más bajo.]
5. **Entrada:** orden **LÍMITE larga** en la zona del FVG / al cierre que confirma el BOS en 1H.
6. **Stop:** bajo el mínimo del pullback (borde inferior del FVG). Riesgo pequeño y fijo (p. ej. 1%).
7. **Objetivo:** la liquidez de arriba (máximo previo del HTF) o múltiplo R fijo (≥2R).

---

## 4. Evidencia que respalda cada pieza

- **FVG (zona):** 45,4% reversión a 1,5R, **estable 44-46% TODOS los años incl. 2026** (121k casos).
- **Estructura/BOS (confirmación + continuación):** 44,2% a 1,5R, **+0,10R/op neto**; fuerte en
  tendencia (2021 +106R, 2025 +158R), flojo en lateral/bajista (2026 −16R).
- **Tendencia HTF (filtro):** comprar el retroceso SOLO en tendencia bajó el drawdown de −37% a −14%.
- **Coste:** el FVG con entrada límite (maker) baja el coste ~3-4x → cruza el muro.

---

## 5. Cómo se PRUEBA (el juez, antes de creernos nada)

- Backtest **multi-moneda**, **sin lookahead** (estructura confirmada con retraso; entrada en cierre).
- **Entrada maker** (coste límite) en el retest; stop/objetivo realistas.
- Métricas: **expectativa neta/op, win%, R total**, y **CRÍTICO: desglose por año con 2026 como prueba**.
- **Verde** solo si: neto/op > 0 **Y** positivo (o al menos plano) en 2026.
- Si pasa → se profesionaliza (paper-trade en Hyperliquid) antes de un euro real.

---

*Operativa propuesta tras la fase de investigación. Pendiente: implementar y validar exactamente esto.*
