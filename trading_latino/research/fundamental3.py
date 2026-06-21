"""
Modelo fundamental REFINADO (craft de verdad):
- RESERVAS de exchange (flujo neto acumulado): si bajan = acumulación institucional = alcista.
- Stablecoins (USDT) creciendo = pólvora seca.
- Sentimiento (F&G) siguiendo.
- Régimen de precio (EMA50) como ancla.
Score continuo -> exposición, con vol-targeting. Validado año a año + hold-out 2026.

Uso:  python -m trading_latino.research.fundamental3
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import requests

from trading_latino.data.download import cargar

CM = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
ANIOS = [2021, 2022, 2023, 2024, 2025, 2026]


def cm(asset, metric):
    url = f"{CM}?assets={asset}&metrics={metric}&frequency=1d&page_size=10000&start_time=2019-01-01"
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
    fin = cm("btc", "FlowInExNtv")
    fout = cm("btc", "FlowOutExNtv")
    usdt = cm("usdt", "SplyCur")
    fjs = requests.get("https://api.alternative.me/fng/?limit=0&format=json", timeout=60).json()
    fng = pd.Series({pd.to_datetime(int(d["timestamp"]), unit="s"): int(d["value"]) for d in fjs["data"]}).sort_index()

    df = pd.DataFrame({"px": px, "fin": fin, "fout": fout, "usdt": usdt, "fng": fng}).dropna()
    df = df[df.index >= "2021-01-01"]
    ret = df["px"].pct_change().fillna(0)

    reservas = (df["fin"] - df["fout"]).cumsum()          # proxy de reservas en exchanges
    acumulacion = (reservas - reservas.shift(30)) < 0      # reservas bajando 30d = acumulación
    stable = df["usdt"] > df["usdt"].rolling(30).mean()    # pólvora seca creciendo
    senti = df["fng"] > 50
    trend = df["px"] > df["px"].ewm(span=50, adjust=False).mean()
    score = acumulacion.astype(int) + stable.astype(int) + senti.astype(int) + trend.astype(int)

    vol = ret.rolling(30).std() * np.sqrt(365)
    vt = (0.50 / vol).clip(upper=1.5)

    def rep(nombre, expo):
        pos = expo.shift(1).fillna(0.0)
        eq = (1 + ret * pos).cumprod()
        dd = (eq / eq.cummax() - 1).min()
        ins = eq[eq.index.year <= 2025]
        rin = ins.iloc[-1] / ins.iloc[0] - 1
        cagr = (1 + rin) ** (1 / 4.99) - 1
        celdas = []
        for y in ANIOS:
            s = eq[eq.index.year == y]
            celdas.append(f"{(s.iloc[-1]/s.iloc[0]-1)*100:+5.0f}" if len(s) > 1 else "  -")
        rr = abs(cagr / dd) if dd < 0 else 0
        print(f"  {nombre:<26}| CAGR {cagr*100:+5.1f}% | DD {dd*100:5.1f}% | C/DD {rr:.2f} | años " + " ".join(celdas))

    print("Refinado (reservas+stablecoins+sentimiento+régimen). Años: " + " ".join(str(y) for y in ANIOS))
    rep("score>=2", (score >= 2).astype(float))
    rep("score>=3", (score >= 3).astype(float))
    rep("score>=2 + vol-target", (score >= 2).astype(float) * vt)
    rep("prop. score/4 + vol-target", (score / 4) * vt)
    rep("score>=2 con leverage 1.5x", (score >= 2).astype(float) * 1.5)


if __name__ == "__main__":
    main()
