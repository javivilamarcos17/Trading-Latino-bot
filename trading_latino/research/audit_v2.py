"""
Auditoría de la estrategia estrella (v2): buscar fallos de principio a fin.
1) ¿El risk-parity concentra todo en el carry? (pesos reales)
2) Atribución: ¿cuánto del retorno viene de carry vs régimen fundamental?
3) Robustez a lookahead: ¿aguanta con 1 día EXTRA de retraso en las señales?

Uso:  python -m trading_latino.research.audit_v2
"""

from __future__ import annotations

import sys

import ccxt
import numpy as np
import pandas as pd
import requests

from trading_latino.research.cartera_v2 import carry, fundamental


def _cagr(eq):
    ins = eq[eq.index.year <= 2025]
    return (ins.iloc[-1] / ins.iloc[0]) ** (1 / 4.99) - 1


def _dd(eq):
    return (eq / eq.cummax() - 1).min()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    ex = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})
    fjs = requests.get("https://api.alternative.me/fng/?limit=0&format=json", timeout=60).json()
    fng = pd.Series({pd.to_datetime(int(d["timestamp"]), unit="s"): int(d["value"]) for d in fjs["data"]}).sort_index()

    cs = pd.concat([carry(ex, "BTC"), carry(ex, "ETH")], axis=1).mean(axis=1)
    fsleeve = pd.concat([fundamental("BTC", fng), fundamental("ETH", fng)], axis=1).mean(axis=1)
    s = pd.DataFrame({"carry": cs, "fund": fsleeve}).fillna(0)
    s = s[s.index >= "2021-01-01"]

    vol = s.rolling(30).std().replace(0, np.nan)
    w = (1 / vol).div((1 / vol).sum(axis=1), axis=0).fillna(0.5)
    print("== 1) PESOS risk-parity (media) ==")
    print(f"  carry: {w['carry'].mean()*100:.1f}%   |   fund: {w['fund'].mean()*100:.1f}%")
    print(f"  vol diaria media -> carry {s['carry'].std()*100:.3f}%  fund {s['fund'].std()*100:.3f}%")

    print("\n== 2) ATRIBUCIÓN de retorno (contribución a la cartera 1x) ==")
    contrib = w.shift(1) * s
    for c in ["carry", "fund"]:
        eq = (1 + contrib[c].fillna(0)).cumprod()
        print(f"  {c:<6}: CAGR contribución {_cagr(eq)*100:+.1f}%")

    print("\n== 3) ROBUSTEZ A LOOKAHEAD (retraso extra en señales) ==")
    port = (w.shift(1) * s).sum(axis=1)
    port_lag = (w.shift(2) * s).sum(axis=1)
    for nombre, p in [("normal (shift1)", port), ("retraso EXTRA (shift2)", port_lag)]:
        eq = (1 + p.fillna(0)).cumprod()
        print(f"  {nombre:<22}| CAGR {_cagr(eq)*100:+.1f}% | DD {_dd(eq)*100:.1f}%")

    print("\n== 4) POTENCIAR: esquemas de asignación (con vol-target 12%, 2x) ==")

    def vt(p, lev=1.0):
        v = p.rolling(30).std() * np.sqrt(365)
        return p * (0.12 / v).clip(upper=3.0).shift(1).fillna(1.0) * lev

    rp_w = w
    cap_w = pd.DataFrame({"carry": w["carry"].clip(upper=0.6)}); cap_w["fund"] = 1 - cap_w["carry"]
    eq_w = pd.DataFrame({"carry": 0.5, "fund": 0.5}, index=s.index)
    co_w = pd.DataFrame({"carry": 1.0, "fund": 0.0}, index=s.index)
    esquemas = {"risk-parity (actual)": rp_w, "carry cap 60%": cap_w, "50/50": eq_w, "solo carry": co_w}
    for nombre, ww in esquemas.items():
        p = vt((ww.shift(1) * s).sum(axis=1), lev=2.0)
        eq = (1 + p.fillna(0)).cumprod()
        out = eq[eq.index.year == 2026]
        rout = (out.iloc[-1] / out.iloc[0] - 1) if len(out) > 1 else float("nan")
        dd = _dd(eq); cagr = _cagr(eq)
        print(f"  {nombre:<22}| CAGR {cagr*100:+6.1f}% | 2026 {rout*100:+6.2f}% | DD {dd*100:6.1f}% | C/DD {abs(cagr/dd) if dd<0 else 0:.2f}")


if __name__ == "__main__":
    main()
