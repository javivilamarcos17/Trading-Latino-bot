"""
PORTFOLIO MAESTRO v3 — según especificación del ANALISTA (2026-07-18), a costes CORREGIDOS.
  Clúster A (siempre ON): trend_rider 1D + atr_break_trend 1D × 3 monedas. Riesgo 0.30% × vol-targeting
     (0.50/vol30d, clip 0.25-1.5). Tope 2 ops/día del clúster.
  Clúster B (solo OSO MADURO >250d desde ATH y dd>40%): fvg_ob_asia + fvg_ob(sin 18-23h) +
     ob_asia_close solo-LARGOS. Riesgo 0.20%. Tope 2 ops/día TOTAL del clúster (corr interna 0.61-0.75).
     Stop diario del clúster −0.4%.
  Clúster C: planbtc 1%/op.
  Topes globales: día −1% → no más entradas; semana −2.5% → solo C.
Ops intradía: research_cache/ops_router.parquet (REGENERADO con costes reales).
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd
from pathlib import Path
from collections import defaultdict
from trading_latino.research.backtest_largo import det_trend_rider, det_atr_break_trend, salida_fija
from trading_latino.research.backtest_ganadoras import LOOKBACK
from trading_latino.research.planbtc_core import bajar_diario, bajar_fng, salida

CACHE = Path("data_store/research_cache"); SLIP = 0.01

def ops_1d():
    f = CACHE / "ops_1d_v3.parquet"
    if f.exists(): return pd.read_parquet(f)
    rows = []
    for coin in ["BTC", "ETH", "SOL"]:
        d15 = pd.read_parquet(CACHE / f"{coin}_15m.parquet"); d15["dt"] = pd.to_datetime(d15["t"], unit="ms")
        d = d15.set_index("dt").resample("1D").agg({"t":"first","apertura":"first","maximo":"max","minimo":"min","cierre":"last","volumen":"sum"}).dropna().reset_index(drop=True)
        cl = d["cierre"].to_numpy()
        ret = np.log(cl[1:]/cl[:-1]); vol = pd.Series(ret).rolling(30).std().to_numpy()*np.sqrt(365)
        for j in range(LOOKBACK, len(d)-1):
            w = d.iloc[j-LOOKBACK:j+1].reset_index(drop=True)
            for det in (det_trend_rider, det_atr_break_trend):
                try: sig = det(w)
                except Exception: continue
                if not sig: continue
                r = salida_fija(d, j, sig["stop"], sig["target"], sig["dir"]=="largo")
                if r is None: continue
                v = vol[j-1] if j-1 < len(vol) and not np.isnan(vol[j-1]) else 0.5
                rows.append((int(d["t"].iloc[j]), r - SLIP, float(np.clip(0.50/v, 0.25, 1.50))))
        print(f"  [1D {coin}] ok")
    o = pd.DataFrame(rows, columns=["t","r","mult"]); o.to_parquet(f, index=False)
    return o

def main():
    print("MAESTRO v3 (spec analista, costes corregidos)\n")
    # ciclo (oso maduro estricto) + planbtc
    d = bajar_diario("BTC"); fng = bajar_fng()
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    ath = np.maximum.accumulate(hi); dias = np.zeros(len(d)); last = 0
    for i in range(len(d)):
        if hi[i] >= ath[i]: last = i
        dias[i] = i - last
    ddp = (ath - cl)/ath
    oso_maduro = pd.DataFrame({"t": d["t"].astype("int64"), "on": (dias > 250) & (ddp > 0.40)})
    farr = pd.merge_asof(d[["t"]].astype({"t":"int64"}), fng, on="t", direction="backward")["fng"].shift(1).to_numpy()
    pb = []
    for i in range(25, len(d)-1):
        if pd.to_datetime(int(d.t.iloc[i]), unit="ms").year < 2021: continue
        ll = lo[i-20:i].min(); fg = farr[i]
        if not (lo[i] < ll and cl[i] > ll): continue
        if fg == fg and fg > 75: continue
        if not (dias[i] > 200 or ddp[i] > 0.50): continue
        e1 = cl[i]; s1 = lo[i]*0.995
        if e1 <= s1: continue
        r = salida(d, i, e1, s1, e1+4*(e1-s1), True)
        if r is not None: pb.append((int(d.t.iloc[i]), "C", r, 0.01))

    o1 = ops_1d()
    oi = pd.read_parquet(CACHE / "ops_router.parquet")
    oi = pd.merge_asof(oi.sort_values("t"), oso_maduro, on="t", direction="backward")
    oi["h"] = pd.to_datetime(oi["t"], unit="ms").dt.hour
    port = [(int(t), "A", r, 0.003*m) for t, r, m in o1[["t","r","mult"]].values]
    for t, r, g, e, dr, on, h in oi[["t","pnl","regimen","estr","dir","on","h"]].values:
        if not on: continue
        if e == "fvg_ob_asia" or (e == "fvg_ob" and h not in (18,19,20,21,22,23)) or (e == "ob_asia_close" and dr == "largo"):
            port.append((int(t), "B", r, 0.002))
    port += pb; port.sort()

    capi = pico = 1.0; dd = 0.0
    cap_dia = defaultdict(int); pnl_dia = defaultdict(float); pnl_B_dia = defaultdict(float); pnl_sem = defaultdict(float)
    anios = {}
    for t, cluster, r, risk in port:
        ts = pd.to_datetime(t, unit="ms"); dia = ts.strftime("%Y%m%d"); sem = ts.strftime("%Y%W")
        if cluster != "C":
            if pnl_dia[dia] <= -0.01 or pnl_sem[sem] <= -0.025: continue        # topes globales
            if cluster == "B" and pnl_B_dia[dia] <= -0.004: continue            # stop diario clúster B
            if cap_dia[(cluster, dia)] >= 2: continue
            cap_dia[(cluster, dia)] += 1
        pnl = risk * r
        a = int(dia[:4])
        if a not in anios: anios[a] = [capi, capi]
        capi *= (1 + pnl); anios[a][1] = capi
        pnl_dia[dia] += pnl; pnl_sem[sem] += pnl
        if cluster == "B": pnl_B_dia[dia] += pnl
        pico = max(pico, capi); dd = max(dd, (pico-capi)/pico)
    print(f"\nRESULTADO v3 ({len(port):,} ops candidatas):")
    for a, v in sorted(anios.items()): print(f"  {a}: {(v[1]/v[0]-1)*100:+7.1f}%")
    print(f"  TOTAL: {(capi-1)*100:+.1f}% | peor caída: -{dd*100:.1f}%")
    print("  (v2 era +92.5%/-26.8% con costes bugueados; v1 -47%)")

if __name__ == "__main__":
    main()
