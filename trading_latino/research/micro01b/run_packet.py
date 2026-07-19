# -*- coding: utf-8 -*-
"""MICRO-01B — EXECUTION PACKET congelado (HYP-MICRO-01B). GUARDADO por gobernanza:
NO corre sin data_store/micro01b/DATA_GATE_PASS.flag Y data_store/micro01b/RUN_APPROVED.flag.
Base canonica: precio 5m FUTUROS + OI 5m FUTUROS (mismo venue). Resample 15m/1h desde 5m.
Pregunta: Delta-log(OI) anade info sobre el futuro CONTROLANDO por el retorno de precio?"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd
from pathlib import Path

BASE = Path(r"c:/Users/javiv/Desktop/Trading Jaime Merino/data_store/micro01b")
OIDIR = Path(r"c:/Users/javiv/Desktop/Trading Jaime Merino/data_store/oi_5m")
# CONFIG CONGELADA
M = 6          # ventana de price_return y Delta-log(OI) (barras)
K = 12         # horizonte forward (barras)
NQ = 5         # quintiles
TFS = {"5m": 5*60*1000, "15m": 15*60*1000, "1h": 60*60*1000}
LAG_CONTROL = 800   # desplazamiento absurdo del OI para el sanity check negativo
rng = np.random.default_rng(101)
SYMS = {"BTC": ("BTCUSDT_price_5m_fut.parquet", "BTCUSDT_oi_5m.parquet"),
        "ETH": ("ETHUSDT_price_5m_fut.parquet", "ETHUSDT_oi_5m.parquet"),
        "SOL": ("SOLUSDT_price_5m_fut.parquet", "SOLUSDT_oi_5m.parquet")}

def guard():
    import hashlib, json
    if not (BASE / "DATA_GATE_PASS.flag").exists():
        print("BLOQUEADO: falta DATA_GATE_PASS.flag (el DATA GATE no ha dado PASS)."); sys.exit(1)
    if not (BASE / "RUN_APPROVED.flag").exists():
        print("BLOQUEADO: falta RUN_APPROVED.flag (el dueno no ha dado RUN_APPROVED=TRUE)."); sys.exit(1)
    # DATA FREEZE: los datos deben coincidir con los hasheados en el gate (reproducibilidad exacta)
    fr = json.load(open(BASE / "DATA_FREEZE.json"))
    for coin, (fp, fo) in SYMS.items():
        for f, d in [(fp, BASE), (fo, OIDIR)]:
            h = hashlib.sha256((d / f).read_bytes()).hexdigest()[:16]
            if fr.get(f) != h:
                print(f"BLOQUEADO: hash de {f} no coincide con DATA_FREEZE.json (dato cambiado tras el gate)."); sys.exit(1)
    print("guard OK: gate PASS + RUN_APPROVED + hashes de datos verificados.")

def atr(hi, lo, cl, n=14):
    tr = np.maximum(hi-lo, np.maximum(abs(hi-np.roll(cl,1)), abs(lo-np.roll(cl,1))))
    return pd.Series(tr).ewm(alpha=1/n, adjust=False).mean().to_numpy()

def cargar(coin, tf_ms):
    fp, fo = SYMS[coin]
    p = pd.read_parquet(BASE/fp).drop_duplicates("t").sort_values("t")
    o = pd.read_parquet(OIDIR/fo).drop_duplicates("t").sort_values("t")[["t","sum_open_interest"]]
    m = pd.merge(p, o, on="t", how="inner")                    # merge exacto 5m (mismo boundary)
    m["grp"] = m.t // tf_ms
    ag = m.groupby("grp").agg(t=("t","first"), maximo=("maximo","max"), minimo=("minimo","min"),
        cierre=("cierre","last"), apertura=("apertura","first"),
        oi_level=("sum_open_interest","last"), n=("t","size"))   # OI_level = ULTIMO snapshot (estado, no flujo)
    esperado = tf_ms // (5*60*1000)
    ag = ag[ag.n >= max(2, esperado*0.5)].reset_index(drop=True)   # NO forward-fill: intervalos incompletos fuera
    return ag

def estimar(coin, tf_ms, lag_oi=0):
    d = cargar(coin, tf_ms)
    cl = d.cierre.to_numpy(); a = atr(d.maximo.to_numpy(), d.minimo.to_numpy(), cl)
    pret = pd.Series(cl).pct_change(M).to_numpy()                # retorno de precio reciente (M barras)
    oi = d.oi_level.to_numpy()
    dloi = pd.Series(np.log(oi)).diff(M).to_numpy()   # PRIMARIA = Delta-log(OI_level) sobre M barras, intra-activo
    if lag_oi: dloi = np.roll(dloi, lag_oi)                     # control negativo: desalinear OI
    fwd = (np.roll(cl, -K) - cl) / a                            # fwd normalizado ATR
    dt = pd.to_datetime(d.t, unit="ms")
    df = pd.DataFrame({"dt": dt, "pret": pret, "dloi": dloi, "fwd": fwd}).dropna()
    df = df.iloc[:-K] if K > 0 else df
    df["coin"] = coin; return df

def efecto_intrabin(df):
    """Efecto de OI CONTROLANDO por precio: dentro de cada quintil de pret, dif fwd (OI-alto - OI-bajo)."""
    df = df.copy(); df["pbin"] = pd.qcut(df.pret, NQ, labels=False, duplicates="drop")
    difs = []
    for b, g in df.groupby("pbin"):
        if len(g) < 50: continue
        oq = pd.qcut(g.dloi, NQ, labels=False, duplicates="drop")
        alto = g.fwd[oq == oq.max()].mean(); bajo = g.fwd[oq == 0].mean()
        difs.append(alto - bajo)
    return np.mean(difs) if difs else np.nan

def main():
    guard()
    print("="*70); print("MICRO-01B — POSITIONING INFORMATION TEST (RUN_APPROVED)"); print("="*70)
    resumen = {}
    for tf in TFS:
        parts = [estimar(c, TFS[tf]) for c in SYMS]
        pool = pd.concat(parts, ignore_index=True)
        eff = efecto_intrabin(pool)
        # bootstrap por bloque semanal (monedas del mismo bloque juntas)
        pool["sem"] = pool.dt.dt.to_period("W")
        sems = [g for _, g in pool.groupby("sem")]
        bs = np.array([efecto_intrabin(pd.concat([sems[i] for i in rng.integers(0,len(sems),len(sems))])) for _ in range(1500)])
        p = 2*min(np.mean(bs<=0), np.mean(bs>=0))
        # control negativo (OI desplazado)
        poolc = pd.concat([estimar(c, TFS[tf], lag_oi=LAG_CONTROL) for c in SYMS], ignore_index=True)
        effc = efecto_intrabin(poolc)
        resumen[tf] = (eff, p, effc)
        print(f"\n[{tf}] efecto intra-precio de OI = {eff:+.4f} ATR (p_sem={p:.3f}) · control desalineado={effc:+.4f} (debe colapsar)")
        for c in SYMS:
            e = efecto_intrabin(estimar(c, TFS[tf])); print(f"     {c}: {e:+.4f}")
        # cuadrantes (interpretacion secundaria)
        pool["pq"]=np.sign(pool.pret); pool["oq"]=np.sign(pool.dloi)
        q = pool.groupby(["pq","oq"]).fwd.mean()
        print(f"     cuadrantes fwd (p_sign,oi_sign): {dict(q.round(3))}")
    # VEREDICTO
    print("\n" + "="*70)
    efs = [resumen[tf][0] for tf in TFS]; ps = [resumen[tf][1] for tf in TFS]
    controles = [abs(resumen[tf][2]) < abs(resumen[tf][0])*0.5 for tf in TFS if not np.isnan(resumen[tf][0])]
    coherente = (np.nanmean(np.sign(efs)) in (1.0,-1.0)) and (min(ps) < 0.10) and all(controles) and abs(np.nanmean(efs))>0.02
    if abs(np.nanmean(efs)) < 0.01 or min(ps) > 0.30:
        v = "KILL — OI no anade informacion sobre price-only"
    elif coherente:
        v = "SUPPORTED INFORMATION — geografia coherente; candidato a FREEZE (ralentizar antes de estrategia)"
    else:
        v = "INCONCLUSIVE — efecto pequeno/inestable o control no colapsa"
    print(f"VEREDICTO MICRO-01B: {v}")
    print(f"  effect medio={np.nanmean(efs):+.4f} ATR · min p_sem={min(ps):.3f} · control colapsa={all(controles)}")
    print("="*70)

if __name__ == "__main__":
    main()
