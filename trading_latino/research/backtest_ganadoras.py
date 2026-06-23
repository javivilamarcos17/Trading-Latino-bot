"""
BACKTEST HISTORICO DE LAS GANADORAS DE LA ARENA
================================================
Verifica si el edge de las estrategias ganadoras en vivo (3 dias recientes)
se mantiene en los MESES ANTERIORES. Solo curiosidad — no toca arena data.

LIMITACIONES HONESTAS (leer antes de interpretar):
  1. ~50 dias de datos (5000 velas x 15m = ~52 dias desde hoy hacia atras)
  2. Salida simulada con OHLCV, sin datos de 1m — aproximacion razonable
  3. Las estrategias se disenaron VIENDO el tramo reciente (sesgo de diseno parcial)
  4. Un solo par de regimenes (el mercado de los ultimos 2 meses)
  5. Lookback 300 velas para EMA200 => los primeros 75h no generan senales

Uso:  python -m trading_latino.research.backtest_ganadoras
"""
from __future__ import annotations
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
import ccxt

# ------------------------------------------------------------------ fuentes de datos
def _ex_hl():
    """Hyperliquid — para detectores 15m (precio real de la arena)."""
    return ccxt.hyperliquid({
        "walletAddress": os.getenv("HL_WALLET", ""),
        "privateKey":    os.getenv("HL_KEY", ""),
        "options": {"defaultType": "swap"},
    })

def _ex_bn():
    """Binance — para historico de 1m. Guarda meses vs los 3-4 dias de Hyperliquid.
    BTC/USDT perp Binance y BTC/USDC Hyperliquid difieren < 0.1% — despreciable."""
    return ccxt.binance({"options": {"defaultType": "future"}})

def descargar(ex, coin, tf="15m", limit=5000) -> pd.DataFrame:
    """Descarga un bloque de velas de Hyperliquid."""
    o = ex.fetch_ohlcv(f"{coin}/USDC:USDC", tf, limit=limit)
    d = pd.DataFrame(o, columns=["t", "apertura", "maximo", "minimo", "cierre", "volumen"])
    d["t"] = d["t"].astype("int64")
    return d.reset_index(drop=True)


def descargar_1m_binance(coin: str, desde_ts: int, hasta_ts: int) -> pd.DataFrame:
    """
    Descarga velas de 1m de Binance Futures en bloques de 1000 (limite de su API).
    Binance guarda hasta 3-6 meses de 1m — suficiente para el backtest de 52 dias.
    Par: BTCUSDT / ETHUSDT perpetuo.
    """
    ex = _ex_bn()
    simbolo = f"{coin}USDT"
    POR_LLAMADA = 1000

    bloques = []
    t = desde_ts
    llamadas = 0
    while t < hasta_ts:
        try:
            o = ex.fetch_ohlcv(simbolo, "1m", since=t, limit=POR_LLAMADA)
        except Exception as e:
            print(f"    [Binance] Error en bloque {llamadas}: {e}")
            break
        if not o:
            break
        bloques.extend(o)
        t = o[-1][0] + 60_000
        llamadas += 1
        if llamadas % 10 == 0:
            print(f"    ... {llamadas} bloques ({len(bloques):,} velas)")

    if not bloques:
        return pd.DataFrame(columns=["t", "apertura", "maximo", "minimo", "cierre", "volumen"])
    d = pd.DataFrame(bloques, columns=["t", "apertura", "maximo", "minimo", "cierre", "volumen"])
    d["t"] = d["t"].astype("int64")
    d = d.drop_duplicates("t").sort_values("t").reset_index(drop=True)
    return d

# ------------------------------------------------------------------ helpers (mismos que arena)
COSTE = 0.0008   # 0.08% round-trip

def _adx(d, n=14):
    h, l, c = d["maximo"], d["minimo"], d["cierre"]
    up = h.diff(); dn = -l.diff()
    pdm = up.clip(lower=0).where(up > dn, 0.0)
    ndm = dn.clip(lower=0).where(dn > up, 0.0)
    atr = (h - l).ewm(alpha=1/n, adjust=False).mean()
    pdi = 100 * pdm.ewm(alpha=1/n, adjust=False).mean() / atr.replace(0, np.nan)
    ndi = 100 * ndm.ewm(alpha=1/n, adjust=False).mean() / atr.replace(0, np.nan)
    dx  = (100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan))
    return dx.ewm(alpha=1/n, adjust=False).mean().to_numpy()

def _rsi(c, n=14):
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn = (-d).clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    return (100 - 100/(1 + up/dn.replace(0, np.nan))).to_numpy()

def _setup(direc, entrada, stop, r=2.0):
    D = (entrada - stop) if direc == "largo" else (stop - entrada)
    if D <= 0: return None
    target = entrada + r * D if direc == "largo" else entrada - r * D
    return {"dir": direc, "entry": float(entrada), "stop": float(stop), "target": float(target), "R": r}

# ------------------------------------------------------------------ detectores (copia fiel de arena.py)
LOOKBACK = 300   # velas de contexto necesarias para EMA200

def det_ob_trend(d):
    """OB activo (vela bajista seguida de ruptura) alineado con EMA200."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    j = len(cl) - 1
    if j < 215 or np.isnan(ema[j]): return None
    px = cl[j]
    for i in range(max(0, j - 30), j - 1):
        if (hi[i] - lo[i]) / cl[i] < 0.0005: continue
        if cl[i] < op[i] and cl[i+1] > hi[i]:        # OB alcista
            if lo[i] <= px <= hi[i] and px > ema[j]:
                return _setup("largo", px, lo[i] * 0.999)
        if cl[i] > op[i] and cl[i+1] < lo[i]:        # OB bajista
            if lo[i] <= px <= hi[i] and px < ema[j]:
                return _setup("corto", px, hi[i] * 1.001)
    return None

def det_ob_plus(d):
    """OB + EMA200 + sin volumen de climax (>2.5x media)."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    vol = d["volumen"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    j = len(cl) - 1
    if j < 215 or np.isnan(ema[j]): return None
    vol_ma = pd.Series(vol).rolling(20).mean().to_numpy()
    px = cl[j]
    for i in range(max(0, j - 30), j - 1):
        if (hi[i] - lo[i]) / cl[i] < 0.0005: continue
        if vol[i] > 2.5 * (vol_ma[i] or 1): continue   # skip climax
        if cl[i] < op[i] and cl[i+1] > hi[i]:
            if lo[i] <= px <= hi[i] and px > ema[j]:
                return _setup("largo", px, lo[i] * 0.999)
        if cl[i] > op[i] and cl[i+1] < lo[i]:
            if lo[i] <= px <= hi[i] and px < ema[j]:
                return _setup("corto", px, hi[i] * 1.001)
    return None

def det_fvg_ob(d):
    """FVG dentro de OB activo (doble confluencia)."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    j = len(cl) - 1
    if j < 215 or np.isnan(ema[j]): return None
    px = cl[j]
    # Buscar FVGs (imbalances de 3 velas)
    for k in range(max(2, j - 15), j - 1):
        fvg_up   = lo[k+1] > hi[k-1]   # FVG alcista
        fvg_down = hi[k+1] < lo[k-1]   # FVG bajista
        if not fvg_up and not fvg_down: continue
        if fvg_up:
            fbot, ftop = hi[k-1], lo[k+1]
            if not (fbot <= px <= ftop and px > ema[j]): continue
            direc = "largo"
        else:
            fbot, ftop = hi[k+1], lo[k-1]
            if not (fbot <= px <= ftop and px < ema[j]): continue
            direc = "corto"
        # Confirmar que el FVG esta dentro de un OB
        for i in range(max(0, j - 50), k - 1):
            if (hi[i] - lo[i]) / cl[i] < 0.0005: continue
            ob_top = hi[i]; ob_bot = lo[i]
            if ob_top - ob_bot < 0.0008 * cl[i]: continue
            if direc == "largo" and cl[i] < op[i] and cl[i+1] > ob_top:
                if ob_bot <= px <= ob_top:
                    return _setup("largo", px, ob_bot * 0.999)
            if direc == "corto" and cl[i] > op[i] and cl[i+1] < ob_bot:
                if ob_bot <= px <= ob_top:
                    return _setup("corto", px, ob_top * 1.001)
    return None

def _hora_utc(ts_ms):
    return pd.to_datetime(int(ts_ms), unit="ms").hour

# --- wrappers con filtro de sesion Asia (h < 7) ---
def det_ob_plus_asia(d):
    if _hora_utc(d["t"].iloc[-1]) >= 7: return None
    return det_ob_plus(d)

def det_ob_trend_r3(d):
    if _hora_utc(d["t"].iloc[-1]) >= 7: return None
    base = det_ob_trend(d)
    if base is None: return None
    D = abs(base["entry"] - base["stop"])
    base["target"] = base["entry"] + 3.0*D if base["dir"] == "largo" else base["entry"] - 3.0*D
    base["R"] = 3.0
    return base

def det_fvg_ob_asia(d):
    if _hora_utc(d["t"].iloc[-1]) >= 7: return None
    return det_fvg_ob(d)

def det_ob_regime(d):
    adx = _adx(d); j = len(d) - 1
    if j < 30 or np.isnan(adx[j]): return None
    return det_ob_trend(d) if adx[j] > 25 else det_ob_plus(d)

def det_ob_regime_asia(d):
    if _hora_utc(d["t"].iloc[-1]) >= 13: return None
    return det_ob_regime(d)

def det_ob_asia(d):
    if _hora_utc(d["t"].iloc[-1]) >= 13: return None
    return det_ob_trend(d)

ESTRATEGIAS = {
    "ob_plus_asia":   det_ob_plus_asia,    # reina actual  (+1.295R)
    "ob_trend_r3":    det_ob_trend_r3,     # #2 actual      (+1.085R)
    "fvg_ob_asia":    det_fvg_ob_asia,     # #3 actual      (+0.654R)
    "ob_regime_asia": det_ob_regime_asia,  # #4 actual      (+0.574R)
    "ob_asia":        det_ob_asia,         # #5 actual      (+0.344R)
}

# ------------------------------------------------------------------ simulacion de salida (OHLCV)
def simular_salida_1m(d1m: pd.DataFrame, ts_entrada: int, stop: float, target: float,
                      es_largo: bool, max_min: int = 480) -> float:
    """
    Simula la salida usando velas de 1m — exactamente igual que la arena en vivo.
    Busca el primer minuto tras ts_entrada en que se toca stop o target.
    Conservative: si ambos se tocan en el mismo minuto, se asume stop primero.
    Devuelve PnL en R neto de COSTE. max_min = maximo de minutos a esperar (8h).
    """
    # encontrar barra de entrada en 1m
    t_arr = d1m["t"].to_numpy()
    # Verificar que el timestamp esta DENTRO del rango de datos 1m disponible
    if ts_entrada < t_arr[0] or ts_entrada > t_arr[-1]:
        return float("nan")   # sin datos 1m para este periodo — excluir del calculo
    mask = t_arr >= ts_entrada
    idx_arr = np.where(mask)[0]
    if len(idx_arr) == 0:
        return float("nan")

    entry_price = d1m["cierre"].iloc[idx_arr[0]]
    D = abs(entry_price - stop)
    if D == 0:
        return -COSTE
    R_mult = abs(target - entry_price) / D

    fin = min(idx_arr[0] + max_min, len(d1m))
    for i in range(idx_arr[0] + 1, fin):
        lo = d1m["minimo"].iloc[i]
        hi = d1m["maximo"].iloc[i]
        if es_largo:
            toco_stop   = lo <= stop
            toco_target = hi >= target
        else:
            toco_stop   = hi >= stop
            toco_target = lo <= target
        if toco_stop and toco_target:
            return -1.0 - COSTE     # conservador: stop primero
        if toco_stop:
            return -1.0 - COSTE
        if toco_target:
            return R_mult - COSTE

    # Max hold: salir al cierre del ultimo minuto disponible
    cl_final = d1m["cierre"].iloc[min(fin - 1, len(d1m) - 1)]
    pnl = (cl_final - entry_price) / D if es_largo else (entry_price - cl_final) / D
    return pnl - COSTE

# ------------------------------------------------------------------ backtest principal
def backtest_moneda(d15: pd.DataFrame, d1m: pd.DataFrame) -> dict:
    """Corre todas las estrategias sobre el DataFrame de 15m, simulando salidas con 1m."""
    resultados = {e: [] for e in ESTRATEGIAS}
    ts = pd.to_datetime(d15["t"], unit="ms")
    ts_arr = d15["t"].to_numpy()

    for j in range(LOOKBACK, len(d15) - 1):
        ventana = d15.iloc[j - LOOKBACK: j + 1].reset_index(drop=True)
        for estr, detector in ESTRATEGIAS.items():
            try:
                sig = detector(ventana)
            except Exception:
                continue
            if sig is None:
                continue
            pnl = simular_salida_1m(
                d1m,
                ts_entrada = int(ts_arr[j]),
                stop       = sig["stop"],
                target     = sig["target"],
                es_largo   = sig["dir"] == "largo",
            )
            if pnl != pnl:   # nan = sin datos 1m para este momento, saltar
                continue
            resultados[estr].append({
                "fecha": ts.iloc[j],
                "dir":   sig["dir"],
                "pnl":   pnl,
                "mes":   ts.iloc[j].strftime("%Y-%m"),
            })

    return resultados

def stat(vals):
    n = len(vals)
    if not n: return 0, 0.0, 0.0
    return n, sum(1 for v in vals if v > 0) / n, sum(vals) / n

# ------------------------------------------------------------------ main
def main():
    print("BACKTEST HISTORICO GANADORAS — salida exacta con velas de 1m")
    print("Descarga ~52 dias de 15m + 1m por moneda (puede tardar 1-2 min).\n")

    try:
        ex = _ex_hl()
    except Exception as e:
        print(f"Error conectando a Hyperliquid: {e}")
        return

    for coin in ["BTC", "ETH"]:
        print(f"{'='*60}")
        # --- 15m para detectores ---
        print(f"  [{coin}] Descargando 15m (5000 velas = ~52 dias)...")
        try:
            d15 = descargar(ex, coin, "15m", 5000)
        except Exception as e:
            print(f"  Error 15m: {e}"); continue

        desde_ts = int(d15["t"].iloc[0])
        hasta_ts = int(d15["t"].iloc[-1]) + 60_000  # +1 min de margen

        fecha_ini = pd.to_datetime(desde_ts, unit="ms").strftime("%Y-%m-%d")
        fecha_fin = pd.to_datetime(hasta_ts, unit="ms").strftime("%Y-%m-%d")
        print(f"  Periodo: {fecha_ini} -> {fecha_fin}  ({len(d15)} velas 15m)")

        # --- 1m para simulacion de salidas (Binance — meses de historia vs 3-4 dias de Hyperliquid)
        # Precios Binance BTCUSDT/ETHUSDT perp difieren <0.1% de Hyperliquid: negligible
        n_min = (hasta_ts - desde_ts) // 60_000
        n_bloques = n_min // 1000 + 2
        print(f"  [{coin}] Descargando 1m de Binance (~{n_bloques} bloques = ~{n_min:,} minutos)...")
        try:
            d1m = descargar_1m_binance(coin, desde_ts, hasta_ts)
        except Exception as e:
            print(f"  Error 1m Binance: {e}"); continue
        print(f"  {len(d1m)} velas 1m descargadas.\n")

        resultados = backtest_moneda(d15, d1m)

        # --- resumen global ---
        print(f"  RESUMEN GLOBAL {coin}:")
        print(f"  {'estrategia':<22} {'n':>5}  {'win':>6}  {'exp/op':>8}  {'total':>8}")
        for estr, ops in resultados.items():
            if not ops:
                print(f"  {estr:<22}   sin senales")
                continue
            pnls = [o["pnl"] for o in ops]
            n, win, exp = stat(pnls)
            total = sum(pnls)
            print(f"  {estr:<22} n={n:>4}  {win*100:>5.0f}%  {exp:>+.3f}R  {total:>+.2f}R total")

        # --- desglose por mes ---
        print(f"\n  DESGLOSE POR MES {coin}:")
        todos_meses = sorted({o["mes"] for ops in resultados.values() for o in ops})
        for mes in todos_meses:
            lineas = []
            for estr, ops in resultados.items():
                pnls = [o["pnl"] for o in ops if o["mes"] == mes]
                if len(pnls) >= 3:
                    n, _, exp = stat(pnls)
                    lineas.append(f"{estr}({n},{exp:+.2f}R)")
            if lineas:
                print(f"    {mes}: " + "  ".join(lineas))

        # --- desglose por sesion ---
        print(f"\n  SESION (h<7=Asia, 7-13=Londres, 13+=NY):")
        for estr, ops in resultados.items():
            if len(ops) < 10: continue
            asia    = [o["pnl"] for o in ops if pd.to_datetime(o["fecha"]).hour < 7]
            londres = [o["pnl"] for o in ops if 7 <= pd.to_datetime(o["fecha"]).hour < 13]
            ny      = [o["pnl"] for o in ops if pd.to_datetime(o["fecha"]).hour >= 13]
            parts = []
            for tag, vals in [("asia", asia), ("lon", londres), ("ny", ny)]:
                if len(vals) >= 3:
                    _, _, e = stat(vals)
                    parts.append(f"{tag}={e:+.2f}R(n={len(vals)})")
            if parts:
                print(f"    {estr:<22} " + "  ".join(parts))

        print()

    print("FIN — recuerda las limitaciones: 52 dias de 15m, salidas exactas con 1m Binance, sesgo de diseno.")
    print("Si el edge se mantiene en varios meses y sesiones = senal robusta.")
    print("Si solo funciona en los ultimos dias = overfitting.")

if __name__ == "__main__":
    main()
