"""
SMC/FVG en MERCADOS TRADICIONALES (forex, oro, índice). ICT/SMC nació en forex, así que probamos
en su terreno. Misma metodología que el estudio de cripto (278k casos): detectar FVG, esperar el
retest, medir reacción a 1,5R contra el umbral aleatorio (40%). Clave: los COSTES aquí son ~10x
menores que en cripto, así que un edge bruto pequeño podría quedar NETO positivo.

Uso:  python -m trading_latino.research.smc_forex
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import yfinance as yf

TICKERS = {"EURUSD=X": 0.00005, "GBPUSD=X": 0.00006, "USDJPY=X": 0.00006,
           "GC=F": 0.0002, "^GSPC": 0.0002}   # ticker -> coste ida+vuelta estimado
OBJETIVO_R = 1.5
RETEST_MAX = 60
BUFFER = 0.0003
MIN_GAP = 0.0004
ANIOS = list(range(2018, 2027))


def reaccion(direccion, entrada, stop, hi, lo, k, n):
    D = (entrada - stop) if direccion == "largo" else (stop - entrada)
    if D <= 0:
        return None
    objetivo = entrada + OBJETIVO_R * D if direccion == "largo" else entrada - OBJETIVO_R * D
    for j in range(k, n):
        if direccion == "largo":
            if lo[j] <= stop: return False
            if hi[j] >= objetivo: return True
        else:
            if hi[j] >= stop: return False
            if lo[j] <= objetivo: return True
    return None


def estudiar(hi, lo, cl, ema, years, coste):
    n = len(cl); regs = []
    for i in range(2, n - 1):
        tend_alcista = cl[i] > ema[i]
        if lo[i] > hi[i - 2] and (lo[i] - hi[i - 2]) / cl[i] > MIN_GAP:
            top = lo[i]; bot = hi[i - 2]
            k = next((x for x in range(i + 1, min(i + 1 + RETEST_MAX, n)) if lo[x] <= top), None)
            if k is not None:
                entrada = top; stop = bot * (1 - BUFFER)
                g = reaccion("largo", entrada, stop, hi, lo, k, n)
                if g is not None:
                    regs.append({"dir": "largo", "gana": g, "anio": years[k], "Dpct": (entrada - stop) / entrada,
                                 "tend": "favor" if tend_alcista else "contra"})
        if hi[i] < lo[i - 2] and (lo[i - 2] - hi[i]) / cl[i] > MIN_GAP:
            bot = hi[i]; top = lo[i - 2]
            k = next((x for x in range(i + 1, min(i + 1 + RETEST_MAX, n)) if hi[x] >= bot), None)
            if k is not None:
                entrada = bot; stop = top * (1 + BUFFER)
                g = reaccion("corto", entrada, stop, hi, lo, k, n)
                if g is not None:
                    regs.append({"dir": "corto", "gana": g, "anio": years[k], "Dpct": (stop - entrada) / entrada,
                                 "tend": "favor" if not tend_alcista else "contra"})
    return regs


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    print(f"FVG en mercados tradicionales (diario). Umbral azar a {OBJETIVO_R}R = {100/(1+OBJETIVO_R):.0f}%\n")
    for tk, coste in TICKERS.items():
        d = yf.download(tk, period="max", interval="1d", progress=False)
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)
        d = d.dropna()
        hi = d["High"].to_numpy(); lo = d["Low"].to_numpy(); cl = d["Close"].to_numpy()
        ema = pd.Series(cl).ewm(span=100, adjust=False).mean().to_numpy()
        years = d.index.year.to_numpy()
        regs = estudiar(hi, lo, cl, ema, years, coste)
        df = pd.DataFrame(regs)
        if df.empty:
            print(f"{tk}: sin FVG"); continue
        win = df["gana"].mean()
        bruto = win * OBJETIVO_R - (1 - win)
        coste_R = (coste / df["Dpct"].clip(lower=0.0003)).mean()
        neto = bruto - coste_R
        rec = "  RENTABLE" if neto > 0 else ""
        print(f"{tk:10}| n={len(df):5d} | reversión {win*100:4.1f}% | bruto {bruto:+.3f}R | "
              f"coste {coste_R:.3f}R | NETO {neto:+.3f}R{rec}")
        fav = df[df["tend"] == "favor"]
        if len(fav) > 50:
            print(f"           a favor de tendencia: {fav['gana'].mean()*100:.1f}% (n={len(fav)})")
        # por año reciente
        wy = df[df["anio"] >= 2018].groupby("anio")["gana"].mean()
        print("           por año: " + " ".join(f"{y}:{v*100:.0f}%" for y, v in wy.items()))


if __name__ == "__main__":
    main()
