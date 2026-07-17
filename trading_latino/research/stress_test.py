"""
STRESS TEST MULTI-AÑO de la cartera ganadora (forward-validada) — ¿qué pasa en TOROS y a años vista?
====================================================================================================
Coge las 3 forward-validadas (ob_asia_close base y SOLO-LARGOS, fvg_ob_asia, fvg_ob) y las lleva a
2021→hoy (toro 21, oso 22, lateral 23, toro 24, oso 25-26) sobre 15m de Binance:
  1. exp/op por AÑO y por RÉGIMEN (alcista/lateral/bajista) — ¿la ganadora sobrevive a un toro?
  2. CURVA DE CARTERA (riesgo 0.25%, tope 6/día) año a año.
  3. MONTE CARLO por bloques de DÍAS (1.000 remuestreos) — distribución de la rentabilidad MENSUAL
     (p5/p50/p95) y de la PEOR CAÍDA (p95) = el estrés máximo honesto.
Todo NETO (comisión en salida_fija + slippage 0.01R). Sin lookahead (régimen con retorno pasado).

Uso:  python -m trading_latino.research.stress_test [desde=2021-01-01]
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd

from trading_latino.research.backtest_largo import descargar_15m_binance, salida_fija, clasificar_regimen
from trading_latino.research.backtest_ganadoras import LOOKBACK, det_ob_trend, det_fvg_ob

SLIP = 0.01

def _hora(ts_ms):
    return pd.to_datetime(int(ts_ms), unit="ms").hour

def det_ob_asia_close(d):
    h = _hora(d["t"].iloc[-1])
    if not (3 <= h < 7): return None
    return det_ob_trend(d)

def det_fvg_ob_asia(d):
    if _hora(d["t"].iloc[-1]) >= 7: return None
    return det_fvg_ob(d)

ESTR = {
    "ob_asia_close":   det_ob_asia_close,
    "fvg_ob_asia":     det_fvg_ob_asia,
    "fvg_ob":          det_fvg_ob,
}

def stat(v):
    n = len(v)
    return n, (sum(1 for x in v if x > 0) / n if n else 0), (sum(v) / n if n else 0)

def main():
    desde = sys.argv[1] if len(sys.argv) > 1 else "2021-01-01"
    desde_ts = int(pd.Timestamp(desde, tz="UTC").timestamp() * 1000)
    hasta_ts = int(pd.Timestamp.now("UTC").timestamp() * 1000)
    print(f"STRESS TEST — cartera forward-validada, {desde} -> hoy, 15m, NETO (+slip {SLIP}R)\n")

    todas = []   # (ts, estrategia, dir, pnl, anio, regimen)
    for coin in ["BTC", "ETH", "SOL"]:
        print(f"[{coin}] descargando 15m...")
        d = descargar_15m_binance(coin, desde_ts, hasta_ts)
        if len(d) < LOOKBACK + 100:
            print("  insuficiente"); continue
        reg = clasificar_regimen(d)
        ts_pd = pd.to_datetime(d["t"], unit="ms")
        n_ops = 0
        for j in range(LOOKBACK, len(d) - 1):
            w = d.iloc[j - LOOKBACK: j + 1].reset_index(drop=True)
            for e, det in ESTR.items():
                try: sig = det(w)
                except Exception: continue
                if not sig: continue
                r = salida_fija(d, j, sig["stop"], sig["target"], sig["dir"] == "largo")
                todas.append((int(d["t"].iloc[j]), e, sig["dir"], r, ts_pd.iloc[j].year, reg[j]))
                n_ops += 1
        print(f"  {coin}: {n_ops:,} ops")

    todas.sort()
    print("\n" + "=" * 100)
    print("1) exp/op POR RÉGIMEN y POR AÑO (neto, slip incluido) — ¿sobrevive al TORO?")
    print("=" * 100)
    variantes = [("ob_asia_close", None), ("ob_asia_close_LARGOS", "largo"), ("fvg_ob_asia", None), ("fvg_ob", None)]
    for nom, dirf in variantes:
        base = nom.replace("_LARGOS", "")
        sel = [t for t in todas if t[1] == base and (dirf is None or t[2] == dirf)]
        pn = [t[3] - SLIP for t in sel]
        n, w, ex = stat(pn)
        print(f"\n{nom}  (n={n:,}, win={w*100:.0f}%, exp NETO={ex:+.3f}R)")
        # por regimen
        cells = []
        for rg in ["alcista", "lateral", "bajista"]:
            v = [t[3] - SLIP for t in sel if t[5] == rg]
            if len(v) >= 30: cells.append(f"{rg}={stat(v)[2]:+.3f}({len(v)})")
        print("  RÉGIMEN: " + "  ".join(cells))
        cells = []
        for a in sorted({t[4] for t in sel}):
            v = [t[3] - SLIP for t in sel if t[4] == a]
            if len(v) >= 30: cells.append(f"{a}={stat(v)[2]:+.2f}({len(v)})")
        print("  AÑO:     " + "  ".join(cells))

    # 2) cartera cronologica (0.25%, tope 6/dia) año a año
    print("\n" + "=" * 100)
    print("2) CARTERA (las 3, riesgo 0.25%, tope 6/día) — retorno por AÑO")
    print("=" * 100)
    from collections import defaultdict
    RISK, CAP = 0.25, 6
    por_dia = defaultdict(int)
    equity_dia = defaultdict(float)      # log-ret por dia (para Monte Carlo)
    capi = pico = 1.0; dd = 0.0
    anio_ini = {}; anio_fin = {}
    for ts, e, dr, r, a, rg in todas:
        dia = pd.to_datetime(ts, unit="ms").strftime("%Y%m%d")
        if por_dia[dia] >= CAP: continue
        por_dia[dia] += 1
        mult = 1 + (RISK / 100) * (r - SLIP)
        capi *= mult
        equity_dia[dia] += np.log(mult)
        pico = max(pico, capi); dd = max(dd, (pico - capi) / pico)
        if a not in anio_ini: anio_ini[a] = capi / mult
        anio_fin[a] = capi
    for a in sorted(anio_ini):
        ret_a = (anio_fin[a] / anio_ini[a] - 1) * 100
        print(f"  {a}: {ret_a:+7.1f}%")
    print(f"  TOTAL: {(capi-1)*100:+.1f}%  |  peor caída histórica: -{dd*100:.1f}%")

    # 3) Monte Carlo por bloques de dias -> distribucion mensual y de drawdown
    print("\n" + "=" * 100)
    print("3) MONTE CARLO (1.000 remuestreos de días) — el estrés máximo")
    print("=" * 100)
    dias_logret = np.array(list(equity_dia.values()))
    rng = np.random.default_rng(42)
    mensual = []; peores_dd = []
    for _ in range(1000):
        muestra = rng.choice(dias_logret, size=30, replace=True)      # un mes sintético
        mensual.append((np.exp(muestra.sum()) - 1) * 100)
        anio = rng.choice(dias_logret, size=365, replace=True)         # un año sintético para DD
        eq = np.exp(np.cumsum(anio)); pk = np.maximum.accumulate(eq)
        peores_dd.append(((pk - eq) / pk).max() * 100)
    mensual = np.array(mensual); peores_dd = np.array(peores_dd)
    print(f"  Rentabilidad MENSUAL: p5={np.percentile(mensual,5):+.1f}%  mediana={np.percentile(mensual,50):+.1f}%  p95={np.percentile(mensual,95):+.1f}%")
    print(f"  Prob. de mes NEGATIVO: {100*(mensual<0).mean():.0f}%")
    print(f"  PEOR CAÍDA en un año (p50/p95): -{np.percentile(peores_dd,50):.1f}% / -{np.percentile(peores_dd,95):.1f}%")
    print("\nLEER ASÍ: si el exp por régimen ALCISTA es negativo, la cartera es de oso/lateral y hay que")
    print("apagarla (o cambiar a las de toro) cuando el régimen gire. El Monte Carlo da el rango honesto.")

if __name__ == "__main__":
    main()
