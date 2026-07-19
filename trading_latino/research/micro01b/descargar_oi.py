# -*- coding: utf-8 -*-
"""Descarga OI 5min de data.binance.vision (gratis) para BTC/ETH/SOL -> parquets consolidados.
Ingenieria de datos (autonoma). Deja MICRO-01B data-ready. No ejecuta experimento."""
import sys, io, zipfile, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import requests
import pandas as pd
from pathlib import Path
OUT = Path(r"c:/Users/javiv/Desktop/Trading Jaime Merino/data_store/oi_5m"); OUT.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0"}
S = requests.Session(); S.headers.update(UA)
BASE = "https://data.binance.vision/data/futures/um/daily/metrics"
INICIO = {"BTCUSDT": "2021-01-01", "ETHUSDT": "2022-01-01", "SOLUSDT": "2022-01-01"}
FIN = "2026-07-17"

for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
    dias = pd.date_range(INICIO[sym], FIN, freq="D")
    trozos = []; ok = 0; fail = 0
    for d in dias:
        f = d.strftime("%Y-%m-%d")
        url = f"{BASE}/{sym}/{sym}-metrics-{f}.zip"
        try:
            r = S.get(url, timeout=20)
            if r.status_code != 200: fail += 1; continue
            z = zipfile.ZipFile(io.BytesIO(r.content))
            df = pd.read_csv(z.open(z.namelist()[0]))
            df = df[["create_time", "sum_open_interest", "sum_open_interest_value"]]
            trozos.append(df); ok += 1
        except Exception:
            fail += 1
        if (ok + fail) % 200 == 0:
            print(f"  {sym}: {ok+fail}/{len(dias)} (ok={ok} fail={fail})", flush=True)
        time.sleep(0.02)
    if trozos:
        full = pd.concat(trozos, ignore_index=True)
        full["t"] = pd.to_datetime(full["create_time"]).values.astype("datetime64[ms]").astype("int64")  # ms robusto (pandas2.x)
        full = full[["t", "sum_open_interest", "sum_open_interest_value"]].drop_duplicates("t").sort_values("t")
        full.to_parquet(OUT / f"{sym}_oi_5m.parquet")
        print(f"GUARDADO {sym}: {len(full):,} filas 5min · {pd.to_datetime(full.t.min(),unit='ms'):%Y-%m-%d} a {pd.to_datetime(full.t.max(),unit='ms'):%Y-%m-%d} (fail={fail})", flush=True)
print("DESCARGA OI COMPLETA")
