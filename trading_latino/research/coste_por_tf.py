"""
¿A partir de qué temporalidad el scalping deja de morir por costes — y aparece (o no) un edge?
Combina las DOS fuerzas en una tabla decisiva, por TF (BTC):
  1) ATR% (movimiento típico) -> tamaño natural del stop -> COSTE-EN-R = coste% / stop%.
  2) Umbral de acierto NETO necesario a 1.5R dado ese coste.
  3) ACIERTO REAL de un scalp representativo (reversión a la media, banda Bollinger 2σ) en esa TF.
  4) Expectativa NETA por operación (taker y maker).

Así se ve si en 5m/15m el acierto real supera el umbral, o si sigue siendo aleatorio + coste.

Uso:  python -m trading_latino.research.coste_por_tf
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd
import ccxt

TFS = ["1m", "3m", "5m", "15m", "30m", "1h"]
TAKER = 0.0007
MAKER = 0.0003
R_OBJ = 1.5
N_BARRAS = 6000


def fetch(ex, tf, n=N_BARRAS):
    ms = ex.parse_timeframe(tf) * 1000
    since = ex.milliseconds() - n * ms
    rows = []
    while since < ex.milliseconds():
        lote = ex.fetch_ohlcv("BTC/USDT:USDT", tf, since=since, limit=1000)
        if not lote:
            break
        rows += lote
        since = lote[-1][0] + ms
        if len(lote) < 1000:
            break
        time.sleep(ex.rateLimit / 1000)
    d = pd.DataFrame(rows, columns=["t", "o", "h", "l", "c", "v"]).drop_duplicates("t")
    return d


def scalp_reversion(d):
    """Bollinger 2σ: mecha fuera de banda + cierre dentro -> reversión. Stop tras mecha, objetivo 1.5R.
    Devuelve lista de (R_bruto, Dpct)."""
    c = d["c"]; ma = c.rolling(20).mean(); sd = c.rolling(20).std()
    up = (ma + 2 * sd).to_numpy(); dn = (ma - 2 * sd).to_numpy()
    h = d["h"].to_numpy(); l = d["l"].to_numpy(); cl = c.to_numpy()
    n = len(cl); trades = []; i = 21
    while i < n - 1:
        largo = l[i] <= dn[i] and cl[i] > dn[i]
        corto = h[i] >= up[i] and cl[i] < up[i]
        if not (largo or corto) or np.isnan(dn[i]):
            i += 1; continue
        if largo:
            entrada = cl[i]; stop = l[i] * 0.999; D = entrada - stop
            obj = entrada + R_OBJ * D
        else:
            entrada = cl[i]; stop = h[i] * 1.001; D = stop - entrada
            obj = entrada - R_OBJ * D
        if D <= 0:
            i += 1; continue
        res = None; j = i + 1
        while j < n:
            if largo:
                if l[j] <= stop: res = -1.0; break
                if h[j] >= obj: res = R_OBJ; break
            else:
                if h[j] >= stop: res = -1.0; break
                if l[j] <= obj: res = R_OBJ; break
            j += 1
        if res is not None:
            trades.append((res, D / entrada))
        i = j + 1
    return trades


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ex = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})
    print(f"BTC scalping por temporalidad (reversión Bollinger, objetivo {R_OBJ}R, ~{N_BARRAS} velas):\n")
    print(f"  {'TF':<5}{'ATR%':>7}{'costeR_tk':>10}{'win_BE':>8}{'win_real':>9}{'ops':>6}{'NETO_tk':>9}{'NETO_mk':>9}  veredicto")
    for tf in TFS:
        d = fetch(ex, tf)
        tr = pd.concat([d["h"] - d["l"], (d["h"] - d["c"].shift()).abs(), (d["l"] - d["c"].shift()).abs()], axis=1).max(axis=1)
        atr = (tr.rolling(14).mean() / d["c"]).median()
        trades = scalp_reversion(d)
        if len(trades) < 30:
            print(f"  {tf:<5}{atr*100:>6.2f}%   pocas ops ({len(trades)})"); continue
        rs = np.array([t[0] for t in trades]); dp = np.array([t[1] for t in trades])
        win = (rs > 0).mean()
        coste_tk = (TAKER / np.clip(dp, 0.0003, None)).mean()
        coste_mk = (MAKER / np.clip(dp, 0.0003, None)).mean()
        be = (1 + coste_tk) / (1 + R_OBJ)                 # win necesario para break-even NETO
        bruto = win * R_OBJ - (1 - win)
        neto_tk = bruto - coste_tk; neto_mk = bruto - coste_mk
        v = "RENTABLE(mk)" if neto_mk > 0 else ("cerca" if neto_mk > -0.05 else "no")
        print(f"  {tf:<5}{atr*100:>6.2f}%{coste_tk:>9.3f}R{be*100:>7.0f}%{win*100:>8.0f}%{len(trades):>6}"
              f"{neto_tk:>+8.3f}R{neto_mk:>+8.3f}R  {v}")
        time.sleep(ex.rateLimit / 1000)

    print("\nLectura: el coste-en-R cae al subir de TF (stops más anchos), pero si win_real ≈ win_BE")
    print("es que NO hay edge: solo cambia cuánto duele el coste, no la ventaja. Lo decisivo es")
    print("si win_real supera de verdad al umbral (win_BE) en 5m/15m.")


if __name__ == "__main__":
    main()
