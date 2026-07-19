# -*- coding: utf-8 -*-
"""BACKFILL precio 5m FUTUROS perp USDT (data.binance.vision) BTC/ETH/SOL -> base canonica MICRO-01B.
MISMO venue que el OI (futures um), para no mezclar spot/perp. Ingenieria de datos, no experimento."""
import sys, io, zipfile, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import requests
import pandas as pd
from pathlib import Path
OUT = Path(r"c:/Users/javiv/Desktop/Trading Jaime Merino/data_store/micro01b"); OUT.mkdir(exist_ok=True)
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0"})
BASE = "https://data.binance.vision/data/futures/um/daily/klines"
INICIO = {"BTCUSDT": "2021-01-01", "ETHUSDT": "2022-01-01", "SOLUSDT": "2022-01-01"}
FIN = "2026-07-17"
COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "qv", "count", "tbv", "tbqv", "ig"]

for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
    dias = pd.date_range(INICIO[sym], FIN, freq="D")
    trozos = []; ok = 0; fail = 0
    for d in dias:
        f = d.strftime("%Y-%m-%d")
        url = f"{BASE}/{sym}/5m/{sym}-5m-{f}.zip"
        try:
            r = S.get(url, timeout=20)
            if r.status_code != 200: fail += 1; continue
            z = zipfile.ZipFile(io.BytesIO(r.content))
            raw = pd.read_csv(z.open(z.namelist()[0]), header=None)
            raw.columns = COLS[:raw.shape[1]]
            raw = raw[pd.to_numeric(raw["open_time"], errors="coerce").notna()]  # quita fila de cabecera si la trae
            trozos.append(raw[["open_time", "open", "high", "low", "close", "volume"]]); ok += 1
        except Exception:
            fail += 1
        if (ok + fail) % 300 == 0:
            print(f"  {sym}: {ok+fail}/{len(dias)} (ok={ok} fail={fail})", flush=True)
        time.sleep(0.02)
    if trozos:
        full = pd.concat(trozos, ignore_index=True)
        full = full.rename(columns={"open_time": "t", "open": "apertura", "high": "maximo", "low": "minimo", "close": "cierre", "volume": "volumen"})
        full["t"] = pd.to_numeric(full["t"], errors="coerce")
        for c in ["apertura", "maximo", "minimo", "cierre", "volumen"]:
            full[c] = pd.to_numeric(full[c], errors="coerce")
        full = full.dropna(subset=["t", "cierre"])
        full["t"] = full["t"].astype("int64")
        mx = int(full["t"].max())
        if mx > 10**14:   full["t"] = full["t"] // 1000   # microsegundos -> ms
        elif mx < 10**11: full["t"] = full["t"] * 1000    # segundos -> ms
        full = full.drop_duplicates("t").sort_values("t")
        full.to_parquet(OUT / f"{sym}_price_5m_fut.parquet")
        print(f"GUARDADO {sym}: {len(full):,} velas 5m fut · {pd.to_datetime(full.t.min(),unit='ms'):%Y-%m-%d} a {pd.to_datetime(full.t.max(),unit='ms'):%Y-%m-%d} (fail={fail})", flush=True)
print("BACKFILL PRICE 5m COMPLETO")
