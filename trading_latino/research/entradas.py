"""
Probar distintos INDICADORES ON-CHAIN de entrada en el sleeve fundamental (régimen "2 de 3").
Se mantiene senti(>50)+tendencia(EMA50) y se cambia la señal on-chain. Validado 2026 + C/DD.

Uso:  python -m trading_latino.research.entradas
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
    fin, fout, addr = cm("FlowInExNtv"), cm("FlowOutExNtv"), cm("AdrActCnt")
    try:
        fees = cm("FeeTotUSD")
    except Exception:
        fees = pd.Series(dtype=float)
    fjs = requests.get("https://api.alternative.me/fng/?limit=0&format=json", timeout=60).json()
    fng = pd.Series({pd.to_datetime(int(d["timestamp"]), unit="s"): int(d["value"]) for d in fjs["data"]}).sort_index()

    cols = {"px": px, "fin": fin, "fout": fout, "addr": addr, "fng": fng}
    if len(fees):
        cols["fees"] = fees
    df = pd.DataFrame(cols).dropna(subset=["px", "fin", "fout", "addr", "fng"])
    df.index = pd.DatetimeIndex(df.index)
    df = df[df.index >= "2021-01-01"]
    ret = df["px"].pct_change().fillna(0)

    senti = (df["fng"] > 50).astype(int)
    trend = (df["px"] > df["px"].ewm(span=50, adjust=False).mean()).astype(int)
    onchain = {
        "inflow<mediana (base)": df["fin"] < df["fin"].rolling(30).median(),
        "inflow cayendo (7d)": df["fin"] < df["fin"].shift(7),
        "flujo neto acumulación": (df["fin"] - df["fout"]).rolling(7).mean() < 0,
        "direcciones creciendo": df["addr"] > df["addr"].shift(30),
    }
    if "fees" in df:
        onchain["comisiones subiendo (red activa)"] = df["fees"] > df["fees"].rolling(30).mean()

    def rep(nombre, oc):
        sig = (oc.astype(int) + senti + trend) >= 2
        pos = sig.shift(1).fillna(False).astype(float)
        eq = (1 + ret * pos).cumprod()
        dd = (eq / eq.cummax() - 1).min()
        ins = eq[eq.index.year <= 2025]; out = eq[eq.index.year == 2026]
        rin = ins.iloc[-1] / ins.iloc[0] - 1
        rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
        cagr = (1 + rin) ** (1 / 4.99) - 1
        print(f"  {nombre:<30}| CAGR {cagr*100:+6.1f}% | 2026 {rout*100:+6.2f}% | DD {dd*100:6.1f}% | C/DD {abs(cagr/dd) if dd<0 else 0:.2f}")

    print("Sleeve fundamental con distinta señal ON-CHAIN de entrada (senti+tendencia fijos):")
    for n, oc in onchain.items():
        rep(n, oc)


if __name__ == "__main__":
    main()
