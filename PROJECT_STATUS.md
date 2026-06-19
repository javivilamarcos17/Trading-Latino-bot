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
- [ ] 📄 **Documentación**
- [ ] 🎬 **Demo**
- [X] 🛠️ **Prototipo funcional** — Funciona de punta a punta, pero NO es fiable ni completo.
- [ ] 🚀 **MVP**
- [ ] 🏭 **Producción**

**Estado: 🛠️ Prototipo funcional.** El backtest de BTC solo-Longs **corre end-to-end**:
descarga datos, calcula indicadores, el cerebro decide, el broker simula con costes en neto
y saca un informe. Resultado del primer backtest (2021-2025): **+4,54% neto** (vs **+204,86%**
de comprar y mantener BTC). Es decir: la máquina funciona, pero **como estrategia todavía no
aporta** — gana poquísimo y rinde muchísimo peor que limitarse a comprar BTC. Falta validar
fuera de muestra, probar las otras reglas de salida y, sobre todo, el módulo de alt-shorts.

---

## 2. ✅ Qué funciona HOY

> Solo lo comprobado de verdad.

- La **documentación**: visión, biblia de la estrategia, roadmap y arquitectura.
- El **esqueleto del proyecto** importa correctamente y la **configuración carga** (probado:
  el comando de la sección 4 imprime los parámetros sin error).
- El **entorno está montado y verificado**: librerías (pandas, ccxt, etc.) instaladas y
  funcionando en Python 3.14.
- **Descarga de datos (Fase 1) funcionando para BTC:** se bajan velas de 1h/4h/1d/1w de
  Binance y se guardan en disco. Verificadas: 43.800 velas de 1h (2021-2025) **sin huecos,
  sin duplicados, sin velas inválidas**.
- Eso es todo. **No calcula indicadores, no opera y no backtestea todavía.**

---

## 3. ❌ Qué NO funciona todavía

- Descarga de las 20 altcoins (de momento solo BTC; las alts se bajan para el módulo 5b).
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
# (1) que el esqueleto y la configuración cargan:
.venv/Scripts/python.exe -c "from trading_latino.config import CONFIG; print('Altcoins:', len(CONFIG.altcoins))"

# (2) descargar el histórico de BTC (1h/4h/1d/1w):
.venv/Scripts/python.exe -m trading_latino.data.download

# (3) verificar la calidad de los datos descargados:
.venv/Scripts/python.exe -m trading_latino.data.quality
# Debe salir "OK ✅" en las 4 temporalidades, con huecos=0 y invalidas=0.
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
