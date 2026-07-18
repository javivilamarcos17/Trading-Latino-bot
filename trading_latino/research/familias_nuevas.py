"""
FAMILIAS NUNCA PROBADAS — Ichimoku, PSAR, Heikin-Ashi, Turtle-55, TTM Squeeze. 4h y 1D,
2021-26, costes CORREGIDOS (nocional->R). Detectores array-based (sin window-slicing, rápido).
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd
from pathlib import Path

CACHE = Path("data_store/research_cache"); COSTE = 0.0008; SLIP_R = 0.01

def sim2R(hi, lo, cl, i, entry, stop, es_largo, maxb=200):
    D = abs(entry - stop)
    if D <= 0 or entry <= 0: return None
    cR = COSTE / (D / entry)
    tgt = entry + 2*D if es_largo else entry - 2*D
    for k in range(i+1, min(i+maxb, len(cl))):
        if es_largo:
            if lo[k] <= stop: return -1 - cR - SLIP_R
            if hi[k] >= tgt: return 2 - cR - SLIP_R
        else:
            if hi[k] >= stop: return -1 - cR - SLIP_R
            if lo[k] <= tgt: return 2 - cR - SLIP_R
    f = min(i+maxb, len(cl)) - 1
    return ((cl[f]-entry) if es_largo else (entry-cl[f]))/D - cR - SLIP_R

def señales(nombre, hi, lo, cl):
    n = len(cl); out = []
    if nombre == "ichimoku":
        tk = (pd.Series(hi).rolling(9).max() + pd.Series(lo).rolling(9).min()).to_numpy()/2
        kj = (pd.Series(hi).rolling(26).max() + pd.Series(lo).rolling(26).min()).to_numpy()/2
        spanA = np.roll((tk+kj)/2, 26); spanB = np.roll((pd.Series(hi).rolling(52).max()+pd.Series(lo).rolling(52).min()).to_numpy()/2, 26)
        for i in range(80, n-1):
            nube_hi = max(spanA[i], spanB[i]); nube_lo = min(spanA[i], spanB[i])
            if tk[i] > kj[i] and tk[i-1] <= kj[i-1] and cl[i] > nube_hi:
                out.append((i, "L", lo[max(0,i-10):i].min()))
            if tk[i] < kj[i] and tk[i-1] >= kj[i-1] and cl[i] < nube_lo:
                out.append((i, "S", hi[max(0,i-10):i].max()))
    elif nombre == "turtle55":
        for i in range(60, n-1):
            if cl[i] > hi[i-55:i].max(): out.append((i, "L", lo[i-10:i].min()))
            if cl[i] < lo[i-55:i].min(): out.append((i, "S", hi[i-10:i].max()))
    elif nombre == "heikin3":
        ha_c = (0.0 + cl); ha_o = np.copy(cl)  # aprox HA
        ha_c = (hi + lo + cl + np.roll(cl,1))/4
        ha_o = (np.roll(ha_c,1) + np.roll(ha_o,1))/2
        verde = ha_c > ha_o
        for i in range(15, n-1):
            if verde[i] and verde[i-1] and verde[i-2] and not verde[i-3]:
                out.append((i, "L", lo[i-5:i].min()))
            if (not verde[i]) and (not verde[i-1]) and (not verde[i-2]) and verde[i-3]:
                out.append((i, "S", hi[i-5:i].max()))
    elif nombre == "psar":
        af0, afmax = 0.02, 0.2
        sar = lo[0]; ep = hi[0]; af = af0; alcista = True
        for i in range(2, n-1):
            sar = sar + af*(ep - sar)
            if alcista:
                if lo[i] < sar:
                    alcista = False; out.append((i, "S", ep)); sar = ep; ep = lo[i]; af = af0
                elif hi[i] > ep: ep = hi[i]; af = min(afmax, af+af0)
            else:
                if hi[i] > sar:
                    alcista = True; out.append((i, "L", ep)); sar = ep; ep = hi[i]; af = af0
                elif lo[i] < ep: ep = lo[i]; af = min(afmax, af+af0)
    elif nombre == "ttm_squeeze":
        c = pd.Series(cl)
        bb_m = c.rolling(20).mean(); bb_sd = c.rolling(20).std()
        tr = np.maximum(hi[1:]-lo[1:], np.maximum(abs(hi[1:]-cl[:-1]), abs(lo[1:]-cl[:-1])))
        atr = pd.Series(np.concatenate([[hi[0]-lo[0]], tr])).rolling(20).mean()
        dentro = ((bb_m + 2*bb_sd) < (bb_m + 1.5*atr)) & ((bb_m - 2*bb_sd) > (bb_m - 1.5*atr))
        dentro = dentro.to_numpy()
        for i in range(30, n-1):
            if dentro[i-6:i].all() and not dentro[i]:
                if cl[i] > (bb_m + 2*bb_sd).iloc[i]: out.append((i, "L", lo[i-8:i].min()))
                elif cl[i] < (bb_m - 2*bb_sd).iloc[i]: out.append((i, "S", hi[i-8:i].max()))
    return out

def main():
    print("FAMILIAS NUEVAS (jamás probadas) — 4h y 1D, 2021-26, NETO corregido\n")
    for tf in ["4h", "1D"]:
        print(f"===== {tf} =====")
        agg = {}
        for coin in ["BTC", "ETH", "SOL"]:
            d15 = pd.read_parquet(CACHE/f"{coin}_15m.parquet"); d15["dt"] = pd.to_datetime(d15["t"], unit="ms")
            d = d15.set_index("dt").resample(tf).agg({"maximo":"max","minimo":"min","cierre":"last"}).dropna().reset_index(drop=True)
            hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
            for fam in ["ichimoku", "turtle55", "heikin3", "psar", "ttm_squeeze"]:
                for i, dr, stop in señales(fam, hi, lo, cl):
                    r = sim2R(hi, lo, cl, i, cl[i], stop, dr == "L")
                    if r is not None and abs(r) < 20:
                        agg.setdefault(fam, []).append(r)
        for fam, v in sorted(agg.items(), key=lambda kv: -np.mean(kv[1])):
            n = len(v); win = sum(1 for x in v if x > 0)/n
            print(f"  {fam:<13} n={n:<5} win={win*100:.0f}%  exp={np.mean(v):+.3f}R")
        print()

if __name__ == "__main__":
    main()
