# PROJECT_STATUS.md — Estado real del proyecto

> 🟢 **Este es el archivo más honesto del proyecto.**
> Aquí no se vende humo: dice qué funciona DE VERDAD hoy y qué no.
> Pensado para que cualquier persona —tú, un socio, un inversor— entienda
> el estado real en 30 segundos, sin saber nada de tecnología.
>
> **Regla de oro:** si algo no está aquí marcado como "funciona", asume que NO funciona.
> Una demo bonita NO es un producto. Documentación NO es código que funciona.
>
> Claude actualiza este archivo cada vez que cambia algo importante.
> Si ves que está desactualizado, pídele: *"Actualiza el PROJECT_STATUS"*.

---

## 1. Estado actual

> Marca con una **X** la casilla real. Solo una. Si dudas entre dos, elige la MENOR.

- [ ] 💡 **Idea**
- [X] 📄 **Documentación** — Está escrito qué se quiere hacer y cómo, pero el producto aún no funciona.
- [ ] 🎬 **Demo**
- [ ] 🛠️ **Prototipo funcional**
- [ ] 🚀 **MVP**
- [ ] 🏭 **Producción**

**Estado: 📄 Documentación.** Tenemos la estrategia investigada y documentada (la "biblia"),
el plan por fases, la arquitectura, y el **esqueleto del proyecto montado con los parámetros
escritos en código**. Pero todavía NO existe nada que descargue datos, calcule indicadores
ni haga un backtest. *(Elegimos la etapa menor: hay cimientos, no producto.)*

---

## 2. ✅ Qué funciona HOY

> Solo lo comprobado de verdad.

- La **documentación**: visión, biblia de la estrategia, roadmap y arquitectura.
- El **esqueleto del proyecto** importa correctamente y la **configuración carga** (probado:
  el comando de la sección 4 imprime los parámetros sin error).
- Eso es todo. **No opera, no descarga datos, no backtestea todavía.**

---

## 3. ❌ Qué NO funciona todavía

- Descarga de datos históricos (Fase 1).
- Indicadores: EMA / ADX / Squeeze / Perfil de Volumen (Fase 2).
- El "cerebro" de la estrategia y la gestión de riesgo (Fase 3).
- El motor de backtesting y el modelo de costes (Fase 4).
- El informe de resultados en neto (Fase 5).
- Conexión a Hyperliquid, paper trading y operativa real (Fases 6-7).
- **En resumen: aún no sabemos si la estrategia es rentable. Eso lo dirá la Fase 5.**

---

## 4. 🧪 Cómo probarlo

Lo único comprobable hoy (que el esqueleto y la configuración funcionan):

```bash
# desde la carpeta del proyecto
python -c "from trading_latino.config import CONFIG; print('Altcoins vigiladas:', len(CONFIG.altcoins), '| Tamaño por trade:', CONFIG.riesgo.TAMANO_POSICION_PCT)"
# Debe imprimir: Altcoins vigiladas: 20 | Tamaño por trade: 0.05
```

---

## 5. 🔚 Última decisión tomada

- **2026-06-18** — Cerrado el diseño de la Fase 0: arquitectura "un cerebro, tres mundos",
  stack (Python 3.12 + pandas/ccxt + motor de backtest propio + Hyperliquid), **principio de
  fidelidad a Merino** (🟦🟨🟥), y parámetros escritos en `trading_latino/config/parameters.py`.

---

## 6. ⏭️ Próxima decisión necesaria

- **Confirmar capital inicial y periodo del backtest** (ahora: 10.000 $, 2021-2025). Decide: tú.
- **Variante de tamaño**: 20 partes (5%) fijo — confirmado por defecto. (10 partes queda como opción.)
- Tras eso → arrancar **Fase 1 (capa de datos)**: descargar el histórico. Decide/hace: Claude.

---

## 7. ⚠️ Riesgos abiertos

- **No está demostrado que la estrategia sea rentable** — la única referencia codificada
  (Ruckard) reporta retornos modestos. Por eso el objetivo nº1 es un backtest honesto.
- **Datos:** Hyperliquid tiene poco histórico; usaremos otro exchange (Binance) para el backtest.
- **Costes reales:** comisiones + funding pueden comerse el beneficio si no se modelan bien.
- **Riesgo financiero:** es trading apalancado con dinero real (fases finales). Empezaremos
  con capital mínimo y solo tras validar en backtest + paper.
- **Dependencia de terceros:** APIs de exchanges (límites, cambios, caídas).

---

## 8. 🎯 Nivel de confianza del estado actual

- [ ] 🟢 Alto
- [X] 🟡 **Medio** — Lo construido (docs + esqueleto + config) está probado y es sólido; pero
  el producto en sí (backtest, operativa) aún no existe, así que la incertidumbre sigue siendo alta.
- [ ] 🔴 Bajo

---

*Última actualización: 2026-06-18 por Claude.*
*Mantiene: Claude (con validación del dueño del proyecto).*
