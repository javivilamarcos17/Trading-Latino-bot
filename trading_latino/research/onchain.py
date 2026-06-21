"""
On-chain (gratis, CoinMetrics) como filtro de régimen sobre BTC, combinado con tendencia.
Señales: flujo NETO a exchanges (entradas-salidas; neto negativo = acumulación = alcista),
inflow bajo, y tendencia de precio (EMA50). Combinaciones para bajar drawdown. Validado 2026.

Uso:  python -m trading_latino.research.onchain
"""

from __future__ import annotations

import sys

import pandas as pd
import requests

BASE = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"


def fetch(metric):
    url = f"{BASE}?assets=btc&metrics={metric}&frequency=1d&page_size=10000&start_time=2020-01-01"
    rows = []
    while url:
        j = requests.get(url, timeout=60).json()
        rows += j.get("data", [])
        url = j.get("next_page_url")
    return pd.Series({pd.Timestamp(r["time"]).tz_localize(None): float(r[metric])
                      for r in rows if r.get(metric) is not None}).sort_index()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    cols = {"px": "PriceUSD", "fin": "FlowInExNtv", "fout": "FlowOutExNtv", "addr": "AdrActCnt"}
    data = {}
    for k, m in cols.items():
        try:
            s = fetch(m)
            if len(s):
                data[k] = s
        except Exception:
            pass
    df = pd.DataFrame(data).dropna()
    df = df[df.index >= "2021-01-01"]
    print(f"On-chain BTC: {df.index[0].date()} -> {df.index[-1].date()} | métricas: {list(df.columns)}")
    ret = df["px"].pct_change().fillna(0)

    def rep(nombre, senal):
        pos = senal.shift(1).fillna(False).astype(float)
        eq = (1 + ret * pos).cumprod()
        dd = (eq / eq.cummax() - 1).min()
        ins = eq[eq.index.year <= 2025]; out = eq[eq.index.year == 2026]
        rin = ins.iloc[-1] / ins.iloc[0] - 1
        rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
        cagr = (1 + rin) ** (1 / 4.99) - 1
        expo = pos.mean() * 100
        print(f"  {nombre:<32}| CAGR {cagr*100:+5.1f}%/a | 2026 {rout*100:+6.2f}% | DD {dd*100:5.1f}% | en mercado {expo:.0f}%")

    tend = df["px"] > df["px"].ewm(span=50, adjust=False).mean()
    inflow_baja = df["fin"] < df["fin"].rolling(30).median()
    rep("buy & hold", pd.Series(True, index=df.index))
    rep("tendencia EMA50", tend)
    rep("inflow bajo", inflow_baja)
    rep("inflow bajo + tendencia", inflow_baja & tend)
    if "fout" in df:
        neto_out = (df["fin"] - df["fout"]) < 0   # más sale que entra = acumulación
        rep("flujo NETO salida (acumul.)", neto_out)
        rep("neto salida + tendencia", neto_out & tend)


if __name__ == "__main__":
    main()
