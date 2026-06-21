"""
ESTADÍSTICA PURA DE CÓMO SE MUEVE EL PRECIO. Sin estrategia: medimos la ESTRUCTURA del movimiento
para ver si hay algo explotable o si es eficiente (aleatorio en dirección). "Es pura estadística"
vale en ambos sentidos: si hay memoria, la encontramos; si no, la estadística lo demuestra.

Mide, sobre muchas monedas (1h y 1d):
  1) AUTOCORRELACIÓN de retornos (lags 1..10): ¿los movimientos persisten (momentum, autocorr>0)
     o se deshacen (reversión, autocorr<0)? Y cómo cambia POR AÑO (¿se ha decaído el edge?).
  2) RATIO DE VARIANZA (Lo-MacKinlay): =1 paseo aleatorio, >1 tendencia, <1 reversión.
  3) PERSISTENCIA DEL SIGNO: P(siguiente vela mismo signo) vs 50%.
  4) Retorno CONDICIONAL tras un movimiento GRANDE (decil extremo): ¿momentum o reversión en colas?
  5) ESTACIONALIDAD: retorno medio por HORA (UTC) y por DÍA de la semana, con t-stat.
  6) Prueba decisiva: el mejor edge direccional, ¿supera los COSTES?

Uso:  python -m trading_latino.research.estadistica_precio
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from trading_latino.data.download import cargar

COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "LINK", "DOT", "LTC", "DOGE", "BCH", "UNI", "AAVE"]
COSTE = 0.0007   # ida+vuelta taker+slippage


def serie(coin, tf):
    d = cargar("binance", coin, tf)
    s = pd.Series(d["cierre"].to_numpy(), index=pd.DatetimeIndex(d["timestamp"]).tz_localize(None))
    return s[s.index >= "2021-01-01"]


def ac(r, lag):
    a = r.iloc[lag:].to_numpy(); b = r.iloc[:-lag].to_numpy()
    m = ~(np.isnan(a) | np.isnan(b))
    if m.sum() < 100:
        return np.nan
    return float(np.corrcoef(a[m], b[m])[0, 1])


def var_ratio(r, q):
    r = r.dropna().to_numpy(); n = len(r)
    if n < q * 10:
        return np.nan
    mu = r.mean(); var1 = r.var()
    rq = pd.Series(r).rolling(q).sum().dropna().to_numpy()
    varq = ((rq - q * mu) ** 2).mean()
    return float(varq / (q * var1)) if var1 > 0 else np.nan


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    for tf in ("1h", "1d"):
        print(f"\n================ TIMEFRAME {tf} ================")
        rets = {}
        for c in COINS:
            try:
                rets[c] = np.log(serie(c, tf)).diff()
            except FileNotFoundError:
                continue

        # 1) AUTOCORRELACIÓN media por lag (across monedas)
        print("1) Autocorrelación de retornos (media de todas las monedas):")
        for lag in (1, 2, 3, 5, 10):
            vals = [ac(r, lag) for r in rets.values()]
            vals = [v for v in vals if not np.isnan(v)]
            print(f"   lag {lag:2d}: {np.mean(vals):+.4f}   (signo {'momentum' if np.mean(vals)>0 else 'reversión'})")

        # 1b) lag-1 por AÑO en BTC (¿decae?)
        if "BTC" in rets:
            r = rets["BTC"]
            print("   BTC lag-1 por año:", " ".join(f"{y}:{ac(r[r.index.year==y],1):+.3f}" for y in range(2021, 2027) if (r.index.year == y).sum() > 100))

        # 2) RATIO DE VARIANZA (BTC)
        if "BTC" in rets:
            print("2) Ratio de varianza BTC (=1 aleatorio, >1 tendencia, <1 reversión):")
            print("   " + " ".join(f"q{q}:{var_ratio(rets['BTC'], q):.3f}" for q in (2, 4, 8, 16)))

        # 3) PERSISTENCIA DEL SIGNO (media monedas)
        ps = []
        for r in rets.values():
            s = np.sign(r.dropna().to_numpy())
            same = (s[1:] == s[:-1]).mean()
            ps.append(same)
        print(f"3) P(siguiente vela mismo signo): {np.mean(ps)*100:.2f}%  (50% = sin memoria de signo)")

        # 4) CONDICIONAL tras movimiento GRANDE (decil extremo) — BTC
        if "BTC" in rets:
            r = rets["BTC"].dropna()
            sig = r.shift(1)
            up = r[sig > sig.quantile(0.9)].mean()
            dn = r[sig < sig.quantile(0.1)].mean()
            print(f"4) BTC retorno medio tras vela MUY alcista: {up*100:+.4f}% | tras MUY bajista: {dn*100:+.4f}%")
            print(f"   (si tras alcista sigue + => momentum; si - => reversión)")

        # 5) ESTACIONALIDAD (BTC) — hora (solo 1h) y día de semana
        if "BTC" in rets:
            r = rets["BTC"].dropna()
            if tf == "1h":
                g = r.groupby(r.index.hour)
                m = g.mean(); sd = g.std(); n = g.count(); t = m / (sd / np.sqrt(n))
                mejor = t.abs().idxmax()
                print(f"5) Estacionalidad BTC por hora: mejor |t| en hora {mejor} (t={t[mejor]:+.2f}, ret medio {m[mejor]*100:+.4f}%)")
                sig = t[t.abs() > 3]
                print(f"   horas con |t|>3 (señal real): {list(sig.index) if len(sig) else 'NINGUNA'}")
            g = r.groupby(r.index.dayofweek)
            m = g.mean(); sd = g.std(); n = g.count(); t = m / (sd / np.sqrt(n))
            dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
            print("   por día:", " ".join(f"{dias[d]}:{m[d]*100:+.3f}%(t{t[d]:+.1f})" for d in m.index))

        # 6) PRUEBA DECISIVA: el mejor edge direccional, ¿supera el coste?
        lag1 = np.mean([ac(r, 1) for r in rets.values() if not np.isnan(ac(r, 1))])
        if "BTC" in rets:
            vol = rets["BTC"].std()
            edge_bruto = abs(lag1) * vol     # retorno esperado por operación ~ |autocorr|*sigma
            print(f"6) Edge direccional bruto estimado/op ~{edge_bruto*100:.4f}%  vs COSTE {COSTE*100:.3f}%  -> "
                  f"{'SUPERA' if edge_bruto > COSTE else 'NO supera el coste'}")


if __name__ == "__main__":
    main()
