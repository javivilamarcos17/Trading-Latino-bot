# CAPA CONTABLE DE FUNDING — fotografía económica real (2026-07-19)

**Fuente/proxy (deliverable #8):** funding Binance perp USDT, intervalos 8h, 2020-09→2026-07.
Es un **HISTORICAL NET ESTIMATE** (proxy Binance perp), NO "exact Hyperliquid historical net".
Posiciones anteriores a 2020-09 no cubiertas. Funding realizado por posición = Σ(funding_rate en
[entrada, salida]) / (D/entrada), con signo: long paga si funding>0, short recibe.
Emparejamiento D/E: núcleo 545/545 (100%), turtle 89/89 (100%), ichimoku fresh.

## [1+2] Gross → Funding → Net por estrategia y dirección (R/op)
| Estrategia | n | gross | funding | NET | funding % gross |
|---|---|---|---|---|---|
| **núcleo** | 545 | +0.337 | +0.092 | **+0.245** | 27% |
| — largo | 296 | +0.495 | +0.139 | +0.355 | |
| — corto | 249 | +0.149 | +0.035 | +0.114 | |
| **turtle** | 89 | +1.121 | +0.175 | **+0.946** | 16% |
| **ichimoku** | 418 | +0.323 | +0.018 | **+0.305** | **6%** |
| — largo | 214 | +0.255 | +0.046 | +0.209 | |
| — corto | 204 | +0.395 | −0.012 | +0.407 | (el corto RECIBE funding) |

## [3] Distribución de holding time (días)
| | mediana | p75 | p90 | p95 | max |
|---|---|---|---|---|---|
| núcleo | 66 | 179 | 191 | 191 | 191 |
| turtle | 78 | 160 | 191 | 191 | 191 |
| ichimoku | **4** | 11 | 27 | 42 | 66 |

## [4] Funding drag por bucket de holding (núcleo) — HALLAZGO CLAVE
| bucket | n | gross | funding | net |
|---|---|---|---|---|
| 0-30d | 144 | **−0.564** | +0.026 | −0.590 |
| 30-90d | 174 | +0.471 | +0.070 | +0.401 |
| 90-180d | 95 | +0.458 | +0.128 | +0.330 |
| >180d | 132 | **+1.056** | +0.166 | +0.890 |

Los holds cortos (0-30d) son los **stop-outs** (gross negativo); el edge vive en los holds LARGOS
(>180d, gross +1.056). El funding crece con el hold (+0.026→+0.166) PERO el neto de los holds largos
sigue siendo +0.890. **El funding es el PRECIO de acceder a la cola convexa, no un coste que mate
un trade lateral.**

## [5] Correlaciones (núcleo)
corr(gross, funding)=+0.26 · corr(dur, funding)=+0.30 · corr(dur, net)=+0.24.
→ Más hold = más funding PERO también más neto. Confirma: el funding acompaña al edge, no lo erosiona
en trades muertos. **NO optimizar salidas para "reducir funding"** (destruiría la convexidad).

## [6] MÉTRICAS OFICIALES NUEVAS (net de fees + slippage + funding, causal)
| Cartera | SIN funding | CON funding (oficial) |
|---|---|---|
| A) Núcleo+Turtle | CAGR +6.6% · DD −10.7% · Calmar 0.62 | **CAGR +5.3% · DD −11.6% · Calmar 0.46** |
| B) +Ichimoku (PORTFOLIO_v1) | CAGR +10.9% · DD −7.9% · Calmar 1.37 | **CAGR +9.3% · DD −9.2% · Calmar 1.01** |

## [7] Δ incremental de Ichimoku (net funding)
ΔCAGR +4.0pp · ΔMaxDD +2.4pp (mejora) · **ΔCalmar +0.56**.
→ Como ichimoku holdea ~4 días (funding solo 6%) mientras núcleo/turtle holdean ~70 días (27%/16%),
**el valor relativo de ichimoku AUMENTA al contar funding**: aporta Calmar sin pagar el peaje de los
holds largos. (Hipótesis del dueño confirmada.)

## [9] Reconciliación
núcleo medio/op: gross +0.337 − slip 0.010 − funding +0.092 = **net +0.235** ✓ (fees ya en cR dentro de gross).

## Conclusión / lenguaje oficial a partir de ahora
- La referencia oficial es SIEMPRE net de fees+slippage+funding. Las cifras pre-funding se etiquetan
  "pre-funding historical baseline".
- **PORTFOLIO_v1 oficial (net de todo): CAGR +9.3%, DD −9.2%, Calmar 1.01** (proxy Binance, estimate).
- Cada Strategy Card futura debe incluir EXPECTED HOLDING TIME y su COST PROFILE (scalper→fees/slip;
  trend 1D→funding/holding; maker→adverse selection). Cada edge tiene su propio enemigo económico.
- NO se optimiza nada como reacción a este hallazgo (medir → entender → congelar; exits serían una
  investigación independiente y preregistrada, no una reacción retrospectiva).
