"""
FUNDING LAB — ¿el funding rate (dato que guardamos y nunca explotamos) tiene edge histórico?
===========================================================================================
Binance guarda AÑOS de funding (cada 8h). Dos hipótesis con lógica económica:
  1. FUNDING FADE (contrarian): funding extremo positivo = todos largos y pagando por estarlo
     = trade masificado -> corto. Extremo negativo -> largo. (Reversión del posicionamiento.)
  2. FUNDING FILTER sobre trend_rider 4h: ¿evitar entrar CONTRA funding extremo mejora el edge?
Todo NETO de costes (0.08% + slippage). Desglose por año para ver robustez.

Uso:  python -m trading_latino.research.funding_lab
"""
from __future__ import annotations
import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd, ccxt

from trading_latino.research.backtest_largo import det_trend_rider, salida_fija
from trading_latino.research.backtest_ganadoras import COSTE, LOOKBACK, _setup

def bajar_funding(coin, desde_ts):
    """Historial de funding de Binance (cada 8h, 1000/llamada)."""
    ex = ccxt.binance({"options": {"defaultType": "future"}})
    rows, t = [], desde_ts
    while True:
        try:
            fr = ex.fetch_funding_rate_history(f"{coin}/USDT:USDT", since=t, limit=1000)
        except Exception as e:
            print(f"  [funding] err: {e}"); time.sleep(3); continue
        if not fr: break
        rows.extend([(r["timestamp"], r["fundingRate"]) for r in fr])
        nt = fr[-1]["timestamp"] + 1
        if nt <= t: break
        t = nt
        if len(fr) < 1000: break
    f = pd.DataFrame(rows, columns=["t", "funding"]).drop_duplicates("t").sort_values("t")
    return f.reset_index(drop=True)

def bajar_4h(coin, desde_ts):
    ex = ccxt.binance({"options": {"defaultType": "future"}})
    TF = 4*60*60_000; bl, t = [], desde_ts
    while True:
        try: o = ex.fetch_ohlcv(f"{coin}USDT", "4h", since=t, limit=1000)
        except Exception: time.sleep(3); continue
        if not o: break
        bl.extend(o); nt = o[-1][0] + TF
        if nt <= t: break
        t = nt
        if len(o) < 1000: break
    d = pd.DataFrame(bl, columns=["t","apertura","maximo","minimo","cierre","volumen"])
    d["t"] = d["t"].astype("int64")
    return d.drop_duplicates("t").sort_values("t").reset_index(drop=True)

def stat(v):
    n=len(v); return n, (sum(1 for x in v if x>0)/n if n else 0), (sum(v)/n if n else 0)

def main():
    desde = int(pd.Timestamp("2023-01-01", tz="UTC").timestamp()*1000)
    SLIP = 0.006
    print("FUNDING LAB — fade contrarian + filtro sobre trend_rider (4h, 2023->hoy, NETO)\n")
    for coin in ["BTC", "ETH", "SOL"]:
        print(f"=== {coin} ===")
        d = bajar_4h(coin, desde)
        f = bajar_funding(coin, desde)
        if len(d) < 500 or len(f) < 100:
            print("  datos insuficientes"); continue
        # funding alineado a cada vela 4h (el último funding CONOCIDO en esa vela; sin lookahead)
        farr = np.interp(d["t"].to_numpy(), f["t"].to_numpy(), f["funding"].to_numpy())
        # percentiles rolling de 90 días (270 velas 4h) para definir "extremo" SIN lookahead
        fs = pd.Series(farr)
        p90 = fs.rolling(540, min_periods=100).quantile(0.90).to_numpy()
        p10 = fs.rolling(540, min_periods=100).quantile(0.10).to_numpy()
        ts = pd.to_datetime(d["t"], unit="ms")
        cl = d["cierre"].to_numpy(); hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()

        # --- H1: FUNDING FADE ---
        fade = {"con_ano": []}
        pnls_fade = []
        for j in range(LOOKBACK, len(d)-1):
            if np.isnan(p90[j]) or np.isnan(p10[j]): continue
            sig = None
            if farr[j] > p90[j] and farr[j] > 0:      # todos largos pagando -> corto
                st = hi[j-10:j].max()*1.001
                if st > cl[j]: sig = _setup("corto", cl[j], st, 2.0)
            elif farr[j] < p10[j] and farr[j] < 0:    # todos cortos pagando -> largo
                st = lo[j-10:j].min()*0.999
                if st < cl[j]: sig = _setup("largo", cl[j], st, 2.0)
            if not sig: continue
            r = salida_fija(d, j, sig["stop"], sig["target"], sig["dir"]=="largo")
            pnls_fade.append((ts.iloc[j].year, r))
        n,w,ex = stat([p for _,p in pnls_fade])
        print(f"  H1 funding_fade   n={n:<4} win={w*100:.0f}%  NETO={ex-SLIP:+.3f}R", end="")
        for y in sorted({a for a,_ in pnls_fade}):
            vy=[p for a,p in pnls_fade if a==y]
            if len(vy)>=10: print(f"  {y}:{sum(vy)/len(vy)-SLIP:+.2f}({len(vy)})", end="")
        print()

        # --- H2: trend_rider CON vs SIN filtro de funding extremo en contra ---
        base, filt = [], []
        for j in range(LOOKBACK, len(d)-1):
            w4 = d.iloc[j-LOOKBACK:j+1].reset_index(drop=True)
            try: sig = det_trend_rider(w4)
            except Exception: continue
            if not sig: continue
            r = salida_fija(d, j, sig["stop"], sig["target"], sig["dir"]=="largo")
            base.append(r)
            # filtro: no largo si funding ya extremo positivo (masificado); no corto si extremo negativo
            if not np.isnan(p90[j]):
                if sig["dir"] == "largo" and farr[j] > p90[j]: continue
                if sig["dir"] == "corto" and farr[j] < p10[j]: continue
            filt.append(r)
        nb,wb,eb = stat(base); nf,wf,ef = stat(filt)
        print(f"  H2 trend_rider    base n={nb} NETO={eb-SLIP:+.3f}R  ||  +filtro_funding n={nf} NETO={ef-SLIP:+.3f}R  -> {'MEJORA' if ef>eb and nf>=30 else 'no mejora'}")
        print()
    print("H1 = contrarian puro sobre funding extremo. H2 = el funding como FILTRO del momentum robusto.")

if __name__ == "__main__":
    main()
