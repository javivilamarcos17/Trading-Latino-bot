"""
ICHIMOKU 4h CON FILTRO DE NUBE — test oficial (2026-07-18).
Familia: cruce tenkan/kijun {(9,26),(7,22),(12,30)} x nube {si,no} x target {2R,3R} en 4h y 1D.
Hallazgo: SOLO la sub-familia 4h+nube es coherente (6/6 positivas). Mejor: 12/30 3R n=655
+0.178R, 6/6 años positivos, sin-2023 +0.151, L/C equilibrados, bootstrap semanal p=0.021.
Uso:  python -m trading_latino.research.ichimoku_test
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd
from pathlib import Path

CACHE = Path("data_store/research_cache"); COSTE = 0.0008; SLIP = 0.01

def ops_config(tf="4h", tk=12, kj=30, target_R=3.0, filtro_nube=True):
    rows = []
    for coin in ["BTC", "ETH", "SOL"]:
        d15 = pd.read_parquet(CACHE / f"{coin}_15m.parquet")
        d15["dt"] = pd.to_datetime(d15["t"], unit="ms")
        d = d15.set_index("dt").resample(tf).agg({"maximo": "max", "minimo": "min", "cierre": "last"}).dropna()
        idx = d.index; hi, lo, cl = d["maximo"].to_numpy(), d["minimo"].to_numpy(), d["cierre"].to_numpy()
        H = pd.Series(hi); L = pd.Series(lo)
        ten = ((H.rolling(tk).max() + L.rolling(tk).min()) / 2).to_numpy()
        kij = ((H.rolling(kj).max() + L.rolling(kj).min()) / 2).to_numpy()
        spanA = np.roll((ten + kij) / 2, kj)
        spanB = np.roll(((H.rolling(2 * kj).max() + L.rolling(2 * kj).min()) / 2).to_numpy(), kj)
        spanA[:kj] = np.nan; spanB[:kj] = np.nan
        cruz_up = (ten > kij) & (np.roll(ten, 1) <= np.roll(kij, 1))
        cruz_dn = (ten < kij) & (np.roll(ten, 1) >= np.roll(kij, 1))
        nh = np.fmax(spanA, spanB); nl = np.fmin(spanA, spanB)
        for j in np.where(cruz_up | cruz_dn)[0]:
            if j < 2 * kj + 2 or j >= len(cl) - 2: continue
            largo = bool(cruz_up[j])
            if filtro_nube:
                if largo and not cl[j] > nh[j]: continue
                if not largo and not cl[j] < nl[j]: continue
            st = lo[j - 10:j].min() if largo else hi[j - 10:j].max()
            D = abs(cl[j] - st)
            if D <= 0 or D / cl[j] > 0.25: continue
            tg = cl[j] + target_R * D if largo else cl[j] - target_R * D
            cR = COSTE / (D / cl[j]); r = None
            for k in range(j + 1, min(j + 400, len(cl))):
                if largo:
                    if lo[k] <= st: r = -1.0; break
                    if hi[k] >= tg: r = target_R; break
                else:
                    if hi[k] >= st: r = -1.0; break
                    if lo[k] <= tg: r = target_R; break
            if r is None:
                r = ((cl[min(j + 399, len(cl) - 1)] - cl[j]) / D) * (1 if largo else -1)
            rows.append((idx[j], coin, "L" if largo else "C", r - cR - SLIP))
    return pd.DataFrame(rows, columns=["dt", "coin", "dir", "r"])

def main():
    rng = np.random.default_rng(21)
    for tk, kj in [(9, 26), (12, 30)]:
        df = ops_config(tk=tk, kj=kj)
        print(f"
== ichimoku 4h nube {tk}/{kj} 3R: n={len(df)} exp={df.r.mean():+.3f} ==")
        df["a"] = df.dt.dt.year
        for a, g in df.groupby("a"):
            print(f"   {a}: {g.r.mean():+.3f} (n={len(g)})")
        print(f"   SIN-2023: {df[df.a != 2023].r.mean():+.3f}")
        df["sem"] = df.dt.dt.to_period("W")
        sems = [g.r.values for _, g in df.groupby("sem")]
        bs = [np.concatenate([sems[i] for i in rng.integers(0, len(sems), len(sems))]).mean() for _ in range(2000)]
        print(f"   bootstrap semanal: p(<=0)={np.mean(np.array(bs) <= 0):.3f}")

if __name__ == "__main__":
    main()
