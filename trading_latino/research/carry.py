"""
Carry de funding diversificado (delta-neutral) sobre un CESTO de perpetuos.
La vía market-neutral: cobrar el funding con el precio cubierto, repartido entre varias
monedas poco correlacionadas en su funding -> más suave y con más capacidad.

Uso:  python -m trading_latino.research.carry
"""

from __future__ import annotations

import sys
import time

import ccxt
import numpy as np
import pandas as pd

SIMBOLOS = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "LINK"]
PERIODOS_ANIO = 3 * 365  # funding cada 8h


def _funding(ex, simbolo):
    sym = f"{simbolo}/USDT:USDT"
    since = ex.parse8601("2021-01-01T00:00:00Z")
    hasta = ex.parse8601("2026-06-21T00:00:00Z")
    filas = []
    while since < hasta:
        lote = ex.fetch_funding_rate_history(sym, since=since, limit=1000)
        if not lote:
            break
        filas += lote
        since = lote[-1]["timestamp"] + 1
        if len(lote) < 1000:
            break
        time.sleep(ex.rateLimit / 1000)
    s = pd.Series({pd.to_datetime(x["timestamp"], unit="ms", utc=True): x["fundingRate"] for x in filas})
    return s[~s.index.duplicated()].sort_index()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    ex = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})
    series = {}
    print("Carry por moneda (delta-neutral, funding bruto anualizado):")
    for s in SIMBOLOS:
        try:
            r = _funding(ex, s).astype(float)
        except Exception as e:
            print(f"  {s}: sin datos ({e})"); continue
        if len(r) < 100:
            continue
        series[s] = r
        print(f"  {s:<5} | {r.mean()*PERIODOS_ANIO*100:+6.2f}%/año | positivo {(r>0).mean()*100:4.1f}% | {len(r)} pagos")

    # Cesta equiponderada: media del funding entre monedas en cada momento
    df = pd.DataFrame(series).sort_index()
    cesta = df.mean(axis=1).dropna()
    acum = np.cumprod(1 + cesta.to_numpy())
    dd = (acum / np.maximum.accumulate(acum) - 1).min()
    print(f"\nCESTA equiponderada ({len(series)} monedas): {cesta.mean()*PERIODOS_ANIO*100:+.2f}%/año bruto | DD {dd*100:.2f}%")
    print("Por año (cesta, suma de funding):")
    for y, g in cesta.groupby(cesta.index.year):
        print(f"  {y}: {g.sum()*100:+6.2f}%")
    print("\nNeto realista (tras comisiones/rebalanceo/capital en 2 patas): ~la mitad-2/3 del bruto.")


if __name__ == "__main__":
    main()
