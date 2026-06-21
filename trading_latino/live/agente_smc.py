"""
AGENTE SMC EN VIVO (Hyperliquid) — INTRADÍA, PAPER-TRADING. Solo lectura, sin órdenes, sin dinero.

Ejecuta la operativa validada como LÓGICA (sin pretender que el backtest la dio por buena):
  - Marco MAYOR (HTF, p.ej. 1h): tendencia (cierre>EMA) + FVG (zona de liquidez), solo con velas CERRADAS.
  - Marco MENOR (LTF intradía, p.ej. 5m/15m): cuando el precio retestea la zona del HTF y se produce un
    CHoCH/BOS (el cierre rompe el último swing del LTF) -> SETUP. Entrada, stop bajo la zona, objetivo R.

Cada ejecución ("tick"):
  1) Actualiza las operaciones EN PAPEL abiertas (¿tocaron stop/objetivo?).
  2) Detecta un setup nuevo en la última vela CERRADA del LTF (sin duplicar, sin mirar el futuro).
  3) Registra TODO en disco (entradas, contexto: funding/OI/tendencia) y muestra el track record.

Ejecútalo cada pocos minutos (tarea programada o bucle) y en unos días tendrás una simulación real.

Uso:  python -m trading_latino.live.agente_smc            # BTC ETH SOL, HTF=1h LTF=15m
      python -m trading_latino.live.agente_smc BTC 1h 5m
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import ccxt
import numpy as np
import pandas as pd

REG = Path(__file__).resolve().parents[2] / "data_store" / "paper"
EMA_LEN = 100
FRACTAL = 2
MIN_GAP = 0.0008
R_MULT = 2.0
BUFFER = 0.0005
RETEST_BARS = 80          # cuántas velas LTF atrás miramos el retest de la zona
DUR = {"1d": pd.Timedelta(days=1), "4h": pd.Timedelta(hours=4),
       "1h": pd.Timedelta(hours=1), "15m": pd.Timedelta(minutes=15), "5m": pd.Timedelta(minutes=5)}


def _ex():
    return ccxt.hyperliquid({"enableRateLimit": True})


def velas(ex, coin, tf, limit=500):
    o = ex.fetch_ohlcv(f"{coin}/USDC:USDC", tf, limit=limit)
    d = pd.DataFrame(o, columns=["t", "apertura", "maximo", "minimo", "cierre", "volumen"])
    d.index = pd.to_datetime(d["t"], unit="ms")
    return d


def zonas_htf(ex, coin, htf):
    """FVG del HTF en tendencia, usando solo velas CERRADAS (la última, en formación, se descarta)."""
    d = velas(ex, coin, htf, 300).iloc[:-1]          # descartar vela en formación
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    ema = d["cierre"].ewm(span=EMA_LEN, adjust=False).mean().to_numpy()
    t = d.index; dur = DUR[htf]; z = []
    for i in range(2, len(cl)):
        t_form = t[i] + dur                           # la zona solo se conoce al cerrar la vela i
        if lo[i] > hi[i - 2] and (lo[i] - hi[i - 2]) / cl[i] > MIN_GAP and cl[i] > ema[i]:
            z.append({"t": t_form, "bot": float(hi[i - 2]), "top": float(lo[i]), "dir": "largo"})
        if hi[i] < lo[i - 2] and (lo[i - 2] - hi[i]) / cl[i] > MIN_GAP and cl[i] < ema[i]:
            z.append({"t": t_form, "bot": float(hi[i]), "top": float(lo[i - 2]), "dir": "corto"})
    return z


def detectar(ex, coin, htf, ltf):
    """Mira la última vela CERRADA del LTF: ¿retest de zona HTF + BOS? Devuelve setup o None + contexto."""
    L = velas(ex, coin, ltf, 500)
    cerr = L.iloc[:-1]                                 # solo velas cerradas
    hi = cerr["maximo"].to_numpy(); lo = cerr["minimo"].to_numpy(); cl = cerr["cierre"].to_numpy()
    t = cerr.index
    w = 2 * FRACTAL + 1
    swh = (cerr["maximo"].rolling(w, center=True).max().to_numpy() == hi)
    swl = (cerr["minimo"].rolling(w, center=True).min().to_numpy() == lo)
    last_sh = pd.Series(np.where(swh, hi, np.nan)).ffill().shift(FRACTAL).to_numpy()
    last_sl = pd.Series(np.where(swl, lo, np.nan)).ffill().shift(FRACTAL).to_numpy()
    j = len(cl) - 1                                     # última vela cerrada

    zonas = zonas_htf(ex, coin, htf)
    precio = float(cl[j])
    # funding/OI para contexto
    try:
        fr = ex.fetch_funding_rate(f"{coin}/USDC:USDC").get("fundingRate")
    except Exception:
        fr = None
    try:
        oi = ex.fetch_open_interest(f"{coin}/USDC:USDC").get("openInterestAmount")
    except Exception:
        oi = None
    ctx = {"precio": precio, "funding": fr, "oi": oi, "ts": int(L["t"].iloc[-2])}

    ventana_lo = lo[max(0, j - RETEST_BARS):j + 1]
    ventana_hi = hi[max(0, j - RETEST_BARS):j + 1]
    for z in zonas:
        if z["dir"] == "largo" and z["t"] < t[j]:
            retest = (ventana_lo <= z["top"]).any() and precio > z["bot"]
            bos = (not np.isnan(last_sh[j])) and cl[j] > last_sh[j] and cl[j - 1] <= last_sh[j]
            if retest and bos:
                entrada = precio; stop = z["bot"] * (1 - BUFFER); D = entrada - stop
                if D > 0:
                    return {"dir": "largo", "entry": entrada, "stop": stop,
                            "target": entrada + R_MULT * D, "R": R_MULT,
                            "zona": [z["bot"], z["top"]]}, ctx
        if z["dir"] == "corto" and z["t"] < t[j]:
            retest = (ventana_hi >= z["bot"]).any() and precio < z["top"]
            bos = (not np.isnan(last_sl[j])) and cl[j] < last_sl[j] and cl[j - 1] >= last_sl[j]
            if retest and bos:
                entrada = precio; stop = z["top"] * (1 + BUFFER); D = stop - entrada
                if D > 0:
                    return {"dir": "corto", "entry": entrada, "stop": stop,
                            "target": entrada - R_MULT * D, "R": R_MULT,
                            "zona": [z["bot"], z["top"]]}, ctx
    return None, ctx


def actualizar_abiertas(ops, L):
    hi = L["maximo"].to_numpy(); lo = L["minimo"].to_numpy(); ts = L["t"].to_numpy()
    for o in ops:
        if o["status"] != "abierta":
            continue
        for k in range(len(ts)):
            if ts[k] <= o["ts"]:
                continue
            if o["dir"] == "largo":
                if lo[k] <= o["stop"]: o.update(status="perdida", R_real=-1.0); break
                if hi[k] >= o["target"]: o.update(status="ganada", R_real=o["R"]); break
            else:
                if hi[k] >= o["stop"]: o.update(status="perdida", R_real=-1.0); break
                if lo[k] <= o["target"]: o.update(status="ganada", R_real=o["R"]); break


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    args = sys.argv[1:]
    coins = [args[0]] if args else ["BTC", "ETH", "SOL"]
    htf = args[1] if len(args) > 1 else "1h"
    ltf = args[2] if len(args) > 2 else "15m"
    ex = _ex(); ex.load_markets()
    REG.mkdir(parents=True, exist_ok=True)
    print(f"AGENTE SMC EN VIVO (paper) | HTF {htf} -> LTF {ltf} | {', '.join(coins)}")

    for coin in coins:
        f = REG / f"agente_{coin}_{htf}_{ltf}.json"
        ops = json.loads(f.read_text()) if f.exists() else []
        L = velas(ex, coin, ltf, 500)
        actualizar_abiertas(ops, L)

        setup, ctx = detectar(ex, coin, htf, ltf)
        ya = any(o["ts"] == ctx["ts"] for o in ops)
        if setup and not ya:
            setup.update(status="abierta", ts=ctx["ts"], coin=coin,
                         fecha=str(pd.to_datetime(ctx["ts"], unit="ms")),
                         funding=ctx["funding"], oi=ctx["oi"])
            ops.append(setup)
            print(f"  [{coin}] NUEVO {setup['dir'].upper()} @ {setup['entry']:.4f} | stop {setup['stop']:.4f} "
                  f"| obj {setup['target']:.4f} ({setup['R']}R) | zona {setup['zona']}")
        f.write_text(json.dumps(ops, indent=2))

        cerradas = [o for o in ops if o["status"] in ("ganada", "perdida")]
        abiertas = [o for o in ops if o["status"] == "abierta"]
        linea = f"  [{coin}] precio {ctx['precio']:.4f} | funding {ctx['funding']} | abiertas {len(abiertas)} | cerradas {len(cerradas)}"
        if cerradas:
            rs = [o["R_real"] for o in cerradas]
            linea += f" | win {sum(1 for r in rs if r>0)/len(rs)*100:.0f}% | R tot {sum(rs):+.1f}"
        print(linea)


if __name__ == "__main__":
    main()
