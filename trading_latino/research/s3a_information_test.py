# -*- coding: utf-8 -*-
"""S3-A INFORMATION TEST (HYP-S3A-001) — sweep -> acceptance/rejection, development data.
Preregistro congelado: nivel Donchian-20, eps=0.10*ATR14, evento 15m, K=12 barras forward,
outcome = fwd_ret normalizado por ATR en la DIRECCION del sweep. Pregunta: la respuesta
(acceptance/rejection) anade informacion sobre el sweep pooled? NO es estrategia."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd
from pathlib import Path
CACHE = Path(r"c:/Users/javiv/Desktop/Trading Jaime Merino/data_store/research_cache")
N, K = 20, 12; EPS_ATR = 0.10; rng = np.random.default_rng(303)

def atr14(hi, lo, cl):
    tr = np.maximum(hi - lo, np.maximum(abs(hi - np.roll(cl, 1)), abs(lo - np.roll(cl, 1))))
    return pd.Series(tr).ewm(alpha=1/14, adjust=False).mean().to_numpy()

rows = []
for coin in ["BTC", "ETH", "SOL"]:
    d = pd.read_parquet(CACHE / f"{coin}_15m.parquet")
    dt = pd.to_datetime(d["t"], unit="ms")
    hi, lo, cl = d["maximo"].to_numpy(), d["minimo"].to_numpy(), d["cierre"].to_numpy()
    atr = atr14(hi, lo, cl)
    dch_hi = pd.Series(hi).rolling(N).max().shift(1).to_numpy()   # nivel = max de N previas (causal)
    dch_lo = pd.Series(lo).rolling(N).min().shift(1).to_numpy()
    for j in range(N + 15, len(cl) - K):
        if np.isnan(dch_hi[j]) or np.isnan(atr[j]) or atr[j] <= 0: continue
        eps = EPS_ATR * atr[j]
        fwd = (cl[j + K] - cl[j]) / atr[j]
        # UP: high cruza el nivel superior
        if hi[j] > dch_hi[j] + eps:
            estado = "acceptance" if cl[j] >= dch_hi[j] else "rejection"
            rows.append((dt.iloc[j], coin, "up", estado, fwd))         # fwd_dir up-positive
        # DOWN: low cruza el nivel inferior
        if lo[j] < dch_lo[j] - eps:
            estado = "acceptance" if cl[j] <= dch_lo[j] else "rejection"
            rows.append((dt.iloc[j], coin, "dn", estado, -fwd))        # fwd_dir en direccion del sweep
df = pd.DataFrame(rows, columns=["dt", "coin", "lado", "estado", "fwd_dir"])
df["sem"] = df.dt.dt.to_period("W")

def bb(sub, nb=3000):
    sems = [g.fwd_dir.values for _, g in sub.groupby("sem")]
    m = np.array([np.concatenate([sems[i] for i in rng.integers(0, len(sems), len(sems))]).mean() for _ in range(nb)])
    return m

print("S3-A INFORMATION TEST — sweep -> acceptance/rejection (BTC/ETH/SOL 15m 2021-26, development)")
print(f"n eventos sweep total = {len(df)} · outcome = fwd_ret {K}barras normalizado ATR, en direccion del sweep\n")
print("Outcome medio por estado (fwd_dir; >0 = continua en direccion del sweep, <0 = revierte):")
pooled = df.fwd_dir.mean()
print(f"  SWEEP POOLED (benchmark):  n={len(df):>6}  fwd_dir={pooled:+.4f}")
for est in ["acceptance", "rejection"]:
    g = df[df.estado == est]
    m = bb(g); p = 2 * min(np.mean(m <= 0), np.mean(m >= 0))
    print(f"  {est:<12}            n={len(g):>6}  fwd_dir={g.fwd_dir.mean():+.4f}  vs_pooled={g.fwd_dir.mean()-pooled:+.4f}  p_semanal={p:.3f}")

# DELTA INFORMACION: acceptance vs rejection (bloque semanal)
ga = df[df.estado == "acceptance"]; gr = df[df.estado == "rejection"]
da = bb(ga); dr = bb(gr); dif = da - dr
p = 2 * min(np.mean(dif <= 0), np.mean(dif >= 0))
print(f"\n[PRIMARIO] Delta-Info = E[acceptance]-E[rejection] = {ga.fwd_dir.mean()-gr.fwd_dir.mean():+.4f}  p_semanal={p:.3f}")
print("  (si acceptance>>rejection y ambos != pooled -> la RESPUESTA anade informacion sobre el sweep solo)")

# robustez: por moneda y por lado (heterogeneidad)
print("\nHeterogeneidad (acceptance - rejection):")
for coin, g in df.groupby("coin"):
    a = g[g.estado=='acceptance'].fwd_dir.mean(); r = g[g.estado=='rejection'].fwd_dir.mean()
    print(f"  {coin}: acceptance={a:+.4f} rejection={r:+.4f} dif={a-r:+.4f} (n={len(g)})")
for lado, g in df.groupby("lado"):
    a = g[g.estado=='acceptance'].fwd_dir.mean(); r = g[g.estado=='rejection'].fwd_dir.mean()
    print(f"  {lado}: acceptance={a:+.4f} rejection={r:+.4f} dif={a-r:+.4f} (n={len(g)})")

# ¿operable tras costes? magnitud en ATR -> en 15m el coste ~0.08%/ATR%. Solo diagnostico.
print(f"\nDiagnostico de magnitud: |Delta-Info| en ATR = {abs(ga.fwd_dir.mean()-gr.fwd_dir.mean()):.3f}")
print("  (recordatorio: information test, NO estrategia; operabilidad se evalua en S3-B si se PROMUEVE)")
