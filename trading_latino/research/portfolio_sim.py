"""
PORTFOLIO SIMULATOR — motor determinista y auditable (2026-07-19, convergencia con IA externa).

Separa GENERACIÓN DE ALPHA (cada estrategia emite sus trades) de ASIGNACIÓN DE CAPITAL (el motor
decide cuánto riesgo aprueba según una jerarquía de topes).

Jerarquía de riesgo (4 capas, todas opcionales salvo la global):
  1. GLOBAL     — presupuesto de riesgo asignado agregado <= cap_global (el 5% de la espec).
  2. ASSET      — presupuesto por moneda (BTC/ETH/SOL) <= cap_asset.
  3. FACTOR     — presupuesto por dirección cripto (long-factor / short-factor) <= cap_factor.
  4. STRATEGY   — presupuesto por estrategia <= cap_strategy.
Cargas de factor = 1 en V1 (BTC=ETH=SOL): las 3 monedas long a la vez = UN factor cripto-long.

NOMENCLATURA (corrección IA externa): lo del tope es el PRESUPUESTO DE RIESGO ASIGNADO (allocated
risk budget), el riesgo inicial que la posición reserva, constante durante su vida en V1. El riesgo
económico real (current_stop_risk) es campo de V2.

DOS MODOS DE CONTABILIDAD (crítico — fallo de causalidad detectado por auditoría IA 2026-07-19):
  - causal=True (V1.1, POR DEFECTO, correcto): motor por EVENTOS entry/exit. El PnL se REALIZA en
    la fecha de SALIDA; el sizing usa la equity realizada EN EL MOMENTO DE ENTRADA. Sin look-ahead.
  - causal=False (reproduce el baseline histórico concilia_portfolio.py, que era NO causal): el PnL
    se acredita en la fecha de ENTRADA. Se conserva solo para demostrar la contaminación del
    baseline y verificar que los streams de trades coinciden.
V1.1 realiza PnL a la salida pero la curva de equity es escalonada (realized), no mark-to-market:
el drawdown intra-trade se subestima → MTM es V2. Full event-driven (SIGNAL/STOP/FUNDING/MARK,
batch de timestamps exactos) también V2, prerequisito de scalping.

Trade = dict con: dt (Timestamp), asset, strategy, direction ('largo'/'corto'), r (R neto),
                   risk (fracción, ej 0.0025), dur (días que ocupa el presupuesto).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

EPS = 1e-9


def _metricas(equity, capital0, maxdd, curva, contribs, decisiones, rechazos, riesgo_rechazado, span_dias):
    cdf = pd.DataFrame(contribs)
    años = max(span_dias / 365.25, 1e-6)
    cagr = (equity / capital0) ** (1 / años) * 100 - 100 if equity > 0 else -100
    calmar = (cagr / (maxdd * 100)) if maxdd > 0 else np.inf
    conc = {}
    if len(cdf):
        cdf = cdf.copy(); cdf["sem"] = pd.to_datetime(cdf["dt"]).dt.to_period("W")
        wk = cdf.groupby("sem").pnl.sum().sort_values(ascending=False)
        pos = wk[wk > 0].sum()
        conc["top5_sem_%_de_ganancias"] = (wk.head(5).sum() / pos * 100) if pos > 0 else np.nan
    return {
        "retorno_total_%": (equity / capital0 - 1) * 100, "maxdd_%": maxdd * 100, "cagr_%": cagr,
        "calmar": calmar, "n_trades": len(contribs), "años": años,
        "rechazos": rechazos, "riesgo_rechazado": riesgo_rechazado,
        "curva": curva, "contribs": cdf, "concentracion": conc,
        "decisiones": pd.DataFrame(decisiones),
    }


def simular(trades, cap_global=0.05, cap_asset=None, cap_factor=None, cap_strategy=None,
            capital0=1.0, causal=True):
    caps = dict(cap_global=cap_global, cap_asset=cap_asset, cap_factor=cap_factor, cap_strategy=cap_strategy)
    if not causal:
        return _simular_no_causal(trades, capital0=capital0, **caps)
    return _simular_causal(trades, capital0=capital0, **caps)


def _viola(caps, uso_g, uso_a, uso_f, uso_s, risk):
    if caps["cap_global"] is not None and uso_g + risk > caps["cap_global"] + EPS: return "global"
    if caps["cap_asset"] is not None and uso_a + risk > caps["cap_asset"] + EPS: return "asset"
    if caps["cap_factor"] is not None and uso_f + risk > caps["cap_factor"] + EPS: return "factor"
    if caps["cap_strategy"] is not None and uso_s + risk > caps["cap_strategy"] + EPS: return "strategy"
    return None


def _simular_causal(trades, cap_global, cap_asset, cap_factor, cap_strategy, capital0):
    """Motor por eventos: el riesgo se reserva en ENTRY, el PnL se realiza en EXIT (causal)."""
    caps = dict(cap_global=cap_global, cap_asset=cap_asset, cap_factor=cap_factor, cap_strategy=cap_strategy)
    ev = []
    for i, t in enumerate(trades):
        fin = t["dt"] + pd.Timedelta(days=max(int(t["dur"]), 1))
        ev.append((t["dt"], 1, i))    # 1 = entry
        ev.append((fin, 0, i))        # 0 = exit (se procesa ANTES que las entradas del mismo instante)
    ev.sort(key=lambda e: (e[0], e[1]))
    equity = capital0; pico = capital0; maxdd = 0.0
    abiertos = {}   # i -> {risk, asset, strategy, direction, pnl_realizar}
    curva = []; contribs = []; decisiones = []
    rechazos = {"global": 0, "asset": 0, "factor": 0, "strategy": 0}; riesgo_rechazado = 0.0
    for (tiempo, kind, i) in ev:
        t = trades[i]
        if kind == 0:
            pos = abiertos.pop(i, None)
            if pos is None: continue
            equity += pos["pnl_realizar"]
            pico = max(pico, equity); maxdd = max(maxdd, (pico - equity) / pico)
            curva.append((tiempo, equity))
            contribs.append({"dt": t["dt"], "strategy": t["strategy"], "asset": t["asset"], "pnl": pos["pnl_realizar"] / capital0})
        else:
            asset, strat, dr, risk, r = t["asset"], t["strategy"], t["direction"], t["risk"], t["r"]
            uso_g = sum(p["risk"] for p in abiertos.values())
            uso_a = sum(p["risk"] for p in abiertos.values() if p["asset"] == asset)
            uso_f = sum(p["risk"] for p in abiertos.values() if p["direction"] == dr)
            uso_s = sum(p["risk"] for p in abiertos.values() if p["strategy"] == strat)
            motivo = _viola(caps, uso_g, uso_a, uso_f, uso_s, risk)
            decisiones.append({"dt": t["dt"], "strategy": strat, "asset": asset, "direction": dr,
                               "requested": risk, "aprobado": motivo is None, "motivo": motivo,
                               "global_antes": uso_g, "r": r})
            if motivo is not None:
                rechazos[motivo] += 1; riesgo_rechazado += risk
                continue
            abiertos[i] = {"risk": risk, "asset": asset, "strategy": strat, "direction": dr,
                           "pnl_realizar": risk * equity * r}   # tamaño fijado sobre equity DE ENTRADA
    span = (trades[-1]["dt"] - trades[0]["dt"]).days if len(trades) > 1 else 1
    # cerrar cualquier posición que quede abierta al final (realiza su PnL al último instante)
    for i, pos in abiertos.items():
        equity += pos["pnl_realizar"]
        pico = max(pico, equity); maxdd = max(maxdd, (pico - equity) / pico)
        contribs.append({"dt": trades[i]["dt"], "strategy": trades[i]["strategy"], "asset": trades[i]["asset"], "pnl": pos["pnl_realizar"] / capital0})
    return _metricas(equity, capital0, maxdd, curva, contribs, decisiones, rechazos, riesgo_rechazado, span)


def _simular_no_causal(trades, cap_global, cap_asset, cap_factor, cap_strategy, capital0):
    """Baseline histórico (NO causal): PnL acreditado en la fecha de entrada. Solo para reproducir."""
    caps = dict(cap_global=cap_global, cap_asset=cap_asset, cap_factor=cap_factor, cap_strategy=cap_strategy)
    ts = sorted(trades, key=lambda z: z["dt"])
    abiertos = []; equity = capital0; pico = capital0; maxdd = 0.0
    curva = []; contribs = []; decisiones = []
    rechazos = {"global": 0, "asset": 0, "factor": 0, "strategy": 0}; riesgo_rechazado = 0.0
    for t in ts:
        dt, asset, strat, dr = t["dt"], t["asset"], t["strategy"], t["direction"]
        risk, r, dur = t["risk"], t["r"], t["dur"]
        abiertos = [o for o in abiertos if o["fin"] > dt]
        uso_g = sum(o["risk"] for o in abiertos)
        uso_a = sum(o["risk"] for o in abiertos if o["asset"] == asset)
        uso_f = sum(o["risk"] for o in abiertos if o["direction"] == dr)
        uso_s = sum(o["risk"] for o in abiertos if o["strategy"] == strat)
        motivo = _viola(caps, uso_g, uso_a, uso_f, uso_s, risk)
        decisiones.append({"dt": dt, "strategy": strat, "asset": asset, "direction": dr,
                           "requested": risk, "aprobado": motivo is None, "motivo": motivo,
                           "global_antes": uso_g, "r": r})
        if motivo is not None:
            rechazos[motivo] += 1; riesgo_rechazado += risk; continue
        abiertos.append({"fin": dt + pd.Timedelta(days=max(int(dur), 1)),
                         "asset": asset, "strategy": strat, "direction": dr, "risk": risk})
        pnl = risk * r
        equity *= (1 + pnl)
        pico = max(pico, equity); maxdd = max(maxdd, (pico - equity) / pico)
        curva.append((dt, equity)); contribs.append({"dt": dt, "strategy": strat, "asset": asset, "pnl": pnl})
    span = (ts[-1]["dt"] - ts[0]["dt"]).days if len(ts) > 1 else 1
    return _metricas(equity, capital0, maxdd, curva, contribs, decisiones, rechazos, riesgo_rechazado, span)


def resumen(nombre, m):
    c = m["concentracion"]
    print(f"{nombre:<38} ret={m['retorno_total_%']:+7.1f}%  DD=-{m['maxdd_%']:.1f}%  CAGR={m['cagr_%']:+5.1f}%  "
          f"Calmar={m['calmar']:.2f}  n={m['n_trades']}  top5sem={c.get('top5_sem_%_de_ganancias', float('nan')):.0f}%")
