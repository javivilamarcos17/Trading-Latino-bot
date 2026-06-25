"""
MERINO MULTI-TEMPORALIDAD — ¿en qué temporalidad funciona de verdad la estrategia de Merino?
============================================================================================
El multi-año solo probaba 15m. Pero en VIVO, Merino era MUCHO mejor en 4h (+0.77R) que en 15m
(~0). Esto prueba det_merino y det_merinox en 15m, 1h y 4h sobre TODO el histórico (2021-now),
con desglose por régimen. Así estudiamos Merino de verdad, en sus temporalidades reales.

Uso:  python -m trading_latino.research.merino_mtf
      python -m trading_latino.research.merino_mtf 1h 4h   (solo esas TF, más rápido)
"""
from __future__ import annotations
import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd, ccxt

from trading_latino.research.backtest_largo import (
    det_merino, det_merinox, det_merino_fiel, clasificar_regimen, salida_fija,
)
from trading_latino.research.backtest_ganadoras import LOOKBACK

TF_MS = {"15m": 15*60_000, "1h": 60*60_000, "4h": 4*60*60_000}
DESDE = "2021-01-01"

def bajar(coin, tf, desde_ts, hasta_ts):
    ex = ccxt.binance({"options": {"defaultType": "future"}})
    paso = TF_MS[tf]; bloques = []; t = desde_ts; n = 0
    while t < hasta_ts:
        o = None
        for intento in range(6):
            try: o = ex.fetch_ohlcv(f"{coin}USDT", tf, since=t, limit=1000); break
            except Exception as e: print(f"    err {n} int{intento}: {e}"); time.sleep(2*(intento+1))
        if not o: break
        bloques.extend(o); t = o[-1][0] + paso; n += 1
        if n % 30 == 0: print(f"    ... {n} bloques ({len(bloques):,})")
    d = pd.DataFrame(bloques, columns=["t","apertura","maximo","minimo","cierre","volumen"])
    d["t"] = d["t"].astype("int64")
    return d.drop_duplicates("t").sort_values("t").reset_index(drop=True)

def _mk(coin):
    return {"merino": lambda d: det_merino(d, coin),
            "merinox": det_merinox,
            "merino_fiel": lambda d: det_merino_fiel(d, coin)}

def stat(v):
    n=len(v); return n, (sum(1 for x in v if x>0)/n if n else 0), (sum(v)/n if n else 0)

def main():
    tfs = [a for a in sys.argv[1:] if a in TF_MS] or ["15m","1h","4h"]
    desde_ts = int(pd.Timestamp(DESDE, tz="UTC").timestamp()*1000)
    hasta_ts = int(pd.Timestamp.now("UTC").timestamp()*1000)
    print(f"MERINO MULTI-TEMPORALIDAD — {tfs} desde {DESDE}. (LB={LOOKBACK} por temporalidad)\n")
    for coin in ["BTC","ETH","SOL"]:
        print("="*66); print(f"  [{coin}]")
        for tf in tfs:
            print(f"  bajando {tf}...")
            d = bajar(coin, tf, desde_ts, hasta_ts)
            if len(d) < 500: print(f"  {tf}: pocos datos"); continue
            reg = clasificar_regimen(d) if tf == "15m" else None  # régimen calibrado para 15m
            dets = _mk(coin)
            res = {k: {"all": [], "alc": [], "lat": [], "baj": []} for k in dets}
            for j in range(LOOKBACK, len(d)-1):
                w = d.iloc[j-LOOKBACK:j+1].reset_index(drop=True)
                for k, det in dets.items():
                    try: sig = det(w)
                    except Exception: continue
                    if not sig: continue
                    r = salida_fija(d, j, sig["stop"], sig["target"], sig["dir"]=="largo")
                    res[k]["all"].append(r)
            ini = pd.to_datetime(int(d['t'].iloc[0]),unit='ms').strftime('%Y-%m')
            print(f"  --- {tf} ({len(d):,} velas, desde {ini}) ---")
            for k in dets:
                n,w,ex = stat(res[k]["all"])
                if n < 20: print(f"    {k:<12} n={n} (pocas)"); continue
                print(f"    {k:<12} n={n:<5} win={w*100:.0f}%  exp={ex:+.3f}R  total={sum(res[k]['all']):+.0f}R")
        print()
    print("CLAVE: comparar el exp/op de Merino entre 15m / 1h / 4h. Su mejor temporalidad es la que vale.")

if __name__ == "__main__":
    main()
