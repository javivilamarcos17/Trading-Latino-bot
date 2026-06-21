"""
Mezcla FUNDAMENTAL + TÉCNICO simple (estructura profesional: fundamental=régimen, técnico=timing).
Puerta fundamental = poca venta a exchanges (on-chain) + sentimiento positivo.
Ayudante técnico básico (uno cada vez). Validado en 2026.

Uso:  python -m trading_latino.research.mix
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import requests

from trading_latino.data.download import cargar

CM = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"


def cm(metric):
    url = f"{CM}?assets=btc&metrics={metric}&frequency=1d&page_size=10000&start_time=2019-01-01"
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
    inflow = cm("FlowInExNtv")
    fjs = requests.get("https://api.alternative.me/fng/?limit=0&format=json", timeout=60).json()
    fng = pd.Series({pd.to_datetime(int(d["timestamp"]), unit="s"): int(d["value"]) for d in fjs["data"]}).sort_index()
    df = pd.DataFrame({"px": px, "inflow": inflow, "fng": fng}).dropna()
    df.index = pd.DatetimeIndex(df.index)
    df = df[df.index >= "2021-01-01"]
    ret = df["px"].pct_change().fillna(0)
    p = df["px"]

    # Puerta FUNDAMENTAL (sin técnico): poca venta + sentimiento
    F = (df["inflow"] < df["inflow"].rolling(30).median()) & (df["fng"] > 50)

    # Ayudantes TÉCNICOS simples
    ema50 = p > p.ewm(span=50, adjust=False).mean()
    ema200 = p > p.ewm(span=200, adjust=False).mean()
    cross = p.ewm(span=10, adjust=False).mean() > p.ewm(span=55, adjust=False).mean()
    delta = p.diff(); ag = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean(); al = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rsi = 100 - 100 / (1 + ag / al.replace(0, np.nan))

    def rep(nombre, senal):
        pos = senal.shift(1).fillna(False).astype(float)
        eq = (1 + ret * pos).cumprod()
        dd = (eq / eq.cummax() - 1).min()
        ins = eq[eq.index.year <= 2025]; out = eq[eq.index.year == 2026]
        rin = ins.iloc[-1] / ins.iloc[0] - 1
        rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
        cagr = (1 + rin) ** (1 / 4.99) - 1
        rr = abs(cagr / dd) if dd < 0 else 0
        print(f"  {nombre:<26}| CAGR {cagr*100:+6.1f}% | 2026 {rout*100:+6.2f}% | DD {dd*100:6.1f}% | C/DD {rr:.2f}")

    print("Fundamental solo, técnico solo, y la MEZCLA (fundamental × técnico):")
    rep("FUND solo (inflow+senti)", F)
    rep("TEC solo (EMA50)", ema50)
    rep("MIX FUND & EMA50", F & ema50)
    rep("MIX FUND & EMA200", F & ema200)
    rep("MIX FUND & cross10/55", F & cross)
    rep("MIX FUND & RSI>50", F & (rsi > 50))
    rep("MIX FUND | EMA50 (cualquiera)", F | ema50)


if __name__ == "__main__":
    main()
