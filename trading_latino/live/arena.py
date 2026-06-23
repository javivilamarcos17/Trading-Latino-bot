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
import time
from pathlib import Path

import ccxt
import numpy as np
import pandas as pd
import requests

REG = Path(__file__).resolve().parents[2] / "data_store" / "paper_arena"
COINS = ["BTC", "ETH"]   # FOCO en BTC (estrella); ETH solo como control anti-sobreajuste
# cada estrategia corre en SUS temporalidades (scalping en rápidas)
ESTRATEGIAS_TF = {
    # Cobertura AMPLIA de temporalidades por familia: tener muestra en CADA TF y poder comparar la
    # MISMA estrategia entre temporalidades (objetivo: sacar lo mejor de cada una con datos reales).
    # Las velas se comparten en caché por (moneda, TF) -> ampliar es casi gratis para la API.
    # --- estructura / tendencia: medios-altos (+ algún rápido para más muestra) ---
    "smc": ["15m", "1h", "4h"], "merino": ["15m", "1h", "4h"],
    "sweep": ["5m", "15m", "1h", "4h"], "ob": ["5m", "15m", "1h", "4h"],
    "ob_trend": ["5m", "15m", "1h", "4h"],
    "elliott": ["15m", "1h", "4h"],
    # --- osciladores / reversión: medios ---
    "fvg": ["5m", "15m", "1h", "4h"], "rsi": ["5m", "15m", "1h"],
    "rsidiv": ["15m", "1h", "4h"],
    # --- scalping / reversión rápida: SOLO vwap (scalp_rev/rev3 RETIRADAS: n=500+, -0.36/-0.47R) ---
    "vwap": ["1m", "5m", "15m"],
    # RETIRADAS 2026-06-23 (muestra suficiente, negativas de forma consistente):
    # scalp_rev n=485 -0.36R, scalp_rev3 n=120 -0.47R, volumen n=20 -0.62R, donchian n=65 -0.36R.
    # --- COMPUESTAS multi-factor (price-action+smart-money y Merino enriquecido) ---
    "adrig": ["15m", "1h", "4h"], "merinox": ["15m", "1h", "4h"],
    # --- MULTI-TEMPORALIDAD real (HTF marca direccion, LTF marca timing) ---
    "mtf": ["15m", "1h", "4h"],
    # --- OB reforzado (lider + filtros validados por datos), en su TF dulce ---
    "ob_plus": ["5m", "15m", "1h"],
    # --- OB ADAPTATIVO al regimen (switcher: ob_trend en tendencia, ob_plus en rango) ---
    "ob_regime": ["5m", "15m", "1h"],
    # --- AdriG/ICT compleja: desplazamiento + FVG + retest a favor del sesgo ---
    "adrig2": ["15m", "1h", "4h"],
    # === PRUEBAS DE SESION (2026-06-23) ===
    # Hallazgo: ob_trend Asia 80%/+1.09R, Londres 70%/+0.92R vs NY 27%/-0.41R.
    # fvg: Asia +0.33R, Londres +0.55R (el backfill '?' lo arrastraba a -0.06R global).
    # Cada sesion tiene su propio caracter — medimos cada hipotesis por separado.
    # A) ob_asia: ob_trend solo en Asia+Londres (00-13 UTC) — test del filtro de sesion
    "ob_asia": ["15m", "1h", "4h"],
    # A2) fvg_asia: fvg con filtro de sesion — confirmacion de que es el tiempo, no el patron
    "fvg_asia": ["5m", "15m", "1h", "4h"],
    # A3) ob_regime_asia: el mejor switcher (ob_regime) solo en la mejor sesion (Asia+Londres)
    "ob_regime_asia": ["15m", "1h"],
    # B) ob_ny_open: ob_trend SOLO en apertura americana (13-15:30 UTC) — tesis ICT/Sensei Trading
    "ob_ny_open": ["5m", "15m", "1h"],
    # C) ob_scalp: 15m zona + 1m timing, solo Asia+Londres — la madre del scalping optimizado
    # (estr especial: multi-TF, run as "1m" but internally uses 15m zones)
    "ob_scalp": ["1m"],
    # D) sensei: ICT Killzone NY — rango asiatico + Judas Swing + ChoCh + FVG/OB en 1m/5m
    # Tesis Sensei Trading: el mercado manipula la liquidez asiatica/londrina al abrir NY
    "sensei": ["1m", "5m"],
    # ===== 5 ALTERNATIVAS NUEVAS (2026-06-23) — paralelas, sin tocar nada existente =====
    # E) orf: Opening Range Breakout — primeros 15min de NY definen el rango del dia
    "orf": ["5m", "15m"],
    # F) fvg_ob: FVG dentro de OB — doble confluencia ICT (la señal mas fuerte de las dos)
    "fvg_ob": ["5m", "15m", "1h"],
    # G) breaker: Breaker Block ICT — OB fallido se convierte en nivel inverso
    "breaker": ["15m", "1h", "4h"],
    # H) asia_sweep: barrido del rango asiatico con recuperacion inmediata (trampa pura)
    "asia_sweep": ["5m", "15m", "1h"],
    # I) london_fade: fade del movimiento de Londres al abrir NY (operativa de sesion pura)
    "london_fade": ["15m", "1h"],
    # adx y scalp_sqz RETIRADAS (2026-06-22): muertas con datos reales (adx 0% acierto / -1.1R;
    # scalp_sqz -0.6/-0.8R con cualquier salida).
}
HTF_DE = {"5m": "15m", "15m": "1h", "1h": "4h", "4h": "1d"}   # marco mayor para SMC según el menor
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


# ----- LOTE NUEVO de alternativas a probar en vivo (variantes + familias nuevas) -----
def det_ob_trend(d):
    """Order Block PERO solo a favor de la tendencia mayor (EMA200). Refina la mejor (ob)."""
    base = det_ob(d)
    if base is None:
        return None
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    j = len(d) - 1; cl = d["cierre"].to_numpy()[j]
    if base["dir"] == "largo" and cl > ema[j]:
        return base
    if base["dir"] == "corto" and cl < ema[j]:
        return base
    return None


def det_ob_plus(d):
    """OB REFORZADO (sobre la familia líder): Order Block + tendencia EMA200 + sanidad de volumen
    (sin clímax >2.5x, que el análisis mostró que falla). Apila SOLO los filtros que los datos validan
    (la tendencia ayuda: ob_trend>ob; el clímax perjudica). Objetivo fijo 2R: los OB necesitan recorrido."""
    base = det_ob(d)
    if base is None:
        return None
    j = len(d) - 1
    cl = d["cierre"].to_numpy()[j]
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    vol = d["volumen"].to_numpy(); vm = d["volumen"].rolling(20).mean().shift(1).to_numpy()
    if np.isnan(ema[j]) or not vm[j] or np.isnan(vm[j]) or vol[j] >= 2.5 * vm[j]:
        return None
    if base["dir"] == "largo" and cl > ema[j]:
        return base
    if base["dir"] == "corto" and cl < ema[j]:
        return base
    return None


def det_fvg_asia(d):
    """fvg CON FILTRO DE SESION — dato real: fvg Asia +0.33R, Londres +0.55R; el -0.06R global
    venia del backfill antiguo sin tag de sesion ('?'). Confirma si el timing es el edge de fvg."""
    h = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)
    if h >= 13:
        return None
    return det_fvg(d)


def det_ob_regime_asia(d):
    """ob_regime (el mejor switcher: +0.63R) con FILTRO de sesion Asia+Londres. La hipotesis
    es que el mejor selector de regimen mas la mejor ventana temporal deberian ser la combinacion
    optima. No tiene precedente en los datos aun — es una apuesta informada."""
    h = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)
    if h >= 13:
        return None
    return det_ob_regime(d)


def det_ob_asia(d):
    """ob_trend CON FILTRO DE SESION — dato real: ob_trend Asia 80%win/+1.09R, Londres 70%/+0.92R,
    NY 27%/-0.41R. El mismo OB que gana de noche MUERE en la sesión americana. Mide si el filtro
    de sesión por sí solo convierte al ganador en una máquina. Corre en 15m/1h/4h como ob_trend."""
    h = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)
    if h >= 13:   # a partir de NY = el edge desaparece según los datos
        return None
    return det_ob_trend(d)


def det_ob_regime(d):
    """OB ADAPTATIVO AL RÉGIMEN (switcher basado en datos reales): en TENDENCIA (ADX>25) usa
    ob_trend (robusto en tendencia, +0.21R); en RANGO (ADX<25) usa ob_plus (especialista de rango,
    +0.64R). Elige el mejor especialista según el ADX del momento. Lo medimos para ver si el switch
    bate a cada uno por separado."""
    adx = _adx(d)
    j = len(d) - 1
    if j < 30 or np.isnan(adx[j]):
        return None
    return det_ob_trend(d) if adx[j] > 25 else det_ob_plus(d)


def det_scalp_rev3(d):
    """Reversión a la media con banda Bollinger MÁS extrema (2.5σ) = señal de más calidad."""
    c = d["cierre"]; ma = c.rolling(20).mean(); sd = c.rolling(20).std()
    up = (ma + 2.5 * sd).to_numpy(); dn = (ma - 2.5 * sd).to_numpy()
    lo = d["minimo"].to_numpy(); hi = d["maximo"].to_numpy(); cl = c.to_numpy(); j = len(cl) - 1
    if j < 25 or np.isnan(dn[j]):
        return None
    if lo[j] <= dn[j] and cl[j] > dn[j]:
        return _setup("largo", cl[j], lo[j] * 0.999, 1.5)
    if hi[j] >= up[j] and cl[j] < up[j]:
        return _setup("corto", cl[j], hi[j] * 1.001, 1.5)
    return None


def det_vwap(d):
    """Rebote en VWAP (50): el precio vuelve al VWAP desde arriba y aguanta -> largo (y espejo)."""
    tp = (d["maximo"] + d["minimo"] + d["cierre"]) / 3
    vwap = ((tp * d["volumen"]).rolling(50).sum() / d["volumen"].rolling(50).sum()).to_numpy()
    lo = d["minimo"].to_numpy(); hi = d["maximo"].to_numpy(); cl = d["cierre"].to_numpy(); j = len(cl) - 1
    if j < 55 or np.isnan(vwap[j]):
        return None
    swl = d["minimo"].iloc[j - 7:j].min(); swh = d["maximo"].iloc[j - 7:j].max()
    if lo[j] <= vwap[j] and cl[j] > vwap[j] and cl[j - 1] > vwap[j - 1]:
        return _setup("largo", cl[j], swl, 2.0)
    if hi[j] >= vwap[j] and cl[j] < vwap[j] and cl[j - 1] < vwap[j - 1]:
        return _setup("corto", cl[j], swh, 2.0)
    return None


def det_donchian(d):
    """Ruptura de canal Donchian (máx/mín de 20 velas) = seguimiento de tendencia (familia nueva)."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy(); j = len(cl) - 1
    if j < 25:
        return None
    hh = hi[j - 20:j].max(); ll = lo[j - 20:j].min()
    sl = lo[j - 10:j].min(); sh = hi[j - 10:j].max()
    if cl[j] > hh and cl[j - 1] <= hh:
        return _setup("largo", cl[j], sl, 2.0)
    if cl[j] < ll and cl[j - 1] >= ll:
        return _setup("corto", cl[j], sh, 2.0)
    return None


def det_adrig(d):
    """AdriG — Smart Money + Price Action (MULTI-FACTOR, no depende de un indicador):
    (1) SESGO de fondo: precio vs EMA200 (proxy del marco mayor).
    (2) UBICACION: largos solo en DESCUENTO del rango / cortos solo en PREMIUM (comprar barato/vender caro).
    (3) GATILLO de price-action: barrido de liquidez (toma un swing previo de 20 velas) + RECLAIM
        (cierra de vuelta al lado correcto) = trampa institucional + giro.
    (4) SANIDAD de volumen: no entrar en clímax extremo (>2.5x media), que estadísticamente falla.
    Stop al otro lado del barrido; objetivo 2R. Pone a prueba la tesis smart-money con datos."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    vol = d["volumen"].to_numpy(); vm = d["volumen"].rolling(20).mean().shift(1).to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    j = len(cl) - 1
    if j < 60 or np.isnan(ema[j]) or np.isnan(vm[j]) or not vm[j]:
        return None
    rh = hi[j - 50:j].max(); rl = lo[j - 50:j].min()
    if rh <= rl:
        return None
    pos = (cl[j] - rl) / (rh - rl)
    volok = vol[j] < 2.5 * vm[j]                     # no clímax extremo
    swl = lo[j - 20:j].min(); swh = hi[j - 20:j].max()
    if cl[j] > ema[j] and pos < 0.45 and volok:      # sesgo alcista + descuento
        if lo[j] <= swl and cl[j] > swl and cl[j] > op[j]:   # barrió el mínimo y reclamó
            return _setup("largo", cl[j], lo[j] * 0.999, 2.0)
    if cl[j] < ema[j] and pos > 0.55 and volok:      # sesgo bajista + premium
        if hi[j] >= swh and cl[j] < swh and cl[j] < op[j]:
            return _setup("corto", cl[j], hi[j] * 1.001, 2.0)
    return None


def det_merinox(d):
    """Merino ENRIQUECIDO (MULTI-FACTOR): tendencia EMA10/55 + fuerza ADX + giro de Squeeze, MÁS
    alineación con el marco mayor (EMA200) y sanidad de volumen (sin clímax). Objetivo 2R."""
    c = d["cierre"]
    e10 = c.ewm(span=10, adjust=False).mean().to_numpy()
    e55 = c.ewm(span=55, adjust=False).mean().to_numpy()
    e200 = c.ewm(span=200, adjust=False).mean().to_numpy()
    hh = d["maximo"].rolling(20).max(); ll = d["minimo"].rolling(20).min()
    mom = (c - ((hh + ll) / 2 + c.rolling(20).mean()) / 2).to_numpy()
    adx = _adx(d)
    vol = d["volumen"].to_numpy(); vm = d["volumen"].rolling(20).mean().shift(1).to_numpy()
    cl = c.to_numpy(); j = len(cl) - 1
    if j < 200 or np.isnan(adx[j]) or np.isnan(mom[j - 1]) or np.isnan(e200[j]) or not vm[j]:
        return None
    swl = d["minimo"].iloc[j - 10:j].min(); swh = d["maximo"].iloc[j - 10:j].max()
    volok = vol[j] < 2.5 * vm[j]
    if e10[j] > e55[j] and cl[j] > e200[j] and adx[j] > 20 and mom[j] > 0 >= mom[j - 1] and volok:
        return _setup("largo", cl[j], swl, 2.0)
    if e10[j] < e55[j] and cl[j] < e200[j] and adx[j] > 20 and mom[j] < 0 <= mom[j - 1] and volok:
        return _setup("corto", cl[j], swh, 2.0)
    return None


def det_adrig2(d):
    """AdriG/ICT smart-money COMPLEJA (multi-factor): DESPLAZAMIENTO institucional (vela de cuerpo
    grande, >1.5x ATR) que deja un FVG (desequilibrio), + SESGO EMA200, + entrada en el RETEST del
    FVG a favor del sesgo. Captura la huella institucional y la entrada en el hueco que dejó el impulso."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    tr = pd.concat([d["maximo"] - d["minimo"], (d["maximo"] - d["cierre"].shift()).abs(),
                    (d["minimo"] - d["cierre"].shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().to_numpy()
    j = len(cl) - 1
    if j < 210 or np.isnan(ema[j]) or np.isnan(atr[j]):
        return None
    for i in range(j - 15, j - 1):                       # FVG por desplazamiento en las últimas velas
        if np.isnan(atr[i]) or atr[i] <= 0:
            continue
        body = abs(cl[i] - op[i])
        if body < 1.5 * atr[i]:                          # exige impulso fuerte (desplazamiento)
            continue
        if cl[i] > op[i] and lo[i + 1] > hi[i - 1]:       # desplazamiento alcista deja FVG alcista
            gap_bot, gap_top = hi[i - 1], lo[i + 1]
            if cl[j] > ema[j] and lo[j] <= gap_top and cl[j] > gap_bot:    # retest a favor del sesgo
                return _setup("largo", cl[j], gap_bot * 0.999, 2.0)
        if cl[i] < op[i] and hi[i + 1] < lo[i - 1]:       # desplazamiento bajista deja FVG bajista
            gap_top, gap_bot = lo[i - 1], hi[i + 1]
            if cl[j] < ema[j] and hi[j] >= gap_bot and cl[j] < gap_top:
                return _setup("corto", cl[j], gap_top * 1.001, 2.0)
    return None


def det_ob_ny_open(d):
    """ob_trend en APERTURA AMERICANA (ICT): solo dispara entre 13:00-15:30 UTC (9:30-11:30 ET).
    Tesis: la apertura de NY toma liquidez de la sesión de Londres y revierte o continúa el sesgo
    del día. El estilo ICT/Sensei Trading opera OBs específicamente en este ventana. Medimos si
    este timing tiene edge diferente al resto de la sesión americana (que muere en −0.41R)."""
    h = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)
    m = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").minute)
    if not (13 <= h < 15 or (h == 15 and m <= 30)):
        return None
    return det_ob_trend(d)


# ===== 5 NUEVAS ALTERNATIVAS (2026-06-23) — no tocan nada existente =====

def det_orf(d):
    """OPENING RANGE BREAKOUT: los primeros 15 min de NY (13:00-13:15 UTC = 9:00-9:15 ET) definen
    el RANGO del dia. Ruptura por encima → largo; por debajo → corto. Stop al otro extremo del
    rango, objetivo 2R. Estrategia institucional clasica, totalmente distinta a todo lo que tenemos.
    Se mide si la ruptura de la apertura tiene edge en cripto (a diferencia de indices/forex)."""
    ts_pd = pd.to_datetime(d["t"].to_numpy(), unit="ms", utc=True)
    j = len(d) - 1
    h = int(ts_pd[j].hour); m = int(ts_pd[j].minute)
    if not (h > 13 or (h == 13 and m >= 15)) or h >= 21:   # solo NY despues de 13:15
        return None
    hoy = ts_pd[j].date()
    mask_or = (ts_pd.date == hoy) & (ts_pd.hour == 13) & (ts_pd.minute < 15)
    idx_or = np.where(mask_or)[0]
    if len(idx_or) < 2:
        return None
    or_hi = d["maximo"].to_numpy()[idx_or].max()
    or_lo = d["minimo"].to_numpy()[idx_or].min()
    if or_hi <= or_lo or (or_hi - or_lo) / d["cierre"].to_numpy()[j] < 0.0003:
        return None
    cl = d["cierre"].to_numpy(); prev_cl = cl[j - 1]
    if cl[j] > or_hi and prev_cl <= or_hi:
        return _setup("largo", cl[j], or_lo, 2.0)
    if cl[j] < or_lo and prev_cl >= or_lo:
        return _setup("corto", cl[j], or_hi, 2.0)
    return None


def det_fvg_ob(d):
    """FVG DENTRO DE OB — doble confluencia ICT: solo el FVG cuya zona cae DENTRO de un Order
    Block activo (EMA200 + mismo sentido). Hipotesis: los FVGs mas potentes son los que se forman
    sobre un OB institucional. Señal de alta calidad, pocas señales, R/R elevado."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    j = len(cl) - 1
    if j < 215 or np.isnan(ema[j]):
        return None
    obs = []
    for i in range(max(0, j - 40), j - 1):
        if np.isnan(ema[i]):
            continue
        if cl[i] < op[i] and cl[i + 1] > hi[i] and (hi[i] - lo[i]) / cl[i] > 0.0008:
            if cl[i] > ema[i]:
                obs.append((hi[i], lo[i], "largo"))
        if cl[i] > op[i] and cl[i + 1] < lo[i] and (hi[i] - lo[i]) / cl[i] > 0.0008:
            if cl[i] < ema[i]:
                obs.append((hi[i], lo[i], "corto"))
    if not obs:
        return None
    for i in range(max(1, j - 20), j - 1):
        if lo[i] > hi[i - 2] and (lo[i] - hi[i - 2]) / cl[i] > 0.0008:   # FVG alcista
            fvg_bot, fvg_top = hi[i - 2], lo[i]
            if lo[j] <= fvg_top and cl[j] > fvg_bot:
                for ob_top, ob_bot, direc in obs:
                    if direc == "largo" and ob_bot <= fvg_bot <= ob_top:
                        return _setup("largo", cl[j], ob_bot * 0.999, 2.0)
        if hi[i] < lo[i - 2] and (lo[i - 2] - hi[i]) / cl[i] > 0.0008:   # FVG bajista
            fvg_top2, fvg_bot2 = lo[i - 2], hi[i]
            if hi[j] >= fvg_bot2 and cl[j] < fvg_top2:
                for ob_top, ob_bot, direc in obs:
                    if direc == "corto" and ob_bot <= fvg_top2 <= ob_top:
                        return _setup("corto", cl[j], ob_top * 1.001, 2.0)
    return None


def det_breaker(d):
    """BREAKER BLOCK (ICT): un OB que falla (precio lo atraviesa completamente) se convierte en
    un bloque INVERSO — el soporte roto es ahora resistencia y viceversa. Concepto ICT puro: las
    instituciones usan el nivel fallido para distribuir/acumular en el retest. Solo a favor de la
    tendencia mayor (EMA200) para evitar señales en contra del sesgo."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    j = len(cl) - 1
    if j < 215 or np.isnan(ema[j]):
        return None
    px = cl[j]; breakers = []
    for i in range(max(0, j - 50), j - 2):
        if np.isnan(ema[i]):
            continue
        ob_top = hi[i]; ob_bot = lo[i]
        if (ob_top - ob_bot) / cl[i] < 0.0008:
            continue
        if cl[i] < op[i] and cl[i + 1] > ob_top:          # OB alcista original
            for k in range(i + 2, j):
                if cl[k] < ob_bot:                          # fallo: precio cerro bajo el low del OB
                    breakers.append((ob_top, ob_bot, "corto"))
                    break
        if cl[i] > op[i] and cl[i + 1] < ob_bot:          # OB bajista original
            for k in range(i + 2, j):
                if cl[k] > ob_top:                          # fallo: precio cerro sobre el high del OB
                    breakers.append((ob_top, ob_bot, "largo"))
                    break
    for ob_top, ob_bot, direc in breakers:
        if direc == "corto" and ob_bot <= px <= ob_top and cl[j] < ema[j]:
            return _setup("corto", px, ob_top * 1.001, 2.0)
        if direc == "largo" and ob_bot <= px <= ob_top and cl[j] > ema[j]:
            return _setup("largo", px, ob_bot * 0.999, 2.0)
    return None


def det_asia_sweep(d):
    """BARRIDO DEL RANGO ASIATICO: precio supera el maximo o minimo de la sesion asiatica
    (00-07 UTC) PERO cierra de vuelta dentro del rango en la misma vela (pin-bar institucional).
    Es la trampa mas limpia: barre los stops en los extremos y revierte inmediatamente.
    Señal muy selectiva — cuando aparece suele ser de alta calidad."""
    ts_pd = pd.to_datetime(d["t"].to_numpy(), unit="ms", utc=True)
    j = len(d) - 1
    if ts_pd[j].hour < 7:                    # no operar durante la propia sesion asiatica
        return None
    hoy = ts_pd[j].date()
    mask_as = (ts_pd.date == hoy) & (ts_pd.hour < 7)
    idx_as = np.where(mask_as)[0]
    if len(idx_as) < 5:
        return None
    hi_a = d["maximo"].to_numpy()[idx_as].max()
    lo_a = d["minimo"].to_numpy()[idx_as].min()
    if hi_a <= lo_a:
        return None
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    if lo[j] < lo_a and cl[j] > lo_a and cl[j] > op[j]:   # barrio el minimo asiatico y recupero
        return _setup("largo", cl[j], lo[j] * 0.999, 2.0)
    if hi[j] > hi_a and cl[j] < hi_a and cl[j] < op[j]:   # barrio el maximo asiatico y recupero
        return _setup("corto", cl[j], hi[j] * 1.001, 2.0)
    return None


def det_london_fade(d):
    """FADE DEL CIERRE DE LONDRES: tras el cierre de Londres (13:00 UTC), el mercado suele
    REVERTIR el movimiento de la sesion londinense. Londres alcista → buscar corto en NY;
    Londres bajista → buscar largo. El timing: primer OB que aparece a favor del fade en NY,
    alineado con EMA200. Tesis: NY 'roba' la liquidez que Londres creo durante la manana."""
    ts_pd = pd.to_datetime(d["t"].to_numpy(), unit="ms", utc=True)
    j = len(d) - 1
    if not (13 <= ts_pd[j].hour < 21):
        return None
    hoy = ts_pd[j].date()
    mask_lon = (ts_pd.date == hoy) & (ts_pd.hour >= 7) & (ts_pd.hour < 13)
    idx_lon = np.where(mask_lon)[0]
    if len(idx_lon) < 5:
        return None
    cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    if np.isnan(ema[j]):
        return None
    lon_open = cl[idx_lon[0]]; lon_close = cl[idx_lon[-1]]
    lon_hi = hi[idx_lon].max(); lon_lo = lo[idx_lon].min()
    london_alcista = lon_close > lon_open
    px = cl[j]
    # OB a favor del fade dentro de NY (post-13:00 UTC), alineado con EMA200
    for i in range(max(idx_lon[-1] + 1, j - 20), j - 1):
        if (hi[i] - lo[i]) / cl[i] < 0.0008:
            continue
        if london_alcista:                              # Londres subio → buscar corto
            if cl[i] > op[i] and cl[i + 1] < lo[i] and px < ema[j]:
                if lo[i] <= px <= hi[i]:
                    return _setup("corto", px, hi[i] * 1.001, 2.0)
        else:                                          # Londres bajo → buscar largo
            if cl[i] < op[i] and cl[i + 1] > hi[i] and px > ema[j]:
                if lo[i] <= px <= hi[i]:
                    return _setup("largo", px, lo[i] * 0.999, 2.0)
    return None


def det_ob_scalp(ex, coin, cache):
    """SCALP INSTITUCIONAL (la madre de la estrategia final): el OB en 15m marca la ZONA
    (OB válido + EMA200 + sin clímax de volumen), y la vela de 1m da el TIMING exacto dentro
    de esa zona (pin-bar de rechazo: mecha >1.5x cuerpo = rechazo institucional real).
    Solo en Asia+Londres (00-13 UTC) donde los datos validan el edge real (+1.09R/+0.92R).
    Stop al borde del OB = stop mucho más ajustado que ob_trend normal. Objetivo 2R.
    Escalable a más TF: si el 1m no da señales, puede probarse con 5m de timing."""
    h = int(pd.Timestamp.now("UTC").hour)
    if h >= 13:
        return None, None

    df15 = velas_cached(ex, coin, "15m", cache)
    d15 = df15.iloc[:-1]
    hi15 = d15["maximo"].to_numpy(); lo15 = d15["minimo"].to_numpy()
    cl15 = d15["cierre"].to_numpy(); op15 = d15["apertura"].to_numpy()
    ema15 = d15["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    vol15 = d15["volumen"].to_numpy()
    vm15 = d15["volumen"].rolling(20).mean().shift(1).to_numpy()
    j15 = len(cl15) - 1
    if j15 < 210:
        return None, None

    zonas = []
    for i in range(max(0, j15 - 30), j15 - 1):
        if np.isnan(ema15[i]) or not vm15[i] or np.isnan(vm15[i]):
            continue
        if vol15[i] >= 2.5 * vm15[i]:
            continue
        if cl15[i] < op15[i] and cl15[i + 1] > hi15[i] and (hi15[i] - lo15[i]) / cl15[i] > 0.0008:
            if cl15[i] > ema15[i]:
                zonas.append((hi15[i], lo15[i], "largo"))
        if cl15[i] > op15[i] and cl15[i + 1] < lo15[i] and (hi15[i] - lo15[i]) / cl15[i] > 0.0008:
            if cl15[i] < ema15[i]:
                zonas.append((hi15[i], lo15[i], "corto"))

    if not zonas:
        return None, None

    df1 = velas_cached(ex, coin, "1m", cache)
    L1 = df1.iloc[:-1]
    hi1 = L1["maximo"].to_numpy(); lo1 = L1["minimo"].to_numpy()
    cl1 = L1["cierre"].to_numpy(); op1 = L1["apertura"].to_numpy()
    j1 = len(cl1) - 1
    if j1 < 30:
        return None, df1

    px = cl1[j1]
    for (ob_top, ob_bot, direc) in reversed(zonas):
        if direc == "largo" and ob_bot <= px <= ob_top:
            cuerpo = abs(cl1[j1] - op1[j1]) + 1e-9
            mecha_inf = min(cl1[j1], op1[j1]) - lo1[j1]
            if mecha_inf > 1.5 * cuerpo and cl1[j1] > op1[j1]:
                return _setup("largo", px, ob_bot * 0.999, 2.0), df1
        if direc == "corto" and ob_bot <= px <= ob_top:
            cuerpo = abs(cl1[j1] - op1[j1]) + 1e-9
            mecha_sup = hi1[j1] - max(cl1[j1], op1[j1])
            if mecha_sup > 1.5 * cuerpo and cl1[j1] < op1[j1]:
                return _setup("corto", px, ob_top * 1.001, 2.0), df1
    return None, df1


def det_sensei(ex, coin, ltf, cache):
    """SENSEI ICT KILLZONE — implementacion mecanica de la operativa del Sensei Trading (ICT):
    1. DIRECCION: sesgo de fondo via EMA200 en 1h (marco mayor).
    2. RANGO ASIATICO: max/min de la sesion 00:00-07:00 UTC del dia actual (liqudez visible).
    3. KILLZONE: solo opera entre 13:00-16:00 UTC (8:00-11:00 AM EST = apertura NY).
    4. JUDAS SWING: el precio barre la liquidez del rango asiatico en la DIRECCION CONTRARIA
       al sesgo (manipulacion institucional: trampa para novatos).
    5. ENTRADA: tras el barrido, busca un FVG o OB en el LTF (1m o 5m) que confirme el giro.
       Stop bajo el punto mas extremo del Judas. Target: lado opuesto del rango asiatico (2R min)."""
    h_utc = int(pd.Timestamp.now("UTC").hour)
    if not (13 <= h_utc < 16):          # solo Killzone de NY
        return None, None

    # 1) SESGO en 1h (marco mayor)
    H1 = velas_cached(ex, coin, "1h", cache).iloc[:-1]
    if len(H1) < 210:
        return None, None
    ema1h = H1["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    cl1h = H1["cierre"].to_numpy()
    sesgo_alcista = cl1h[-1] > ema1h[-1]

    # 2) RANGO ASIATICO del dia actual (00:00-07:00 UTC)
    L_ltf = velas_cached(ex, coin, ltf, cache)
    ts_arr = L_ltf["t"].to_numpy()
    hi_ltf = L_ltf["maximo"].to_numpy(); lo_ltf = L_ltf["minimo"].to_numpy()
    cl_ltf = L_ltf["cierre"].to_numpy()
    hoy_utc = pd.Timestamp.now("UTC").date()
    ts_pd = pd.to_datetime(ts_arr, unit="ms", utc=True)
    mask_asia = (ts_pd.date == hoy_utc) & (ts_pd.hour < 7)
    idx_asia = np.where(mask_asia)[0]
    if len(idx_asia) < 3:
        return None, L_ltf
    asia_hi = hi_ltf[idx_asia].max()
    asia_lo = lo_ltf[idx_asia].min()
    if asia_hi <= asia_lo:
        return None, L_ltf

    # 3) JUDAS: precio barro la liquidez CONTRARIA al sesgo en la Killzone de HOY
    mask_ky = (ts_pd.date == hoy_utc) & (ts_pd.hour >= 13) & (ts_pd.hour < 16)
    idx_ky = np.where(mask_ky)[0]
    if len(idx_ky) < 3:
        return None, L_ltf

    # En sesgo alcista: Judas = caida bajo el minimo asiatico (barre stops de compradores)
    # En sesgo bajista: Judas = subida sobre el maximo asiatico (barre stops de vendedores)
    judas_alcista = sesgo_alcista and lo_ltf[idx_ky].min() < asia_lo
    judas_bajista = (not sesgo_alcista) and hi_ltf[idx_ky].max() > asia_hi
    if not judas_alcista and not judas_bajista:
        return None, L_ltf

    # Punto extremo del Judas (stop tecnico)
    judas_extreme = lo_ltf[idx_ky].min() if judas_alcista else hi_ltf[idx_ky].max()

    # 4) ENTRADA: FVG o OB en el LTF tras el Judas, con precio ya de vuelta al lado correcto
    cerr = L_ltf.iloc[:-1].reset_index(drop=True)
    hi_c = cerr["maximo"].to_numpy(); lo_c = cerr["minimo"].to_numpy()
    cl_c = cerr["cierre"].to_numpy(); op_c = cerr["apertura"].to_numpy()
    j = len(cl_c) - 1
    if j < 20:
        return None, L_ltf

    px = cl_c[j]
    if judas_alcista:
        # Precio debe haber vuelto SOBRE el minimo asiatico (barre y recupera)
        if px <= asia_lo:
            return None, L_ltf
        # Buscar FVG alcista en las ultimas 10 velas del LTF
        for i in range(max(0, j - 10), j - 1):
            if lo_c[i] > hi_c[i - 2] and (lo_c[i] - hi_c[i - 2]) / cl_c[i] > 0.0005:
                if lo_c[j] <= lo_c[i] and cl_c[j] > hi_c[i - 2]:
                    stop = judas_extreme * 0.999
                    if stop >= px:
                        continue
                    return _setup("largo", px, stop, 2.0), L_ltf
        # Buscar OB alcista si no hay FVG
        for i in range(max(0, j - 10), j - 1):
            if cl_c[i] < op_c[i] and cl_c[i + 1] > hi_c[i]:
                if lo_c[i] <= px <= hi_c[i]:
                    stop = judas_extreme * 0.999
                    if stop >= px:
                        continue
                    return _setup("largo", px, stop, 2.0), L_ltf
    else:
        if px >= asia_hi:
            return None, L_ltf
        for i in range(max(0, j - 10), j - 1):
            if hi_c[i] < lo_c[i - 2] and (lo_c[i - 2] - hi_c[i]) / cl_c[i] > 0.0005:
                if hi_c[j] >= hi_c[i] and cl_c[j] < lo_c[i - 2]:
                    stop = judas_extreme * 1.001
                    if stop <= px:
                        continue
                    return _setup("corto", px, stop, 2.0), L_ltf
        for i in range(max(0, j - 10), j - 1):
            if cl_c[i] > op_c[i] and cl_c[i + 1] < lo_c[i]:
                if lo_c[i] <= px <= hi_c[i]:
                    stop = judas_extreme * 1.001
                    if stop <= px:
                        continue
                    return _setup("corto", px, stop, 2.0), L_ltf
    return None, L_ltf


def velas_cached(ex, coin, tf, cache, limit=500):
    """Cachea las velas por (moneda, TF) durante el tick: muchas estrategias comparten las MISMAS
    velas -> se piden una sola vez (evita el 429 de Hyperliquid y acelera)."""
    k = (coin, tf)
    if k not in cache:
        cache[k] = velas(ex, coin, tf, limit)
    return cache[k]


def sesion_de(ts):
    """Sesión de mercado (UTC) de una operación. Detecta la apertura de NY (mercado USA)."""
    h = pd.to_datetime(ts, unit="ms").hour
    if 13 <= h < 15:
        return "ny_open"        # apertura USA (~9:30-11:00 ET)
    if 13 <= h < 21:
        return "ny"
    if 7 <= h < 13:
        return "londres"
    if h < 7:
        return "asia"
    return "cierre"


def det_elliott(d):
    """Proxy mecánico de ELLIOTT — entrada en ONDA 3: tras onda 1 (impulso) + onda 2 (retroceso 38-85%
    que NO rompe el origen), la ruptura del techo de onda 1 dispara la onda 3. Stop bajo onda 2.
    (No es Elliott "puro" —el conteo es subjetivo— pero captura su parte operable.) Espejo bajista."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    j = len(cl) - 1
    if j < 60:
        return None
    F = 2
    sh = [i for i in range(F, j - F) if hi[i] == hi[i - F:i + F + 1].max()]
    sl = [i for i in range(F, j - F) if lo[i] == lo[i - F:i + F + 1].min()]
    if len(sh) < 1 or len(sl) < 2:
        return None
    # ALCISTA: inicio(low0) -> techo onda1(h1) -> fondo onda2(low2) -> ruptura de h1 = onda3
    h1 = sh[-1]
    lb = [i for i in sl if i < h1]; la = [i for i in sl if i > h1]
    if lb and la:
        low0, low2 = lb[-1], la[-1]
        w1 = hi[h1] - lo[low0]
        if w1 > 0:
            retr = (hi[h1] - lo[low2]) / w1
            if lo[low2] > lo[low0] and 0.38 <= retr <= 0.85 and cl[j] > hi[h1] and cl[j - 1] <= hi[h1]:
                return _setup("largo", cl[j], lo[low2], 2.5)
    # BAJISTA (espejo)
    l1 = sl[-1]
    hb = [i for i in sh if i < l1]; ha = [i for i in sh if i > l1]
    if hb and ha:
        high0, high2 = hb[-1], ha[-1]
        w1d = hi[high0] - lo[l1]
        if w1d > 0:
            retrd = (hi[high2] - lo[l1]) / w1d
            if hi[high2] < hi[high0] and 0.38 <= retrd <= 0.85 and cl[j] < lo[l1] and cl[j - 1] >= lo[l1]:
                return _setup("corto", cl[j], hi[high2], 2.5)
    return None


def det_smc(ex, coin, ltf, cache):
    htf = HTF_DE[ltf]
    H = velas_cached(ex, coin, htf, cache).iloc[:-1]
    hi = H["maximo"].to_numpy(); lo = H["minimo"].to_numpy(); clh = H["cierre"].to_numpy()
    ema = H["cierre"].ewm(span=100, adjust=False).mean().to_numpy()
    zonas = []
    for i in range(2, len(clh)):
        if lo[i] > hi[i - 2] and (lo[i] - hi[i - 2]) / clh[i] > 0.0008 and clh[i] > ema[i]:
            zonas.append((hi[i - 2], lo[i], "largo"))
        if hi[i] < lo[i - 2] and (lo[i - 2] - hi[i]) / clh[i] > 0.0008 and clh[i] < ema[i]:
            zonas.append((hi[i], lo[i - 2], "corto"))
    L = velas_cached(ex, coin, ltf, cache).iloc[:-1]
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


def det_mtf(ex, coin, ltf, cache):
    """MULTI-TEMPORALIDAD de verdad: el marco MAYOR (HTF) marca la DIRECCION (tendencia EMA50 +
    impulso a favor) y el marco MENOR da el TIMING (ruptura de estructura tras el retroceso). Es la
    operativa 'estoy alcista en el marco grande, espero el retest y entro al giro'. SIN lookahead:
    solo velas CERRADAS (HTF y LTF). Stop al otro lado del último swing; objetivo 2R."""
    Lfull = velas_cached(ex, coin, ltf, cache)
    htf = HTF_DE.get(ltf)
    if htf is None:
        return None, Lfull
    H = velas_cached(ex, coin, htf, cache).iloc[:-1]          # HTF cerrado
    ch = H["cierre"].to_numpy()
    if len(ch) < 60:
        return None, Lfull
    e50 = H["cierre"].ewm(span=50, adjust=False).mean().to_numpy()
    htf_up = ch[-1] > e50[-1] and ch[-1] > ch[-5]            # marco mayor alcista + con impulso
    htf_dn = ch[-1] < e50[-1] and ch[-1] < ch[-5]
    L = Lfull.iloc[:-1]                                       # LTF cerrado
    last_sh, last_sl = _swings(L)
    cl = L["cierre"].to_numpy(); lo = L["minimo"].to_numpy(); hi = L["maximo"].to_numpy()
    j = len(cl) - 1
    if j < 30:
        return None, Lfull
    swl = lo[j - 10:j].min(); swh = hi[j - 10:j].max()
    if htf_up and not np.isnan(last_sh[j]) and cl[j] > last_sh[j] and cl[j - 1] <= last_sh[j]:
        return _setup("largo", cl[j], swl), Lfull            # ruptura de estructura al alza a favor del HTF
    if htf_dn and not np.isnan(last_sl[j]) and cl[j] < last_sl[j] and cl[j - 1] >= last_sl[j]:
        return _setup("corto", cl[j], swh), Lfull
    return None, Lfull


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
    if estr == "ob_trend":
        return det_ob_trend(cerr)
    if estr == "ob_plus":
        return det_ob_plus(cerr)
    if estr == "ob_regime":
        return det_ob_regime(cerr)
    if estr == "adrig2":
        return det_adrig2(cerr)
    if estr == "scalp_rev3":
        return det_scalp_rev3(cerr)
    if estr == "vwap":
        return det_vwap(cerr)
    if estr == "donchian":
        return det_donchian(cerr)
    if estr == "elliott":
        return det_elliott(cerr)
    if estr == "adrig":
        return det_adrig(cerr)
    if estr == "merinox":
        return det_merinox(cerr)
    if estr == "ob_asia":
        return det_ob_asia(cerr)
    if estr == "ob_ny_open":
        return det_ob_ny_open(cerr)
    if estr == "fvg_asia":
        return det_fvg_asia(cerr)
    if estr == "ob_regime_asia":
        return det_ob_regime_asia(cerr)
    if estr == "orf":
        return det_orf(cerr)
    if estr == "fvg_ob":
        return det_fvg_ob(cerr)
    if estr == "breaker":
        return det_breaker(cerr)
    if estr == "asia_sweep":
        return det_asia_sweep(cerr)
    if estr == "london_fade":
        return det_london_fade(cerr)
    return None


def _delta_oi(coin, oi_now):
    """Δ Open Interest (%): OI subiendo = dinero NUEVO entrando; bajando + precio arriba = squeeze.
    Mantiene un pequeño histórico por moneda en disco (persiste en la rama arena-data)."""
    f = REG / "_oihist.json"
    try:
        hist = json.loads(f.read_text()) if f.exists() else {}
    except Exception:
        hist = {}
    arr = hist.get(coin, [])
    if oi_now:
        arr.append([int(time.time()), oi_now]); arr = arr[-300:]
        hist[coin] = arr
        try:
            f.write_text(json.dumps(hist))
        except Exception:
            pass
    if len(arr) >= 5 and oi_now and arr[-5][1]:
        return round((oi_now / arr[-5][1] - 1) * 100, 2)
    return None


def _mercado(ex, coin, cache):
    """Contexto de MERCADO (funding, OI, ΔOI, Fear&Greed) — lo que NO se puede reconstruir del
    histórico de velas. Se pide UNA vez por moneda por tick (cacheado) para no saturar la API."""
    if coin not in cache:
        try:
            fr = ex.fetch_funding_rate(f"{coin}/USDC:USDC").get("fundingRate")
        except Exception:
            fr = None
        try:
            oi = ex.fetch_open_interest(f"{coin}/USDC:USDC").get("openInterestAmount")
        except Exception:
            oi = None
        cache[coin] = (fr, oi, _delta_oi(coin, oi))
    if "fng" not in cache:                                    # Fear & Greed, una vez por tick
        try:
            cache["fng"] = int(requests.get("https://api.alternative.me/fng/?limit=1",
                                            timeout=15).json()["data"][0]["value"])
        except Exception:
            cache["fng"] = None
    fr, oi, doi = cache[coin]
    return fr, oi, doi, cache["fng"]


def _ob_snapshot(ex, coin):
    """Snapshot del Order Book (top 5 bid/ask): IRREEMPLAZABLE, no se puede reconstruir después.
    Devuelve spread%, muro bid más gordo, muro ask más gordo y los niveles top-5 de cada lado."""
    try:
        ob = ex.fetch_order_book(f"{coin}/USDC:USDC", limit=20)
        bids = ob.get("bids", [])[:5]; asks = ob.get("asks", [])[:5]
        if not bids or not asks:
            return {}
        spread_pct = round((asks[0][0] - bids[0][0]) / bids[0][0] * 100, 4)
        bid_wall = max(bids, key=lambda x: x[1]) if bids else None
        ask_wall = max(asks, key=lambda x: x[1]) if asks else None
        return {
            "spread_%": spread_pct,
            "bid_wall_px": round(bid_wall[0], 4) if bid_wall else None,
            "bid_wall_sz": round(bid_wall[1], 2) if bid_wall else None,
            "ask_wall_px": round(ask_wall[0], 4) if ask_wall else None,
            "ask_wall_sz": round(ask_wall[1], 2) if ask_wall else None,
            "bids5": [[round(b[0], 4), round(b[1], 2)] for b in bids],
            "asks5": [[round(a[0], 4), round(a[1], 2)] for a in asks],
        }
    except Exception:
        return {}


def registrar_ctx_mercado(ex, coin, ts, px, fr, oi, fng):
    """Registro CONTINUO (append, JSONL) del contexto de mercado IRREEMPLAZABLE: funding, OI,
    Fear&Greed y snapshot del Order Book (no se puede reconstruir de velas). Con esto + las velas
    (siempre recuperables via API) se puede SIMULAR cualquier operativa futura. Una línea por tick."""
    f = REG / f"_ctx_{coin}.jsonl"
    try:
        row = {"ts": int(ts), "px": px, "funding": fr, "oi": oi, "fng": fng}
        row.update(_ob_snapshot(ex, coin))                         # spread + muros + top-5 niveles
        with f.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    except Exception:
        pass


def contexto(ex, coin, L, cache, cerr=None):
    """Contexto RICO por operación — para diagnosticar POR QUÉ funciona/falla y afinar luego.
    Incluye: funding/OI + ΔOI (posicionamiento), premium/discount + liquidez, ATR%/ADX (vol y
    tendencia-vs-rango), Fear&Greed (sentimiento) y volumen relativo. No es predicción: es CONTEXTO.
    `cerr` = velas hasta la vela de la SEÑAL (para fijar el contexto de precio en ese instante exacto,
    no en el de 'ahora'); si no se pasa, usa la última vela cerrada de L."""
    fr, oi, doi, fng = _mercado(ex, coin, cache)
    if cerr is None:
        cerr = L.iloc[:-1]
    px = float(cerr["cierre"].iloc[-1])
    hi = cerr["maximo"].tail(100); lo = cerr["minimo"].tail(100)
    rh = float(hi.max()); rl = float(lo.min())
    pos = round((px - rl) / (rh - rl), 2) if rh > rl else 0.5
    arr = hi[hi > px]; aba = lo[lo < px]
    dliq_up = round((arr.min() / px - 1) * 100, 2) if len(arr) else None
    dliq_dn = round((1 - aba.max() / px) * 100, 2) if len(aba) else None
    out = {"funding": fr, "oi": oi, "d_oi_%": doi, "fng": fng,
           "pos_rango": pos, "liq_arriba_%": dliq_up, "liq_abajo_%": dliq_dn}
    if len(cerr) >= 30:                                        # ATR%, ADX (vol y régimen), volumen
        try:
            tr = pd.concat([cerr["maximo"] - cerr["minimo"], (cerr["maximo"] - cerr["cierre"].shift()).abs(),
                            (cerr["minimo"] - cerr["cierre"].shift()).abs()], axis=1).max(axis=1)
            out["atr_%"] = round(float((tr.rolling(14).mean() / cerr["cierre"]).iloc[-1]) * 100, 3)
            adxarr = _adx(cerr)
            adxv = float(adxarr[-1])
            out["adx"] = round(adxv, 1)
            out["adx_dir"] = "subiendo" if adxarr[-1] > adxarr[-2] else "bajando"  # aceleracion del regimen
            out["regimen"] = "tendencia" if adxv > 25 else "rango"
            out["vol_rel"] = round(float(cerr["volumen"].iloc[-1] / cerr["volumen"].tail(20).mean()), 2)
        except Exception:
            pass
    # RSI en 1h y EMA50 en 1h (sesgo del marco mayor): info MULTI-TF que enriquece el diagnostico
    try:
        if ("1h_data", coin) in cache:
            d1h = cache[("1h_data", coin)]
        else:
            d1h = velas_cached(ex, coin, "1h", cache)
            cache[("1h_data", coin)] = d1h
        c1h = d1h["cierre"]
        rsi1h = float(_rsi(c1h)[-1])
        ema50_1h = float(c1h.ewm(span=50, adjust=False).mean().iloc[-1])
        out["rsi_1h"] = round(rsi1h, 1)
        out["ema50_1h_dist_%"] = round((px / ema50_1h - 1) * 100, 2)   # distancia % al EMA50 del 1h
    except Exception:
        pass
    # RANGO ASIATICO del dia actual (fundamental para setup Sensei / ICT Killzone)
    try:
        hoy_utc = pd.Timestamp.now("UTC").date()
        ts_arr2 = cerr["t"].to_numpy()
        ts_pd2 = pd.to_datetime(ts_arr2, unit="ms", utc=True)
        mask_as = (ts_pd2.date == hoy_utc) & (ts_pd2.hour < 7)
        idx_as = np.where(mask_as)[0]
        if len(idx_as) >= 3:
            out["asia_hi"] = round(float(cerr["maximo"].to_numpy()[idx_as].max()), 4)
            out["asia_lo"] = round(float(cerr["minimo"].to_numpy()[idx_as].min()), 4)
            out["asia_rango_%"] = round((out["asia_hi"] - out["asia_lo"]) / out["asia_lo"] * 100, 2)
            out["px_vs_asia"] = ("premium" if px > out["asia_hi"] else
                                 "descuento" if px < out["asia_lo"] else "dentro")
    except Exception:
        pass
    # SESION ANTERIOR: qué hizo la sesión que acaba de terminar (tesis Sensei Trading / ICT)
    try:
        h_sig = int(pd.to_datetime(int(cerr["t"].iloc[-1]), unit="ms").hour)
        # Asia cierra a las 07:00 UTC; Londres cierra a las 13:00; NY cierra a las 21:00
        # Buscamos el rango de la sesión anterior al momento de la señal
        if 7 <= h_sig < 13:
            ses_ant_range = (0, 7)      # la señal es en Londres -> sesion anterior = Asia
            ses_ant_nombre = "asia"
        elif 13 <= h_sig < 21:
            ses_ant_range = (7, 13)     # señal en NY -> sesion anterior = Londres
            ses_ant_nombre = "londres"
        else:
            ses_ant_range = (13, 21)    # señal en Asia/Cierre -> sesion anterior = NY del dia anterior
            ses_ant_nombre = "ny"
        ts_arr = cerr["t"].to_numpy()
        cl_arr = cerr["cierre"].to_numpy()
        horas = pd.to_datetime(ts_arr, unit="ms").hour
        mask = (horas >= ses_ant_range[0]) & (horas < ses_ant_range[1])
        idx = np.where(mask)[0]
        if len(idx) >= 3:
            ses_open = cl_arr[idx[0]]; ses_close = cl_arr[idx[-1]]
            ses_hi = cerr["maximo"].to_numpy()[idx].max(); ses_lo = cerr["minimo"].to_numpy()[idx].min()
            out["ses_ant"] = ses_ant_nombre
            out["ses_ant_dir"] = "alcista" if ses_close > ses_open else "bajista"
            out["ses_ant_rango_%"] = round((ses_hi - ses_lo) / ses_open * 100, 2)
    except Exception:
        pass
    return out


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
    vcache = {}         # velas por (moneda, TF) compartidas entre estrategias (evita 429)

    # --- REGISTRO CONTINUO del contexto de mercado (una vez por moneda por tick, haya señal o no) ---
    # Es lo único irreemplazable: con esto + las velas se puede simular cualquier operativa futura.
    ahora_ms = int(time.time() * 1000)
    for coin in COINS:
        try:
            m1_cache[coin] = velas(ex, coin, "1m", 5000)
        except Exception:
            m1_cache[coin] = None
        try:
            fr, oi, doi, fng = _mercado(ex, coin, ctx_cache)
            px = float(m1_cache[coin]["cierre"].iloc[-1]) if m1_cache[coin] is not None and len(m1_cache[coin]) else None
            registrar_ctx_mercado(ex, coin, ahora_ms, px, fr, oi, fng)
        except Exception:
            pass

    for estr, tfs_estr in ESTRATEGIAS_TF.items():
        for coin in COINS:
            for tf in tfs_estr:
                f = REG / f"{estr}_{coin}_{tf}.json"
                ops = json.loads(f.read_text()) if f.exists() else []
                last_ts = max((o["ts"] for o in ops), default=0)
                nuevos = []     # (ts, setup) de TODAS las velas cerradas desde la última ejecución
                try:
                    if estr == "smc":
                        s, L = det_smc(ex, coin, tf, vcache)
                        tsl = int(L["t"].iloc[-2])
                        if s and tsl > last_ts:
                            nuevos.append((tsl, s, L.iloc[:-1]))
                    elif estr == "mtf":
                        s, L = det_mtf(ex, coin, tf, vcache)
                        tsl = int(L["t"].iloc[-2])           # última vela CERRADA (L = frame completo)
                        if s and tsl > last_ts:
                            nuevos.append((tsl, s, L.iloc[:-1]))
                    elif estr == "ob_scalp":
                        s, L = det_ob_scalp(ex, coin, vcache)
                        if L is None:
                            L = velas_cached(ex, coin, "1m", vcache)
                        tsl = int(L["t"].iloc[-2])           # última 1m cerrada
                        if s and tsl > last_ts:
                            nuevos.append((tsl, s, L.iloc[:-1]))
                    elif estr == "sensei":
                        s, L = det_sensei(ex, coin, tf, vcache)
                        if L is None:
                            L = velas_cached(ex, coin, tf, vcache)
                        tsl = int(L["t"].iloc[-2])
                        if s and tsl > last_ts:
                            nuevos.append((tsl, s, L.iloc[:-1]))
                    else:
                        L = velas_cached(ex, coin, tf, vcache)
                        closed = L.iloc[:-1].reset_index(drop=True)   # velas YA cerradas
                        tsa = closed["t"].to_numpy()
                        for p in range(max(0, len(closed) - 50), len(closed)):
                            if tsa[p] <= last_ts:                      # ya registrada antes
                                continue
                            s = detectar_cerr(estr, closed.iloc[:p + 1], coin)   # evalúa esa vela
                            if s:
                                nuevos.append((int(tsa[p]), s, closed.iloc[:p + 1]))   # vela de la señal
                except Exception as e:
                    print(f"  {estr}/{coin}/{tf}: error {type(e).__name__}: {e}"); continue
                if coin not in m1_cache:
                    try:
                        m1_cache[coin] = velas(ex, coin, "1m", 5000)
                    except Exception:
                        m1_cache[coin] = None
                actualizar(ops, L, m1_cache[coin])
                for ts_p, s, cerr_sig in nuevos:
                    if any(o["ts"] == ts_p for o in ops):
                        continue
                    s.update(status="abierta", ts=ts_p, estr=estr, coin=coin, tf=tf,
                             fecha=str(pd.to_datetime(ts_p, unit="ms")), sesion=sesion_de(ts_p))
                    try:
                        s.update(contexto(ex, coin, L, ctx_cache, cerr=cerr_sig))
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
