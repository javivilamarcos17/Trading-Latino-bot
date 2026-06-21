"""
Mejora del candidato: diversificar carry y régimen fundamental en BTC + ETH (los más limpios)
+ vol-targeting a nivel cartera. Comparado con el candidato v1 (solo BTC). Validado 2026.

Uso:  python -m trading_latino.research.cartera_v2
"""

from __future__ import annotations

import sys
import time

import ccxt
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


def carry(ex, sym):
    since = ex.parse8601("2021-01-01T00:00:00Z"); fil = []
    while since < ex.parse8601("2026-06-21T00:00:00Z"):
        lote = ex.fetch_funding_rate_history(f"{sym}/USDT:USDT", since=since, limit=1000)
        if not lote:
            break
        fil += lote; since = lote[-1]["timestamp"] + 1
        if len(lote) < 1000:
            break
        time.sleep(ex.rateLimit / 1000)
    s = pd.Series({pd.to_datetime(x["timestamp"], unit="ms").tz_localize(None): x["fundingRate"] for x in fil})
    return s.groupby(s.index.normalize()).sum() * 0.5


def fundamental(sym, fng):
    d = cargar("binance", sym, "1d")
    px = pd.Series(d["cierre"].to_numpy(), index=pd.DatetimeIndex(d["timestamp"]).tz_localize(None))
    inflow = cm(sym.lower(), "FlowInExNtv")
    df = pd.DataFrame({"px": px, "inflow": inflow, "fng": fng}).dropna()
    ret = df["px"].pct_change().fillna(0)
    sig = ((df["inflow"] < df["inflow"].rolling(30).median()).astype(int)
           + (df["fng"] > 50).astype(int)
           + (df["px"] > df["px"].ewm(span=50, adjust=False).mean()).astype(int)) >= 2
    return ret * sig.shift(1).fillna(False)


def stats(nombre, r):
    eq = (1 + r.fillna(0)).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    ins = eq[eq.index.year <= 2025]
    rin = ins.iloc[-1] / ins.iloc[0] - 1
    cagr = (1 + rin) ** (1 / 4.99) - 1
    aa = " ".join(f"{(eq[eq.index.year==y].iloc[-1]/eq[eq.index.year==y].iloc[0]-1)*100:+4.0f}" if len(eq[eq.index.year==y]) > 1 else "  -" for y in ANIOS)
    print(f"  {nombre:<22}| CAGR {cagr*100:+6.1f}% | DD {dd*100:6.1f}% | C/DD {abs(cagr/dd) if dd<0 else 0:5.2f} | {aa}")


def rp(cols_df):
    vol = cols_df.rolling(30).std().replace(0, np.nan)
    w = (1 / vol).div((1 / vol).sum(axis=1), axis=0).fillna(1 / cols_df.shape[1])
    return (w.shift(1) * cols_df).sum(axis=1)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    ex = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})
    fjs = requests.get("https://api.alternative.me/fng/?limit=0&format=json", timeout=60).json()
    fng = pd.Series({pd.to_datetime(int(d["timestamp"]), unit="s"): int(d["value"]) for d in fjs["data"]}).sort_index()

    s = pd.DataFrame({
        "carry_btc": carry(ex, "BTC"), "carry_eth": carry(ex, "ETH"),
        "fund_btc": fundamental("BTC", fng), "fund_eth": fundamental("ETH", fng),
    })
    s = s[s.index >= "2021-01-01"].fillna(0)

    v1 = rp(s[["carry_btc", "fund_btc"]])                       # candidato v1 (solo BTC)
    carry_sleeve = s[["carry_btc", "carry_eth"]].mean(axis=1)
    fund_sleeve = s[["fund_btc", "fund_eth"]].mean(axis=1)
    v2 = rp(pd.DataFrame({"carry": carry_sleeve, "fund": fund_sleeve}))   # v2 (BTC+ETH)
    # vol-target a nivel cartera (objetivo 12% anual)
    volp = v2.rolling(30).std() * np.sqrt(365)
    v2_vt = v2 * (0.12 / volp).clip(upper=3.0).shift(1).fillna(1.0)

    print("Comparativa (CAGR a 2025, DD, años 21·22·23·24·25·26):")
    stats("v1 BTC 1x", v1)
    stats("v1 BTC 2x", v1 * 2)
    stats("v2 BTC+ETH 1x", v2)
    stats("v2 BTC+ETH 2x", v2 * 2)
    stats("v2 + vol-target", v2_vt)
    stats("v2 + vol-target 2x", v2_vt * 2)


if __name__ == "__main__":
    main()
