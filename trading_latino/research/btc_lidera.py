"""
¿LIDERA BTC a las alts? (lead-lag). Idea del dueño: operar una alt usando BTC de REFERENCIA.
Si el movimiento PASADO de BTC predice el de la alt (BTC se mueve primero, la alt reacciona después),
eso es explotable — a diferencia de la estructura de precio, que es eficiente.

Mide, por temporalidad (1h, 4h, 1d) y promediando alts:
  1) CORRELACIÓN CRUZADA: corr(retorno alt en t, retorno BTC en t-lag) para lag 0,1,2.
     lag0 = beta contemporánea (no explotable). lag>=1 POSITIVO = BTC lidera = explotable.
  2) ESTRATEGIA: largo la alt la barra siguiente a una subida fuerte de BTC (y corto tras bajada),
     neto de costes, por año con 2026 de prueba. ¿Supera el coste / el azar?

Uso:  python -m trading_latino.research.btc_lidera
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from trading_latino.data.download import cargar

ALTS = ["ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "LINK", "DOT", "LTC", "DOGE", "BCH", "UNI", "AAVE", "NEAR"]
COSTE = 0.0007
ANIOS = [2021, 2022, 2023, 2024, 2025, 2026]


def ret(coin, tf):
    d = cargar("binance", coin, tf)
    s = pd.Series(d["cierre"].to_numpy(), index=pd.DatetimeIndex(d["timestamp"]).tz_localize(None))
    return s[s.index >= "2021-01-01"].pct_change()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    for tf in ("1h", "4h", "1d"):
        print(f"\n================ {tf} ================")
        btc = ret("BTC", tf)
        alts = {a: ret(a, tf) for a in ALTS}

        # 1) correlación cruzada media
        print("1) Correlación cruzada corr(alt[t], BTC[t-lag]) — media de alts:")
        for lag in (0, 1, 2):
            cc = []
            for a, r in alts.items():
                df = pd.DataFrame({"a": r, "b": btc.shift(lag)}).dropna()
                if len(df) > 200:
                    cc.append(df["a"].corr(df["b"]))
            etiqueta = "beta contemporánea" if lag == 0 else ("BTC LIDERA (explotable si >0)" if lag >= 1 else "")
            print(f"   lag {lag}: {np.mean(cc):+.4f}   {etiqueta}")

        # 2) estrategia: seguir a BTC con un paso de retraso (umbral = sigma de BTC)
        sig = btc.rolling(50).std()
        senal = pd.Series(0.0, index=btc.index)
        senal[btc > sig] = 1.0          # BTC subió fuerte -> largo alt la barra siguiente
        senal[btc < -sig] = -1.0        # BTC bajó fuerte -> corto alt la barra siguiente
        pos = senal.shift(1).fillna(0)  # se ejecuta en la barra siguiente (sin lookahead)
        cambio = pos.diff().abs().fillna(0)

        filas = []
        for a, r in alts.items():
            df = pd.DataFrame({"r": r, "pos": pos, "ch": cambio}).dropna()
            pl = df["pos"] * df["r"] - df["ch"] * COSTE
            filas.append(pl)
        port = pd.concat(filas, axis=1).mean(axis=1).dropna()
        eq = (1 + port).cumprod()
        dd = (eq / eq.cummax() - 1).min()
        ins = eq[eq.index.year <= 2025]
        cagr = (ins.iloc[-1] / ins.iloc[0]) ** (1 / max((ins.index[-1] - ins.index[0]).days / 365, 0.5)) - 1
        aa = " ".join(f"{y}:{(eq[eq.index.year==y].iloc[-1]/eq[eq.index.year==y].iloc[0]-1)*100:+5.0f}%" if len(eq[eq.index.year == y]) > 1 else f"{y}:-" for y in ANIOS)
        print(f"2) Seguir a BTC (1 barra de retraso), cartera de alts, NETO de costes:")
        print(f"   CAGR {cagr*100:+.1f}% | DD {dd*100:.1f}% | {aa}")


if __name__ == "__main__":
    main()
