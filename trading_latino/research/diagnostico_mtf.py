"""
DIAGNÓSTICO de la operativa ganadora (FVG diario + BOS 1H) — buscar DÓNDE FALLA.
Re-corre la lógica con el lookahead corregido y disecciona cada operación:
  - LARGOS vs CORTOS (si solo ganan largos -> sospecha de beta alcista/survivorship).
  - por MONEDA (¿lo sostiene una sola o es general?).
  - por DISTANCIA DE STOP (las de stop pequeño mueren en el muro de coste).
  - DRAWDOWN de la curva en R y RACHA de pérdidas máxima.
  - los peores años/condiciones.

Uso:  python -m trading_latino.research.diagnostico_mtf
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from trading_latino.data.download import cargar

COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "LINK", "DOT", "LTC", "DOGE", "BCH", "UNI", "AAVE"]
HTF, LTF = "1d", "1h"
DUR = {"1d": pd.Timedelta(days=1), "4h": pd.Timedelta(hours=4), "1h": pd.Timedelta(hours=1)}
FRACTAL = 2
EMA_LEN = 100
MIN_GAP = 0.001
COSTE = 0.0007
R_MULT = 2.0
MAX_LTF = 600


def serie(coin, tf):
    d = cargar("binance", coin, tf)
    d = d.copy(); d.index = pd.DatetimeIndex(d["timestamp"]).tz_localize(None)
    return d[d.index >= "2021-01-01"]


def zonas(coin):
    d = serie(coin, HTF)
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    ema = d["cierre"].ewm(span=EMA_LEN, adjust=False).mean().to_numpy()
    t = d.index; dur = DUR[HTF]; z = []
    for i in range(2, len(cl)):
        tf_ = t[i] + dur
        if lo[i] > hi[i - 2] and (lo[i] - hi[i - 2]) / cl[i] > MIN_GAP and cl[i] > ema[i]:
            z.append((tf_, hi[i - 2], lo[i], "largo"))
        if hi[i] < lo[i - 2] and (lo[i - 2] - hi[i]) / cl[i] > MIN_GAP and cl[i] < ema[i]:
            z.append((tf_, hi[i], lo[i - 2], "corto"))
    return z


def backtest(coin):
    L = serie(coin, LTF)
    if len(L) < 100:
        return []
    hi = L["maximo"].to_numpy(); lo = L["minimo"].to_numpy(); cl = L["cierre"].to_numpy()
    t = L.index.to_numpy()
    w = 2 * FRACTAL + 1
    swh = (pd.Series(hi).rolling(w, center=True).max().to_numpy() == hi)
    swl = (pd.Series(lo).rolling(w, center=True).min().to_numpy() == lo)
    last_sh = pd.Series(np.where(swh, hi, np.nan)).ffill().shift(FRACTAL).to_numpy()
    last_sl = pd.Series(np.where(swl, lo, np.nan)).ffill().shift(FRACTAL).to_numpy()
    n = len(cl); regs = []
    for (tf_form, bot, top, direc) in zonas(coin):
        k0 = int(np.searchsorted(t, np.datetime64(tf_form)))
        retest = False
        for k in range(k0 + 1, min(k0 + MAX_LTF, n - 1)):
            if direc == "largo":
                if lo[k] <= bot:
                    break
                if lo[k] <= top:
                    retest = True
                if retest and not np.isnan(last_sh[k]) and cl[k] > last_sh[k] and cl[k - 1] <= last_sh[k]:
                    entrada = cl[k]; stop = bot; D = entrada - stop
                    if D <= 0:
                        continue
                    obj = entrada + R_MULT * D; res = None; dur_v = 0
                    for m in range(k + 1, n):
                        dur_v = m - k
                        if lo[m] <= stop: res = -1.0; break
                        if hi[m] >= obj: res = R_MULT; break
                    if res is not None:
                        regs.append((coin, "largo", pd.Timestamp(t[k]).year, D / entrada, res - COSTE / (D / entrada), dur_v))
                    break
            else:
                if hi[k] >= top:
                    break
                if hi[k] >= bot:
                    retest = True
                if retest and not np.isnan(last_sl[k]) and cl[k] < last_sl[k] and cl[k - 1] >= last_sl[k]:
                    entrada = cl[k]; stop = top; D = stop - entrada
                    if D <= 0:
                        continue
                    obj = entrada - R_MULT * D; res = None; dur_v = 0
                    for m in range(k + 1, n):
                        dur_v = m - k
                        if hi[m] >= stop: res = -1.0; break
                        if lo[m] <= obj: res = R_MULT; break
                    if res is not None:
                        regs.append((coin, "corto", pd.Timestamp(t[k]).year, D / entrada, res - COSTE / (D / entrada), dur_v))
                    break
    return regs


def resumen(et, sub):
    if len(sub) < 20:
        print(f"  {et:<22}| n={len(sub):4d} (pocas)"); return
    r = sub["R"].to_numpy()
    print(f"  {et:<22}| n={len(sub):4d} | win {(r>0).mean()*100:4.1f}% | exp/op {r.mean():+.3f}R | R tot {r.sum():+6.0f}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    todo = []
    for c in COINS:
        todo += backtest(c)
    df = pd.DataFrame(todo, columns=["coin", "dir", "anio", "Dpct", "R", "velas"])
    r = df["R"].to_numpy()
    print(f"=== OPERATIVA {HTF}->{LTF} (lookahead corregido): {len(df)} ops ===")
    print(f"win {(r>0).mean()*100:.1f}% (azar {100/(1+R_MULT):.0f}%) | exp/op {r.mean():+.3f}R | R tot {r.sum():+.0f}\n")

    print("1) LARGOS vs CORTOS (si los cortos NO ganan -> sospecha de beta/survivorship):")
    resumen("largos", df[df["dir"] == "largo"]); resumen("cortos", df[df["dir"] == "corto"])

    print("\n2) POR AÑO (2026 = prueba ciega):")
    for y, g in df.groupby("anio"):
        resumen(str(y), g)

    print("\n3) POR MONEDA (¿lo sostiene una sola?):")
    porc = df.groupby("coin")["R"].agg(["sum", "count", "mean"]).sort_values("sum", ascending=False)
    for c, row in porc.iterrows():
        print(f"  {c:<6}| n={int(row['count']):4d} | exp/op {row['mean']:+.3f}R | R tot {row['sum']:+6.0f}")

    print("\n4) POR DISTANCIA DE STOP (las de stop pequeño = muro de coste):")
    for et, m in [("stop <0.5%", df["Dpct"] < 0.005), ("0.5-1.5%", df["Dpct"].between(0.005, 0.015)), ("1.5-3%", df["Dpct"].between(0.015, 0.03)), (">3%", df["Dpct"] > 0.03)]:
        resumen(et, df[m])

    print("\n5) ROBUSTEZ de la curva:")
    eq = (1 + 0.01 * df.sort_index()["R"]).cumprod()      # arriesgando 1%/op en orden de cierre
    dd = (eq / eq.cummax() - 1).min()
    signos = (df["R"] > 0).astype(int).to_numpy()
    racha = 0; peor = 0
    for s in signos:
        racha = 0 if s == 1 else racha + 1
        peor = max(peor, racha)
    print(f"  drawdown (1%/op) {dd*100:.1f}% | racha de pérdidas máxima {peor} ops | "
          f"ops perdedoras seguidas frecuentes -> exige aguante")


if __name__ == "__main__":
    main()
