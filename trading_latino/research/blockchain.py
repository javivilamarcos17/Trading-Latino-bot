"""
Más señales BLOCKCHAIN (info pública e infinita) para mejorar el régimen fundamental:
- reservas de exchange bajando (acumulación), direcciones activas (adopción/uso),
  NVT (valoración vs uso real de la red), inflow bajo. + S&P (risk-on macro) de bonus.
Medimos cada señal sola y añadida a la base, validado en 2026.

Uso:  python -m trading_latino.research.blockchain
"""

from __future__ import annotations

import sys

import pandas as pd
import requests
import yfinance as yf

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
    fin, fout = cm("FlowInExNtv"), cm("FlowOutExNtv")
    addr = cm("AdrActCnt")
    fjs = requests.get("https://api.alternative.me/fng/?limit=0&format=json", timeout=60).json()
    fng = pd.Series({pd.to_datetime(int(d["timestamp"]), unit="s"): int(d["value"]) for d in fjs["data"]}).sort_index()
    try:
        sp = yf.download("^GSPC", start="2020-01-01", progress=False)["Close"].iloc[:, 0]
        sp.index = pd.DatetimeIndex(sp.index).tz_localize(None)
    except Exception:
        sp = pd.Series(dtype=float)

    df = pd.DataFrame({"px": px, "fin": fin, "fout": fout, "addr": addr, "fng": fng})
    if len(sp):
        df["sp"] = sp.reindex(df.index).ffill()
    df = df.dropna(subset=["px", "fin", "fout", "addr", "fng"])
    df = df[df.index >= "2021-01-01"]
    df.index = pd.DatetimeIndex(df.index)
    ret = df["px"].pct_change().fillna(0)

    reservas = (df["fin"] - df["fout"]).cumsum()
    sig = {
        "inflow_bajo": df["fin"] < df["fin"].rolling(30).median(),
        "senti(>50)": df["fng"] > 50,
        "trend(EMA50)": df["px"] > df["px"].ewm(span=50, adjust=False).mean(),
        "reservas_bajando": (reservas - reservas.shift(30)) < 0,
        "addr_creciendo": df["addr"] > df["addr"].rolling(90).mean(),
    }
    if "sp" in df:
        sig["SP_riskon"] = df["sp"] > df["sp"].ewm(span=50, adjust=False).mean()

    def rep(nombre, senal):
        pos = senal.shift(1).fillna(False).astype(float)
        eq = (1 + ret * pos).cumprod()
        dd = (eq / eq.cummax() - 1).min()
        ins = eq[eq.index.year <= 2025]; out = eq[eq.index.year == 2026]
        rin = ins.iloc[-1] / ins.iloc[0] - 1
        rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
        cagr = (1 + rin) ** (1 / 4.99) - 1
        print(f"  {nombre:<22}| CAGR {cagr*100:+6.1f}% | 2026 {rout*100:+6.2f}% | DD {dd*100:6.1f}% | mcdo {pos.mean()*100:.0f}%")

    print("Cada señal blockchain SOLA (largo BTC cuando está activa):")
    for n, s in sig.items():
        rep(n, s)
    base = (sig["inflow_bajo"].astype(int) + sig["senti(>50)"].astype(int) + sig["trend(EMA50)"].astype(int)) >= 2
    print("\nBase (2 de 3) + cada señal nueva como confirmación extra:")
    rep("BASE 2de3", base)
    for n in ["reservas_bajando", "addr_creciendo"] + (["SP_riskon"] if "sp" in df else []):
        rep(f"BASE & {n}", base & sig[n])


if __name__ == "__main__":
    main()
