"""
Divergencias de RSI como confirmación de entrada (BTC diario).
Divergencia alcista = precio baja en N días pero RSI sube (pérdida de fuerza bajista).
Probada: sola, y como confirmación del régimen fundamental. Validado 2026.

Uso:  python -m trading_latino.research.rsidiv
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
    df.index = pd.DatetimeIndex(df.index); df = df[df.index >= "2021-01-01"]
    ret = df["px"].pct_change().fillna(0)
    p = df["px"]

    delta = p.diff(); ag = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean(); al = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rsi = 100 - 100 / (1 + ag / al.replace(0, np.nan))
    N = 14
    div_alcista = (p < p.shift(N)) & (rsi > rsi.shift(N)) & (rsi < 50)   # precio baja, RSI sube, en zona baja
    div_reciente = div_alcista.rolling(7).max().fillna(0).astype(bool)   # hubo divergencia en últimos 7d

    base = ((df["inflow"] < df["inflow"].rolling(30).median()).astype(int)
            + (df["fng"] > 50).astype(int)
            + (p > p.ewm(span=50, adjust=False).mean()).astype(int)) >= 2

    def rep(nombre, senal):
        pos = senal.shift(1).fillna(False).astype(float)
        eq = (1 + ret * pos).cumprod()
        dd = (eq / eq.cummax() - 1).min()
        ins = eq[eq.index.year <= 2025]; out = eq[eq.index.year == 2026]
        rin = ins.iloc[-1] / ins.iloc[0] - 1
        rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
        cagr = (1 + rin) ** (1 / 4.99) - 1
        print(f"  {nombre:<32}| CAGR {cagr*100:+6.1f}% | 2026 {rout*100:+6.2f}% | DD {dd*100:6.1f}% | C/DD {abs(cagr/dd) if dd<0 else 0:.2f} | mcdo {pos.mean()*100:.0f}%")

    print(f"Divergencias RSI ({int(div_alcista.sum())} señales en el periodo):")
    rep("solo divergencia (7d activa)", div_reciente)
    rep("régimen base (2 de 3)", base)
    rep("régimen + confirma divergencia", base & div_reciente)


if __name__ == "__main__":
    main()
