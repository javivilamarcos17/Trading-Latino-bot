"""
REVERSIÓN DIARIA (mean-reversion): la estadística mostró que tras una CAÍDA fuerte, el día siguiente
rebota (+0,32% tras día muy bajista en BTC), y la autocorrelación diaria es negativa y persistente
TODOS los años (incl. 2026). Aquí lo convertimos en estrategia y lo medimos en serio: neto de costes,
multi-moneda, por año, con 2026 como prueba.

Dos versiones:
  A) COMPRAR LA CAÍDA (long-only): entrar largo cuando el retorno diario < -k·sigma; mantener H días.
     Captura el rebote + la deriva alcista. Se compara con comprar-y-mantener.
  B) REVERSIÓN DÓLAR-NEUTRAL: cada día largo los que MÁS cayeron / corto los que MÁS subieron,
     mantener H días. Aísla la reversión del beta de mercado (gana suba o baje el mercado).

Uso:  python -m trading_latino.research.reversion_diaria
"""

from __future__ import annotations

import sys

import pandas as pd

from trading_latino.data.download import cargar

COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "LINK", "DOT", "LTC", "DOGE", "BCH", "UNI", "AAVE", "NEAR", "APT"]
COSTE = 0.0007
ANIOS = [2021, 2022, 2023, 2024, 2025, 2026]


def precios():
    out = {}
    for c in COINS:
        try:
            d = cargar("binance", c, "1d")
        except FileNotFoundError:
            continue
        s = pd.Series(d["cierre"].to_numpy(), index=pd.DatetimeIndex(d["timestamp"]).tz_localize(None))
        out[c] = s[s.index >= "2021-01-01"]
    return pd.DataFrame(out).sort_index()


def stats(nombre, r):
    eq = (1 + r.fillna(0)).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    ins = eq[eq.index.year <= 2025]
    cagr = (ins.iloc[-1] / ins.iloc[0]) ** (1 / 4.99) - 1
    aa = " ".join(f"{(eq[eq.index.year==y].iloc[-1]/eq[eq.index.year==y].iloc[0]-1)*100:+5.0f}" if len(eq[eq.index.year == y]) > 1 else "    -" for y in ANIOS)
    print(f"  {nombre:<34}| CAGR {cagr*100:+6.1f}% | DD {dd*100:6.1f}% | C/DD {abs(cagr/dd) if dd<0 else 0:4.2f} | {aa}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    P = precios()
    R = P.pct_change()
    print(f"{P.shape[1]} monedas, {len(P)} días. (años 21·22·23·24·25·26; 2026 = prueba)\n")

    # baseline: comprar y mantener (media de las monedas)
    stats("comprar y mantener (media)", R.mean(axis=1))

    print("\nA) COMPRAR LA CAÍDA (largo tras caída > k·sigma, mantener H días), cartera media:")
    sigma = R.rolling(30).std()
    for k in (1.0, 1.5, 2.0):
        for H in (1, 2, 3):
            senal = (R < -k * sigma)                      # ayer cayó fuerte
            pos = senal.shift(1).fillna(False)
            # mantener H días: la posición sigue activa H días tras la señal
            pos = pos.rolling(H).max().fillna(0).astype(bool)
            ret_coin = R.where(pos, 0.0)
            turn = pos.astype(int).diff().abs().fillna(0)
            ret = (ret_coin - turn * COSTE).mean(axis=1)
            stats(f"comprar caída k={k} H={H}", ret)

    print("\nA2) COMPRAR LA CAÍDA SOLO EN TENDENCIA ALCISTA (precio > media 200d):")
    ma200 = P.rolling(200).mean()
    tendencia_alcista = (P > ma200)
    for k in (1.0, 1.5):
        for H in (2, 3):
            senal = (R < -k * sigma) & tendencia_alcista
            pos = senal.shift(1).fillna(False)
            pos = pos.rolling(H).max().fillna(0).astype(bool)
            turn = pos.astype(int).diff().abs().fillna(0)
            ret = (R.where(pos, 0.0) - turn * COSTE).mean(axis=1)
            stats(f"caída+tendencia k={k} H={H}", ret)

    print("\nB) REVERSIÓN DÓLAR-NEUTRAL (largo los que más cayeron / corto los que más subieron):")
    for H in (1, 2, 3):
        W = pd.DataFrame(0.0, index=P.index, columns=P.columns)
        for dia in P.index:
            rr = R.loc[dia].dropna()
            if len(rr) < 6:
                continue
            n = max(1, len(rr) // 3)
            W.loc[dia, rr.nsmallest(n).index] = 0.5 / n     # largo los que cayeron
            W.loc[dia, rr.nlargest(n).index] = -0.5 / n     # corto los que subieron
        Wh = W.shift(1)
        if H > 1:
            Wh = Wh.rolling(H).mean()                        # repartir la entrada en H días (menos rotación)
        ret = (Wh * R).sum(axis=1)
        turn = (Wh - Wh.shift(1)).abs().sum(axis=1)
        stats(f"reversión neutral H={H}", ret - turn * COSTE)


if __name__ == "__main__":
    main()
