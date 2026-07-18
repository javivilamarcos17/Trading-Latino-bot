"""
BARRIDO DE TEMPORALIDADES INÉDITAS — 30m y 2h (nunca probadas) para nuestras mejores piezas.
Desde caché 15m 2021-26 (resampleo, sin descargas). Neto de costes. exp/op y por régimen.
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd
from pathlib import Path
from trading_latino.research.backtest_largo import (det_trend_rider, det_atr_break, det_atr_break_trend,
    det_merino, det_merinox, det_merino_fiel, det_donchian, det_mean_rev_2R, salida_fija, clasificar_regimen)
from trading_latino.research.protocolo import det_rsi2_rebound, det_hybrid_momo

def det_turtle55(d):
    """Turtle Traders: ruptura del max/min de 55 velas (validada 4h +0.136R n=1830, 1D +0.198R)."""
    hi=d["maximo"].to_numpy(); lo=d["minimo"].to_numpy(); cl=d["cierre"].to_numpy(); j=len(cl)-1
    if j<60: return None
    from trading_latino.research.backtest_ganadoras import _setup
    if cl[j]>hi[j-55:j].max(): return _setup("largo", cl[j], lo[j-10:j].min(), 2.0)
    if cl[j]<lo[j-55:j].min(): return _setup("corto", cl[j], hi[j-10:j].max(), 2.0)
    return None
from trading_latino.research.backtest_ganadoras import LOOKBACK, det_ob_trend, det_fvg_ob

CACHE = Path("data_store/research_cache"); SLIP = 0.01
VPD = {"30min":48,"1h":24,"2h":12,"8h":3,"12h":2,"1D":1}

def stat(v):
    n=len(v); return n,(sum(1 for x in v if x>0)/n if n else 0),(sum(v)/n if n else 0)

def main():
    import sys as _s
    tfs=_s.argv[1:] or ["30min","2h"]
    for tf in tfs:
        print(f"\n===== TEMPORALIDAD {tf} (2021-2026, 3 monedas, NETO) =====")
        agg = {}
        for coin in ["BTC","ETH","SOL"]:
            d15 = pd.read_parquet(CACHE/f"{coin}_15m.parquet")
            d15["dt"]=pd.to_datetime(d15["t"],unit="ms")
            d = d15.set_index("dt").resample(tf).agg({"t":"first","apertura":"first","maximo":"max","minimo":"min","cierre":"last","volumen":"sum"}).dropna().reset_index(drop=True)
            reg = clasificar_regimen(d, dias=90)
            # ajusta velas/dia del clasificador
            na = 90*VPD[tf]; cl=d["cierre"].to_numpy()
            reg = np.full(len(cl),"?",dtype=object)
            if len(cl)>na:
                r = cl[na:]/cl[:-na]-1
                reg[na:] = np.where(r>0.25,"alcista",np.where(r<-0.25,"bajista","lateral"))
            dets = {"ob_trend":det_ob_trend, "fvg_ob":det_fvg_ob, "atr_break":det_atr_break,
                    "atr_break_trend":det_atr_break_trend, "trend_rider":det_trend_rider,
                    "merino":lambda w: det_merino(w,coin), "merinox":det_merinox,
                    "merino_fiel":lambda w: det_merino_fiel(w,coin), "donchian":det_donchian,
                    "mean_rev":det_mean_rev_2R, "rsi2":det_rsi2_rebound, "hybrid":det_hybrid_momo, "turtle55":det_turtle55}
            for j in range(LOOKBACK, len(d)-1):
                w = d.iloc[j-LOOKBACK:j+1].reset_index(drop=True)
                for e,det in dets.items():
                    try: sig=det(w)
                    except Exception: continue
                    if not sig: continue
                    r = salida_fija(d, j, sig["stop"], sig["target"], sig["dir"]=="largo")
                    if r is None: continue
                    agg.setdefault(e,{"all":[],"alcista":[],"lateral":[],"bajista":[]})
                    agg[e]["all"].append(r-SLIP)
                    if reg[j] in agg[e]: agg[e][reg[j]].append(r-SLIP)
            print(f"  [{coin}] hecho ({len(d):,} velas)")
        print(f"  {'estrategia':<16}{'n':>7}{'exp':>9}{'alcista':>10}{'lateral':>10}{'bajista':>10}")
        for e,dd in sorted(agg.items(), key=lambda kv:-stat(kv[1]['all'])[2]):
            n,w,ex = stat(dd["all"])
            cells=[]
            for rg in ["alcista","lateral","bajista"]:
                nn,_,ee = stat(dd[rg])
                cells.append(f"{ee:+.3f}" if nn>=30 else "—")
            print(f"  {e:<16}{n:>7}{ex:>+9.3f}{cells[0]:>10}{cells[1]:>10}{cells[2]:>10}")

if __name__ == "__main__":
    main()
