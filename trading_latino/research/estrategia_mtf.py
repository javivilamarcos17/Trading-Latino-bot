"""
OPERATIVA SMC MULTI-TIMEFRAME (implementación de docs/OPERATIVA_SMC_MTF.md), PARAMETRIZADA por
temporalidades para PROBAR en qué marcos vive el edge (más altos o más bajos).

Lógica (largo; espejo corto):
  - En el marco MAYOR (HTF): tendencia alcista (cierre > EMA) y un FVG alcista (zona de liquidez).
  - El precio retrocede y RETESTEA esa zona del HTF.
  - En el marco MENOR (LTF), dentro de la zona: CHoCH/BOS alcista = el cierre ROMPE el último swing
    high del LTF (cambio de carácter) -> ENTRADA larga.
  - Stop bajo la zona; objetivo = múltiplo R.
Sin lookahead (swings confirmados con retraso; entrada en cierre que rompe; resultado hacia delante).
Neto de costes. Desglose por AÑO con 2026 como prueba.

Uso:  python -m trading_latino.research.estrategia_mtf
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from trading_latino.data.download import cargar

COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "LINK", "DOT", "LTC", "DOGE", "BCH", "UNI", "AAVE"]
COMBOS = [("1w", "1d"), ("1d", "4h"), ("1d", "1h"), ("4h", "1h")]
DUR = {"1w": pd.Timedelta(days=7), "1d": pd.Timedelta(days=1),
       "4h": pd.Timedelta(hours=4), "1h": pd.Timedelta(hours=1)}
FRACTAL = 2
EMA_LEN = 100
MIN_GAP = 0.001
COSTE = 0.0007       # taker conservador; con entrada límite (maker) sería menor
R_MULT = 2.0
MAX_LTF = 600        # ventana máxima (en velas LTF) que una zona sigue viva
ANIOS = [2021, 2022, 2023, 2024, 2025, 2026]


def serie(coin, tf):
    d = cargar("binance", coin, tf)
    d = d.copy(); d.index = pd.DatetimeIndex(d["timestamp"]).tz_localize(None)
    return d[d.index >= "2021-01-01"]


def zonas_htf(coin, htf):
    """FVG del marco mayor en su tendencia: lista de (t_form, bot, top, dir)."""
    d = serie(coin, htf)
    if len(d) < 50:
        return []
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    ema = d["cierre"].ewm(span=EMA_LEN, adjust=False).mean().to_numpy()
    t = d.index
    dur = DUR[htf]
    z = []
    for i in range(2, len(cl)):
        # la zona solo se CONOCE cuando la vela HTF i cierra -> t_form = cierre (apertura + duración)
        t_form = t[i] + dur
        if lo[i] > hi[i - 2] and (lo[i] - hi[i - 2]) / cl[i] > MIN_GAP and cl[i] > ema[i]:
            z.append((t_form, hi[i - 2], lo[i], "largo"))
        if hi[i] < lo[i - 2] and (lo[i - 2] - hi[i]) / cl[i] > MIN_GAP and cl[i] < ema[i]:
            z.append((t_form, hi[i], lo[i - 2], "corto"))
    return z


def backtest(coin, htf, ltf):
    zonas = zonas_htf(coin, htf)
    if not zonas:
        return []
    L = serie(coin, ltf)
    if len(L) < 100:
        return []
    hi = L["maximo"].to_numpy(); lo = L["minimo"].to_numpy(); cl = L["cierre"].to_numpy()
    t = L.index.to_numpy()
    w = 2 * FRACTAL + 1
    swh = (pd.Series(hi).rolling(w, center=True).max().to_numpy() == hi)
    swl = (pd.Series(lo).rolling(w, center=True).min().to_numpy() == lo)
    last_sh = pd.Series(np.where(swh, hi, np.nan)).ffill().shift(FRACTAL).to_numpy()
    last_sl = pd.Series(np.where(swl, lo, np.nan)).ffill().shift(FRACTAL).to_numpy()
    n = len(cl)
    regs = []

    for (tf_form, bot, top, direc) in zonas:
        # primer índice LTF posterior a la formación de la zona
        k0 = int(np.searchsorted(t, np.datetime64(tf_form)))
        retesteado = False
        for k in range(k0 + 1, min(k0 + MAX_LTF, n - 1)):
            if direc == "largo":
                if lo[k] <= bot:          # rellenó/atravesó la zona -> inválida
                    if not retesteado and lo[k] >= bot:
                        retesteado = True
                    break
                if lo[k] <= top:          # entró en la zona = retest
                    retesteado = True
                if retesteado and not np.isnan(last_sh[k]) and cl[k] > last_sh[k] and cl[k - 1] <= last_sh[k]:
                    entrada = cl[k]; stop = bot; D = entrada - stop
                    if D <= 0:
                        continue
                    objetivo = entrada + R_MULT * D; res = None
                    for m in range(k + 1, n):
                        if lo[m] <= stop: res = -1.0; break
                        if hi[m] >= objetivo: res = R_MULT; break
                    if res is not None:
                        regs.append((pd.Timestamp(t[k]).year, res - COSTE / (D / entrada)))
                    break
            else:
                if hi[k] >= top:
                    break
                if hi[k] >= bot:
                    retesteado = True
                if retesteado and not np.isnan(last_sl[k]) and cl[k] < last_sl[k] and cl[k - 1] >= last_sl[k]:
                    entrada = cl[k]; stop = top; D = stop - entrada
                    if D <= 0:
                        continue
                    objetivo = entrada - R_MULT * D; res = None
                    for m in range(k + 1, n):
                        if hi[m] >= stop: res = -1.0; break
                        if lo[m] <= objetivo: res = R_MULT; break
                    if res is not None:
                        regs.append((pd.Timestamp(t[k]).year, res - COSTE / (D / entrada)))
                    break
    return regs


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    print(f"Operativa SMC MTF (FVG {{HTF}} + BOS {{LTF}}), objetivo {R_MULT}R, coste {COSTE*100:.3f}%.")
    print("Probando combinaciones de temporalidades (2026 = prueba ciega):\n")
    breakeven = 100 / (1 + R_MULT)
    for htf, ltf in COMBOS:
        todo = []
        for c in COINS:
            todo += backtest(c, htf, ltf)
        if len(todo) < 30:
            print(f"  {htf:>2}->{ltf:<3}: solo {len(todo)} ops"); continue
        df = pd.DataFrame(todo, columns=["anio", "R"])
        rs = df["R"].to_numpy(); win = (rs > 0).mean()
        aa = []
        for y in ANIOS:
            sub = df[df["anio"] == y]
            aa.append(f"{y}:{sub['R'].sum():+.0f}R(n{len(sub)})" if len(sub) else f"{y}:-")
        marca = "  <<<" if rs.mean() > 0 and df[df["anio"] == 2026]["R"].sum() >= 0 else ""
        print(f"  {htf:>2}->{ltf:<3} | ops {len(df):4d} | win {win*100:4.1f}% (azar {breakeven:.0f}%) | "
              f"exp/op {rs.mean():+.3f}R | R tot {rs.sum():+6.0f}{marca}")
        print(f"        {'  '.join(aa)}")


if __name__ == "__main__":
    main()
