"""
PROTOCOLO DE PRUEBAS — el pipeline profesional para evaluar CUALQUIER estrategia igual.
======================================================================================
Coge cada estrategia y la pasa por las MISMAS etapas, produciendo un VEREDICTO comparable:

  ETAPA 1 — MULTI-TEMPORALIDAD: la prueba en 15m, 1h y 4h -> ¿cuál es SU mejor temporalidad?
  ETAPA 2 — MULTI-RÉGIMEN: desglose por clima (alcista/lateral/bajista) en su mejor TF.
  ETAPA 3 — COSTES REALES: comisión (0.08%) + slippage medido (~0.006R) -> exp NETO.
  ETAPA 4 — VEREDICTO:
       ROBUSTA   = NETO positivo en >=2 climas (sirve en varios mercados)
       DE RÉGIMEN = NETO positivo en 1 clima (herramienta de banquillo para ese clima)
       DESCARTAR = no es positivo neto en ningún clima

Datos: histórico de Binance (por defecto 2 años, cubre toro 2024 + lateral + oso). Sin lookahead.
Uso:  python -m trading_latino.research.protocolo
      python -m trading_latino.research.protocolo 1.0   (años de histórico)
"""
from __future__ import annotations
import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd, ccxt

from trading_latino.research.backtest_largo import (
    det_ob_trend, det_ob_plus, det_merino, det_merinox, det_merino_fiel,
    det_vwap, det_donchian, det_atr_break, det_atr_break_trend, det_trend_rider,
    det_mean_rev_2R, salida_fija, salida_donchian,
)
from trading_latino.research.backtest_ganadoras import LOOKBACK

TF_MS = {"15m": 15*60_000, "1h": 60*60_000, "4h": 4*60*60_000}
VPD = {"15m": 96, "1h": 24, "4h": 6}     # velas por día (para el régimen)
COSTE_R_FIJO = 0.006                       # slippage medido del spread en vivo (la comisión ya está en salida_fija)

# (detector, modo_salida)  modo: "fija" | "donchian"
def _estrats(coin):
    return {
        "merino":       (lambda d: det_merino(d, coin), "fija"),
        "merinox":      (det_merinox, "fija"),
        "merino_fiel":  (lambda d: det_merino_fiel(d, coin), "fija"),
        "ob_trend":     (det_ob_trend, "fija"),
        "ob_plus":      (det_ob_plus, "fija"),
        "atr_break":    (det_atr_break, "fija"),
        "atr_break_trend": (det_atr_break_trend, "fija"),
        "donchian_2R":  (det_donchian, "fija"),
        "trend_rider":  (det_trend_rider, "donchian"),
        "vwap":         (det_vwap, "fija"),
        "mean_rev":     (det_mean_rev_2R, "fija"),
    }

def bajar(coin, tf, desde_ts, hasta_ts):
    ex = ccxt.binance({"options": {"defaultType": "future"}})
    paso = TF_MS[tf]; bl = []; t = desde_ts; n = 0
    while t < hasta_ts:
        o = None
        for it in range(6):
            try: o = ex.fetch_ohlcv(f"{coin}USDT", tf, since=t, limit=1000); break
            except Exception: time.sleep(2*(it+1))
        if not o: break
        bl.extend(o); t = o[-1][0] + paso; n += 1
    d = pd.DataFrame(bl, columns=["t","apertura","maximo","minimo","cierre","volumen"])
    d["t"] = d["t"].astype("int64")
    return d.drop_duplicates("t").sort_values("t").reset_index(drop=True)

def regimen(d, tf):
    """alcista/lateral/bajista por el retorno de los últimos 90 días (sin lookahead)."""
    cl = d["cierre"].to_numpy(); na = 90 * VPD[tf]
    reg = np.full(len(cl), "?", dtype=object)
    if len(cl) > na:
        r = cl[na:]/cl[:-na] - 1
        reg[na:] = np.where(r > 0.25, "alcista", np.where(r < -0.25, "bajista", "lateral"))
    return reg

def stat(v):
    n=len(v); return n, (sum(1 for x in v if x>0)/n if n else 0), (sum(v)/n if n else 0)

def evaluar_coin(coin, tfs, desde_ts, hasta_ts):
    """Devuelve {estrat: {tf: {clima: [pnls]}}} para una moneda."""
    out = {e: {tf: {"all":[], "alcista":[], "lateral":[], "bajista":[]} for tf in tfs} for e in _estrats(coin)}
    for tf in tfs:
        d = bajar(coin, tf, desde_ts, hasta_ts)
        if len(d) < LOOKBACK + 50: continue
        reg = regimen(d, tf)
        estr = _estrats(coin)
        for j in range(LOOKBACK, len(d)-1):
            w = d.iloc[j-LOOKBACK:j+1].reset_index(drop=True)
            cl_reg = reg[j]
            for e,(det,modo) in estr.items():
                try: sig = det(w)
                except Exception: continue
                if not sig: continue
                if modo == "donchian":
                    r = salida_donchian(d, j, sig["stop"], sig["dir"]=="largo")
                else:
                    r = salida_fija(d, j, sig["stop"], sig["target"], sig["dir"]=="largo")
                out[e][tf]["all"].append(r)
                if cl_reg in out[e][tf]: out[e][tf][cl_reg].append(r)
        print(f"  [{coin}] {tf} hecho ({len(d):,} velas)")
    return out

def main():
    anios = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    tfs = ["15m","1h","4h"]
    hasta = int(pd.Timestamp.now("UTC").timestamp()*1000)
    desde = int((pd.Timestamp.now("UTC") - pd.Timedelta(days=int(anios*365))).timestamp()*1000)
    print(f"PROTOCOLO DE PRUEBAS — {anios} años, TFs {tfs}. Comisión incluida + slippage {COSTE_R_FIJO}R.\n")

    # agregamos las 3 monedas
    agg = {}
    for coin in ["BTC","ETH","SOL"]:
        oc = evaluar_coin(coin, tfs, desde, hasta)
        for e, tfd in oc.items():
            agg.setdefault(e, {tf:{"all":[], "alcista":[], "lateral":[], "bajista":[]} for tf in tfs})
            for tf, cd in tfd.items():
                for clima, v in cd.items(): agg[e][tf][clima].extend(v)

    print("\n" + "="*92)
    print("SCORECARD — cada estrategia en su MEJOR temporalidad, NETO de costes, por clima")
    print("="*92)
    print(f"{'estrategia':<14}{'mejorTF':>8}{'n':>7}{'NETO':>9}{'alcista':>12}{'lateral':>12}{'bajista':>12}  VEREDICTO")
    filas = []
    for e, tfd in agg.items():
        # mejor TF por exp neto (con n>=30)
        best_tf, best_net, best = None, -9, None
        for tf, cd in tfd.items():
            n,w,ex = stat(cd["all"])
            if n >= 30 and (ex - COSTE_R_FIJO) > best_net:
                best_net = ex - COSTE_R_FIJO; best_tf = tf; best = cd
        if best is None:
            print(f"{e:<14}{'—':>8}  (pocas señales en todas las TF)"); continue
        climas = {}
        for c in ["alcista","lateral","bajista"]:
            n,w,ex = stat(best[c]); climas[c] = (ex - COSTE_R_FIJO, n) if n >= 20 else (None, n)
        pos = sum(1 for c in climas.values() if c[0] is not None and c[0] > 0)
        if pos >= 2: ver = "ROBUSTA"
        elif pos == 1: ver = "DE REGIMEN"
        else: ver = "DESCARTAR"
        def cell(c):
            v,n = climas[c]; return f"{v:+.3f}({n})" if v is not None else f"{'—':>10}"
        n_all = stat(best["all"])[0]
        filas.append((best_net, e, best_tf, n_all, climas, ver))
    filas.sort(reverse=True)
    for best_net, e, best_tf, n_all, climas, ver in filas:
        def cell(c):
            v,n = climas[c]; return (f"{v:+.3f}({n})" if v is not None else "—").rjust(12)
        print(f"{e:<14}{best_tf:>8}{n_all:>7}{best_net:>+9.3f}{cell('alcista')}{cell('lateral')}{cell('bajista')}  {ver}")
    print("\nROBUSTA = sirve en varios climas. DE REGIMEN = banquillo de un clima. NETO ya descuenta costes.")

if __name__ == "__main__":
    main()
