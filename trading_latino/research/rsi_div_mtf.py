"""
RSI DIVERGENCIA + MULTI-TEMPORALIDAD — petición explícita del dueño (2026-07-19, sesión Sonnet).
Idea: divergencia de RSI en el marco MENOR (timing), confirmada por una "zona de cambio de
tendencia" en el marco MAYOR (RSI extremo o precio estirado del EMA200) = filtro de contexto.
Distinto de los 4 intentos previos de RSI (todos naive, un solo marco) que fallaron: aquí se
exige la confluencia multi-temporal que el dueño identifica como la pieza que faltaba.

Metodología causal: los pivotes (swing high/low) se detectan con fractal de K velas a cada lado —
un pivote en el índice i solo se CONFIRMA (y es usable) en el índice i+K, nunca antes. Sin esto,
sería lookahead (mirar al futuro para saber que un máximo fue el máximo).

Uso:  python -m trading_latino.research.rsi_div_mtf
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd
from pathlib import Path

CACHE = Path("data_store/research_cache"); COSTE = 0.0008; SLIP = 0.01


def rsi(cl, n=14):
    d = np.diff(cl, prepend=cl[0])
    up = np.where(d > 0, d, 0.0); dn = np.where(d < 0, -d, 0.0)
    ru = pd.Series(up).ewm(alpha=1 / n, adjust=False).mean().to_numpy()
    rd = pd.Series(dn).ewm(alpha=1 / n, adjust=False).mean().to_numpy()
    rs = np.divide(ru, rd, out=np.full_like(ru, np.nan), where=rd != 0)
    return 100 - 100 / (1 + rs)


def swings_causales(hi, lo, k=5):
    """Pivotes fractales de K velas. Devuelve listas de (indice_pivote, indice_confirmacion)."""
    n = len(hi); sh = []; sl = []
    for i in range(k, n - k):
        if hi[i] == hi[i - k:i + k + 1].max() and (hi[i - k:i] < hi[i]).all() and (hi[i + 1:i + k + 1] < hi[i]).all():
            sh.append((i, i + k))
        if lo[i] == lo[i - k:i + k + 1].min() and (lo[i - k:i] > lo[i]).all() and (lo[i + 1:i + k + 1] > lo[i]).all():
            sl.append((i, i + k))
    return sh, sl


def construir(tf_bajo="4h", tf_alto="1D", k=5, filtro_mtf=70, target_R=2.0):
    rows = []
    for coin in ["BTC", "ETH", "SOL"]:
        d15 = pd.read_parquet(CACHE / f"{coin}_15m.parquet")
        d15["dt"] = pd.to_datetime(d15["t"], unit="ms")
        db = d15.set_index("dt").resample(tf_bajo).agg(
            {"maximo": "max", "minimo": "min", "cierre": "last"}).dropna().reset_index()
        da = d15.set_index("dt").resample(tf_alto).agg(
            {"maximo": "max", "minimo": "min", "cierre": "last"}).dropna().reset_index()
        hi, lo, cl = db["maximo"].to_numpy(), db["minimo"].to_numpy(), db["cierre"].to_numpy()
        dt_bajo = db["dt"].to_numpy()
        rsi_bajo = rsi(cl)
        rsi_alto = rsi(da["cierre"].to_numpy())
        # RSI del marco mayor, propagado (asof) al marco menor — causal (solo el ultimo cierre alto conocido)
        da_r = pd.DataFrame({"dt": da["dt"], "rsi_alto": rsi_alto})
        rsi_alto_en_bajo = pd.merge_asof(pd.DataFrame({"dt": dt_bajo}), da_r, on="dt", direction="backward")["rsi_alto"].to_numpy()

        sh, sl = swings_causales(hi, lo, k)
        for tipo, swings, rev_largo in [("bajista", sh, False), ("alcista", sl, True)]:
            prev = None
            for i, conf in swings:
                if prev is not None:
                    i0, conf0 = prev
                    precio_actual, precio_prev = (hi[i], hi[i0]) if not rev_largo else (lo[i], lo[i0])
                    rsi_actual, rsi_prev = rsi_bajo[i], rsi_bajo[i0]
                    diverge = (precio_actual > precio_prev and rsi_actual < rsi_prev) if not rev_largo \
                        else (precio_actual < precio_prev and rsi_actual > rsi_prev)
                    if diverge and not np.isnan(rsi_alto_en_bajo[conf]):
                        zona_ok = (rsi_alto_en_bajo[conf] > filtro_mtf) if not rev_largo \
                            else (rsi_alto_en_bajo[conf] < (100 - filtro_mtf))
                        if zona_ok and conf < len(cl) - 2:
                            entry = cl[conf]
                            stop = precio_actual * (1.005 if not rev_largo else 0.995)
                            D = abs(entry - stop)
                            if D > 0 and D / entry < 0.25:
                                tg = entry - target_R * D if not rev_largo else entry + target_R * D
                                cR = COSTE / (D / entry); r = None
                                for kk in range(conf + 1, min(conf + 300, len(cl))):
                                    if rev_largo:
                                        if lo[kk] <= stop: r = -1.0; break
                                        if hi[kk] >= tg: r = target_R; break
                                    else:
                                        if hi[kk] >= stop: r = -1.0; break
                                        if lo[kk] <= tg: r = target_R; break
                                if r is not None:
                                    rows.append((pd.Timestamp(dt_bajo[conf]), coin, tipo, r - cR - SLIP))
                prev = (i, conf)
    return pd.DataFrame(rows, columns=["dt", "coin", "tipo", "r"])


def main():
    rng = np.random.default_rng(51)
    print("RSI DIVERGENCIA + MTF — familia (tf_bajo x filtro_mtf x target):")
    for tf_bajo in ["4h", "1h"]:
        for filtro in [65, 70, 75]:
            for tgt in [1.5, 2.0]:
                df = construir(tf_bajo=tf_bajo, filtro_mtf=filtro, target_R=tgt)
                if len(df) < 20:
                    print(f"  {tf_bajo:<4} filtro>{filtro} tgt{tgt}: n={len(df)} (insuficiente)")
                    continue
                n = len(df); ex = df.r.mean(); w = (df.r > 0).mean() * 100
                print(f"  {tf_bajo:<4} filtro>{filtro} tgt{tgt}: n={n:>4} exp={ex:+.3f}R win={w:.0f}%")

    print("\nDETALLE de la mejor combinación candidata (4h, filtro 70, target 2R):")
    df = construir(tf_bajo="4h", filtro_mtf=70, target_R=2.0)
    if len(df) >= 20:
        df["a"] = df.dt.dt.year
        for a, g in df.groupby("a"):
            print(f"  {a}: {g.r.mean():+.3f} (n={len(g)})")
        sin23 = df[df.a != 2023]
        print(f"  SIN-2023: {sin23.r.mean():+.3f} (n={len(sin23)})")
        print(f"  bajista(corto) {df[df.tipo=='bajista'].r.mean():+.3f} (n={(df.tipo=='bajista').sum()})"
              f" · alcista(largo) {df[df.tipo=='alcista'].r.mean():+.3f} (n={(df.tipo=='alcista').sum()})")
        for coin, g in df.groupby("coin"):
            print(f"  {coin}: {g.r.mean():+.3f} (n={len(g)})")
        df["dia"] = df.dt.dt.date
        dsum = df.groupby("dia").r.mean().values
        bs = [rng.choice(dsum, len(dsum), replace=True).mean() for _ in range(3000)]
        p = 2 * min(np.mean(np.array(bs) <= 0), np.mean(np.array(bs) >= 0))
        print(f"  bootstrap por EPISODIO(dia, n={len(dsum)}): p={p:.3f}")


if __name__ == "__main__":
    main()
