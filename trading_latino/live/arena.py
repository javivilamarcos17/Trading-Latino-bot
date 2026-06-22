"""
ARENA EN VIVO (Hyperliquid) — varias ESTRATEGIAS x varias TEMPORALIDADES, en PAPEL. Sin órdenes.

Filosofía: en vez de creernos un backtest, ponemos a competir las estrategias más prometedoras EN
DIRECTO, registramos TODO (aciertos y fallos) y vemos cuál funciona de verdad estos días. Adaptativo:
añadir o ajustar una estrategia es una función más. Cada operación se mide en % (neto de coste) para
que TODAS sean comparables en una tabla.

Estrategias incluidas (las prometedoras + Merino):
  - smc     : FVG del marco mayor (1h) + BOS en el menor (la operativa SMC).
  - merino  : Trading Latino (EMA10/55 + ADX>23 + Squeeze momentum), bracket 2R.
  - sweep   : barrido de liquidez (máx/mín iguales) + reversión.
  - fvg     : retest simple de FVG en la propia temporalidad.

Ejecútalo cada pocos minutos (tarea programada o bucle). En unos días tendrás la simulación real.

Uso:  python -m trading_latino.live.arena
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import ccxt
import numpy as np
import pandas as pd

REG = Path(__file__).resolve().parents[2] / "data_store" / "paper_arena"
COINS = ["BTC", "ETH", "SOL", "XRP", "DOGE", "AVAX"]   # red ampliada para recoger más datos
# cada estrategia corre en SUS temporalidades (scalping en rápidas)
ESTRATEGIAS_TF = {
    "smc": ["15m", "1h"], "merino": ["15m", "1h"], "sweep": ["15m", "1h"], "fvg": ["15m", "1h"],
    "ob": ["15m", "1h"], "rsi": ["15m", "1h"], "volumen": ["15m", "1h"], "adx": ["15m", "1h"],
    "rsidiv": ["15m", "1h", "4h"], "scalp_sqz": ["1m", "5m"], "scalp_rev": ["1m", "5m"],
}
HTF_DE = {"15m": "1h", "1h": "4h"}      # marco mayor para SMC según el menor
# Coste REALISTA por operación (ida+vuelta): Hyperliquid taker ~0.035%/lado + slippage.
# Lo ponemos conservador (0.08%) para que la rentabilidad medida sea honesta, no optimista.
COSTE = 0.0008
R_MULT = 2.0
FRACTAL = 2


def _ex():
    return ccxt.hyperliquid({"enableRateLimit": True, "timeout": 20000})


def velas(ex, coin, tf, limit=500):
    o = ex.fetch_ohlcv(f"{coin}/USDC:USDC", tf, limit=limit)
    d = pd.DataFrame(o, columns=["t", "apertura", "maximo", "minimo", "cierre", "volumen"])
    return d


def _swings(d):
    w = 2 * FRACTAL + 1
    swh = (d["maximo"].rolling(w, center=True).max().to_numpy() == d["maximo"].to_numpy())
    swl = (d["minimo"].rolling(w, center=True).min().to_numpy() == d["minimo"].to_numpy())
    last_sh = pd.Series(np.where(swh, d["maximo"], np.nan)).ffill().shift(FRACTAL).to_numpy()
    last_sl = pd.Series(np.where(swl, d["minimo"], np.nan)).ffill().shift(FRACTAL).to_numpy()
    return last_sh, last_sl


def _adx(d, n=14):
    h, l, c = d["maximo"], d["minimo"], d["cierre"]
    up = h.diff(); dn = -l.diff()
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / n, adjust=False).mean()
    pdi = 100 * pd.Series(pdm, index=d.index).ewm(alpha=1 / n, adjust=False).mean() / atr
    mdi = 100 * pd.Series(mdm, index=d.index).ewm(alpha=1 / n, adjust=False).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean().to_numpy()


def _setup(direc, entrada, stop, r=R_MULT):
    D = (entrada - stop) if direc == "largo" else (stop - entrada)
    if D <= 0:
        return None
    target = entrada + r * D if direc == "largo" else entrada - r * D
    return {"dir": direc, "entry": float(entrada), "stop": float(stop), "target": float(target)}


def _rsi(c, n=14):
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return (100 - 100 / (1 + up / dn.replace(0, np.nan))).to_numpy()


# ---------- detectores: reciben velas CERRADAS y devuelven setup en la última, o None ----------
def det_merino(d, coin):
    c = d["cierre"]
    e10 = c.ewm(span=10, adjust=False).mean().to_numpy()
    e55 = c.ewm(span=55, adjust=False).mean().to_numpy()
    hh = d["maximo"].rolling(20).max(); ll = d["minimo"].rolling(20).min()
    mom = (c - ((hh + ll) / 2 + c.rolling(20).mean()) / 2).to_numpy()
    adx = _adx(d)
    j = len(c) - 1
    cl = c.to_numpy()
    if j < 60 or np.isnan(adx[j]) or np.isnan(mom[j - 1]):
        return None
    swl = d["minimo"].iloc[j - 10:j].min(); swh = d["maximo"].iloc[j - 10:j].max()
    if e10[j] > e55[j] and adx[j] > 23 and mom[j] > 0 >= mom[j - 1]:        # momentum gira alcista
        return _setup("largo", cl[j], swl)
    if coin != "BTC" and e10[j] < e55[j] and adx[j] > 23 and mom[j] < 0 <= mom[j - 1]:  # Merino no corta BTC
        return _setup("corto", cl[j], swh)
    return None


def det_sweep(d):
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    vol = d["volumen"].to_numpy(); vm = d["volumen"].rolling(20).mean().shift(1).to_numpy()
    j = len(cl) - 1
    if j < 60:
        return None
    sh = hi[j - 50:j].max(); sl = lo[j - 50:j].min()
    cuerpo = abs(cl[j] - op[j]) + 1e-9
    volok = vm[j] and vol[j] > 1.8 * vm[j]
    if hi[j] > sh and cl[j] < sh and volok and (hi[j] - max(cl[j], op[j])) > cuerpo:   # barrido máx -> corto
        return _setup("corto", cl[j], hi[j] * 1.0007)
    if lo[j] < sl and cl[j] > sl and volok and (min(cl[j], op[j]) - lo[j]) > cuerpo:   # barrido mín -> largo
        return _setup("largo", cl[j], lo[j] * 0.9993)
    return None


def det_fvg(d):
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    j = len(cl) - 1
    if j < 30:
        return None
    # ¿la vela j-1..j-3 formó un FVG que se está retesteando ahora?
    for i in range(j - 20, j - 1):
        if lo[i] > hi[i - 2] and (lo[i] - hi[i - 2]) / cl[i] > 0.0008:      # FVG alcista
            if lo[j] <= lo[i] and cl[j] > hi[i - 2]:                        # retest y aguanta
                return _setup("largo", cl[j], hi[i - 2] * 0.9993)
        if hi[i] < lo[i - 2] and (lo[i - 2] - hi[i]) / cl[i] > 0.0008:      # FVG bajista
            if hi[j] >= hi[i] and cl[j] < lo[i - 2]:
                return _setup("corto", cl[j], lo[i - 2] * 1.0007)
    return None


def det_scalp_sqz(d):
    """Scalp: Squeeze momentum + RSI. Momentum gira y RSI confirma. Stop ajustado, objetivo 1.5R."""
    c = d["cierre"]
    hh = d["maximo"].rolling(20).max(); ll = d["minimo"].rolling(20).min()
    mom = (c - ((hh + ll) / 2 + c.rolling(20).mean()) / 2).to_numpy()
    rsi = _rsi(c)
    cl = c.to_numpy(); j = len(cl) - 1
    if j < 25 or np.isnan(mom[j - 1]) or np.isnan(rsi[j]):
        return None
    swl = d["minimo"].iloc[j - 7:j].min(); swh = d["maximo"].iloc[j - 7:j].max()
    if mom[j] > 0 >= mom[j - 1] and rsi[j] > 50:
        return _setup("largo", cl[j], swl, 1.5)
    if mom[j] < 0 <= mom[j - 1] and rsi[j] < 50:
        return _setup("corto", cl[j], swh, 1.5)
    return None


def det_scalp_rev(d):
    """Scalp: reversión a la media. Mecha fuera de la banda de Bollinger 2σ y cierre dentro -> reversión."""
    c = d["cierre"]; ma = c.rolling(20).mean(); sd = c.rolling(20).std()
    up = (ma + 2 * sd).to_numpy(); dn = (ma - 2 * sd).to_numpy()
    lo = d["minimo"].to_numpy(); hi = d["maximo"].to_numpy(); cl = c.to_numpy()
    j = len(cl) - 1
    if j < 25 or np.isnan(dn[j]):
        return None
    if lo[j] <= dn[j] and cl[j] > dn[j]:
        return _setup("largo", cl[j], lo[j] * 0.999, 1.5)
    if hi[j] >= up[j] and cl[j] < up[j]:
        return _setup("corto", cl[j], hi[j] * 1.001, 1.5)
    return None


def det_ob(d):
    """Order Block: última vela opuesta antes de un impulso; retest de su zona -> entrada."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    j = len(cl) - 1
    if j < 25:
        return None
    for i in range(j - 20, j - 1):
        if cl[i] < op[i] and cl[i + 1] > hi[i] and (hi[i] - lo[i]) / cl[i] > 0.0008:    # OB alcista
            if lo[i] <= lo[j] <= hi[i] and cl[j] > lo[i]:
                return _setup("largo", cl[j], lo[i] * 0.999)
        if cl[i] > op[i] and cl[i + 1] < lo[i] and (hi[i] - lo[i]) / cl[i] > 0.0008:    # OB bajista
            if lo[i] <= hi[j] <= hi[i] and cl[j] < hi[i]:
                return _setup("corto", cl[j], hi[i] * 1.001)
    return None


def det_rsi(d):
    """RSI: sale de sobreventa (<30) -> largo; sale de sobrecompra (>70) -> corto."""
    c = d["cierre"]; rsi = _rsi(c); cl = c.to_numpy(); j = len(cl) - 1
    if j < 20 or np.isnan(rsi[j - 1]):
        return None
    swl = d["minimo"].iloc[j - 7:j].min(); swh = d["maximo"].iloc[j - 7:j].max()
    if rsi[j - 1] < 30 <= rsi[j]:
        return _setup("largo", cl[j], swl)
    if rsi[j - 1] > 70 >= rsi[j]:
        return _setup("corto", cl[j], swh)
    return None


def det_volumen(d):
    """Clímax de volumen: pico de volumen + mecha de rechazo larga -> reversión."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    vol = d["volumen"].to_numpy(); vm = d["volumen"].rolling(20).mean().shift(1).to_numpy()
    j = len(cl) - 1
    if j < 25 or not vm[j] or np.isnan(vm[j]):
        return None
    cuerpo = abs(cl[j] - op[j]) + 1e-9
    if vol[j] > 3 * vm[j]:
        if (min(cl[j], op[j]) - lo[j]) > 1.5 * cuerpo:
            return _setup("largo", cl[j], lo[j] * 0.999)
        if (hi[j] - max(cl[j], op[j])) > 1.5 * cuerpo:
            return _setup("corto", cl[j], hi[j] * 1.001)
    return None


def det_adx(d):
    """ADX: tendencia fuerte y creciente (>25) a favor de la EMA20 -> continuación."""
    c = d["cierre"]; e20 = c.ewm(span=20, adjust=False).mean().to_numpy(); adx = _adx(d); cl = c.to_numpy()
    j = len(cl) - 1
    if j < 40 or np.isnan(adx[j]) or np.isnan(adx[j - 1]):
        return None
    swl = d["minimo"].iloc[j - 7:j].min(); swh = d["maximo"].iloc[j - 7:j].max()
    if adx[j] > 25 and adx[j] > adx[j - 1] and cl[j] > e20[j] and cl[j] > cl[j - 1]:
        return _setup("largo", cl[j], swl)
    if adx[j] > 25 and adx[j] > adx[j - 1] and cl[j] < e20[j] and cl[j] < cl[j - 1]:
        return _setup("corto", cl[j], swh)
    return None


def det_rsidiv(d):
    """Divergencia RSI: precio hace mínimo más bajo pero RSI más alto (alcista) -> largo; espejo bajista."""
    c = d["cierre"]; rsi = _rsi(c)
    lo = d["minimo"].to_numpy(); hi = d["maximo"].to_numpy(); cl = c.to_numpy()
    j = len(cl) - 1
    if j < 45 or np.isnan(rsi[j]):
        return None
    vent = range(j - 30, j - 4)
    pl = min(vent, key=lambda k: lo[k])      # mínimo de precio previo
    ph = max(vent, key=lambda k: hi[k])      # máximo de precio previo
    if lo[j] < lo[pl] and rsi[j] > rsi[pl] and rsi[j] < 50:        # divergencia alcista
        return _setup("largo", cl[j], lo[j] * 0.999, 2.0)
    if hi[j] > hi[ph] and rsi[j] < rsi[ph] and rsi[j] > 50:        # divergencia bajista
        return _setup("corto", cl[j], hi[j] * 1.001, 2.0)
    return None


def det_smc(ex, coin, ltf):
    htf = HTF_DE[ltf]
    H = velas(ex, coin, htf, 300).iloc[:-1]
    hi = H["maximo"].to_numpy(); lo = H["minimo"].to_numpy(); clh = H["cierre"].to_numpy()
    ema = H["cierre"].ewm(span=100, adjust=False).mean().to_numpy()
    zonas = []
    for i in range(2, len(clh)):
        if lo[i] > hi[i - 2] and (lo[i] - hi[i - 2]) / clh[i] > 0.0008 and clh[i] > ema[i]:
            zonas.append((hi[i - 2], lo[i], "largo"))
        if hi[i] < lo[i - 2] and (lo[i - 2] - hi[i]) / clh[i] > 0.0008 and clh[i] < ema[i]:
            zonas.append((hi[i], lo[i - 2], "corto"))
    L = velas(ex, coin, ltf, 500).iloc[:-1]
    last_sh, last_sl = _swings(L)
    cl = L["cierre"].to_numpy(); lo2 = L["minimo"].to_numpy(); hi2 = L["maximo"].to_numpy()
    j = len(cl) - 1
    if j < 30:
        return None, L
    for (bot, top, direc) in zonas[-30:]:
        if direc == "largo" and (lo2[j - 60:j + 1] <= top).any() and cl[j] > bot:
            if not np.isnan(last_sh[j]) and cl[j] > last_sh[j] and cl[j - 1] <= last_sh[j]:
                return _setup("largo", cl[j], bot * 0.9993), L
        if direc == "corto" and (hi2[j - 60:j + 1] >= bot).any() and cl[j] < top:
            if not np.isnan(last_sl[j]) and cl[j] < last_sl[j] and cl[j - 1] >= last_sl[j]:
                return _setup("corto", cl[j], top * 1.0007), L
    return None, L


def detectar(estr, ex, coin, tf):
    if estr == "smc":
        s, L = det_smc(ex, coin, tf); return s, L
    L = velas(ex, coin, tf, 500)
    cerr = L.iloc[:-1]
    if estr == "merino":
        return det_merino(cerr, coin), L
    if estr == "sweep":
        return det_sweep(cerr), L
    if estr == "fvg":
        return det_fvg(cerr), L
    if estr == "scalp_sqz":
        return det_scalp_sqz(cerr), L
    if estr == "scalp_rev":
        return det_scalp_rev(cerr), L
    if estr == "ob":
        return det_ob(cerr), L
    if estr == "rsi":
        return det_rsi(cerr), L
    if estr == "volumen":
        return det_volumen(cerr), L
    if estr == "adx":
        return det_adx(cerr), L
    if estr == "rsidiv":
        return det_rsidiv(cerr), L
    return None, L


def detectar_cerr(estr, cerr, coin):
    """Ejecuta el detector (no-SMC) sobre un frame cuya ÚLTIMA fila es la vela a evaluar.
    Permite revisar bar a bar las velas que cerraron desde la última ejecución (backfill)."""
    if estr == "merino":
        return det_merino(cerr, coin)
    if estr == "sweep":
        return det_sweep(cerr)
    if estr == "fvg":
        return det_fvg(cerr)
    if estr == "ob":
        return det_ob(cerr)
    if estr == "rsi":
        return det_rsi(cerr)
    if estr == "volumen":
        return det_volumen(cerr)
    if estr == "adx":
        return det_adx(cerr)
    if estr == "rsidiv":
        return det_rsidiv(cerr)
    if estr == "scalp_sqz":
        return det_scalp_sqz(cerr)
    if estr == "scalp_rev":
        return det_scalp_rev(cerr)
    return None


def contexto(ex, coin, L, cache):
    """Contexto NO-precio + liquidez de cada operación, para entender luego qué la hace funcionar.
    funding/OI = posicionamiento (independiente del precio). pos_rango = premium/discount (0=suelo,
    1=techo). dist_liq = % a la liquidez (swing) más cercana arriba/abajo."""
    if coin not in cache:
        try:
            fr = ex.fetch_funding_rate(f"{coin}/USDC:USDC").get("fundingRate")
        except Exception:
            fr = None
        try:
            oi = ex.fetch_open_interest(f"{coin}/USDC:USDC").get("openInterestAmount")
        except Exception:
            oi = None
        cache[coin] = (fr, oi)
    fr, oi = cache[coin]
    cerr = L.iloc[:-1]
    px = float(cerr["cierre"].iloc[-1])
    hi = cerr["maximo"].tail(100); lo = cerr["minimo"].tail(100)
    rh = float(hi.max()); rl = float(lo.min())
    pos = round((px - rl) / (rh - rl), 2) if rh > rl else 0.5
    arr = hi[hi > px]; aba = lo[lo < px]
    dliq_up = round((arr.min() / px - 1) * 100, 2) if len(arr) else None
    dliq_dn = round((1 - aba.max() / px) * 100, 2) if len(aba) else None
    return {"funding": fr, "oi": oi, "pos_rango": pos, "liq_arriba_%": dliq_up, "liq_abajo_%": dliq_dn}


POLITICAS = ("fixed", "be05", "be10", "t125", "trail")


def actualizar(ops, L, m1=None):
    """Resuelve las operaciones abiertas sobre el camino REAL de 1 minuto (m1) cuando cubre la entrada
    (orden correcto stop-vs-objetivo). Mide EN PARALELO 5 políticas de salida para tener datos reales:
      fixed (stop/objetivo fijos) · be05/be10 (break-even al llegar a 0.5R/1R) · t125 (objetivo 1.25R)
      · trail (trailing stop a 1R del máximo). Guarda el resultado NETO en R de cada una."""
    for o in ops:
        if o["status"] != "abierta":
            continue
        res = m1 if (m1 is not None and len(m1) and int(m1["t"].iloc[0]) <= o["ts"]) else L
        hi = res["maximo"].to_numpy(); lo = res["minimo"].to_numpy(); ts = res["t"].to_numpy()
        entry = o["entry"]; stop0 = o["stop"]; target = o["target"]
        D = abs(entry - stop0) or 1e-9
        largo = o["dir"] == "largo"
        cost_R = COSTE / (D / entry)
        t125 = entry + (1.25 * D if largo else -1.25 * D)
        st = {p: stop0 for p in POLITICAS}
        armed = {"be05": False, "be10": False}
        best = entry; cerr = {}; mfe = mae = 0.0
        for k in range(len(ts)):
            if ts[k] <= o["ts"]:
                continue
            fav = (hi[k] - entry) / D if largo else (entry - lo[k]) / D
            adv = (entry - lo[k]) / D if largo else (hi[k] - entry) / D
            mfe = max(mfe, fav); mae = max(mae, adv)
            for p in POLITICAS:
                if p in cerr:
                    continue
                tgt = t125 if p == "t125" else target
                stop_hit = (lo[k] <= st[p]) if largo else (hi[k] >= st[p])
                tgt_hit = (hi[k] >= tgt) if largo else (lo[k] <= tgt)
                if stop_hit:
                    cerr[p] = (st[p] - entry) / D if largo else (entry - st[p]) / D
                elif tgt_hit:
                    cerr[p] = (tgt - entry) / D if largo else (entry - tgt) / D
            if not armed["be05"] and fav >= 0.5:
                armed["be05"] = True; st["be05"] = entry
            if not armed["be10"] and fav >= 1.0:
                armed["be10"] = True; st["be10"] = entry
            best = max(best, hi[k]) if largo else min(best, lo[k])
            tl = (best - D) if largo else (best + D)
            st["trail"] = max(st["trail"], tl) if largo else min(st["trail"], tl)
            if "fixed" in cerr:
                break
        if "fixed" in cerr:
            ex = cerr["fixed"]
            o.update(status="cerrada", exit=entry + ex * D if largo else entry - ex * D)
            o["pnl"] = ex * (D / entry) - COSTE
            o["mfe_R"] = round(mfe, 2); o["mae_R"] = round(mae, 2)
            o["res"] = "1m" if res is m1 else "tf"
            o["exits"] = {p: round(cerr.get(p, ex) - cost_R, 3) for p in POLITICAS}   # R NETO real por salida


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ex = _ex(); ex.load_markets()
    REG.mkdir(parents=True, exist_ok=True)
    print("ARENA EN VIVO (paper) — estrategias x temporalidades. Sin órdenes, sin dinero.\n")
    tabla = []
    ctx_cache = {}      # funding/OI por moneda, una sola vez por tick
    m1_cache = {}       # velas de 1m por moneda (para resolver con el recorrido real)
    for estr, tfs_estr in ESTRATEGIAS_TF.items():
        for coin in COINS:
            for tf in tfs_estr:
                f = REG / f"{estr}_{coin}_{tf}.json"
                ops = json.loads(f.read_text()) if f.exists() else []
                last_ts = max((o["ts"] for o in ops), default=0)
                nuevos = []     # (ts, setup) de TODAS las velas cerradas desde la última ejecución
                try:
                    if estr == "smc":
                        s, L = det_smc(ex, coin, tf)
                        tsl = int(L["t"].iloc[-2])
                        if s and tsl > last_ts:
                            nuevos.append((tsl, s))
                    else:
                        L = velas(ex, coin, tf, 500)
                        closed = L.iloc[:-1].reset_index(drop=True)   # velas YA cerradas
                        tsa = closed["t"].to_numpy()
                        for p in range(max(0, len(closed) - 50), len(closed)):
                            if tsa[p] <= last_ts:                      # ya registrada antes
                                continue
                            s = detectar_cerr(estr, closed.iloc[:p + 1], coin)   # evalúa esa vela
                            if s:
                                nuevos.append((int(tsa[p]), s))
                except Exception as e:
                    print(f"  {estr}/{coin}/{tf}: error {type(e).__name__}: {e}"); continue
                if coin not in m1_cache:
                    try:
                        m1_cache[coin] = velas(ex, coin, "1m", 5000)
                    except Exception:
                        m1_cache[coin] = None
                actualizar(ops, L, m1_cache[coin])
                for ts_p, s in nuevos:
                    if any(o["ts"] == ts_p for o in ops):
                        continue
                    s.update(status="abierta", ts=ts_p, estr=estr, coin=coin, tf=tf,
                             fecha=str(pd.to_datetime(ts_p, unit="ms")))
                    try:
                        s.update(contexto(ex, coin, L, ctx_cache))
                    except Exception:
                        pass
                    ops.append(s)
                    print(f"  NUEVO {estr}/{coin}/{tf} {s['dir'].upper()} @ {s['entry']:.4f} stop {s['stop']:.4f} obj {s['target']:.4f}")
                f.write_text(json.dumps(ops, indent=2))
                cerr = [o for o in ops if o["status"] == "cerrada"]
                ab = [o for o in ops if o["status"] == "abierta"]
                if cerr:
                    pnl = [o["pnl"] for o in cerr]
                    eq = np.prod([1 + p for p in pnl]) - 1
                    win = sum(1 for p in pnl if p > 0) / len(pnl)
                    tabla.append((estr, coin, tf, len(cerr), len(ab), win, eq))
                else:
                    tabla.append((estr, coin, tf, 0, len(ab), float("nan"), 0.0))

    print("\n=== LEADERBOARD (acumulado en papel) ===")
    print(f"  {'estrategia':<8} {'coin':<5} {'tf':<4} | cerradas abiertas |  win  | retorno acum")
    for estr, coin, tf, nc, na, win, eq in sorted(tabla, key=lambda x: -x[6]):
        wtxt = f"{win*100:4.0f}%" if nc else "  - "
        print(f"  {estr:<8} {coin:<5} {tf:<4} | {nc:>8} {na:>8} | {wtxt} | {eq*100:+7.2f}%")


if __name__ == "__main__":
    main()
