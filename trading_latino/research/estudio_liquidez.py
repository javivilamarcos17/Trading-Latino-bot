"""
ESTUDIO DIAGNÓSTICO: ¿cómo reacciona el precio cuando barre un pool de liquidez, y POR QUÉ?
No es una estrategia con P&L — es un MICROSCOPIO para DEPURAR el detector del sniper.

Detecta cada BARRIDO de un pool (máximos/mínimos IGUALES = stops apilados), SIN LOOKAHEAD (solo
usa swings ya confirmados), y mide la REACCIÓN realista: ¿alcanza 1,5R a favor antes que el stop?
+ excursión máxima favorable (MFE) y adversa (MAE) en R. Luego trocea por CONDICIONES (fuerza del
pool, volumen, tendencia, mecha, hora) para ver QUÉ predice la reacción -> eso depura el detector.

CAPTURA EL MÁXIMO DE DATOS: BTC en 5m/15m/30m/1h + ~20 monedas en 1h, todo combinado.

Uso:  python -m trading_latino.research.estudio_liquidez
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from trading_latino.data.download import cargar

FRACTAL = 3
LOOKBACK = 120
TOL = 0.0012
N_FWD = 16
BUFFER = 0.0007
OBJETIVO_R = 1.5

OTRAS = ["ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "NEAR", "APT", "SUI", "ARB", "OP",
         "POL", "LINK", "UNI", "AAVE", "LTC", "BCH", "DOT", "TIA", "DOGE"]
PARES = [("BTC", "5m"), ("BTC", "15m"), ("BTC", "30m"), ("BTC", "1h")] + [(c, "1h") for c in OTRAS]


def analizar(d, moneda, tf):
    d = d.copy()
    d.index = pd.DatetimeIndex(d["timestamp"]).tz_localize(None)
    d = d[d.index >= "2021-01-01"]
    if len(d) < LOOKBACK + N_FWD + 50:
        return []
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy(); vol = d["volumen"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    volmed = pd.Series(vol).rolling(20).mean().shift(1).to_numpy()
    hora = d.index.hour.to_numpy()
    n = len(cl)

    # swings fractales (vectorizado). OJO: un swing en j se CONFIRMA en j+FRACTAL.
    w = 2 * FRACTAL + 1
    rmax = pd.Series(hi).rolling(w, center=True).max().to_numpy()
    rmin = pd.Series(lo).rolling(w, center=True).min().to_numpy()
    sh_val = np.where(hi == rmax, hi, np.nan)
    sl_val = np.where(lo == rmin, lo, np.nan)
    # niveles de pool conocidos en i = swings confirmados (desplazar FRACTAL para no mirar el futuro)
    nivel_alto = pd.Series(sh_val).rolling(LOOKBACK, min_periods=1).max().shift(FRACTAL).to_numpy()
    nivel_bajo = pd.Series(sl_val).rolling(LOOKBACK, min_periods=1).min().shift(FRACTAL).to_numpy()

    def evaluar(direccion, entrada, stop, D, i):
        objetivo = entrada - OBJETIVO_R * D if direccion == "corto" else entrada + OBJETIVO_R * D
        gana = None
        for k in range(i + 1, min(i + 1 + N_FWD, n)):
            if direccion == "corto":
                if hi[k] >= stop: gana = False; break
                if lo[k] <= objetivo: gana = True; break
            else:
                if lo[k] <= stop: gana = False; break
                if hi[k] >= objetivo: gana = True; break
        fh = hi[i + 1:i + 1 + N_FWD]; fl = lo[i + 1:i + 1 + N_FWD]
        if len(fh) == 0:
            return None, 0, 0
        if direccion == "corto":
            mfe = (entrada - fl.min()) / D; mae = (fh.max() - entrada) / D
        else:
            mfe = (fh.max() - entrada) / D; mae = (entrada - fl.min()) / D
        return (None if gana is None else bool(gana)), mfe, mae

    regs = []
    lo_inf = LOOKBACK + FRACTAL
    for i in range(lo_inf, n - N_FWD):
        na = nivel_alto[i]; nb = nivel_bajo[i]
        cuerpo = abs(cl[i] - op[i]) + 1e-9
        vr = vol[i] / volmed[i] if volmed[i] and volmed[i] > 0 else 0.0
        # ventana de swings confirmados para contar toques (sin futuro)
        if not np.isnan(na) and hi[i] > na and cl[i] < na:
            entrada = cl[i]; stop = hi[i] * (1 + BUFFER); D = stop - entrada
            if D > 0:
                vent = sh_val[i - lo_inf:i - FRACTAL]
                toques = int(np.nansum(vent >= na * (1 - TOL)))
                gana, mfe, mae = evaluar("corto", entrada, stop, D, i)
                if gana is not None:
                    regs.append({"moneda": moneda, "tf": tf, "dir": "corto", "gana": gana,
                                 "toques": toques, "vol": vr, "mfe": mfe, "mae": mae,
                                 "tendencia": "a favor" if cl[i] < ema[i] else "contra",
                                 "mecha": (hi[i] - max(cl[i], op[i])) / cuerpo, "hora": int(hora[i])})
        if not np.isnan(nb) and lo[i] < nb and cl[i] > nb:
            entrada = cl[i]; stop = lo[i] * (1 - BUFFER); D = entrada - stop
            if D > 0:
                vent = sl_val[i - lo_inf:i - FRACTAL]
                toques = int(np.nansum(vent <= nb * (1 + TOL)))
                gana, mfe, mae = evaluar("largo", entrada, stop, D, i)
                if gana is not None:
                    regs.append({"moneda": moneda, "tf": tf, "dir": "largo", "gana": gana,
                                 "toques": toques, "vol": vr, "mfe": mfe, "mae": mae,
                                 "tendencia": "a favor" if cl[i] > ema[i] else "contra",
                                 "mecha": (min(cl[i], op[i]) - lo[i]) / cuerpo, "hora": int(hora[i])})
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
        r = analizar(d, moneda, tf)
        todo += r
        if r:
            print(f"  {moneda} {tf}: {len(r)} barridos | reversión {np.mean([x['gana'] for x in r])*100:.1f}%")

    df = pd.DataFrame(todo)
    print(f"\n=== TOTAL: {len(df)} barridos (todas las monedas/TF) ===")
    print(f"Tasa de reversión BASE (alcanza {OBJETIVO_R}R antes que el stop): {df['gana'].mean()*100:.1f}%")
    # umbral de rentabilidad: con objetivo 1.5R necesitas ganar > 1/(1+1.5)=40% (bruto, sin costes)
    print(f"Umbral para ser rentable a {OBJETIVO_R}R (sin costes): {100/(1+OBJETIVO_R):.0f}%")
    print(f"MFE mediana (reacción favorable máx): {df['mfe'].median():.2f}R | MAE mediana: {df['mae'].median():.2f}R\n")

    def trocear(titulo, buckets):
        print(f"  por {titulo}:")
        for et, mask in buckets:
            sub = df[mask]
            if len(sub) < 50:
                continue
            print(f"    {et:<20}| n={len(sub):6d} | reversión {sub['gana'].mean()*100:4.1f}% | MFE med {sub['mfe'].median():.2f}R")

    trocear("FUERZA POOL (toques)", [("2", df["toques"] == 2), ("3-5", df["toques"].between(3, 5)), ("6+", df["toques"] >= 6)])
    trocear("VOLUMEN", [("<1.2x", df["vol"] < 1.2), ("1.2-2x", df["vol"].between(1.2, 2)), (">2x", df["vol"] > 2)])
    trocear("TENDENCIA", [("a favor", df["tendencia"] == "a favor"), ("contra", df["tendencia"] == "contra")])
    trocear("MECHA rechazo", [("<1x", df["mecha"] < 1), ("1-2x", df["mecha"].between(1, 2)), (">2x", df["mecha"] > 2)])
    trocear("HORA UTC", [("0-7", df["hora"].between(0, 7)), ("8-13", df["hora"].between(8, 13)), ("14-21", df["hora"].between(14, 21)), ("22-23", df["hora"] >= 22)])
    trocear("TIMEFRAME", [(tf, df["tf"] == tf) for tf in ["5m", "15m", "30m", "1h"]])

    fuerte = df[(df["toques"] >= 3) & (df["vol"] > 2) & (df["tendencia"] == "a favor") & (df["mecha"] > 1)]
    if len(fuerte) >= 50:
        print(f"\n  COMBINADO (3+ toques + vol>2x + a favor + mecha>1x): n={len(fuerte)} | "
              f"reversión {fuerte['gana'].mean()*100:.1f}% | MFE med {fuerte['mfe'].median():.2f}R")


if __name__ == "__main__":
    main()
