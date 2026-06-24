"""
BACKTEST MULTI-AÑO (Binance 15m) — ¿qué estrategias sobreviven a VARIOS REGIMENES?
==================================================================================
El backtest de 52 dias solo cubre UN regimen (oso/miedo 2026). Este saca AÑOS de
datos de Binance (toro 2021, oso 2022, recuperacion 2023-24, etc.) y mide cada
estrategia con DESGLOSE POR AÑO. Asi vemos si un edge es real o solo del tramo actual.

CLAVE METODOLOGICA:
  - Las salidas se simulan sobre las MISMAS velas de 15m (conservador: si en una vela
    se tocan stop y target, gana el stop). Menos preciso que 1m pero suficiente para
    swings y permite cubrir años sin descargar millones de velas de 1m.
  - DONCHIAN se mide con su salida REAL de trend-following (cruce de linea media =
    dejar correr la ganancia), NO con 2R fijo — porque medirlo a 2R mata su edge.
  - Todas las cifras NETAS de COSTE (0.08% ida+vuelta).

Uso:  python -m trading_latino.research.backtest_largo
      python -m trading_latino.research.backtest_largo 2023-01-01   (fecha de inicio)
"""
from __future__ import annotations
import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
import ccxt

# Reutilizamos detectores y helpers ya validados del otro backtest (su main esta guardado)
from trading_latino.research.backtest_ganadoras import (
    COSTE, LOOKBACK, _adx, _rsi, _setup,
    det_ob_trend, det_ob_plus, det_ob_regime,
)

DESDE_DEFAULT = "2021-01-01"   # cubre toro 2021 + oso 2022 + 2023-2026

# ------------------------------------------------------------------ descarga 15m Binance multi-año
def descargar_15m_binance(coin: str, desde_ts: int, hasta_ts: int) -> pd.DataFrame:
    """15m de Binance Futures en bloques de 1000. Binance guarda años de 15m."""
    ex = ccxt.binance({"options": {"defaultType": "future"}})
    simbolo = f"{coin}USDT"
    TF_MS = 15 * 60_000
    bloques, t, n = [], desde_ts, 0
    while t < hasta_ts:
        o = None
        for intento in range(6):                       # REINTENTOS: un hipo de red no debe cortar la descarga
            try:
                o = ex.fetch_ohlcv(simbolo, "15m", since=t, limit=1000)
                break
            except Exception as e:
                espera = 2 * (intento + 1)
                print(f"    [Binance] error bloque {n} (intento {intento+1}/6): {e} — reintento en {espera}s")
                time.sleep(espera)
        if o is None:                                  # solo se rinde tras 6 intentos fallidos
            print(f"    [Binance] bloque {n} FALLA tras 6 intentos. Descarga PARCIAL (hasta aqui).")
            break
        if not o:
            break
        bloques.extend(o)
        t = o[-1][0] + TF_MS
        n += 1
        if n % 20 == 0:
            print(f"    ... {n} bloques ({len(bloques):,} velas)")
    if not bloques:
        return pd.DataFrame(columns=["t", "apertura", "maximo", "minimo", "cierre", "volumen"])
    d = pd.DataFrame(bloques, columns=["t", "apertura", "maximo", "minimo", "cierre", "volumen"])
    d["t"] = d["t"].astype("int64")
    return d.drop_duplicates("t").sort_values("t").reset_index(drop=True)

# ------------------------------------------------------------------ detectores extra (portados de arena.py)
def det_merino(d, coin="ETH"):
    """Trading Latino: EMA10/55 + ADX>23 + giro de Squeeze momentum. (Merino no corta BTC)."""
    c = d["cierre"]
    e10 = c.ewm(span=10, adjust=False).mean().to_numpy()
    e55 = c.ewm(span=55, adjust=False).mean().to_numpy()
    hh = d["maximo"].rolling(20).max(); ll = d["minimo"].rolling(20).min()
    mom = (c - ((hh + ll) / 2 + c.rolling(20).mean()) / 2).to_numpy()
    adx = _adx(d); j = len(c) - 1; cl = c.to_numpy()
    if j < 60 or np.isnan(adx[j]) or np.isnan(mom[j - 1]): return None
    swl = d["minimo"].iloc[j - 10:j].min(); swh = d["maximo"].iloc[j - 10:j].max()
    if e10[j] > e55[j] and adx[j] > 23 and mom[j] > 0 >= mom[j - 1]:
        return _setup("largo", cl[j], swl)
    if coin != "BTC" and e10[j] < e55[j] and adx[j] > 23 and mom[j] < 0 <= mom[j - 1]:
        return _setup("corto", cl[j], swh)
    return None

def det_merinox(d):
    """Merino enriquecido: + alineacion EMA200 + sin climax de volumen."""
    c = d["cierre"]
    e10 = c.ewm(span=10, adjust=False).mean().to_numpy()
    e55 = c.ewm(span=55, adjust=False).mean().to_numpy()
    e200 = c.ewm(span=200, adjust=False).mean().to_numpy()
    hh = d["maximo"].rolling(20).max(); ll = d["minimo"].rolling(20).min()
    mom = (c - ((hh + ll) / 2 + c.rolling(20).mean()) / 2).to_numpy()
    adx = _adx(d)
    vol = d["volumen"].to_numpy(); vm = d["volumen"].rolling(20).mean().shift(1).to_numpy()
    cl = c.to_numpy(); j = len(cl) - 1
    if j < 200 or np.isnan(adx[j]) or np.isnan(mom[j - 1]) or np.isnan(e200[j]) or not vm[j]: return None
    swl = d["minimo"].iloc[j - 10:j].min(); swh = d["maximo"].iloc[j - 10:j].max()
    volok = vol[j] < 2.5 * vm[j]
    if e10[j] > e55[j] and cl[j] > e200[j] and adx[j] > 20 and mom[j] > 0 >= mom[j - 1] and volok:
        return _setup("largo", cl[j], swl, 2.0)
    if e10[j] < e55[j] and cl[j] < e200[j] and adx[j] > 20 and mom[j] < 0 <= mom[j - 1] and volok:
        return _setup("corto", cl[j], swh, 2.0)
    return None

def det_merinox_adx(d):
    """merinox + ADX SUBIENDO (momentum acelerando). Hipótesis: la pista en vivo (ADX-sube=+1.96R vs
    ADX-baja=-0.68R) era n=7 (ruido); aquí se prueba a ESCALA multi-año (miles de ops) si el filtro
    'solo entrar cuando el momentum acelera' mejora a merinox de verdad."""
    sig = det_merinox(d)
    if sig is None: return None
    adx = _adx(d)
    if len(adx) >= 2 and not np.isnan(adx[-1]) and not np.isnan(adx[-2]) and adx[-1] > adx[-2]:
        return sig
    return None

def det_vwap(d):
    """Rebote en VWAP(50): el precio vuelve al VWAP y aguanta -> largo (y espejo)."""
    tp = (d["maximo"] + d["minimo"] + d["cierre"]) / 3
    vwap = ((tp * d["volumen"]).rolling(50).sum() / d["volumen"].rolling(50).sum()).to_numpy()
    lo = d["minimo"].to_numpy(); hi = d["maximo"].to_numpy(); cl = d["cierre"].to_numpy(); j = len(cl) - 1
    if j < 55 or np.isnan(vwap[j]): return None
    swl = d["minimo"].iloc[j - 7:j].min(); swh = d["maximo"].iloc[j - 7:j].max()
    if lo[j] <= vwap[j] and cl[j] > vwap[j] and cl[j - 1] > vwap[j - 1]:
        return _setup("largo", cl[j], swl, 2.0)
    if hi[j] >= vwap[j] and cl[j] < vwap[j] and cl[j - 1] < vwap[j - 1]:
        return _setup("corto", cl[j], swh, 2.0)
    return None

def det_mean_rev(d, target_mode="2R"):
    """REVERSIÓN A LA MEDIA (anti-tendencia): comprar capitulación / vender euforia.
    Banda inferior (SMA20 − 2.5σ) + RSI14<25 + clímax de volumen (>1.8× media) = agotamiento.
    En 50d (régimen bajista) PERDIÓ (-0.32R): atrapar cuchillos. Aquí se prueba en régimen LATERAL
    (2023) que es donde la reversión a la media DEBERÍA funcionar. Espejo para euforia.
    target_mode: '2R' (comparable) | 'mean' (salida natural a la SMA20)."""
    cl = d["cierre"].to_numpy(); hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    vol = d["volumen"].to_numpy(); j = len(cl) - 1
    if j < 30: return None
    sma20 = d["cierre"].rolling(20).mean().to_numpy()
    std20 = d["cierre"].rolling(20).std().to_numpy()
    rsi = _rsi(d["cierre"])
    vm = pd.Series(vol).rolling(20).mean().to_numpy()
    if np.isnan(sma20[j]) or np.isnan(std20[j]) or np.isnan(rsi[j]) or not vm[j]: return None
    atr = _atr14_largo(d)
    banda_inf = sma20[j] - 2.5 * std20[j]; banda_sup = sma20[j] + 2.5 * std20[j]
    if lo[j] <= banda_inf and rsi[j] < 25 and vol[j] > 1.8 * vm[j]:
        entry = cl[j]; stop = lo[j] - 0.5 * atr[j]
        if target_mode == "mean":
            D = entry - stop
            if D <= 0: return None
            r = (sma20[j] - entry) / D
            return _setup("largo", entry, stop, r) if r > 0 else None
        return _setup("largo", entry, stop, 2.0)
    if hi[j] >= banda_sup and rsi[j] > 75 and vol[j] > 1.8 * vm[j]:
        entry = cl[j]; stop = hi[j] + 0.5 * atr[j]
        if target_mode == "mean":
            D = stop - entry
            if D <= 0: return None
            r = (entry - sma20[j]) / D
            return _setup("corto", entry, stop, r) if r > 0 else None
        return _setup("corto", entry, stop, 2.0)
    return None

def det_mean_rev_2R(d):   return det_mean_rev(d, "2R")
def det_mean_rev_mean(d): return det_mean_rev(d, "mean")

def _atr14_largo(d):
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    tr = np.maximum(hi[1:] - lo[1:],
                    np.maximum(np.abs(hi[1:] - cl[:-1]), np.abs(lo[1:] - cl[:-1])))
    tr_full = np.concatenate([[hi[0] - lo[0]], tr])
    return pd.Series(tr_full).ewm(span=14, adjust=False).mean().to_numpy()

def det_atr_break(d):
    """Canal de Keltner (EMA20 ± 2×ATR14). Misma lógica que en backtest_ganadoras."""
    cl = d["cierre"].to_numpy(); hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    j = len(cl) - 1
    if j < 30: return None
    atr   = _atr14_largo(d)
    ema20 = d["cierre"].ewm(span=20, adjust=False).mean().to_numpy()
    if np.isnan(atr[j]) or np.isnan(ema20[j]) or np.isnan(atr[j-1]) or np.isnan(ema20[j-1]): return None
    bu  = ema20[j]   + 2.0 * atr[j];   bd  = ema20[j]   - 2.0 * atr[j]
    bu1 = ema20[j-1] + 2.0 * atr[j-1]; bd1 = ema20[j-1] - 2.0 * atr[j-1]
    sl = lo[max(0, j-10):j].min(); sh = hi[max(0, j-10):j].max()
    if cl[j] > bu and cl[j-1] <= bu1: return _setup("largo", cl[j], sl, 2.0)
    if cl[j] < bd and cl[j-1] >= bd1: return _setup("corto", cl[j], sh, 2.0)
    return None

def det_atr_break_trend(d):
    """ATR Breakout + alineación EMA200."""
    j = len(d) - 1
    if j < 215: return None
    ema200 = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    if np.isnan(ema200[j]): return None
    base = det_atr_break(d)
    if base is None: return None
    cl = d["cierre"].to_numpy()
    if base["dir"] == "largo" and cl[j] < ema200[j]: return None
    if base["dir"] == "corto" and cl[j] > ema200[j]: return None
    return base

DONCHIAN_N = 20
def det_donchian(d):
    """Ruptura de canal Donchian (N=20). SIN target fijo — la salida la gestiona el motor
    de trend-following (cruce de linea media). Devuelve setup SIN target util."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy(); j = len(cl) - 1
    if j < DONCHIAN_N + 5: return None
    hh = hi[j - DONCHIAN_N:j].max(); ll = lo[j - DONCHIAN_N:j].min()
    sl = lo[j - 10:j].min(); sh = hi[j - 10:j].max()
    if cl[j] > hh and cl[j - 1] <= hh:
        return _setup("largo", cl[j], sl, 2.0)
    if cl[j] < ll and cl[j - 1] >= ll:
        return _setup("corto", cl[j], sh, 2.0)
    return None

# ------------------------------------------------------------------ simuladores de salida (sobre 15m)
def salida_fija(d, j_ent, stop, target, es_largo, max_bars=192):
    """Sale en stop o target (lo que toque antes). Conservador: stop gana si ambos en la misma vela."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    entry = cl[j_ent]; D = abs(entry - stop)
    if D == 0: return -COSTE
    Rt = abs(target - entry) / D
    fin = min(j_ent + max_bars, len(d))
    for i in range(j_ent + 1, fin):
        if es_largo:
            if lo[i] <= stop: return -1.0 - COSTE
            if hi[i] >= target: return Rt - COSTE
        else:
            if hi[i] >= stop: return -1.0 - COSTE
            if lo[i] <= target: return Rt - COSTE
    salida = cl[min(fin - 1, len(d) - 1)]
    pnl = (salida - entry) / D if es_largo else (entry - salida) / D
    return pnl - COSTE

def salida_donchian(d, j_ent, stop, es_largo, n=DONCHIAN_N, max_bars=1500):
    """Trend-following REAL: aguanta hasta que el precio cruza la LINEA MEDIA del canal
    en contra (o salta el stop inicial). R = riesgo inicial (entry-stop). Deja correr ganancias."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    entry = cl[j_ent]; D = abs(entry - stop)
    if D == 0: return -COSTE
    fin = min(j_ent + max_bars, len(d))
    for i in range(j_ent + 1, fin):
        # stop inicial de proteccion
        if es_largo and lo[i] <= stop: return -1.0 - COSTE
        if not es_largo and hi[i] >= stop: return -1.0 - COSTE
        # linea media del canal en i
        if i < n: continue
        ml = (hi[i - n:i].max() + lo[i - n:i].min()) / 2
        if es_largo and cl[i] < ml:
            return (cl[i] - entry) / D - COSTE
        if not es_largo and cl[i] > ml:
            return (entry - cl[i]) / D - COSTE
    salida = cl[min(fin - 1, len(d) - 1)]
    pnl = (salida - entry) / D if es_largo else (entry - salida) / D
    return pnl - COSTE

# ------------------------------------------------------------------ variantes con FILTRO (la pregunta abierta)
def _hora(d):
    return int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)

def _ses_ant_bajista(d):
    """¿La sesión anterior (Asia/Londres/NY) cerró por debajo de donde abrió? (deducible del precio)."""
    h = _hora(d)
    if 7 <= h < 13:   rng = (0, 7)
    elif 13 <= h < 21: rng = (7, 13)
    else:              rng = (13, 21)
    t = d["t"].to_numpy(); cl = d["cierre"].to_numpy()
    hh = pd.to_datetime(t, unit="ms").hour
    idx = np.where((hh >= rng[0]) & (hh < rng[1]))[0]
    if len(idx) < 2: return None
    blo = idx[idx >= idx.max() - 30]
    return cl[blo[-1]] < cl[blo[0]]

# La PREGUNTA: ¿el filtro Asia hace robusto al OB (que base no tiene edge)?
def det_ob_plus_asia(d):
    if _hora(d) >= 7: return None
    return det_ob_plus(d)
def det_ob_regime_asia(d):
    if _hora(d) >= 13: return None
    return det_ob_regime(d)
# La 2ª palanca: ¿saltarse longs tras sesión previa bajista mejora el OB?
def det_ob_trend_nofade(d):
    sig = det_ob_trend(d)
    if sig and sig["dir"] == "largo" and _ses_ant_bajista(d) is True:
        return None
    return sig

# ------------------------------------------------------------------ registro de estrategias
# cada entrada: (detector, modo_salida)  modo: "fija" | "donchian"
def _mk_merino(coin):
    return lambda d: det_merino(d, coin)

def estrategias_para(coin):
    return {
        # --- familia OB base (multi-año: SIN edge, -0.03R) ---
        "ob_trend":  (det_ob_trend,  "fija"),
        "ob_plus":   (det_ob_plus,   "fija"),
        # --- LA PREGUNTA ABIERTA: ¿el filtro Asia/prev-sesión rescata el OB across regímenes? ---
        "ob_plus_asia":    (det_ob_plus_asia,    "fija"),   # ¿el filtro Asia es robusto o suerte reciente?
        "ob_regime_asia":  (det_ob_regime_asia,  "fija"),
        "ob_trend_nofade": (det_ob_trend_nofade, "fija"),   # ¿saltar longs tras sesión previa bajista mejora?
        # --- Merino / momentum (LA familia robusta del multi-año) ---
        "merino":      (_mk_merino(coin), "fija"),
        "merinox":     (det_merinox,     "fija"),
        "merinox_adx": (det_merinox_adx, "fija"),   # PRUEBA: ¿ADX subiendo (momentum acelera) mejora merinox?
        # --- VWAP rolling (sin anclar — baseline) ---
        "vwap":      (det_vwap,      "fija"),
        # --- Donchian: 2 hipótesis de salida enfrentadas ---
        "donchian_2R":    (det_donchian, "fija"),      # ¿funciona con salida fija?
        "donchian_trend": (det_donchian, "donchian"),  # ¿funciona dejando correr?
        # --- ATR Breakout (canal adaptativo vs Donchian fijo) ---
        "atr_break":       (det_atr_break,       "fija"),  # baseline sin filtros
        "atr_break_trend": (det_atr_break_trend, "fija"),  # + EMA200: ¿mejora en todos los regímenes?
        # --- Mean Reversion (anti-tendencia): perdió en 50d bajista, ¿gana en lateral 2023? ---
        "mean_rev_2R":   (det_mean_rev_2R,   "fija"),
        "mean_rev_mean": (det_mean_rev_mean, "fija"),
    }

# ------------------------------------------------------------------ clasificacion de REGIMEN (sin mirar al futuro)
def clasificar_regimen(d, dias=90, umbral=0.25):
    """Etiqueta CADA vela por el régimen de mercado en ese instante, usando SOLO el pasado
    (retorno de los últimos `dias`): así una operación sabe si ocurrió en crash, lateral o subida.
      alcista  = el precio subió  > +umbral en 90 días (toro/euforia)
      bajista  = el precio cayó   < -umbral en 90 días (crash/oso)
      lateral  = se movió en medio (rango/aburrimiento)
    Objetivo (no se eligen fechas a dedo = sin autoengaño). 96 velas de 15m = 1 día."""
    cl = d["cierre"].to_numpy()
    n_atras = dias * 96
    reg = np.full(len(cl), "?", dtype=object)
    if len(cl) > n_atras:
        r = cl[n_atras:] / cl[:-n_atras] - 1
        reg[n_atras:] = np.where(r > umbral, "alcista", np.where(r < -umbral, "bajista", "lateral"))
    return reg

# ------------------------------------------------------------------ motor
def backtest(d, coin):
    estr = estrategias_para(coin)
    res = {e: [] for e in estr}
    ts = pd.to_datetime(d["t"], unit="ms")
    reg = clasificar_regimen(d)                       # régimen por vela (alcista/bajista/lateral)
    for j in range(LOOKBACK, len(d) - 1):
        ventana = d.iloc[j - LOOKBACK: j + 1].reset_index(drop=True)
        for nombre, (det, modo) in estr.items():
            try:
                sig = det(ventana)
            except Exception:
                continue
            if sig is None: continue
            es_largo = sig["dir"] == "largo"
            if modo == "donchian":
                pnl = salida_donchian(d, j, sig["stop"], es_largo)
            else:
                pnl = salida_fija(d, j, sig["stop"], sig["target"], es_largo)
            res[nombre].append({"anio": ts.iloc[j].year, "regimen": reg[j], "pnl": pnl, "dir": sig["dir"]})
    return res

def stat(v):
    n = len(v)
    if not n: return 0, 0.0, 0.0
    return n, sum(1 for x in v if x > 0) / n, sum(v) / n

def main():
    desde = sys.argv[1] if len(sys.argv) > 1 else DESDE_DEFAULT
    desde_ts = int(pd.Timestamp(desde, tz="UTC").timestamp() * 1000)
    hasta_ts = int(pd.Timestamp.now("UTC").timestamp() * 1000)
    print(f"BACKTEST MULTI-AÑO — desde {desde} hasta hoy. Salidas sobre 15m (conservador).")
    print("Donchian se mide con su salida REAL (trend-following), no 2R fijo.\n")

    for coin in ["BTC", "ETH", "SOL"]:
        print("=" * 64)
        print(f"  [{coin}] descargando 15m de Binance desde {desde}...")
        d = descargar_15m_binance(coin, desde_ts, hasta_ts)
        if len(d) < 500:
            print(f"  {coin}: datos insuficientes ({len(d)} velas), salto."); continue
        ini = pd.to_datetime(int(d['t'].iloc[0]), unit='ms').strftime('%Y-%m-%d')
        fin = pd.to_datetime(int(d['t'].iloc[-1]), unit='ms').strftime('%Y-%m-%d')
        print(f"  {len(d):,} velas 15m  ({ini} -> {fin})")
        # AVISO de truncamiento: si la descarga quedó >2 dias corta, los datos NO son completos
        horas_falta = (hasta_ts - int(d['t'].iloc[-1])) / 3_600_000
        if horas_falta > 48:
            print(f"  ⚠️⚠️ DATOS INCOMPLETOS: faltan {horas_falta/24:.0f} dias hasta hoy. "
                  f"El regimen reciente NO esta cubierto. Revisar descarga antes de fiarse.")
        print()

        res = backtest(d, coin)

        print(f"  GLOBAL {coin}:")
        print(f"  {'estrategia':<18} {'n':>6} {'win':>6} {'exp/op':>9} {'total':>10}")
        for e, ops in res.items():
            pnls = [o["pnl"] for o in ops]
            n, w, ex = stat(pnls)
            if not n:
                print(f"  {e:<18}   sin senales"); continue
            print(f"  {e:<18} {n:>6} {w*100:>5.0f}% {ex:>+8.3f}R {sum(pnls):>+9.1f}R")

        print(f"\n  POR AÑO {coin} (exp/op | n):")
        anios = sorted({o["anio"] for ops in res.values() for o in ops})
        print(f"  {'estrategia':<18} " + " ".join(f"{a:>13}" for a in anios))
        for e, ops in res.items():
            celdas = []
            for a in anios:
                pn = [o["pnl"] for o in ops if o["anio"] == a]
                if len(pn) >= 10:
                    _, _, ex = stat(pn)
                    celdas.append(f"{ex:>+6.2f}({len(pn):>4})")
                else:
                    celdas.append(f"{'—':>13}")
            print(f"  {e:<18} " + " ".join(celdas))
        print()

        # --- DESGLOSE POR RÉGIMEN: lo que de verdad importa (¿gana en crash/lateral/subida?) ---
        print(f"  POR RÉGIMEN {coin} (exp/op | n) — ¿en qué CLIMA de mercado gana cada una?:")
        regs = ["alcista", "lateral", "bajista"]
        # cuántas velas hubo de cada régimen (para contexto)
        reg_all = clasificar_regimen(d)
        from collections import Counter
        cnt = Counter(reg_all[LOOKBACK:])
        print(f"  {'(velas por clima)':<18} " + " ".join(f"{r}={cnt.get(r,0):,}".rjust(15) for r in regs))
        print(f"  {'estrategia':<18} " + " ".join(f"{r:>15}" for r in regs))
        for e, ops in res.items():
            celdas = []
            for r in regs:
                pn = [o["pnl"] for o in ops if o.get("regimen") == r]
                if len(pn) >= 10:
                    _, _, ex = stat(pn)
                    celdas.append(f"{ex:>+7.2f}({len(pn):>5})")
                else:
                    celdas.append(f"{'—':>15}")
            print(f"  {e:<18} " + " ".join(celdas))
        print()

    print("FIN — busca estrategias POSITIVAS en VARIOS climas (alcista Y lateral Y bajista).")
    print("Un edge que solo gana en bajista = herramienta de un clima. Que gana en los 3 = robusto de verdad.")

if __name__ == "__main__":
    main()
