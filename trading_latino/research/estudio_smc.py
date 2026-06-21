"""
ESTUDIO RIGUROSO del resto del kit "Smart Money": FAIR VALUE GAPS (vacíos de liquidez) y ORDER BLOCKS.
Mismo microscopio que el de barridos: detectar la formación, esperar el RETEST de la zona, y medir
la REACCIÓN a 1,5R contra el umbral de un paseo aleatorio (40%). Sin lookahead, multi-moneda.

  - FVG alcista: hueco entre la máxima de la vela i-2 y la mínima de la i (el precio "saltó" dejando
    un vacío). Tesis: el precio vuelve a rellenar el hueco y REBOTA -> largo en el retest.
  - FVG bajista: hueco a la baja -> corto en el retest.
  - Order Block alcista: última vela bajista antes de un impulso alcista (rompe su máxima). Tesis:
    el precio vuelve a la zona del OB y rebota -> largo en el retest. (y espejo bajista)

Si la reversión en el retest supera el 40% (y los costes), hay edge. Si ronda 40%, es aleatorio.

Uso:  python -m trading_latino.research.estudio_smc
"""

from __future__ import annotations

import sys

import pandas as pd

from trading_latino.data.download import cargar

COSTE = 0.0007        # ida+vuelta taker+slippage
OBJETIVO_R = 1.5
N_FWD = 16
RETEST_MAX = 60
BUFFER = 0.0007
MIN_GAP = 0.0015      # tamaño mínimo del hueco/zona (0.15%) para que sea relevante

OTRAS = ["ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "NEAR", "APT", "SUI", "ARB", "OP",
         "POL", "LINK", "UNI", "AAVE", "LTC", "BCH", "DOT", "TIA", "DOGE"]
PARES = [("BTC", "5m"), ("BTC", "15m"), ("BTC", "1h")] + [(c, "1h") for c in OTRAS]


def reaccion(direccion, entrada, stop, hi, lo, k):
    """Desde el retest (bar k), ¿toca antes 1.5R a favor o el stop? Devuelve True/False/None."""
    D = (entrada - stop) if direccion == "largo" else (stop - entrada)
    if D <= 0:
        return None
    objetivo = entrada + OBJETIVO_R * D if direccion == "largo" else entrada - OBJETIVO_R * D
    n = len(hi)
    for j in range(k, min(k + N_FWD, n)):
        if direccion == "largo":
            if lo[j] <= stop: return False
            if hi[j] >= objetivo: return True
        else:
            if hi[j] >= stop: return False
            if lo[j] <= objetivo: return True
    return None


def analizar(d, moneda, tf):
    d = d.copy()
    d.index = pd.DatetimeIndex(d["timestamp"]).tz_localize(None)
    d = d[d.index >= "2021-01-01"]
    if len(d) < 300:
        return []
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    n = len(cl)
    regs = []

    def primer_retest(top, bot, desde, hacia_abajo):
        """Primer bar en (desde, desde+RETEST_MAX] cuyo rango entra en [bot, top]."""
        for k in range(desde + 1, min(desde + 1 + RETEST_MAX, n)):
            if hacia_abajo and lo[k] <= top:   # vuelve a bajar al hueco (FVG alcista/OB alcista)
                return k
            if (not hacia_abajo) and hi[k] >= bot:  # vuelve a subir al hueco (bajista)
                return k
        return None

    for i in range(2, n - 1):
        tend_alcista = cl[i] > ema[i]
        # ---- FVG alcista: low[i] > high[i-2]
        if lo[i] > hi[i - 2] and (lo[i] - hi[i - 2]) / cl[i] > MIN_GAP:
            top = lo[i]; bot = hi[i - 2]
            k = primer_retest(top, bot, i, hacia_abajo=True)
            if k is not None:
                entrada = top; stop = bot * (1 - BUFFER)
                g = reaccion("largo", entrada, stop, hi, lo, k)
                if g is not None:
                    regs.append({"tipo": "FVG", "dir": "largo", "gana": g, "anio": int(d.index[k].year),
                                 "Dpct": (entrada - stop) / entrada,
                                 "tendencia": "a favor" if tend_alcista else "contra", "tf": tf})
        # ---- FVG bajista: high[i] < low[i-2]
        if hi[i] < lo[i - 2] and (lo[i - 2] - hi[i]) / cl[i] > MIN_GAP:
            bot = hi[i]; top = lo[i - 2]
            k = primer_retest(top, bot, i, hacia_abajo=False)
            if k is not None:
                entrada = bot; stop = top * (1 + BUFFER)
                g = reaccion("corto", entrada, stop, hi, lo, k)
                if g is not None:
                    regs.append({"tipo": "FVG", "dir": "corto", "gana": g, "anio": int(d.index[k].year),
                                 "Dpct": (stop - entrada) / entrada,
                                 "tendencia": "a favor" if not tend_alcista else "contra", "tf": tf})
        # ---- Order Block alcista: vela i bajista + vela i+1 rompe su máxima
        if cl[i] < op[i] and cl[i + 1] > hi[i] and (hi[i] - lo[i]) / cl[i] > MIN_GAP:
            top = hi[i]; bot = lo[i]
            k = primer_retest(top, bot, i + 1, hacia_abajo=True)
            if k is not None:
                entrada = top; stop = bot * (1 - BUFFER)
                g = reaccion("largo", entrada, stop, hi, lo, k)
                if g is not None:
                    regs.append({"tipo": "OB", "dir": "largo", "gana": g, "anio": int(d.index[k].year),
                                 "Dpct": (entrada - stop) / entrada,
                                 "tendencia": "a favor" if tend_alcista else "contra", "tf": tf})
        # ---- Order Block bajista: vela i alcista + vela i+1 rompe su mínima
        if cl[i] > op[i] and cl[i + 1] < lo[i] and (hi[i] - lo[i]) / cl[i] > MIN_GAP:
            top = hi[i]; bot = lo[i]
            k = primer_retest(top, bot, i + 1, hacia_abajo=False)
            if k is not None:
                entrada = bot; stop = top * (1 + BUFFER)
                g = reaccion("corto", entrada, stop, hi, lo, k)
                if g is not None:
                    regs.append({"tipo": "OB", "dir": "corto", "gana": g, "anio": int(d.index[k].year),
                                 "Dpct": (stop - entrada) / entrada,
                                 "tendencia": "a favor" if not tend_alcista else "contra", "tf": tf})
    return regs


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    todo = []
    for moneda, tf in PARES:
        try:
            d = cargar("binance", moneda, tf)
        except FileNotFoundError:
            continue
        todo += analizar(d, moneda, tf)

    df = pd.DataFrame(todo)
    print(f"=== {len(df)} retests de FVG/OB (todas las monedas/TF), sin lookahead ===")
    print(f"Umbral de paseo aleatorio a {OBJETIVO_R}R: {100/(1+OBJETIVO_R):.0f}%  (por debajo = peor que aleatorio)\n")

    def linea(et, sub):
        if len(sub) < 50:
            return
        print(f"  {et:<28}| n={len(sub):6d} | reversión {sub['gana'].mean()*100:4.1f}%")

    for tipo in ("FVG", "OB"):
        st = df[df["tipo"] == tipo]
        linea(f"{tipo} (todos)", st)
        linea(f"{tipo} a FAVOR de tendencia", st[st["tendencia"] == "a favor"])
        linea(f"{tipo} CONTRA tendencia", st[st["tendencia"] == "contra"])

    # ---- JUEZ DECISIVO: ¿supera los COSTES? expectativa NETA por operación ----
    print("\n=== EXPECTATIVA NETA POR OPERACIÓN (¿supera el coste?) ===")
    print(f"  coste {COSTE*100:.3f}% ida+vuelta | objetivo {OBJETIVO_R}R")
    for tipo in ("FVG", "OB"):
        st = df[df["tipo"] == tipo]
        win = st["gana"].mean()
        bruto = win * OBJETIVO_R - (1 - win)          # expectativa bruta en R
        coste_R = (COSTE / st["Dpct"].clip(lower=0.0005)).mean()
        neto = bruto - coste_R
        print(f"  {tipo}: win {win*100:.1f}% | bruto {bruto:+.3f}R | coste {coste_R:.3f}R | NETO {neto:+.3f}R | "
              f"D medio {st['Dpct'].median()*100:.2f}% | {'RENTABLE' if neto > 0 else 'no rentable'}")

    # ---- ¿AGUANTA EN 2026? win rate por año ----
    print("\n=== WIN RATE POR AÑO (umbral azar 40%) ===")
    for tipo in ("FVG", "OB"):
        st = df[df["tipo"] == tipo]
        wy = st.groupby("anio")["gana"].agg(["mean", "count"])
        print(f"  {tipo}: " + " ".join(f"{int(y)}:{r['mean']*100:.0f}%(n{int(r['count'])})" for y, r in wy.iterrows()))

    print()
    for tf in ("5m", "15m", "1h"):
        linea(f"TODO en {tf}", df[df["tf"] == tf])


if __name__ == "__main__":
    main()
