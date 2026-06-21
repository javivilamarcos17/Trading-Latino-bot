"""
SETUP MULTI-TIMEFRAME + RUPTURA DE ESTRUCTURA (SMC / CHoCH-BOS), tal como lo describió el dueño:

  Tendencia alcista (HTF) -> retroceso en 4H -> el precio hace el MÍNIMO MÁS BAJO y luego ROMPE el
  MÁXIMO ANTERIOR (el swing high que precedió a ese mínimo) = cambio de carácter -> ENTRADA LARGA.
  Stop bajo el mínimo del retroceso; objetivo = múltiplo R. (Y su espejo bajista en tendencia bajista.)

Es continuación de tendencia tras pullback confirmada por ruptura de estructura. Sin lookahead
(swings confirmados con retraso fractal; entrada en cierre que rompe; resultado hacia delante).
Neto de costes, multi-moneda en 4H, win% y expectativa por AÑO (2026 = prueba).

Uso:  python -m trading_latino.research.estructura_mtf
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from trading_latino.data.download import cargar

COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "LINK", "DOT", "LTC", "DOGE", "BCH",
         "UNI", "AAVE", "NEAR", "APT", "SUI", "ARB", "OP", "POL", "TIA"]
TF = "4h"
FRACTAL = 2
TREND_LEN = 200       # EMA larga en 4h ~ tendencia mayor (proxy de "semanal")
COSTE = 0.0007
ANIOS = [2021, 2022, 2023, 2024, 2025, 2026]


def analizar(coin, r_mult):
    try:
        d = cargar("binance", coin, TF)
    except FileNotFoundError:
        return []
    d.index = pd.DatetimeIndex(d["timestamp"]).tz_localize(None)
    d = d[d.index >= "2021-01-01"]
    if len(d) < 300:
        return []
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    ema = d["cierre"].ewm(span=TREND_LEN, adjust=False).mean().to_numpy()
    n = len(cl)
    w = 2 * FRACTAL + 1
    swh = (pd.Series(hi).rolling(w, center=True).max().to_numpy() == hi)
    swl = (pd.Series(lo).rolling(w, center=True).min().to_numpy() == lo)

    regs = []
    in_trade = False
    j = FRACTAL + 1
    # referencias de estructura para LARGO: último swing low (pullback) y el swing high previo
    while j < n - 1:
        # swings CONFIRMADOS hasta el bar j (un swing en t se confirma en t+FRACTAL)
        # buscamos: mínimo más bajo reciente y el máximo que lo precede
        ini = max(FRACTAL, j - 120)
        idx = np.arange(ini, j - FRACTAL)
        if len(idx) < 10:
            j += 1; continue
        lows = idx[swl[ini:j - FRACTAL]]
        highs = idx[swh[ini:j - FRACTAL]]
        if len(lows) == 0 or len(highs) == 0:
            j += 1; continue

        if not in_trade and cl[j] > ema[j]:
            # LARGO: mínimo más bajo del tramo y el máximo anterior a ese mínimo
            ll = lows[np.argmin(lo[lows])]
            highs_prev = highs[highs < ll]
            if len(highs_prev):
                ph = hi[highs_prev[-1]]                 # máximo que precede al mínimo más bajo
                if cl[j] > ph and cl[j - 1] <= ph:      # ROMPE el máximo anterior (BOS alcista)
                    entrada = cl[j]; stop = lo[ll]; D = entrada - stop
                    if D > 0:
                        objetivo = entrada + r_mult * D
                        res = None
                        for t in range(j + 1, n):
                            if lo[t] <= stop: res = -1.0; break
                            if hi[t] >= objetivo: res = r_mult; break
                        if res is not None:
                            regs.append({"coin": coin, "dir": "largo", "R": res - COSTE / (D / entrada),
                                         "anio": int(d.index[j].year)})
                        in_trade = False
        if not in_trade and cl[j] < ema[j]:
            # CORTO (espejo): máximo más alto del tramo y el mínimo anterior a ese máximo
            hh = highs[np.argmax(hi[highs])]
            lows_prev = lows[lows < hh]
            if len(lows_prev):
                pl = lo[lows_prev[-1]]
                if cl[j] < pl and cl[j - 1] >= pl:       # ROMPE el mínimo anterior (BOS bajista)
                    entrada = cl[j]; stop = hi[hh]; D = stop - entrada
                    if D > 0:
                        objetivo = entrada - r_mult * D
                        res = None
                        for t in range(j + 1, n):
                            if hi[t] >= stop: res = -1.0; break
                            if lo[t] <= objetivo: res = r_mult; break
                        if res is not None:
                            regs.append({"coin": coin, "dir": "corto", "R": res - COSTE / (D / entrada),
                                         "anio": int(d.index[j].year)})
        j += 1
    return regs


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    print(f"Setup MTF + ruptura de estructura (BOS/CHoCH) en {TF}, {len(COINS)} monedas. (2026=prueba)\n")
    for r_mult in (1.5, 2.0, 3.0):
        todo = []
        for c in COINS:
            todo += analizar(c, r_mult)
        df = pd.DataFrame(todo)
        if df.empty:
            print(f"  objetivo {r_mult}R: sin operaciones"); continue
        rs = df["R"].to_numpy()
        win = (rs > 0).mean()
        breakeven = 100 / (1 + r_mult)
        aa = []
        for y in ANIOS:
            sub = df[df["anio"] == y]
            aa.append(f"{y}:{(sub['R']>0).mean()*100:.0f}%/{sub['R'].sum():+.0f}R(n{len(sub)})" if len(sub) else f"{y}:-")
        print(f"  objetivo {r_mult}R | ops {len(df):4d} | win {win*100:4.1f}% (azar {breakeven:.0f}%) | "
              f"R neto total {rs.sum():+6.1f} | exp/op {rs.mean():+.3f}R")
        print(f"     por año: {'  '.join(aa)}")


if __name__ == "__main__":
    main()
