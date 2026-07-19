"""
PORTFOLIO SIMULATOR V1 — motor determinista y auditable (2026-07-19, convergencia con IA externa).

Separa GENERACIÓN DE ALPHA (cada estrategia emite sus trades) de ASIGNACIÓN DE CAPITAL (el motor
decide cuánto riesgo aprueba según una jerarquía de topes). Reproduce el baseline conocido antes
de probar nada nuevo (Test 0).

Jerarquía de riesgo (4 capas, todas opcionales salvo la global):
  1. GLOBAL     — riesgo abierto agregado <= cap_global (el 5% de la espec).
  2. ASSET      — riesgo abierto por moneda (BTC/ETH/SOL) <= cap_asset.
  3. FACTOR     — riesgo abierto por dirección cripto (long-factor / short-factor) <= cap_factor.
  4. STRATEGY   — riesgo abierto por estrategia <= cap_strategy.
Cargas de factor = 1 en V1 (BTC=ETH=SOL): las 3 monedas long a la vez = UN factor cripto-long.

NOMENCLATURA (corrección IA externa 2026-07-19): lo que rastreamos para el tope NO es "open risk"
económico, es el PRESUPUESTO DE RIESGO ASIGNADO (allocated risk budget): el riesgo inicial que la
posición reserva del presupuesto, constante durante su vida en V1. El riesgo económico real
(current_stop_risk, según se mueva el stop) es un campo de V2. No confundir capital reservado por
política con riesgo económico actual.

Contabilidad (fiel al baseline concilia_portfolio.py, para poder reproducir +44.5%/-12.4%):
  - Equity COMPUESTA sobre NAV realizado en la fecha de entrada: equity *= (1 + risk * R_neto).
    El sizing usa la equity realizada EN EL TIMESTAMP DE ENTRADA (explícito, no mark-to-market).
  - PnL se contabiliza en la fecha de ENTRADA (V1); el presupuesto asignado se rastrea durante la
    duración de la posición para el tope (una posición "ocupa" su riesgo `dur` días).
  V1 es entry-event-driven (no full event-driven): suficiente para PnL-a-la-entrada y reproducir
  el baseline; el refactor a event-driven (SIGNAL/ENTRY/STOP/EXIT/FUNDING/MARK) es prerequisito
  para scalping/trailing/funding-realizado (V2).
  - Orden de asignación: por fecha de entrada (causal). El primero que llega, se asigna primero;
    los que no caben se RECHAZAN y se registra el motivo (coste de oportunidad del tope).
  V2 futuro: PnL a la salida + curva mark-to-market + cargas de factor empíricas.

Trade = dict con: dt (Timestamp), asset, strategy, direction ('largo'/'corto'), r (R neto),
                   risk (fracción, ej 0.0025), dur (días que ocupa el riesgo).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

EPS = 1e-9


def simular(trades, cap_global=0.05, cap_asset=None, cap_factor=None, cap_strategy=None, capital0=1.0):
    """Ejecuta el portfolio. Devuelve dict con métricas, curva de equity, rechazos y contribuciones."""
    ts = sorted(trades, key=lambda z: z["dt"])
    abiertos = []          # cada uno: {"fin","asset","strategy","direction","risk"}
    equity = capital0; pico = capital0; maxdd = 0.0
    curva = []; contribs = []; decisiones = []
    rechazos = {"global": 0, "asset": 0, "factor": 0, "strategy": 0}
    riesgo_rechazado = 0.0

    for t in ts:
        dt, asset, strat, dr = t["dt"], t["asset"], t["strategy"], t["direction"]
        risk, r, dur = t["risk"], t["r"], t["dur"]
        # liberar posiciones cuyo riesgo ya expiró
        abiertos = [o for o in abiertos if o["fin"] > dt]
        uso_g = sum(o["risk"] for o in abiertos)
        uso_a = sum(o["risk"] for o in abiertos if o["asset"] == asset)
        uso_f = sum(o["risk"] for o in abiertos if o["direction"] == dr)
        uso_s = sum(o["risk"] for o in abiertos if o["strategy"] == strat)
        motivo = None
        if cap_global is not None and uso_g + risk > cap_global + EPS:
            motivo = "global"
        elif cap_asset is not None and uso_a + risk > cap_asset + EPS:
            motivo = "asset"
        elif cap_factor is not None and uso_f + risk > cap_factor + EPS:
            motivo = "factor"
        elif cap_strategy is not None and uso_s + risk > cap_strategy + EPS:
            motivo = "strategy"
        decisiones.append({"dt": dt, "strategy": strat, "asset": asset, "direction": dr,
                           "requested": risk, "aprobado": motivo is None, "motivo": motivo,
                           "global_antes": uso_g, "r": r})
        if motivo is not None:
            rechazos[motivo] += 1; riesgo_rechazado += risk
            continue
        abiertos.append({"fin": dt + pd.Timedelta(days=max(int(dur), 1)),
                         "asset": asset, "strategy": strat, "direction": dr, "risk": risk})
        pnl = risk * r
        equity *= (1 + pnl)
        pico = max(pico, equity); maxdd = max(maxdd, (pico - equity) / pico)
        curva.append((dt, equity)); contribs.append({"dt": dt, "strategy": strat, "asset": asset, "pnl_frac": pnl})

    cdf = pd.DataFrame(contribs)
    dias = (ts[-1]["dt"] - ts[0]["dt"]).days if len(ts) > 1 else 1
    años = max(dias / 365.25, 1e-6)
    cagr = (equity ** (1 / años) - 1) * 100 if equity > 0 else -100
    calmar = (cagr / (maxdd * 100)) if maxdd > 0 else np.inf

    # concentración: top-5 semanas y Gini de PnL semanal (proxy de episodio)
    conc = {}
    if len(cdf):
        cdf = cdf.copy(); cdf["sem"] = pd.to_datetime(cdf["dt"]).dt.to_period("W")
        wk = cdf.groupby("sem").pnl_frac.sum().sort_values(ascending=False)
        pos = wk[wk > 0].sum()
        conc["top5_sem_%_de_ganancias"] = (wk.head(5).sum() / pos * 100) if pos > 0 else np.nan
        x = np.sort(wk.values); n = len(x)
        if n > 0 and x.sum() != 0:
            conc["gini_pnl_semanal"] = (2 * np.sum((np.arange(1, n + 1)) * x) / (n * x.sum()) - (n + 1) / n)
    return {
        "retorno_total_%": (equity - 1) * 100, "maxdd_%": maxdd * 100, "cagr_%": cagr,
        "calmar": calmar, "n_trades": len(contribs), "años": años,
        "rechazos": rechazos, "riesgo_rechazado": riesgo_rechazado,
        "curva": curva, "contribs": cdf, "concentracion": conc,
        "decisiones": pd.DataFrame(decisiones),
    }


def resumen(nombre, m):
    c = m["concentracion"]
    print(f"{nombre:<34} ret={m['retorno_total_%']:+7.1f}%  DD=-{m['maxdd_%']:.1f}%  CAGR={m['cagr_%']:+5.1f}%  "
          f"Calmar={m['calmar']:.2f}  n={m['n_trades']}  top5sem={c.get('top5_sem_%_de_ganancias', float('nan')):.0f}%  "
          f"rechazos={ {k: v for k, v in m['rechazos'].items() if v} }")
