"""
BARRIDO 5 MINUTOS NATIVO — última casilla del mapa de temporalidades.
Lee {coin}_5m.parquet (2024-26, descargado 2026-07-18). Mismos 13 detectores y coste
que barrido_tf. NETO de costes (cR = COSTE/(D/entry) vía salida_fija + SLIP).
Nota: 2024-26 solamente (el 5m no existe en cache más atrás) — etiquetar resultados como
ventana corta al sintetizar.

Uso:  python -m trading_latino.research.barrido_5m
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd
from pathlib import Path
from trading_latino.research.backtest_largo import (det_trend_rider, det_atr_break, det_atr_break_trend,
    det_merino, det_merinox, det_merino_fiel, det_donchian, det_mean_rev_2R, salida_fija)
from trading_latino.research.protocolo import det_rsi2_rebound, det_hybrid_momo
from trading_latino.research.barrido_tf import det_turtle55
from trading_latino.research.backtest_ganadoras import LOOKBACK, det_ob_trend, det_fvg_ob

CACHE = Path("data_store/research_cache"); SLIP = 0.01
VPD = 288  # velas de 5min por día

def stat(v):
    n = len(v); return n, (sum(1 for x in v if x > 0) / n if n else 0), (sum(v) / n if n else 0)

def main():
    print("\n===== TEMPORALIDAD 5min NATIVA (2024-2026, 3 monedas, NETO) =====")
    agg = {}
    for coin in ["BTC", "ETH", "SOL"]:
        d = pd.read_parquet(CACHE / f"{coin}_5m.parquet").reset_index(drop=True)
        na = 90 * VPD; cl = d["cierre"].to_numpy()
        reg = np.full(len(cl), "?", dtype=object)
        if len(cl) > na:
            r = cl[na:] / cl[:-na] - 1
            reg[na:] = np.where(r > 0.25, "alcista", np.where(r < -0.25, "bajista", "lateral"))
        dets = {"ob_trend": det_ob_trend, "fvg_ob": det_fvg_ob, "atr_break": det_atr_break,
                "atr_break_trend": det_atr_break_trend, "trend_rider": det_trend_rider,
                "merino": lambda w: det_merino(w, coin), "merinox": det_merinox,
                "merino_fiel": lambda w: det_merino_fiel(w, coin), "donchian": det_donchian,
                "mean_rev": det_mean_rev_2R, "rsi2": det_rsi2_rebound, "hybrid": det_hybrid_momo,
                "turtle55": det_turtle55}
        for j in range(LOOKBACK, len(d) - 1):
            w = d.iloc[j - LOOKBACK:j + 1].reset_index(drop=True)
            for e, det in dets.items():
                try: sig = det(w)
                except Exception: continue
                if not sig: continue
                r = salida_fija(d, j, sig["stop"], sig["target"], sig["dir"] == "largo")
                if r is None: continue
                agg.setdefault(e, {"all": [], "alcista": [], "lateral": [], "bajista": []})
                agg[e]["all"].append(r - SLIP)
                if reg[j] in agg[e]: agg[e][reg[j]].append(r - SLIP)
        print(f"  [{coin}] hecho ({len(d):,} velas)")
    print(f"  {'estrategia':<16}{'n':>7}{'exp':>9}{'alcista':>10}{'lateral':>10}{'bajista':>10}")
    for e, dd in sorted(agg.items(), key=lambda kv: -stat(kv[1]['all'])[2]):
        n, w, ex = stat(dd["all"])
        cells = []
        for rg in ["alcista", "lateral", "bajista"]:
            nn, _, ee = stat(dd[rg])
            cells.append(f"{ee:+.3f}" if nn >= 30 else "—")
        print(f"  {e:<16}{n:>7}{ex:>+9.3f}{cells[0]:>10}{cells[1]:>10}{cells[2]:>10}")

if __name__ == "__main__":
    main()
