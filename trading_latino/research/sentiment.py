"""
Señal FUNDAMENTAL/SENTIMIENTO (no técnica): índice Fear & Greed de cripto (alternative.me, gratis).
Hipótesis contraria clásica: comprar con miedo, reducir con codicia. Validado en 2026.

Uso:  python -m trading_latino.research.sentiment
"""

from __future__ import annotations

import sys

import pandas as pd
import requests

from trading_latino.data.download import cargar


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    js = requests.get("https://api.alternative.me/fng/?limit=0&format=json", timeout=60).json()
    fng = pd.Series({pd.to_datetime(int(d["timestamp"]), unit="s"): int(d["value"]) for d in js["data"]}).sort_index()

    btc = cargar("binance", "BTC", "1d")
    px = pd.Series(btc["cierre"].to_numpy(), index=pd.DatetimeIndex(btc["timestamp"]).tz_localize(None))

    df = pd.DataFrame({"px": px, "fng": fng}).dropna()
    df = df[df.index >= "2021-01-01"]
    print(f"Fear&Greed + BTC: {df.index[0].date()} -> {df.index[-1].date()} ({len(df)} días) | F&G actual {df['fng'].iloc[-1]}")
    ret = df["px"].pct_change().fillna(0)

    def rep(nombre, senal):
        pos = senal.shift(1).fillna(False).astype(float)
        eq = (1 + ret * pos).cumprod()
        dd = (eq / eq.cummax() - 1).min()
        ins = eq[eq.index.year <= 2025]; out = eq[eq.index.year == 2026]
        rin = ins.iloc[-1] / ins.iloc[0] - 1
        rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
        cagr = (1 + rin) ** (1 / 4.99) - 1
        print(f"  {nombre:<30}| CAGR {cagr*100:+5.1f}%/a | 2026 {rout*100:+6.2f}% | DD {dd*100:5.1f}% | en mcdo {pos.mean()*100:.0f}%")

    f = df["fng"]
    rep("buy & hold", pd.Series(True, index=df.index))
    rep("comprar con MIEDO (<40)", f < 40)
    rep("comprar con miedo extremo (<25)", f < 25)
    rep("fuera en CODICIA (>75)", f < 75)
    rep("seguir sentimiento (>50)", f > 50)
    rep("zona media (40-75)", (f >= 40) & (f <= 75))


if __name__ == "__main__":
    main()
