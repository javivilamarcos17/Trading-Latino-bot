"""
CARTERA DE EDGES: combina las 3 fuentes que sobrevivieron 2026, poco correlacionadas:
  1) Carry de funding (market-neutral)
  2) Régimen fundamental (on-chain inflow + sentimiento + tendencia) sobre BTC
  3) Momentum transversal (long fuertes / short débiles en alts)
Pesos por risk-parity (inverso a la volatilidad). Validado en 2026.

Uso:  python -m trading_latino.research.cartera_edges
"""

from __future__ import annotations

import sys
import time

import ccxt
import numpy as np
import pandas as pd
import requests

from trading_latino.config import CONFIG
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


def stream_carry():
    ex = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})
    since = ex.parse8601("2021-01-01T00:00:00Z"); filas = []
    while since < ex.parse8601("2026-06-21T00:00:00Z"):
        lote = ex.fetch_funding_rate_history("BTC/USDT:USDT", since=since, limit=1000)
        if not lote:
            break
        filas += lote; since = lote[-1]["timestamp"] + 1
        if len(lote) < 1000:
            break
        time.sleep(ex.rateLimit / 1000)
    s = pd.Series({pd.to_datetime(x["timestamp"], unit="ms").tz_localize(None): x["fundingRate"] for x in filas})
    # neto realista: capital atado en 2 patas (spot+perp) + comisiones -> ~mitad del bruto
    return s.groupby(s.index.normalize()).sum() * 0.5


def stream_fundamental():
    btc = cargar("binance", "BTC", "1d")
    px = pd.Series(btc["cierre"].to_numpy(), index=pd.DatetimeIndex(btc["timestamp"]).tz_localize(None))
    inflow = cm("FlowInExNtv")
    fjs = requests.get("https://api.alternative.me/fng/?limit=0&format=json", timeout=60).json()
    fng = pd.Series({pd.to_datetime(int(d["timestamp"]), unit="s"): int(d["value"]) for d in fjs["data"]}).sort_index()
    df = pd.DataFrame({"px": px, "inflow": inflow, "fng": fng}).dropna()
    ret = df["px"].pct_change().fillna(0)
    sig = ((df["inflow"] < df["inflow"].rolling(30).median()).astype(int)
           + (df["fng"] > 50).astype(int)
           + (df["px"] > df["px"].ewm(span=50, adjust=False).mean()).astype(int)) >= 2
    return ret * sig.shift(1).fillna(False)


def stream_xsection(universo=None):
    universo = universo or (list(CONFIG.altcoins) + ["BTC"])
    cl = {}
    for s in universo:
        try:
            d = cargar("binance", s, "1d")
            cl[s] = pd.Series(d["cierre"].to_numpy(), index=pd.DatetimeIndex(d["timestamp"]).tz_localize(None))
        except Exception:
            pass
    px = pd.DataFrame(cl).sort_index(); ret = px.pct_change()
    mom = px.pct_change(30); K = 4
    pos = pd.DataFrame(0.0, index=px.index, columns=px.columns); ult = None
    for i, f in enumerate(px.index):
        if i < 30:
            continue
        if ult is None or (f - ult).days >= 7:
            m = mom.loc[f].dropna()
            if len(m) >= 2 * K:
                fila = pd.Series(0.0, index=px.columns)
                fila[m.nlargest(K).index] = 1.0 / K; fila[m.nsmallest(K).index] = -1.0 / K
                pos.loc[f] = fila.values; ult = f
            else:
                pos.loc[f] = pos.iloc[i - 1].values
        else:
            pos.loc[f] = pos.iloc[i - 1].values
    pnl = (pos.shift(1).fillna(0.0) * ret).sum(axis=1)
    turnover = (pos - pos.shift(1)).abs().sum(axis=1)
    return pnl - turnover * 0.0012   # coste realista (shortear alts ilíquidas es caro)


def _stats(nombre, r):
    eq = (1 + r.fillna(0)).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    ins = eq[eq.index.year <= 2025]; out = eq[eq.index.year == 2026]
    rin = ins.iloc[-1] / ins.iloc[0] - 1
    rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
    cagr = (1 + rin) ** (1 / 4.99) - 1
    aa = " ".join(f"{(eq[eq.index.year==y].iloc[-1]/eq[eq.index.year==y].iloc[0]-1)*100:+4.0f}" if len(eq[eq.index.year==y]) > 1 else "  -" for y in [2021, 2022, 2023, 2024, 2025, 2026])
    print(f"  {nombre:<16}| CAGR {cagr*100:+6.1f}% | DD {dd*100:6.1f}% | C/DD {abs(cagr/dd) if dd<0 else 0:5.2f} | años {aa}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    viejas = ["ETH", "BNB", "XRP", "ADA", "LTC", "BCH", "DOT", "LINK", "DOGE"]  # existían en 2021
    s = pd.DataFrame({
        "carry": stream_carry(),
        "fundamental": stream_fundamental(),
        "xs_full": stream_xsection(),
        "xs_old": stream_xsection(viejas),
    })
    s = s[s.index >= "2021-01-01"].fillna(0)

    def cartera(cols, lev=1.0):
        sub = s[cols]
        vol = sub.rolling(30).std().replace(0, np.nan)
        w = (1 / vol).div((1 / vol).sum(axis=1), axis=0).fillna(1 / len(cols))
        return (w.shift(1) * sub).sum(axis=1) * lev

    print("Cada edge por separado:")
    for c in ["carry", "fundamental", "xs_full", "xs_old"]:
        _stats(c, s[c])
    print("\nVerificación — ¿depende del transversal (con sesgo de superviviencia)?")
    _stats("núcleo (C+F) 1x", cartera(["carry", "fundamental"], 1))
    _stats("núcleo (C+F) 2x", cartera(["carry", "fundamental"], 2))
    _stats("+xs viejas 2x", cartera(["carry", "fundamental", "xs_old"], 2))
    _stats("+xs full 2x", cartera(["carry", "fundamental", "xs_full"], 2))


if __name__ == "__main__":
    main()
