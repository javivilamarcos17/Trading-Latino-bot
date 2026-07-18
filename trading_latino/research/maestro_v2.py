"""
PORTFOLIO MAESTRO v2 — columna 4h robusta + FVG-Asia en oso maduro + planbtc, con presupuesto
POR estrategia (corrige el sesgo de "primeras N del día") y tope 2/día/estrategia.
Datos: caché 15m→4h resampleada (2021-26), ops intradía parquet, BTC diario+F&G reales.
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd
from pathlib import Path
from collections import defaultdict
from trading_latino.research.backtest_largo import det_atr_break_trend, det_merino, salida_fija
from trading_latino.research.backtest_ganadoras import LOOKBACK
from trading_latino.research.planbtc_core import bajar_diario, bajar_fng, salida

CACHE = Path("data_store/research_cache"); SLIP = 0.01

def ops4h():
    f = CACHE / "ops_4h.parquet"
    if f.exists(): return pd.read_parquet(f)
    rows = []
    for coin in ["BTC", "ETH", "SOL"]:
        d15 = pd.read_parquet(CACHE / f"{coin}_15m.parquet")
        d15["dt"] = pd.to_datetime(d15["t"], unit="ms")
        d4 = d15.set_index("dt").resample("4h").agg({"t":"first","apertura":"first","maximo":"max","minimo":"min","cierre":"last","volumen":"sum"}).dropna().reset_index(drop=True)
        dets = {"atr4h": det_atr_break_trend, "merino4h": lambda w: det_merino(w, coin)}
        for j in range(LOOKBACK, len(d4)-1):
            w = d4.iloc[j-LOOKBACK:j+1].reset_index(drop=True)
            for e, det in dets.items():
                try: sig = det(w)
                except Exception: continue
                if not sig: continue
                r = salida_fija(d4, j, sig["stop"], sig["target"], sig["dir"]=="largo")
                rows.append((int(d4["t"].iloc[j]), e, r))
        print(f"  [{coin}] 4h hecho")
    o = pd.DataFrame(rows, columns=["t","estr","pnl"]); o.to_parquet(f, index=False)
    return o

def main():
    print("MAESTRO v2 — columna 4h + FVG-Asia (oso maduro) + planbtc | presupuesto por estrategia\n")
    o4 = ops4h()
    d = bajar_diario("BTC"); fng = bajar_fng()
    hi=d["maximo"].to_numpy(); lo=d["minimo"].to_numpy(); cl=d["cierre"].to_numpy()
    ath=np.maximum.accumulate(hi); dias=np.zeros(len(d)); last=0
    for i in range(len(d)):
        if hi[i]>=ath[i]: last=i
        dias[i]=i-last
    ddp=(ath-cl)/ath
    cond=(dias>250)&(ddp>0.40)
    ciclo=pd.DataFrame({"t":d["t"].astype("int64"),"ciclo":cond})
    farr=pd.merge_asof(d[["t"]].astype({"t":"int64"}),fng,on="t",direction="backward")["fng"].shift(1).to_numpy()
    pb=[]
    for i in range(25,len(d)-1):
        if pd.to_datetime(int(d.t.iloc[i]),unit="ms").year<2021: continue
        ll=lo[i-20:i].min(); fg=farr[i]
        if not(lo[i]<ll and cl[i]>ll): continue
        if fg==fg and fg>75: continue
        if not(dias[i]>200 or ddp[i]>0.50): continue
        e1=cl[i]; s1=lo[i]*0.995
        if e1<=s1: continue
        r=salida(d,i,e1,s1,e1+4*(e1-s1),True)
        if r is not None: pb.append((int(d.t.iloc[i]),"planbtc",r,0.01))
    oi=pd.read_parquet(CACHE/"ops_router.parquet")
    oi=pd.merge_asof(oi.sort_values("t"),ciclo,on="t",direction="backward")
    port=[]
    for t,r,g,e,dr,cic in oi[["t","pnl","regimen","estr","dir","ciclo"]].values:
        if e in ("fvg_ob_asia","fvg_ob") and cic: port.append((int(t),e,r,0.0025))
        elif e=="ob_asia_close" and cic and dr=="largo": port.append((int(t),e,r,0.0025))
    for t,e,r in o4[["t","estr","pnl"]].values:
        port.append((int(t),e,r,0.0025))
    port+=pb; port.sort()
    capi=pico=1.0; dd=0; cap=defaultdict(int); anios={}
    for t,e,r,risk in port:
        dia=pd.to_datetime(t,unit="ms").strftime("%Y%m%d")
        if e!="planbtc":
            if cap[(e,dia)]>=2: continue          # tope 2/día POR estrategia (sin sesgo de hora)
            cap[(e,dia)]+=1
        a=int(dia[:4])
        if a not in anios: anios[a]=[capi,capi]
        capi*=(1+risk*(r-SLIP)); anios[a][1]=capi
        pico=max(pico,capi); dd=max(dd,(pico-capi)/pico)
    for a,v in sorted(anios.items()): print(f"  {a}: {(v[1]/v[0]-1)*100:+7.1f}%")
    print(f"  TOTAL: {(capi-1)*100:+.1f}% | peor caída: -{dd*100:.1f}%")
    print("  (v1 era -47% con caída -66%; estáticas -48% a -81%)")

if __name__ == "__main__":
    main()
