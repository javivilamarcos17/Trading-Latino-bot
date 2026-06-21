"""
ESTUDIO PROFESIONAL: ¿cómo se RELACIONAN los indicadores y las temporalidades, y mejora la
CONFLUENCIA el resultado? En vez de apilar señales sueltas, medimos:

  1) CORRELACIÓN entre señales (¿redundantes o aportan info independiente?).
  2) Partiendo de un DISPARADOR (giro de momentum Squeeze), ¿cómo cambia el ACIERTO según CUÁNTOS
     indicadores coinciden (confluencia 0..5) y si el MARCO MAYOR (diario) está ALINEADO?
  3) Salida bracket 2R, sin lookahead (HTF del día anterior). Multi-moneda.

Si el acierto sube de forma clara con la confluencia y con el alineamiento HTF -> ahí hay método
profesional (combinar), no en la señal suelta. Si no sube -> la confluencia tampoco salva al precio.

Uso:  python -m trading_latino.research.confluencia
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from trading_latino.data.download import cargar

COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "LINK", "DOT", "LTC", "DOGE", "BCH"]
R_MULT = 2.0
COSTE = 0.0008


def _rsi(c, n=14):
    d = c.diff(); up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def _adx(d, n=14):
    h, l, c = d["maximo"], d["minimo"], d["cierre"]
    up = h.diff(); dn = -l.diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=d.index)
    mdm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=d.index)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/n, adjust=False).mean()
    pdi = 100 * pdm.ewm(alpha=1/n, adjust=False).mean() / atr
    mdi = 100 * mdm.ewm(alpha=1/n, adjust=False).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1/n, adjust=False).mean()


def serie(coin, tf):
    d = cargar("binance", coin, tf)
    d.index = pd.DatetimeIndex(d["timestamp"]).tz_localize(None)
    return d[d.index >= "2021-01-01"]


def analizar(coin):
    d = serie(coin, "1h")
    if len(d) < 300:
        return None
    c = d["cierre"]
    ema50 = c.ewm(span=50, adjust=False).mean()
    hh = d["maximo"].rolling(20).max(); ll = d["minimo"].rolling(20).min()
    mom = (c - ((hh + ll) / 2 + c.rolling(20).mean()) / 2)
    rsi = _rsi(c); adx = _adx(d); volma = d["volumen"].rolling(20).mean()

    # marco MAYOR (diario), sin lookahead: usar la tendencia del día ANTERIOR
    dia = serie(coin, "1d")
    dt = (dia["cierre"] > dia["cierre"].ewm(span=50, adjust=False).mean()).astype(int)
    dt.index = pd.DatetimeIndex(dia["timestamp"]).tz_localize(None).normalize()
    dt = dt.shift(1)                                  # día previo
    htf_up = dt.reindex(d.index.normalize()).to_numpy()

    # señales alcistas (1/0)
    s_trend = (c > ema50).astype(int).to_numpy()
    s_rsi = (rsi > 50).astype(int).to_numpy()
    s_adx = (adx > 23).astype(int).to_numpy()
    s_vol = (d["volumen"] > volma).astype(int).to_numpy()
    s_htf = np.nan_to_num(htf_up).astype(int)
    momn = mom.to_numpy(); cl = c.to_numpy()
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); idx = d.index
    n = len(cl)

    filas = []
    for i in range(60, n - 1):
        # DISPARADOR largo: el momentum gira a positivo
        if not (momn[i] > 0 >= momn[i - 1]):
            continue
        conf = s_trend[i] + s_rsi[i] + s_adx[i] + s_vol[i] + s_htf[i]   # 0..5
        entrada = cl[i]; stop = lo[i - 7:i].min(); D = entrada - stop
        if D <= 0:
            continue
        obj = entrada + R_MULT * D; res = None
        for j in range(i + 1, n):
            if lo[j] <= stop: res = -1.0; break
            if hi[j] >= obj: res = R_MULT; break
        if res is None:
            continue
        filas.append({"conf": int(conf), "htf": int(s_htf[i]), "R": res - COSTE / (D / entrada),
                      "trend": s_trend[i], "rsi": s_rsi[i], "adx": s_adx[i], "vol": s_vol[i],
                      "anio": idx[i].year})
    return pd.DataFrame(filas)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    todo = []
    for c in COINS:
        try:
            df = analizar(c)
        except FileNotFoundError:
            continue
        if df is not None and len(df):
            todo.append(df)
    df = pd.concat(todo, ignore_index=True)
    print(f"Disparador = giro de momentum alcista. {len(df)} señales (1h, {len(todo)} monedas).")
    print(f"Umbral azar a {R_MULT}R = 33%.\n")

    print("1) ¿Sube el acierto con la CONFLUENCIA (nº de indicadores que coinciden)?")
    print(f"   {'confluencia':<12}{'n':>7}{'win':>7}{'exp/op':>9}")
    for k in range(0, 6):
        sub = df[df["conf"] == k]
        if len(sub) < 30:
            continue
        print(f"   {k} de 5      {len(sub):>7}{(sub['R']>0).mean()*100:>6.0f}%{sub['R'].mean():>+8.3f}R")

    print("\n2) ¿Ayuda el ALINEAMIENTO con el marco MAYOR (diario)?")
    for et, m in [("HTF alcista (a favor)", df["htf"] == 1), ("HTF bajista (en contra)", df["htf"] == 0)]:
        sub = df[m]
        print(f"   {et:<24} n={len(sub):>6} | win {(sub['R']>0).mean()*100:.0f}% | exp/op {sub['R'].mean():+.3f}R")

    print("\n3) Confluencia ALTA (>=4) + HTF a favor  vs  señal sola débil (<=1):")
    alta = df[(df["conf"] >= 4) & (df["htf"] == 1)]; baja = df[df["conf"] <= 1]
    for et, sub in [("ALTA conf + HTF", alta), ("BAJA conf", baja)]:
        if len(sub) >= 20:
            print(f"   {et:<18} n={len(sub):>6} | win {(sub['R']>0).mean()*100:.0f}% | exp/op {sub['R'].mean():+.3f}R")

    print("\n4) CORRELACIÓN entre señales (¿redundantes o independientes?):")
    cm = df[["trend", "rsi", "adx", "vol", "htf"]].corr()
    print(cm.round(2).to_string())

    print("\n5) Confluencia alta por AÑO (¿se mantiene? 2026 = prueba):")
    for y in [2021, 2022, 2023, 2024, 2025, 2026]:
        sub = alta[alta["anio"] == y]
        if len(sub) >= 10:
            print(f"   {y}: n={len(sub):>4} win {(sub['R']>0).mean()*100:.0f}% exp {sub['R'].mean():+.3f}R")


if __name__ == "__main__":
    main()
