"""
Modelo de POSICIONAMIENTO fundamental: combina las señales (gratis) que sobrevivieron 2026
- on-chain: flujos a exchanges bajos (poca venta)
- sentimiento: Fear&Greed siguiendo tendencia (>50)
- precio: tendencia EMA50 (control de drawdown)
Largo en BTC según el régimen fundamental. Validado en 2026.

Uso:  python -m trading_latino.research.fundamental
"""

from __future__ import annotations

import sys

import pandas as pd
import requests

from trading_latino.data.download import cargar

CM = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"


def cm(metric):
    url = f"{CM}?assets=btc&metrics={metric}&frequency=1d&page_size=10000&start_time=2020-01-01"
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
    df = df[df.index >= "2021-01-01"]
    ret = df["px"].pct_change().fillna(0)

    inflow_bajo = df["inflow"] < df["inflow"].rolling(30).median()
    senti = df["fng"] > 50
    tend = df["px"] > df["px"].ewm(span=50, adjust=False).mean()

    def rep(nombre, senal):
        pos = senal.shift(1).fillna(False).astype(float)
        eq = (1 + ret * pos).cumprod()
        dd = (eq / eq.cummax() - 1).min()
        ins = eq[eq.index.year <= 2025]; out = eq[eq.index.year == 2026]
        rin = ins.iloc[-1] / ins.iloc[0] - 1
        rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
        cagr = (1 + rin) ** (1 / 4.99) - 1
        # ratio retorno/DD anual
        rr = abs(cagr / dd) if dd < 0 else 0
        print(f"  {nombre:<34}| CAGR {cagr*100:+5.1f}%/a | 2026 {rout*100:+6.2f}% | DD {dd*100:5.1f}% | C/DD {rr:.2f} | mcdo {pos.mean()*100:.0f}%")

    print(f"Datos: {df.index[0].date()} -> {df.index[-1].date()}")
    rep("buy & hold", pd.Series(True, index=df.index))
    rep("inflow bajo + sentimiento", inflow_bajo & senti)
    rep("inflow bajo + tendencia", inflow_bajo & tend)
    rep("sentimiento + tendencia", senti & tend)
    rep("los 3 (inflow+senti+tend)", inflow_bajo & senti & tend)
    rep("2 de 3 (mayoría)", (inflow_bajo.astype(int) + senti.astype(int) + tend.astype(int)) >= 2)

    print("\nExprimiendo '2 de 3' con apalancamiento controlado (ojo: días de -30% pueden liquidar):")
    sig2 = (inflow_bajo.astype(int) + senti.astype(int) + tend.astype(int)) >= 2
    for L in [1.0, 1.5, 2.0, 2.5]:
        pos = sig2.shift(1).fillna(False).astype(float) * L
        eq = (1 + ret * pos).cumprod()
        dd = (eq / eq.cummax() - 1).min()
        ins = eq[eq.index.year <= 2025]; out = eq[eq.index.year == 2026]
        rin = ins.iloc[-1] / ins.iloc[0] - 1
        rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
        cagr = (1 + rin) ** (1 / 4.99) - 1
        print(f"  {L}x | CAGR {cagr*100:+6.1f}%/a | 2026 {rout*100:+6.2f}% | DD {dd*100:6.1f}%")


if __name__ == "__main__":
    main()
