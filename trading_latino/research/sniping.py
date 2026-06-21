"""
SNIPING por barrido de liquidez (estilo "Smart Money"/manipulación), proxy con OHLCV.
Idea del dueño: arriesgar SIEMPRE un % pequeño de la cuenta pero muy apalancado (stop ajustado),
entrando "al tiro" donde hay manipulación: un STOP-HUNT / barrido de liquidez.

Cómo lo detectamos sin order-book (que no tenemos en histórico): los stops se acumulan justo
por encima de máximos recientes (liquidez de compra) y por debajo de mínimos recientes (liquidez
de venta). Un BARRIDO = el precio pincha ese extremo con la mecha pero CIERRA de vuelta dentro
(barrida fallida = agarraron liquidez y revierten).
  - Barrido de un MÁXIMO reciente -> entrada CORTA (cazaron stops arriba, revierte abajo).
  - Barrido de un MÍNIMO reciente -> entrada LARGA.
Stop justo detrás de la mecha; objetivo = múltiplo R. Riesgo fijo 1% por operación.
Reportamos BRUTO vs NETO (taker+slippage) porque aquí los costes deciden. Hold-out 2026.

Uso:  python -m trading_latino.research.sniping
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from trading_latino.data.download import cargar

TF = "15m"
COSTE_RT = 0.0015          # ida+vuelta: taker ~0.045%x2 + slippage en stop/entrada de mercado
RIESGO = 0.01              # 1% de la cuenta por operación


def cargar_px(tf):
    d = cargar("binance", "BTC", tf)
    d.index = pd.DatetimeIndex(d["timestamp"]).tz_localize(None)
    return d[d.index >= "2021-01-01"]


def backtest(d, lookback, r_mult, coste=COSTE_RT, buffer=0.0005):
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    idx = d.index
    n = len(cl)
    # swing previos (sin incluir la barra actual)
    sh = pd.Series(hi).rolling(lookback).max().shift(1).to_numpy()
    sl = pd.Series(lo).rolling(lookback).min().shift(1).to_numpy()

    trades = []   # (fecha, R_neto)
    i = lookback + 1
    while i < n:
        corto = hi[i] > sh[i] and cl[i] < sh[i]      # barrido de máximo -> short
        largo = lo[i] < sl[i] and cl[i] > sl[i]      # barrido de mínimo -> long
        if not (corto or largo):
            i += 1; continue
        entrada = cl[i]
        if corto:
            stop = hi[i] * (1 + buffer); D = stop - entrada
            objetivo = entrada - r_mult * D
        else:
            stop = lo[i] * (1 - buffer); D = entrada - stop
            objetivo = entrada + r_mult * D
        if D <= 0:
            i += 1; continue
        # recorrer barras siguientes hasta tocar stop u objetivo
        resultado = None
        j = i + 1
        while j < n:
            if corto:
                if hi[j] >= stop: resultado = -1.0; break
                if lo[j] <= objetivo: resultado = r_mult; break
            else:
                if lo[j] <= stop: resultado = -1.0; break
                if hi[j] >= objetivo: resultado = r_mult; break
            j += 1
        if resultado is None:
            break
        coste_R = coste / (D / entrada)               # coste en unidades de R
        trades.append((idx[j], resultado - coste_R))
        i = j + 1                                       # no solapar operaciones
    return trades


def backtest_refinado(d, lookback, r_mult, coste=COSTE_RT, buffer=0.0005):
    """Barrido + filtro de TENDENCIA (EMA200) + CONFIRMACIÓN (la barra siguiente cierra a favor).
    Solo largos-de-mínimo en tendencia alcista; solo cortos-de-máximo en bajista."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    idx = d.index; n = len(cl)
    sh = pd.Series(hi).rolling(lookback).max().shift(1).to_numpy()
    sl = pd.Series(lo).rolling(lookback).min().shift(1).to_numpy()
    trades = []
    i = lookback + 1
    while i < n - 1:
        corto = hi[i] > sh[i] and cl[i] < sh[i] and cl[i] < ema[i]      # barrido máx en tendencia bajista
        largo = lo[i] < sl[i] and cl[i] > sl[i] and cl[i] > ema[i]      # barrido mín en tendencia alcista
        if not (corto or largo):
            i += 1; continue
        # confirmación: la barra i+1 cierra a favor de la reversión
        if corto and not (cl[i + 1] < cl[i]):
            i += 1; continue
        if largo and not (cl[i + 1] > cl[i]):
            i += 1; continue
        k = i + 1; entrada = cl[k]
        if corto:
            stop = hi[i] * (1 + buffer); D = stop - entrada; objetivo = entrada - r_mult * D
        else:
            stop = lo[i] * (1 - buffer); D = entrada - stop; objetivo = entrada + r_mult * D
        if D <= 0:
            i += 1; continue
        resultado = None; j = k + 1
        while j < n:
            if corto:
                if hi[j] >= stop: resultado = -1.0; break
                if lo[j] <= objetivo: resultado = r_mult; break
            else:
                if lo[j] <= stop: resultado = -1.0; break
                if hi[j] >= objetivo: resultado = r_mult; break
            j += 1
        if resultado is None:
            break
        trades.append((idx[j], resultado - coste / (D / entrada)))
        i = j + 1
    return trades


def backtest_detector(d, lookback, r_mult, coste=COSTE_RT, buffer=0.0005,
                      vol_mult=2.0, mecha_min=1.0, iguales_tol=0.0015, stop_mult=1.0):
    """Detección MEJORADA del snipe: barrido de una zona de liquidez (máximos/mínimos IGUALES)
    con (1) PICO DE VOLUMEN, (2) MECHA de rechazo larga, (3) a favor de tendencia EMA200.
    Devuelve trades y el coste-en-R medio (el "muro")."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy(); vol = d["volumen"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    vol_med = pd.Series(vol).rolling(lookback).mean().shift(1).to_numpy()
    idx = d.index; n = len(cl)
    trades = []; costes_R = []
    i = lookback + 1
    while i < n - 1:
        vent_hi = hi[i - lookback:i]; vent_lo = lo[i - lookback:i]
        nivel_alto = vent_hi.max(); nivel_bajo = vent_lo.min()
        # ¿zona de liquidez? = al menos 2 toques "iguales" cerca del extremo
        iguales_arriba = (vent_hi >= nivel_alto * (1 - iguales_tol)).sum() >= 2
        iguales_abajo = (vent_lo <= nivel_bajo * (1 + iguales_tol)).sum() >= 2
        cuerpo = abs(cl[i] - op[i]) + 1e-9
        mecha_sup = hi[i] - max(cl[i], op[i]); mecha_inf = min(cl[i], op[i]) - lo[i]
        vol_ok = vol[i] > vol_mult * (vol_med[i] if vol_med[i] > 0 else 1e18)
        corto = (hi[i] > nivel_alto and cl[i] < nivel_alto and iguales_arriba and cl[i] < ema[i]
                 and vol_ok and mecha_sup > mecha_min * cuerpo)
        largo = (lo[i] < nivel_bajo and cl[i] > nivel_bajo and iguales_abajo and cl[i] > ema[i]
                 and vol_ok and mecha_inf > mecha_min * cuerpo)
        if not (corto or largo):
            i += 1; continue
        entrada = cl[i]
        if corto:
            stop = (hi[i] + stop_mult * (hi[i] - entrada)) * (1 + buffer); D = stop - entrada
            objetivo = entrada - r_mult * D
        else:
            stop = (lo[i] - stop_mult * (entrada - lo[i])) * (1 - buffer); D = entrada - stop
            objetivo = entrada + r_mult * D
        if D <= 0:
            i += 1; continue
        resultado = None; j = i + 1
        while j < n:
            if corto:
                if hi[j] >= stop: resultado = -1.0; break
                if lo[j] <= objetivo: resultado = r_mult; break
            else:
                if lo[j] <= stop: resultado = -1.0; break
                if hi[j] >= objetivo: resultado = r_mult; break
            j += 1
        if resultado is None:
            break
        c_R = coste / (D / entrada); costes_R.append(coste / (D / entrada) if coste else (COSTE_RT / (D / entrada)))
        trades.append((idx[j], resultado - c_R))
        i = j + 1
    muro = float(np.mean(costes_R)) if costes_R else float("nan")
    return trades, muro


def resumen(nombre, trades):
    if len(trades) < 10:
        print(f"  {nombre:<34}| solo {len(trades)} ops"); return
    fechas = [t[0] for t in trades]; rs = np.array([t[1] for t in trades])
    s = pd.Series(rs, index=pd.DatetimeIndex(fechas))
    eq = (1 + RIESGO * s).cumprod()                    # capital arriesgando 1% por op
    dd = (eq / eq.cummax() - 1).min()
    ins = s[s.index.year <= 2025]; out = s[s.index.year == 2026]
    win = (rs > 0).mean()
    aa = " ".join(f"{s[s.index.year==y].sum():+5.1f}R" if (s.index.year == y).any() else "    -" for y in [2021, 2022, 2023, 2024, 2025, 2026])
    print(f"  {nombre:<34}| ops {len(trades):4d} | win {win*100:4.1f}% | R_tot {rs.sum():+7.1f} | "
          f"2026 {out.sum():+5.1f}R | DD {dd*100:5.1f}% | {aa}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    d = cargar_px(TF)
    print(f"BTC {TF} | {len(d)} velas {d.index[0].date()}→{d.index[-1].date()}")
    print(f"Riesgo 1%/op. Coste ida+vuelta {COSTE_RT*100:.2f}%. (años: 21·22·23·24·25·26)\n")
    print("DETECTOR (liquidez en niveles IGUALES + pico VOLUMEN + MECHA larga + tendencia)")
    print("¿supera el MURO de coste? edge/op = ganancia BRUTA media por op (R); MURO = coste medio/op (R)")
    for lb in (30, 50):
        for rm in (2.0, 3.0):
            for sm in (1.0, 3.0):    # stop ajustado (más leverage) vs stop ancho (menos)
                tr_b, muro = backtest_detector(d, lb, rm, coste=0.0, stop_mult=sm)
                tr_n, _ = backtest_detector(d, lb, rm, stop_mult=sm)
                if len(tr_b) < 10:
                    print(f"  lb{lb} obj{rm}R stop×{sm:.0f} | solo {len(tr_b)} ops (muy selectivo)"); continue
                rs = np.array([r for _, r in tr_b]); edge = rs.mean()
                net = np.array([r for _, r in tr_n]).sum()
                veredicto = "PASA" if edge > muro else "no pasa"
                print(f"  lb{lb} obj{rm}R stop×{sm:.0f} | ops {len(tr_b):4d} | win {(rs>0).mean()*100:4.0f}% | "
                      f"edge/op {edge:+.3f}R | MURO {muro:.3f}R | {veredicto} | neto {net:+.0f}R")


if __name__ == "__main__":
    main()
