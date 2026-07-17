"""
ROUTER TEST — ¿mejora usar CADA operativa SOLO en su momento (régimen) vs usarlas siempre?
=========================================================================================
El mapa régimen→operativa sale de la EVIDENCIA PREVIA (protocolo/funding lab), no se ajusta aquí:
  bajista/lateral -> familia Asia (ob_asia_close, fvg_ob_asia, fvg_ob)   [probadas en estos climas]
  alcista         -> trend_rider                                          [la única que gana en toro]
Comparación con la MISMA vara (2021-2026, 15m, neto, riesgo 0.25%, tope 6/día):
  A) SOLO familia Asia, siempre    B) TODAS siempre    C) ROUTER (cada clima su herramienta)
Métrica: retorno total, por año, peor caída. + Monte Carlo mensual del ganador.
Con CACHÉ de velas en disco (data_store/research_cache) — descargar una vez, investigar mil veces.

Uso:  python -m trading_latino.research.router_test [desde=2021-01-01]
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd
from pathlib import Path
from collections import defaultdict

from trading_latino.research.backtest_largo import descargar_15m_binance, salida_fija, clasificar_regimen, det_trend_rider
from trading_latino.research.backtest_ganadoras import LOOKBACK, det_ob_trend, det_fvg_ob

CACHE = Path(__file__).resolve().parents[2] / "data_store" / "research_cache"
CACHE.mkdir(parents=True, exist_ok=True)
SLIP = 0.01

def velas_cacheadas(coin, desde_ts, hasta_ts):
    """Descarga 15m UNA vez y lo guarda en parquet; siguientes runs solo bajan lo que falte."""
    f = CACHE / f"{coin}_15m.parquet"
    d = pd.read_parquet(f) if f.exists() else pd.DataFrame()
    if len(d):
        ult = int(d["t"].iloc[-1])
        if ult < hasta_ts - 15*60_000:
            extra = descargar_15m_binance(coin, ult + 15*60_000, hasta_ts)
            d = pd.concat([d, extra]).drop_duplicates("t").sort_values("t").reset_index(drop=True)
    else:
        d = descargar_15m_binance(coin, desde_ts, hasta_ts)
    d.to_parquet(f, index=False)
    return d[d["t"] >= desde_ts].reset_index(drop=True)

def _hora(ts_ms): return pd.to_datetime(int(ts_ms), unit="ms").hour

def det_ob_asia_close(d):
    if not (3 <= _hora(d["t"].iloc[-1]) < 7): return None
    return det_ob_trend(d)

def det_fvg_ob_asia(d):
    if _hora(d["t"].iloc[-1]) >= 7: return None
    return det_fvg_ob(d)

ASIA = {"ob_asia_close": det_ob_asia_close, "fvg_ob_asia": det_fvg_ob_asia, "fvg_ob": det_fvg_ob}
TORO = {"trend_rider": det_trend_rider}

def stat(v):
    n = len(v)
    return n, (sum(1 for x in v if x > 0)/n if n else 0), (sum(v)/n if n else 0)

def simular(ops, risk=0.25, cap=6):
    """ops = [(ts, pnl)] cronológicas. Devuelve (ret%, dd%, por_año, logret_por_día)."""
    ops = sorted(ops)
    capi = pico = 1.0; dd = 0.0
    por_dia = defaultdict(int); logret_dia = defaultdict(float)
    a_ini, a_fin = {}, {}
    for ts, r in ops:
        dia = pd.to_datetime(ts, unit="ms").strftime("%Y%m%d")
        if por_dia[dia] >= cap: continue
        por_dia[dia] += 1
        mult = 1 + (risk/100) * (r - SLIP)
        a = int(dia[:4])
        if a not in a_ini: a_ini[a] = capi
        capi *= mult
        logret_dia[dia] += np.log(mult)
        a_fin[a] = capi
        pico = max(pico, capi); dd = max(dd, (pico - capi)/pico)
    anios = {a: (a_fin[a]/a_ini[a]-1)*100 for a in a_ini}
    return (capi-1)*100, dd*100, anios, logret_dia

def main():
    desde = sys.argv[1] if len(sys.argv) > 1 else "2021-01-01"
    desde_ts = int(pd.Timestamp(desde, tz="UTC").timestamp()*1000)
    hasta_ts = int(pd.Timestamp.now("UTC").timestamp()*1000)
    print(f"ROUTER TEST — {desde} -> hoy. A=Asia siempre | B=todas siempre | C=ROUTER por régimen\n")

    ops_asia, ops_toro = [], []   # (ts, pnl, regimen, estr, dir)
    for coin in ["BTC", "ETH", "SOL"]:
        print(f"[{coin}] velas (caché)...")
        d = velas_cacheadas(coin, desde_ts, hasta_ts)
        print(f"  {len(d):,} velas 15m")
        reg = clasificar_regimen(d)
        for j in range(LOOKBACK, len(d)-1):
            w = d.iloc[j-LOOKBACK:j+1].reset_index(drop=True)
            for grupo, dets, dest in [("asia", ASIA, ops_asia), ("toro", TORO, ops_toro)]:
                for e, det in dets.items():
                    try: sig = det(w)
                    except Exception: continue
                    if not sig: continue
                    r = salida_fija(d, j, sig["stop"], sig["target"], sig["dir"] == "largo")
                    dest.append((int(d["t"].iloc[j]), r, reg[j], e, sig["dir"]))
        print(f"  ops acumuladas: asia={len(ops_asia):,} toro={len(ops_toro):,}")
    # persistir ops -> nunca mas recomputar (investigacion barata para siempre)
    pd.DataFrame(ops_asia + ops_toro, columns=["t", "pnl", "regimen", "estr", "dir"]).to_parquet(
        CACHE / "ops_router.parquet", index=False)
    print(f"  [cache] ops guardadas en research_cache/ops_router.parquet")

    # POR OPERATIVA: exp NETO por régimen y por año (lo que pidió el dueño)
    todas_det = ops_asia + ops_toro
    variantes = [("ob_asia_close", "ob_asia_close", None), ("ob_asia_close_LARGOS", "ob_asia_close", "largo"),
                 ("fvg_ob_asia", "fvg_ob_asia", None), ("fvg_ob", "fvg_ob", None), ("trend_rider", "trend_rider", None)]
    print("\nPOR OPERATIVA — exp/op NETO (por régimen y por año):")
    for nom, base, dirf in variantes:
        sel = [t for t in todas_det if t[3] == base and (dirf is None or t[4] == dirf)]
        pn = [t[1] - SLIP for t in sel]
        n, wn, ex = stat(pn)
        if not n: continue
        print(f"  {nom}  (n={n:,}, win={wn*100:.0f}%, exp={ex:+.3f}R)")
        cells = []
        for rg in ["alcista", "lateral", "bajista"]:
            v = [t[1] - SLIP for t in sel if t[2] == rg]
            if len(v) >= 30: cells.append(f"{rg}={stat(v)[2]:+.3f}({len(v)})")
        print("     RÉGIMEN: " + "  ".join(cells))
        cells = []
        for a in sorted({pd.to_datetime(t[0], unit='ms').year for t in sel}):
            v = [t[1] - SLIP for t in sel if pd.to_datetime(t[0], unit='ms').year == a]
            if len(v) >= 30: cells.append(f"{a}={stat(v)[2]:+.2f}({len(v)})")
        print("     AÑO:     " + "  ".join(cells))

    # A / B / C
    print("\n" + "="*96)
    print(f"{'escenario':<26}{'ops':>7}{'TOTAL':>10}{'peor caída':>12}  por año")
    print("="*96)
    escA = [(t, r) for t, r, g, e, dr in ops_asia]
    escB = [(t, r) for t, r, g, e, dr in ops_asia + ops_toro]
    escC = [(t, r) for t, r, g, e, dr in ops_asia if g in ("bajista", "lateral")] + \
           [(t, r) for t, r, g, e, dr in ops_toro if g == "alcista"]
    # D) ROTACIÓN por evidencia reciente (walk-forward, sin lookahead): cada operativa solo se opera
    # si SU rendimiento en los últimos 45 días (ops ya CERRADAS) es positivo con n>=15. Es el "usar
    # cada una cuando está funcionando" hecho matemática: rotación adaptativa, no mapa fijo.
    VENT = 45 * 86400_000
    hist = defaultdict(list)          # estr -> [(ts, pnl)] cronológico
    todas_ops = sorted(ops_asia + ops_toro)
    escD = []
    MADURA = 2 * 86400_000            # una op solo cuenta para decidir cuando ya habra cerrado (~2d)
    for ts, r, g, e, dr in todas_ops:
        h = hist[e]
        while h and h[0][0] < ts - VENT: h.pop(0)
        cerradas = [p for hts, p in h if hts < ts - MADURA]
        if len(cerradas) >= 15 and sum(cerradas)/len(cerradas) > 0:
            escD.append((ts, r))
        hist[e].append((ts, r))
    resultados = {}
    for nom, ops in [("A) Asia siempre", escA), ("B) Todas siempre", escB), ("C) ROUTER por régimen", escC),
                     ("D) ROTACIÓN 45d adaptativa", escD)]:
        ret, dd, anios, logret = simular(ops)
        resultados[nom] = (ret, dd, logret)
        stranios = "  ".join(f"{a}:{v:+.0f}%" for a, v in sorted(anios.items()))
        print(f"{nom:<26}{len(ops):>7}{ret:>+9.1f}%{('-'+format(dd,'.1f')+'%'):>12}  {stranios}")

    # Monte Carlo del mejor
    mejor = max(resultados, key=lambda k: resultados[k][0]/max(resultados[k][1], 1))
    _, _, logret = resultados[mejor]
    arr = np.array(list(logret.values()))
    rng = np.random.default_rng(42)
    mensual = [(np.exp(rng.choice(arr, 30, replace=True).sum())-1)*100 for _ in range(1000)]
    dds = []
    for _ in range(1000):
        eq = np.exp(np.cumsum(rng.choice(arr, 365, replace=True))); pk = np.maximum.accumulate(eq)
        dds.append(((pk-eq)/pk).max()*100)
    mensual = np.array(mensual)
    print(f"\nMONTE CARLO del mejor ({mejor}):")
    print(f"  mes: p5={np.percentile(mensual,5):+.1f}%  mediana={np.percentile(mensual,50):+.1f}%  p95={np.percentile(mensual,95):+.1f}%  |  prob mes negativo={100*(mensual<0).mean():.0f}%")
    print(f"  peor caída anual: p50=-{np.percentile(dds,50):.1f}%  p95=-{np.percentile(dds,95):.1f}%")
    print("\nSi C gana a A y B en retorno Y caída -> el router por régimen queda VALIDADO para construirlo en vivo.")

if __name__ == "__main__":
    main()
