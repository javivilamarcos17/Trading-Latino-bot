"""
MAPA DE LIQUIDEZ EN VIVO sobre Hyperliquid (DEX). SOLO LECTURA — no envía órdenes, no usa dinero.

Es el cimiento del "sniper de liquidez": leer en tiempo real DÓNDE está la liquidez que el precio
tiende a buscar (el imán) y dónde habría reacción tras barrerla. Dos fuentes:

  1) CLUSTERS DE STOPS (el imán real): máximos/mínimos IGUALES en el histórico reciente. Encima de
     máximos iguales se apilan stops de cortos + órdenes de compra (liquidez "buy-side"); debajo de
     mínimos iguales, stops de largos (liquidez "sell-side"). El precio tiende a ir a barrerlos.
  2) MUROS DEL ORDER-BOOK (vista inmediata): órdenes en reposo grandes cerca del precio.

Más contexto: Open Interest (cuánto apalancamiento hay) y funding (sesgo de posicionamiento).

NO es backtesteable (no hay histórico gratis de book/liquidaciones): este módulo SIRVE PARA OBSERVAR
EN VIVO y, más adelante, paper-tradear señales y medir si el mapa real da edge.

Uso:  python -m trading_latino.live.mapa_liquidez            # snapshot de BTC
      python -m trading_latino.live.mapa_liquidez ETH SOL    # otras monedas
"""

from __future__ import annotations

import sys

import ccxt
import numpy as np
import pandas as pd


def _ex():
    return ccxt.hyperliquid({"enableRateLimit": True})


def _simbolo(moneda: str) -> str:
    return f"{moneda}/USDC:USDC"


def pools_liquidez(velas: pd.DataFrame, fractal: int = 3, tol: float = 0.0015):
    """Detecta zonas de liquidez = clusters de máximos/mínimos IGUALES (swings repetidos).

    Devuelve dos DataFrames (arriba, abajo) con columnas: nivel, toques.
    Más 'toques' = más stops apilados = imán más fuerte.
    """
    hi = velas["maximo"].to_numpy(); lo = velas["minimo"].to_numpy()
    n = len(hi)
    # swings tipo fractal: extremo local en ventana ±fractal
    swh, swl = [], []
    for i in range(fractal, n - fractal):
        if hi[i] == max(hi[i - fractal:i + fractal + 1]):
            swh.append(hi[i])
        if lo[i] == min(lo[i - fractal:i + fractal + 1]):
            swl.append(lo[i])

    def agrupar(niveles):
        niveles = sorted(niveles)
        grupos = []
        for x in niveles:
            if grupos and abs(x - grupos[-1]["c"]) / grupos[-1]["c"] <= tol:
                g = grupos[-1]; g["n"] += 1; g["c"] = (g["c"] * (g["n"] - 1) + x) / g["n"]
            else:
                grupos.append({"c": x, "n": 1})
        return pd.DataFrame(grupos)

    arriba = agrupar(swh); abajo = agrupar(swl)
    return arriba, abajo


def muros_book(ob, mult: float = 3.0):
    """Niveles del order-book con tamaño >> mediana = muros (liquidez en reposo)."""
    bids = pd.DataFrame(ob["bids"], columns=["px", "sz"])
    asks = pd.DataFrame(ob["asks"], columns=["px", "sz"])
    med = pd.concat([bids["sz"], asks["sz"]]).median()
    mb = bids[bids["sz"] > mult * med]; ma = asks[asks["sz"] > mult * med]
    return mb, ma, med


def snapshot(ex, moneda: str):
    sym = _simbolo(moneda)
    ob = ex.fetch_order_book(sym, limit=20)
    mid = (ob["bids"][0][0] + ob["asks"][0][0]) / 2
    velas = pd.DataFrame(ex.fetch_ohlcv(sym, "15m", limit=500),
                         columns=["t", "apertura", "maximo", "minimo", "cierre", "volumen"])
    arriba, abajo = pools_liquidez(velas)
    mb, ma, med = muros_book(ob)
    try:
        oi = ex.fetch_open_interest(sym).get("openInterestAmount")
    except Exception:
        oi = None
    try:
        fr = ex.fetch_funding_rate(sym).get("fundingRate")
    except Exception:
        fr = None

    print(f"\n===== {moneda}  | precio ~{mid:,.1f}  | OI {oi}  | funding {fr*100 if fr is not None else float('nan'):+.4f}%/h =====")

    # Pools de liquidez ARRIBA (imán de compra / stops de cortos) más cercanos
    pa = arriba[arriba["c"] > mid].copy()
    pa["dist%"] = (pa["c"] / mid - 1) * 100
    pa = pa.sort_values("dist%").head(4)
    print("  Liquidez ARRIBA (stops de cortos / objetivo si sube):")
    for _, r in pa.iterrows():
        print(f"    {r['c']:>11,.1f}  (+{r['dist%']:.2f}%)  toques={int(r['n'])}")

    pb = abajo[abajo["c"] < mid].copy()
    pb["dist%"] = (1 - pb["c"] / mid) * 100
    pb = pb.sort_values("dist%").head(4)
    print("  Liquidez ABAJO (stops de largos / objetivo si baja):")
    for _, r in pb.iterrows():
        print(f"    {r['c']:>11,.1f}  (-{r['dist%']:.2f}%)  toques={int(r['n'])}")

    # Muros del book inmediatos
    print(f"  Muros order-book (mediana tamaño {med:.3f}):")
    if len(ma):
        a0 = ma.iloc[0]; print(f"    venta: {a0['px']:>11,.1f} (+{(a0['px']/mid-1)*100:.2f}%) tam {a0['sz']:.2f}")
    if len(mb):
        b0 = mb.iloc[-1]; print(f"    compra: {b0['px']:>11,.1f} (-{(1-b0['px']/mid)*100:.2f}%) tam {b0['sz']:.2f}")

    # Lectura simple: ¿qué imán está más cerca? (tesis "draw on liquidity")
    da = pa["dist%"].min() if len(pa) else np.nan
    db = pb["dist%"].min() if len(pb) else np.nan
    if not np.isnan(da) and not np.isnan(db):
        lado = "ARRIBA" if da < db else "ABAJO"
        print(f"  >> Imán de liquidez más cercano: {lado} ({min(da, db):.2f}%). Tesis: el precio tiende a buscarlo.")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    monedas = sys.argv[1:] or ["BTC"]
    ex = _ex(); ex.load_markets()
    print("MAPA DE LIQUIDEZ EN VIVO — Hyperliquid (solo lectura, sin órdenes)")
    for m in monedas:
        try:
            snapshot(ex, m)
        except Exception as e:
            print(f"  {m}: error ({type(e).__name__}: {e})")


if __name__ == "__main__":
    main()
