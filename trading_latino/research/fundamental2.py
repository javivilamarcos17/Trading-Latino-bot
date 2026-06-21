"""
Pulido del modelo fundamental de posicionamiento:
- añade señal: oferta de stablecoins (USDT) creciendo = liquidez/pólvora seca (alcista).
- añade vol-targeting: escala la exposición a la volatilidad (doma el drawdown sin tocar la señal).
Validado en 2026.  Uso:  python -m trading_latino.research.fundamental2
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import requests

from trading_latino.data.download import cargar

CM = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"


def cm(asset, metric):
    url = f"{CM}?assets={asset}&metrics={metric}&frequency=1d&page_size=10000&start_time=2020-01-01"
    rows = []
    while url:
        j = requests.get(url, timeout=60).json()
        rows += j.get("data", [])
        url = j.get("next_page_url")
    return pd.Series({pd.Timestamp(r["time"]).tz_localize(None): float(r[metric]) for r in rows if r.get(metric)}).sort_index()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    btc = cargar("binance", "BTC", "1d")
    px = pd.Series(btc["cierre"].to_numpy(), index=pd.DatetimeIndex(btc["timestamp"]).tz_localize(None))
    inflow = cm("btc", "FlowInExNtv")
    fjs = requests.get("https://api.alternative.me/fng/?limit=0&format=json", timeout=60).json()
    fng = pd.Series({pd.to_datetime(int(d["timestamp"]), unit="s"): int(d["value"]) for d in fjs["data"]}).sort_index()
    try:
        usdt = cm("usdt", "SplyCur")
    except Exception:
        usdt = pd.Series(dtype=float)
    print(f"USDT supply disponible: {'sí' if len(usdt) else 'NO (sigo sin ella)'}")

    cols = {"px": px, "inflow": inflow, "fng": fng}
    if len(usdt):
        cols["usdt"] = usdt
    df = pd.DataFrame(cols).dropna()
    df = df[df.index >= "2021-01-01"]
    ret = df["px"].pct_change().fillna(0)

    inflow_bajo = df["inflow"] < df["inflow"].rolling(30).median()
    senti = df["fng"] > 50
    tend = df["px"] > df["px"].ewm(span=50, adjust=False).mean()
    señales = [inflow_bajo, senti, tend]
    if "usdt" in df:
        señales.append(df["usdt"] > df["usdt"].rolling(30).mean())   # stablecoins creciendo
    score = sum(s.astype(int) for s in señales)
    N = len(señales)

    vol = ret.rolling(30).std() * np.sqrt(365)
    objetivo = 0.50  # vol objetivo anual

    def rep(nombre, expo):
        pos = expo.shift(1).fillna(0.0)
        eq = (1 + ret * pos).cumprod()
        dd = (eq / eq.cummax() - 1).min()
        ins = eq[eq.index.year <= 2025]; out = eq[eq.index.year == 2026]
        rin = ins.iloc[-1] / ins.iloc[0] - 1
        rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
        cagr = (1 + rin) ** (1 / 4.99) - 1
        rr = abs(cagr / dd) if dd < 0 else 0
        print(f"  {nombre:<32}| CAGR {cagr*100:+6.1f}%/a | 2026 {rout*100:+6.2f}% | DD {dd*100:6.1f}% | C/DD {rr:.2f}")

    print(f"Ensemble de {N} señales fundamentales:")
    base = (score >= 2).astype(float)
    rep(f"score>=2 de {N} (1x)", base)
    rep(f"score>=3 de {N} (1x)", (score >= 3).astype(float))
    # vol-target sobre score>=2
    vt = base * (objetivo / vol).clip(upper=2.0)
    rep("score>=2 + vol-target (cap2x)", vt)
    vt15 = base * (objetivo / vol).clip(upper=1.5)
    rep("score>=2 + vol-target (cap1.5x)", vt15)
    # exposición proporcional al score (más señales = más exposición) + vol-target
    prop = (score / N) * (objetivo / vol).clip(upper=2.0)
    rep("exposición prop. al score + VT", prop)


if __name__ == "__main__":
    main()
