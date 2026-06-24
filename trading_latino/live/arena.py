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
COINS = ["BTC", "ETH", "SOL"]   # 3 monedas = 3x velocidad de datos; SOL añadida 2026-06-23
# cada estrategia corre en SUS temporalidades (scalping en rápidas)
ESTRATEGIAS_TF = {
    # Cobertura AMPLIA de temporalidades por familia: tener muestra en CADA TF y poder comparar la
    # MISMA estrategia entre temporalidades (objetivo: sacar lo mejor de cada una con datos reales).
    # Las velas se comparten en caché por (moneda, TF) -> ampliar es casi gratis para la API.
    # ============================================================
    # ESTRATEGIAS — TFs DEPURADOS CON DATOS REALES (2026-06-23)
    # Regla: se elimina un TF cuando tiene >=5 ops y es consistentemente negativo.
    # El 15m es el TF ganador de casi todo. El 5m solo funciona para FVG puro.
    # El 4h tiene pocos datos (pocas señales/dia) y resultado negativo en la mayoria.
    # ============================================================

    # --- ESTRUCTURA / TENDENCIA (medios-altos) ---
    "smc": ["15m", "1h", "4h"],
    # merino: RETIRADO 1h 2026-06-24 (n=13, -0.83R). El 4h es el mejor (+0.77R), 15m neutral. La familia
    # Merino (validada robusta en multi-año: +0.058R en 6 años) vive en 15m/4h, no en 1h.
    "merino": ["15m", "4h"],
    # sweep RETIRADA 2026-06-23: n=18, hasta su MEJOR salida (t125) = -0.18R. Negativa en todas las salidas.
    # "sweep": ["15m", "1h", "4h"],
    # RETIRADO 5m (58ops -0.32R), 1h (27ops -0.24R), 4h (18ops -0.42R).
    # Solo 15m tiene edge real: +1.01R 76%win (n=66). Fuera del 15m el OB pierde toda la magia.
    "ob_trend": ["15m"],
    "elliott_ob": ["15m", "1h", "4h"],   # Elliott+OB: TFs medios donde el patron tiene sentido

    # --- FVG — RETIRADA DEFINITIVA 2026-06-23 ---
    # fvg n=533 exp=-0.049R: muestra maxima de confianza, negativo en todos los TFs y salidas.
    # fvg_asia n=167 exp=-0.072R: el filtro Asia NO ayuda al FVG sin OB.
    # LECCION: FVG solo no tiene edge. FVG+OB (fvg_ob) si funciona (+0.380R). La confluencia es clave.
    # rsi_ob RETIRADA 2026-06-24: se aflojo para que disparara (estaba en n=0), y al hacerlo CONFIRMO que
    # pierde (-0.64R, n=10). La familia RSI ya fallo 4 veces (rsi -0.92R, rsidiv -0.60R, rsidiv_ob, rsi_ob).
    # El rescate cumplio su funcion: darnos la respuesta. Las divergencias/extremos RSI no tienen edge aqui.
    # "rsi_ob": ["5m", "15m", "1h"],
    # rsidiv_ob RETIRADA 2026-06-24: n=7 en 5 dias (apenas dispara, 1.3/dia) Y pierde (-0.60R mejor
    # salida). La familia divergencia ya fallo antes (rsidiv base retirada). Confirma: las divergencias
    # RSI no tienen edge aqui (cazan giros que no ocurren). Menos es mas.
    # "rsidiv_ob": ["15m", "1h"],

    # RETIRADAS definitivamente (muestra suficiente, todas las salidas negativas):
    # vwap 91ops -0.43R (1m -0.72R, 5m -0.38R, 15m -0.20R) — muerto en todos los TF y exits.
    # ob 513ops -0.39R tagged, scalp_rev 485ops, scalp_rev3 120ops, donchian 65ops,
    # rsi 33ops -0.92R, rsidiv 105ops -0.60R, adx 53ops -0.98R, scalp_sqz 270ops -0.69R.

    # --- COMPUESTAS multi-factor ---
    "adrig": ["15m", "1h", "4h"],
    # merinox = LA ESTRATEGIA ROBUSTA (multi-año BTC: +0.080R, POSITIVA en los 6 años Y en lateral+bajista).
    # RETIRADO 1h 2026-06-24 (n=9, -1.06R). El 4h (+0.38R) y 15m (+0.15R) son sus TF. Promocionada a
    # estrategia PRINCIPAL del proyecto (sustituye a la familia OB, que no tiene edge multi-año).
    "merinox": ["15m", "4h"],
    # RETIRADO 4h de adrig2 (18 ops -1.10R). RETIRADO 1h 2026-06-24: con muestra (n=29) el 1h da
    # -0.72R mientras el 15m da +0.05R. El desplazamiento institucional da pocas señales y malas en 1h.
    # Queda solo 15m (marginal, +0.05R, y solo BTC gana: +0.29R). En vigilancia.
    "adrig2": ["15m"],

    # --- MULTI-TEMPORALIDAD ---
    "mtf": ["15m", "1h", "4h"],

    # --- FAMILIA OB DEPURADA ---
    # ob_plus base RETIRADA 2026-06-24: DOBLE confirmacion de que no tiene edge — multi-año
    # (BTC/ETH/SOL 2021-2026, ~47k ops): -0.006 a -0.029R, negativa en los 6 años y 3 climas; Y en vivo
    # -0.214R (n=155). El OB SIN filtro de sesion no funciona. Se mantiene ob_plus_asia (filtro Asia, a validar).
    # "ob_plus": ["15m"],
    # ob_plus_asia_r3: COMBINATION de los dos mejores hallazgos:
    #   ob_plus_asia (reina, +1.295R n=66) + objetivo 3R (como ob_trend_r3, +1.085R n=79).
    #   Si el precio alcanza 2R y continua (evidenciado por trail < fixed), probar 3R captura mas.
    "ob_plus_asia_r3": ["15m"],
    # ob_asia_close: OB solo en cierre de Tokyo (03-07h UTC).
    #   sub_sesion revela: tokyo_close +0.68R vs tokyo_open +0.04R. La ultima parte de Asia
    #   es donde el mercado hace los movimientos mas limpios antes de que abra Londres.
    "ob_asia_close": ["15m"],
    # breaker_prev_ny: breaker (+0.014R muerto) RESUCITADO por filtro sesion anterior NY.
    #   Cuando NY anterior fue alcista: breaker = +1.52R win=94% (n=18). El contexto del
    #   dia anterior cambia completamente el edge — el breaker necesita momentum previo de NY.
    # breaker_prev_ny RETIRADA 2026-06-23: con mas datos (n=19) el edge se evaporo — hasta su
    #   MEJOR salida (be05) = -0.58R. El +1.52R inicial (n=18) era ruido de muestra pequena.
    # "breaker_prev_ny": ["15m"],
    # ob_regime base RETIRADA 2026-06-24: DOBLE confirmacion sin edge — multi-año (BTC/ETH/SOL,
    # ~47k ops): -0.026 a -0.029R, negativa en 6 años y 3 climas; Y en vivo -0.23R (n=198). El switcher
    # OB sin filtro de sesion no funciona en NINGUN clima. Se mantiene ob_regime_asia (+0.35R, a validar).
    # "ob_regime": ["15m"],

    # --- PRUEBAS DE SESION ---
    # ob_asia: RETIRADO 1h (9 ops -0.43R). El edge de sesion es solo en 15m (+0.97R) y 4h vigila.
    "ob_asia": ["15m", "4h"],
    # fvg_asia RETIRADA DEFINITIVA 2026-06-23: n=167 exp=-0.072R, negativo en 15m y 1h.
    # El filtro Asia SIN OB no funciona. fvg_ob_asia (con OB) si es positivo (+0.654R).
    # ob_regime_asia: 15m (+0.97R) es el star, 1h (-0.11R 6ops) poca muestra — la mantenemos.
    "ob_regime_asia": ["15m", "1h"],
    # ob_ny_open: -0.478R fixed pero trail=+0.152R (n=20). Poca muestra, mantener para confirmar.
    "ob_ny_open": ["15m"],    # retirado 5m y 1h, solo 15m para seguir midiendo

    # --- SCALP/MULTI-TF especiales ---
    "ob_scalp": ["1m"],
    "sensei": ["1m", "5m"],

    # --- ALTERNATIVAS (en recoleccion de datos) ---
    # donchian: RE-ACTIVADA 2026-06-23 con criterio. Se retiro por -0.39R en vivo... pero se midio
    # SOLO con salida 2R, que MATA un trend-following (su edge es dejar correr ganancias grandes).
    # Backtest Binance (50d): donchian a 2R = +0.05/+0.24R; "dejar correr" = -0.05/-0.08R en oso/lateral,
    # pero deberia brillar en tendencia fuerte (toro). El arena mide LAS 5 SALIDAS a la vez (fixed=cortar
    # pronto, trail=dejar correr) -> con esto medimos EN VIVO la tesis del video (cortar vs dejar correr)
    # y en QUE regimen gana cada una. 15m (el TF que el video dice que filtra el ruido) + 1h de control.
    # RETIRADO 1h 2026-06-24 (-0.65R live). Multi-año: donchian_2R (salida FIJA) gana en alts
    # (+0.036R ETH/SOL); donchian_trend (dejar correr) PIERDE -> la tesis del video era falsa, el corte
    # en 2R funciona mejor. El arena mide las 5 salidas en 15m y confirma cual gana.
    "donchian": ["15m"],
    # atr_break: AÑADIDA 2026-06-23 tras validar en Binance 50d (1m exacto): +0.41R en BTC Y ETH,
    #   win 52% (vs 36-41% de las OB), positivo los 2 meses y las 2 monedas. Sesgo de diseño BAJO
    #   (canal de Keltner de manual + concepto del video, no exprimido de estos datos). Perfil de edge
    #   DISTINTO: gana en NY (+0.53R) donde las OB mueren (-0.12R) -> diversifica de verdad. Canal
    #   adaptativo (EMA20 ± 2·ATR14): en alta volatilidad las bandas se abren y filtran fakeouts mejor
    #   que el Donchian fijo. La variante con filtro Asia/EMA200 NO mejoraba la base -> entra la base sola.
    #   VINDICADA en multi-año (BTC 2021-2026: +0.018R, mejor en bajista +0.11R). El -0.47R en vivo era
    #   mala suerte de muestra pequeña (n=51). RETIRADO 1h 2026-06-24 (-0.72R live, patrón sistémico).
    "atr_break": ["15m"],
    "orf": ["5m", "15m"],
    "fvg_ob": ["15m", "1h"],     # RETIRADO 5m (6 ops -1.40R); 15m +1.83R 100%win es el star
    # breaker RETIRADA 2026-06-23: n=104, hasta su MEJOR salida = -0.05R. 104 ops sin edge y sin
    #   tesis fuerte que la respalde. Su variante prev_ny tambien murio con datos. Familia agotada.
    # "breaker": ["15m", "4h"],
    # asia_sweep RETIRADA DEFINITIVA 2026-06-23: n=23 exp=-0.564R, la peor estrategia del arena.
    # El barrido del rango asiatico es REAL (el precio barra el rango) pero la entrada es mala.
    # El mismo concepto funciona mejor en judas_swing_ob (con confirmacion OB de reversal).
    "london_fade": ["15m", "1h"],

    # ===== AÑADIDAS 2026-06-23 — de la primera ronda de calibración =====
    # RETIRADO 5m de ob_plus_asia 2026-06-24 (n=76, -0.18R): arrastraba a la ganadora. 15m/1h se quedan.
    "ob_plus_asia": ["15m", "1h"],
    "smc_asia": ["15m", "1h", "4h"],
    "choch": ["15m", "1h", "4h"],
    # RETIRADO 5m de ema_pullback 2026-06-24: 5m=-0.46R (n=32) = ruido. El pullback a EMA necesita
    # estructura que el 5m no da tiempo a formar. (Nota: el 5m SÍ sirve para orf, +0.12R -> no se generaliza.)
    # RETIRADO 1h tambien 2026-06-24 (n=21, -0.65R): patron sistemico, el 1h pierde. El 15m es +0.19R.
    "ema_pullback": ["15m"],
    # ===== AÑADIDAS 2026-06-23 — segunda ronda, basadas en analisis de datos en vivo =====
    # N) fvg_ob_asia: EL HALLAZGO DEL DIA — fvg_ob 15m Asia = 100% win +1.8R (n=15).
    #    El mismo setup en Londres/NY = negativo. Filtrar a Asia pura es la clave.
    #    RETIRADO 1h 2026-06-24 (n=23, -0.55R): la ganadora vive en 15m, el 1h la lastra.
    "fvg_ob_asia": ["15m"],
    # O) adrig2_asia RETIRADA 2026-06-23: n=120 exp=-0.140R — el filtro de sesion DESTROZA adrig2.
    #    adrig2 base = +0.030R; con filtro Asia = -0.140R. Adrig2 necesita NY/Londres (volumen alto).
    #    LECCION: los patrones de desplazamiento institucional NO mejoran con filtro Asia (al reves que OB).
    # P) ob_trend_r3: ob_trend en Asia con objetivo 3R. Los datos muestran que ob_plus_asia
    #    (fixed=+1.30R) NO se mejora con trailing (trail=+0.14R). El precio alcanza el objetivo
    #    Y sigue. Probar 3R para ver si podemos capturar mas ganancia en los mejores setups.
    #    RETIRADO 1h 2026-06-24 (n=32, -0.67R): la ganadora (+0.89R) vive en 15m; el 1h la lastra.
    "ob_trend_r3": ["15m"],
    # RONDA 3 — estrategias de ventana de mercado basadas en ICT + datos propios
    # Q) silver_bullet: FVG en las 3 killzones ICT (08h London, 15h NYSE 10AM, 19h NYSE 2PM).
    #    El institucional opera en ventanas horarias muy concretas; el FVG dentro de esa ventana
    #    tiene el mayor edge segun la metodologia ICT (validado en forex, probandolo en cripto).
    "silver_bullet": ["5m", "15m"],
    # R) judas_swing_ob: London open (07-10h) barre el rango asiatico (trampa institucional)
    #    y luego forma OB en la direccion CONTRARIA. Es el 'Judas Swing' ICT — la manipulation
    #    mas documentada: Londres engana al retail antes de moverse en la direccion real.
    # judas_swing_ob RETIRADA 2026-06-23: en mucho tiempo solo genero n=4 (apenas dispara) Y pierde
    #   (-1.56R). Patron demasiado restrictivo: sin muestra util y negativa. Concepto ICT no cuaja aqui.
    # "judas_swing_ob": ["5m", "15m"],
    # S) ny_london_sweep: NY open (13-15h) barre el rango de Londres y revierte.
    #    El paralelo del Judas Swing en la transicion London → NY. Ya tenemos london_hi/lo en
    #    contexto; esta estrategia verifica si NY 'roba' liquidez de Londres antes de seguir.
    "ny_london_sweep": ["5m", "15m"],
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
    """Ruptura de canal Donchian (máx/mín de 20 velas) = seguimiento de tendencia.
    Lógica económica (no curve-fit): si el precio supera el MÁXIMO de las últimas 20 velas, hay
    demanda real empujando (ruptura genuina); espejo a la baja. Entrada al CIERRE de la vela de
    ruptura (cl[j] cruza la banda y cl[j-1] aún no) — exige cierre, no solo mecha (filtra fakeouts).
    Stop al swing opuesto de 10 velas. El objetivo 2R aquí es solo el ancla del riesgo: el arena
    mide 5 salidas en paralelo (fixed=cortar pronto vs trail=dejar correr), que es como medimos EN
    VIVO la tesis del video (Donchian rinde dejando correr) y en qué régimen gana cada salida."""
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


def det_atr_break(d):
    """Ruptura de canal de Keltner (EMA20 ± 2·ATR14) = breakout ADAPTATIVO a la volatilidad.
    Lógica económica (no curve-fit): a diferencia del Donchian (canal fijo de N velas), aquí el
    canal se ensancha cuando sube la volatilidad (ATR alto) y se estrecha cuando baja. En cripto,
    donde la volatilidad cambia mucho, eso exige MÁS empuje para dar señal en mercados nerviosos
    (filtra fakeouts) y reacciona antes en mercados tranquilos. Entrada al CIERRE que cruza la banda
    (cl[j] fuera, cl[j-1] dentro). Stop al swing opuesto de 10 velas, ancla 2R. El arena mide las 5
    salidas en paralelo. Validada en Binance 50d (1m): +0.41R BTC y ETH, win 52%, gana en NY donde
    las OB pierden -> perfil de edge complementario."""
    cl = d["cierre"].to_numpy(); hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    j = len(cl) - 1
    if j < 30:
        return None
    # ATR14 (Wilder via EWM) sobre el True Range
    tr = np.maximum(hi[1:] - lo[1:],
                    np.maximum(np.abs(hi[1:] - cl[:-1]), np.abs(lo[1:] - cl[:-1])))
    tr_full = np.concatenate([[hi[0] - lo[0]], tr])
    atr = pd.Series(tr_full).ewm(span=14, adjust=False).mean().to_numpy()
    ema20 = d["cierre"].ewm(span=20, adjust=False).mean().to_numpy()
    if np.isnan(atr[j]) or np.isnan(ema20[j]) or np.isnan(atr[j - 1]) or np.isnan(ema20[j - 1]):
        return None
    bu = ema20[j] + 2.0 * atr[j]; bd = ema20[j] - 2.0 * atr[j]
    bu1 = ema20[j - 1] + 2.0 * atr[j - 1]; bd1 = ema20[j - 1] - 2.0 * atr[j - 1]
    sl = lo[max(0, j - 10):j].min(); sh = hi[max(0, j - 10):j].max()
    # NOTA 2026-06-24: el multi-año sugeria añadir filtro EMA200 (atr_break_trend > base), PERO el VIVO
    # (lo MAS real) lo contradice en el régimen actual: sobre_ema200 = -0.82R = el peor caso. Como el vivo
    # manda, se deja la base SIN filtro y se deja que los datos en vivo decidan. (Revertido tras revisar.)
    if cl[j] > bu and cl[j - 1] <= bu1:
        return _setup("largo", cl[j], sl, 2.0)
    if cl[j] < bd and cl[j - 1] >= bd1:
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


def det_ob_plus_asia(d):
    """ob_plus CON FILTRO DE SOLO ASIA PURA (00-07 UTC). Dato real del analisis de sesion:
    ob_plus Asia n=38 +1.03R 79%win, pero Londres n=19 -0.97R 11%win (DESTRUYE el edge).
    El edge de ob_plus esta SOLO en Asia, no en el conjunto Asia+Londres. Por eso el filtro
    es h<7 (no h<13 como ob_asia/fvg_asia). Solo opera las mejores horas de ob_plus."""
    h = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)
    if h >= 7:
        return None
    return det_ob_plus(d)


def det_elliott_ob(d):
    """Elliott mecanico (onda 3) + OB activo como soporte/resistencia en la zona del stop.
    Elliott puro = 0% win porque falla en el timing. Con un OB valido en la zona de onda 2
    (donde ponemos el stop), el nivel tiene respaldo estructural real, no solo fractal.
    EMA200 obligatorio para no ir contra el sesgo de fondo."""
    s = det_elliott(d)
    if s is None:
        return None
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    j = len(cl) - 1
    if j < 215 or np.isnan(ema[j]):
        return None
    stop = s["stop"]
    for i in range(max(0, j - 50), j - 1):
        if (hi[i] - lo[i]) / cl[i] < 0.0005:
            continue
        if s["dir"] == "largo" and cl[i] < op[i] and cl[i + 1] > hi[i]:
            if lo[i] <= stop <= hi[i] and cl[j] > ema[j]:
                return s
        if s["dir"] == "corto" and cl[i] > op[i] and cl[i + 1] < lo[i]:
            if lo[i] <= stop <= hi[i] and cl[j] < ema[j]:
                return s
    return None


def det_rsi_ob(d):
    """RSI sale de extremo (<30→≥30 o >70→≤70) Y precio esta en zona OB activa (EMA200).
    El RSI aporta el momentum (el mercado estaba en panico/euforia), el OB aporta la
    estructura (nivel institucional real). Solo cuando ambos coinciden simultaneamente.
    rsi puro = -0.92R tagged; el OB actua como filtro estructural de calidad."""
    c = d["cierre"]; rsi = _rsi(c); cl = c.to_numpy(); j = len(cl) - 1
    if j < 215 or np.isnan(rsi[j - 1]):
        return None
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); op = d["apertura"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    if np.isnan(ema[j]):
        return None
    # AFLOJADO 2026-06-24 (RESCATE): exigir el cruce EXACTO en esta vela hacia que rsi_ob NO disparara
    # NUNCA (n=0 en semanas) — el RSI casi nunca cruza justo cuando el precio esta dentro de un OB.
    # Ahora: el RSI estuvo en extremo (<35/>65) en las ultimas 5 velas y se esta recuperando ahora,
    # dando VENTANA para coincidir con la zona OB. Asi generamos datos para evaluarla de verdad.
    look = rsi[max(0, j - 5):j]
    sale_sobreventa = len(look) and np.nanmin(look) < 35 and rsi[j] >= 35 and rsi[j] >= rsi[j - 1]
    sale_sobrecompra = len(look) and np.nanmax(look) > 65 and rsi[j] <= 65 and rsi[j] <= rsi[j - 1]
    if not sale_sobreventa and not sale_sobrecompra:
        return None
    for i in range(max(0, j - 30), j - 1):
        if (hi[i] - lo[i]) / cl[i] < 0.0008:
            continue
        if sale_sobreventa and cl[j] > ema[j]:
            if cl[i] < op[i] and cl[i + 1] > hi[i] and lo[i] <= cl[j] <= hi[i]:
                return _setup("largo", cl[j], lo[i] * 0.999)
        if sale_sobrecompra and cl[j] < ema[j]:
            if cl[i] > op[i] and cl[i + 1] < lo[i] and lo[i] <= cl[j] <= hi[i]:
                return _setup("corto", cl[j], hi[i] * 1.001)
    return None


def det_rsidiv_ob(d):
    """Divergencia RSI + OB activo (doble confirmacion): precio hace nuevo extremo pero RSI no
    lo acompana (divergencia clasica), Y hay un OB institucional en la zona. La divergencia sola
    genera falsos (-0.60R tagged); el OB actua como filtro de estructura que valida el nivel.
    Solo opera divergencias que ocurren EN una zona OB real, alineada con EMA200."""
    c = d["cierre"]; rsi = _rsi(c)
    lo = d["minimo"].to_numpy(); hi = d["maximo"].to_numpy(); cl = c.to_numpy()
    op = d["apertura"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    j = len(cl) - 1
    if j < 215 or np.isnan(rsi[j]) or np.isnan(ema[j]):
        return None
    vent = range(j - 30, j - 4)
    pl = min(vent, key=lambda k: lo[k])
    ph = max(vent, key=lambda k: hi[k])
    div_bull = lo[j] < lo[pl] and rsi[j] > rsi[pl] and rsi[j] < 50
    div_bear = hi[j] > hi[ph] and rsi[j] < rsi[ph] and rsi[j] > 50
    if not div_bull and not div_bear:
        return None
    for i in range(max(0, j - 40), j - 1):
        if (hi[i] - lo[i]) / cl[i] < 0.0008:
            continue
        if div_bull and cl[j] > ema[j] and cl[i] < op[i] and cl[i + 1] > hi[i]:
            if lo[i] <= cl[j] <= hi[i]:
                return _setup("largo", cl[j], lo[j] * 0.999, 2.0)
        if div_bear and cl[j] < ema[j] and cl[i] > op[i] and cl[i + 1] < lo[i]:
            if lo[i] <= cl[j] <= hi[i]:
                return _setup("corto", cl[j], hi[j] * 1.001, 2.0)
    return None


def det_choch(d):
    """CHANGE OF CHARACTER (ChoCh ICT/SMC): el precio rompe la ultima estructura en sentido
    CONTRARIO al sesgo previo, senalando un cambio de regimen. El mercado pasa de hacer
    swing highs descendentes a romper uno al alza (ChoCh alcista), o lo opuesto (bajista).
    Solo Asia+Londres (h<13): datos reales validan rango+Asia como la mejor ventana (+1.49R 93%).
    A favor de EMA200 para no operar reversiones contra el sesgo macro de fondo."""
    h = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)
    if h >= 13:
        return None
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    j = len(cl) - 1
    if j < 215 or np.isnan(ema[j]):
        return None
    F = 3
    sh = [i for i in range(F, j - F) if hi[i] == max(hi[max(0, i - F):i + F + 1])]
    sl = [i for i in range(F, j - F) if lo[i] == min(lo[max(0, i - F):i + F + 1])]
    if len(sh) < 2 or len(sl) < 2:
        return None
    last_sh = sh[-1]; prev_sh = sh[-2]
    last_sl = sl[-1]; prev_sl = sl[-2]
    # ChoCh ALCISTA: estructura bajista (SH descendentes) rota al alza
    if hi[last_sh] < hi[prev_sh]:
        if cl[j] > hi[last_sh] and cl[j - 1] <= hi[last_sh] and cl[j] > ema[j]:
            return _setup("largo", cl[j], lo[last_sl] * 0.999, 2.0)
    # ChoCh BAJISTA: estructura alcista (SL ascendentes) rota a la baja
    if lo[last_sl] > lo[prev_sl]:
        if cl[j] < lo[last_sl] and cl[j - 1] >= lo[last_sl] and cl[j] < ema[j]:
            return _setup("corto", cl[j], hi[last_sh] * 1.001, 2.0)
    return None


def det_ema_pullback(d):
    """PULLBACK A EMA21 EN TENDENCIA: el precio retrocede hasta la EMA21 mientras la EMA200
    senala tendencia alcista/bajista. La vela toca la EMA21 y cierra de vuelta a favor.
    ADX>18 para confirmar que hay tendencia real, no ruido lateral.
    Solo Asia+Londres (h<13): datos validan tendencia+Asia como ventana viable (+0.52R 60%).
    Estrategia completamente distinta a la familia OB: mide el pullback clasico a la media."""
    h = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)
    if h >= 13:
        return None
    c = d["cierre"]
    e21 = c.ewm(span=21, adjust=False).mean().to_numpy()
    e200 = c.ewm(span=200, adjust=False).mean().to_numpy()
    adx = _adx(d)
    cl = c.to_numpy(); lo = d["minimo"].to_numpy(); hi = d["maximo"].to_numpy()
    j = len(cl) - 1
    if j < 215 or np.isnan(e200[j]) or np.isnan(e21[j]) or np.isnan(adx[j]):
        return None
    if adx[j] < 18:
        return None
    swl = d["minimo"].iloc[j - 7:j].min(); swh = d["maximo"].iloc[j - 7:j].max()
    if cl[j] > e200[j] and lo[j] <= e21[j] and cl[j] > e21[j] and cl[j] > cl[j - 1]:
        return _setup("largo", cl[j], swl, 2.0)
    if cl[j] < e200[j] and hi[j] >= e21[j] and cl[j] < e21[j] and cl[j] < cl[j - 1]:
        return _setup("corto", cl[j], swh, 2.0)
    return None


def det_smc_asia(ex, coin, ltf, cache):
    """SMC (FVG marco mayor + BOS marco menor) CON FILTRO de sesion Asia+Londres (h<13 UTC).
    smc es la estrategia con mejor edge en datos reales (+0.77R tagged). La hipotesis:
    el SMC en sesion americana se degrada como ob (mismo patron: institucional de noche).
    Muestra aun pequena para confirmar, pero la hipotesis tiene sentido estructural fuerte."""
    h_utc = int(pd.Timestamp.now("UTC").hour)
    if h_utc >= 13:
        return None, velas_cached(ex, coin, ltf, cache)
    return det_smc(ex, coin, ltf, cache)


def det_fvg_ob_asia(d):
    """FVG_OB CON FILTRO ASIA (h<7 UTC) — el descubrimiento mas importante de la arena hasta ahora.
    Analisis de fvg_ob por sesion muestra:
      - fvg_ob 15m Asia:    n=15 ops, TODAS positivas, rango +1.77R a +1.94R  (100% win)
      - fvg_ob 5m  Londres: n=6  ops, TODAS negativas, rango -1.34R a -1.45R (0% win)
    La doble confluencia FVG-dentro-de-OB funciona PERFECTAMENTE en Asia y FALLA en NY/Londres.
    Hipotesis: en Asia el mercado es menos manipulado (menos volumen), las zonas institucionales
    se respetan mas limpiamente. Filtramos a solo Asia pura (h<7) para capturar ese edge."""
    h = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)
    if h >= 7:   # solo Asia pura; London y NY destruyen el patron
        return None
    return det_fvg_ob(d)


def det_adrig2_asia(d):
    """AdriG2 (desplazamiento institucional + FVG + retest) CON FILTRO Asia+Londres.
    adrig2 15m = +0.72R 29ops — excelente resultado. La hipotesis es que el patron
    de desplazamiento+FVG, al igual que todos los patrones OB, mejora con filtro de sesion.
    Aplicamos el mismo filtro h<13 que mejoro ob_trend -> ob_asia (+1.13R en Asia)."""
    h = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)
    if h >= 13:
        return None
    return det_adrig2(d)


def det_ob_trend_r3(d):
    """ob_trend CON OBJETIVO 3R (en vez de 2R). Los datos muestran que ob_plus_asia
    fixed=+1.30R y que el trail NO mejora el fixed (trail=+0.14R vs fixed=+1.30R para ob_plus_asia).
    Eso significa que los OB buenos ALCANZAN el objetivo y el precio CONTINUA mas alla.
    Esta variante prueba si ampliar el objetivo a 3R captura mas ganancia en los mejores setups.
    Solo en Asia (h<7) donde el edge es maximo. Mismo detector que ob_trend pero objetivo 3R."""
    h = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)
    if h >= 7:
        return None
    base = det_ob(d)
    if base is None:
        return None
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    j = len(d) - 1; cl = d["cierre"].to_numpy()[j]
    if np.isnan(ema[j]):
        return None
    if base["dir"] == "largo" and cl > ema[j]:
        D = base["entry"] - base["stop"]
        base["target"] = base["entry"] + 3.0 * D    # 3R en vez de 2R
        return base
    if base["dir"] == "corto" and cl < ema[j]:
        D = base["stop"] - base["entry"]
        base["target"] = base["entry"] - 3.0 * D
        return base
    return None


def det_ob_asia_close(d):
    """OB EN EL CIERRE DE TOKIO (03-07h UTC) — dato de sub_sesion revela que tokyo_close
    (+0.68R) es la mejor sub-sesion, mejor que tokyo_open (+0.04R) y london_open (+0.02R).
    Intuicion: el final de Asia es cuando los institucionales asiaticos cierran posiciones
    y el mercado hace sus movimientos mas limpios antes de que llegue Londres.
    Refinamiento de ob_asia (00-07h +0.34R) para capturar solo la ventana con mayor edge."""
    h = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)
    if not (3 <= h < 7):    # solo tokyo_close (03-07h UTC)
        return None
    return det_ob_trend(d)


def _prev_ny_alcista(d):
    """Calcula si la sesion NY anterior (13-21h UTC del dia anterior) fue alcista.
    Retorna True si cierre NY > apertura NY, False si fue bajista, None si sin datos."""
    ts_pd = pd.to_datetime(d["t"].to_numpy(), unit="ms", utc=True)
    j = len(d) - 1
    hoy = ts_pd[j].date()
    import datetime
    ayer = hoy - datetime.timedelta(days=1)
    mask_ny = (ts_pd.date == ayer) & (ts_pd.hour >= 13) & (ts_pd.hour < 21)
    idx_ny = np.where(mask_ny)[0]
    if len(idx_ny) < 4:
        return None
    cl = d["cierre"].to_numpy()
    return cl[idx_ny[-1]] > cl[idx_ny[0]]


def det_breaker_prev_ny(d):
    """BREAKER CON FILTRO SESION ANTERIOR NY ALCISTA — el hallazgo mas potente del analisis.
    breaker general = +0.014R (casi muerto), PERO cuando la sesion NY anterior fue alcista
    sube a +1.52R win=94% (n=18). El contexto macro (lo que hizo NY) cambia completamente
    el edge del breaker. El 'breaker block' institucional necesita momentum de la sesion
    anterior para confirmar que la estructura esta respaldada por flujo real."""
    prev = _prev_ny_alcista(d)
    if prev is None or not prev:   # necesitamos NY alcista del dia anterior
        return None
    return det_breaker(d)


def det_ob_plus_asia_r3(d):
    """LA REINA CON OBJETIVO 3R: ob_plus_asia (+1.295R, #1 en la arena) con objetivo ampliado.
    La logica: ob_plus_asia fixed=+1.295R vs trail=+0.414R → el precio alcanza 2R y CONTINUA.
    ob_trend_r3 (tambien Asia, objetivo 3R) = +1.085R confirma que el mercado en Asia durante
    tendencia supera los 2R con frecuencia. Esta variante prueba si ob_plus (con sus filtros
    adicionales: EMA200 + sin climax de volumen) captura aun mas ganancia con 3R."""
    h = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)
    if h >= 7:
        return None
    base = det_ob_plus(d)
    if base is None:
        return None
    D = abs(base["entry"] - base["stop"])
    if base["dir"] == "largo":
        base["target"] = base["entry"] + 3.0 * D
    else:
        base["target"] = base["entry"] - 3.0 * D
    return base


def det_silver_bullet(d):
    """ICT SILVER BULLET — FVG en las 3 ventanas killzone donde el institucional es mas activo.
    Ventanas UTC: 08-09h (London open = 3AM EST), 15-16h (NYSE 10AM), 19-20h (NYSE 2PM).
    Busca FVG que se formo dentro de la ventana y al que el precio regresa para retestear.
    EMA200 alineada para no ir en contra del sesgo macro. Una de las estrategias ICT
    mas estudiadas y documentadas: el institucional deja huellas en esas horas concretas."""
    h = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)
    if h not in (8, 15, 19):   # solo dentro de las 3 killzones de 1h
        return None
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    cl = d["cierre"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    j = len(cl) - 1
    if j < 215 or np.isnan(ema[j]):
        return None
    for i in range(max(2, j - 8), j - 1):
        # FVG alcista: hi[i-1] < lo[i+1] → zona de imbalance que el precio regresa a tocar
        if lo[i + 1] > hi[i - 1]:
            fvg_bot = hi[i - 1]; fvg_top = lo[i + 1]
            if cl[j] > ema[j] and fvg_bot <= cl[j] <= fvg_top:
                return _setup("largo", cl[j], fvg_bot * 0.999, 2.0)
        # FVG bajista: lo[i-1] > hi[i+1]
        if hi[i + 1] < lo[i - 1]:
            fvg_bot = hi[i + 1]; fvg_top = lo[i - 1]
            if cl[j] < ema[j] and fvg_bot <= cl[j] <= fvg_top:
                return _setup("corto", cl[j], fvg_top * 1.001, 2.0)
    return None


def det_judas_swing_ob(d):
    """JUDAS SWING + OB: London open (07-10 UTC) barre el rango asiatico (trampa institucional)
    y luego forma un Order Block en la direccion CONTRARIA. El 'Judas Swing' es el patron ICT
    mas documentado: Londres engana al retail (breakout falso sobre Asia H/L) antes de moverse
    en la direccion real con los institucionales. Entrada en el primer OB de reversal."""
    h = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)
    if not (7 <= h < 10):
        return None
    ts_pd = pd.to_datetime(d["t"].to_numpy(), unit="ms", utc=True)
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    j = len(cl) - 1
    if j < 215 or np.isnan(ema[j]):
        return None
    # Rango asiatico (0-7 UTC del mismo dia)
    mask_asia = ts_pd.hour < 7
    idx_asia = np.where(mask_asia)[0]
    if len(idx_asia) < 3:
        return None
    asia_hi = hi[idx_asia].max(); asia_lo = lo[idx_asia].min()
    # Velas de Londres ya transcurridas (07-10 UTC)
    mask_lon = (ts_pd.hour >= 7) & (ts_pd.hour < 10)
    idx_lon = np.where(mask_lon)[0]
    if len(idx_lon) < 2:
        return None
    swept_hi = hi[idx_lon].max() > asia_hi   # Londres barrio el maximo asiatico → trampa bajista
    swept_lo = lo[idx_lon].min() < asia_lo   # Londres barrio el minimo asiatico → trampa alcista
    if not swept_hi and not swept_lo:
        return None
    # Buscar OB de reversal en las ultimas velas (dentro de la ventana de Londres)
    if swept_hi and cl[j] < ema[j]:
        for i in range(max(0, j - 10), j - 1):
            if (hi[i] - lo[i]) / cl[i] < 0.0005: continue
            if cl[i] > op[i] and cl[i + 1] < lo[i] and lo[i] <= cl[j] <= hi[i]:
                return _setup("corto", cl[j], hi[i] * 1.001, 2.0)
    if swept_lo and cl[j] > ema[j]:
        for i in range(max(0, j - 10), j - 1):
            if (hi[i] - lo[i]) / cl[i] < 0.0005: continue
            if cl[i] < op[i] and cl[i + 1] > hi[i] and lo[i] <= cl[j] <= hi[i]:
                return _setup("largo", cl[j], lo[i] * 0.999, 2.0)
    return None


def det_ny_london_sweep(d):
    """NY SWEEP DEL RANGO LONDINENSE: NY open (13-15 UTC) barre el maximo/minimo de Londres
    y luego revierte con OB. Paralelo del Judas Swing en la transicion London → NY.
    Tesis: NY primero 'roba' la liquidez que Londres acumulo (stops por encima/debajo del rango
    de 7-13h) y luego continua en la direccion opuesta. EMA200 como filtro de sesgo macro."""
    h = int(pd.to_datetime(int(d["t"].iloc[-1]), unit="ms").hour)
    if not (13 <= h < 15):
        return None
    ts_pd = pd.to_datetime(d["t"].to_numpy(), unit="ms", utc=True)
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    cl = d["cierre"].to_numpy(); op = d["apertura"].to_numpy()
    ema = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    j = len(cl) - 1
    if j < 215 or np.isnan(ema[j]):
        return None
    # Rango londinense (7-13 UTC)
    mask_lon = (ts_pd.hour >= 7) & (ts_pd.hour < 13)
    idx_lon = np.where(mask_lon)[0]
    if len(idx_lon) < 4:
        return None
    lon_hi = hi[idx_lon].max(); lon_lo = lo[idx_lon].min()
    # Velas NY actuales (13-15 UTC)
    mask_ny = (ts_pd.hour >= 13) & (ts_pd.hour < 15)
    idx_ny = np.where(mask_ny)[0]
    if len(idx_ny) < 1:
        return None
    swept_lon_hi = hi[idx_ny].max() > lon_hi   # NY barrio el maximo de Londres → trampa alcista
    swept_lon_lo = lo[idx_ny].min() < lon_lo   # NY barrio el minimo de Londres → trampa bajista
    if not swept_lon_hi and not swept_lon_lo:
        return None
    # Buscar OB de reversal tras el sweep
    if swept_lon_hi and cl[j] < ema[j]:
        for i in range(max(0, j - 10), j - 1):
            if (hi[i] - lo[i]) / cl[i] < 0.0005: continue
            if cl[i] > op[i] and cl[i + 1] < lo[i] and lo[i] <= cl[j] <= hi[i]:
                return _setup("corto", cl[j], hi[i] * 1.001, 2.0)
    if swept_lon_lo and cl[j] > ema[j]:
        for i in range(max(0, j - 10), j - 1):
            if (hi[i] - lo[i]) / cl[i] < 0.0005: continue
            if cl[i] < op[i] and cl[i + 1] > hi[i] and lo[i] <= cl[j] <= hi[i]:
                return _setup("largo", cl[j], lo[i] * 0.999, 2.0)
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


def sub_sesion_de(ts):
    """Sub-sesión más granular: aperturas/cierres específicos de bolsas reales.
    Cripto opera 24/7 pero los movimientos siguen los horarios de las bolsas tradicionales:
      - Tokyo (TYO):   abre 0:00 UTC, cierra 6:00 UTC (Nikkei, JPY)
      - London (LON):  abre 8:00 UTC, cierra 16:30 UTC (FTSE, EUR)
      - NYSE/NASDAQ:   abre 13:30 UTC, cierra 20:00 UTC (S&P500, Nasdaq)
    Las aperturas son los momentos de mayor volatilidad e institucional."""
    h = pd.to_datetime(ts, unit="ms").hour
    m = pd.to_datetime(ts, unit="ms").minute
    if 0 <= h < 2:   return "tokyo_open"      # Nikkei, JPY activo
    if 2 <= h < 5:   return "tokyo_mid"       # Sesion tokio plena
    if 5 <= h < 7:   return "tokyo_close"     # Cierre Tokio, bancos japoneses cierran posiciones
    if 7 <= h < 9:   return "london_open"     # Frankfurt 8:00, London 8:00 — maxima volatilidad EU
    if 9 <= h < 13:  return "london_mid"      # Sesion Londres plena
    if h == 13 or (h == 14 and m < 30):
        return "ny_preopen"                    # CME/NASDAQ pre-market activo (hasta 13:30 NYSE open)
    if h == 14 and m >= 30 or (h == 15 and m < 30):
        return "nyse_open"                     # Primeros 60min de NYSE (9:30-10:30 ET) — mayor vol
    if 15 <= h < 20: return "ny_mid"          # Sesion NY plena
    if 20 <= h < 21: return "ny_close"        # 4PM ET cierre NYSE, square de posiciones
    return "overnight"                         # Baja liquidez, solo cripto-nativo


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
    if estr == "atr_break":
        return det_atr_break(cerr)
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
    if estr == "ob_plus_asia":
        return det_ob_plus_asia(cerr)
    if estr == "elliott_ob":
        return det_elliott_ob(cerr)
    if estr == "rsi_ob":
        return det_rsi_ob(cerr)
    if estr == "rsidiv_ob":
        return det_rsidiv_ob(cerr)
    if estr == "choch":
        return det_choch(cerr)
    if estr == "ema_pullback":
        return det_ema_pullback(cerr)
    if estr == "fvg_ob_asia":
        return det_fvg_ob_asia(cerr)
    if estr == "adrig2_asia":
        return det_adrig2_asia(cerr)
    if estr == "ob_trend_r3":
        return det_ob_trend_r3(cerr)
    if estr == "ob_plus_asia_r3":
        return det_ob_plus_asia_r3(cerr)
    if estr == "ob_asia_close":
        return det_ob_asia_close(cerr)
    if estr == "breaker_prev_ny":
        return det_breaker_prev_ny(cerr)
    if estr == "silver_bullet":
        return det_silver_bullet(cerr)
    if estr == "judas_swing_ob":
        return det_judas_swing_ob(cerr)
    if estr == "ny_london_sweep":
        return det_ny_london_sweep(cerr)
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
    if len(cerr) >= 200:                                       # EMA200 en el TF de la señal
        try:
            ema200_tf = float(cerr["cierre"].ewm(span=200, adjust=False).mean().iloc[-1])
            out["ema200_dist_%"] = round((px / ema200_tf - 1) * 100, 2)
            out["sobre_ema200"] = px > ema200_tf
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
        # RESPALDO sobre_ema200: si el TF de la señal no tenía 200 velas, usar EMA200 del 1h
        # (referencia de tendencia robusta y SIEMPRE disponible) -> contexto en vivo completo.
        if "sobre_ema200" not in out and len(c1h) >= 200:
            ema200_1h = float(c1h.ewm(span=200, adjust=False).mean().iloc[-1])
            out["sobre_ema200"] = px > ema200_1h
            out["ema200_dist_%"] = round((px / ema200_1h - 1) * 100, 2)
    except Exception:
        pass
    # MICRO-CONTEXTO 5m (INFORMATIVO, no señal): el 5m como timing fino de entrada. NO genera trades
    # (eso era ruido), pero registra si el micro-momentum CONFIRMA o CONTRADICE la entrada del 15m.
    # El laboratorio cruzará "m5_trend vs dirección" para ver si las entradas 5m-alineadas ganan más.
    try:
        if ("5m_data", coin) in cache:
            d5 = cache[("5m_data", coin)]
        else:
            d5 = velas_cached(ex, coin, "5m", cache)
            cache[("5m_data", coin)] = d5
        c5 = d5["cierre"]
        if len(c5) >= 21:
            e9 = float(c5.ewm(span=9, adjust=False).mean().iloc[-1])
            e21 = float(c5.ewm(span=21, adjust=False).mean().iloc[-1])
            out["m5_trend"] = "up" if e9 > e21 else "down"      # micro-tendencia 5m
            out["m5_rsi"] = round(float(_rsi(c5)[-1]), 1)        # micro momentum
            vm5 = float(d5["volumen"].tail(20).mean())
            out["m5_vol_rel"] = round(float(d5["volumen"].iloc[-1] / vm5), 2) if vm5 else None
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
    # RANGO DE LONDRES (07-13 UTC) — espejo del asiatico, clave para london_fade y sensei
    try:
        hoy_utc2 = pd.Timestamp.now("UTC").date()
        ts_arr3 = cerr["t"].to_numpy()
        ts_pd3 = pd.to_datetime(ts_arr3, unit="ms", utc=True)
        mask_lon = (ts_pd3.date == hoy_utc2) & (ts_pd3.hour >= 7) & (ts_pd3.hour < 13)
        idx_lon = np.where(mask_lon)[0]
        if len(idx_lon) >= 3:
            out["london_hi"] = round(float(cerr["maximo"].to_numpy()[idx_lon].max()), 4)
            out["london_lo"] = round(float(cerr["minimo"].to_numpy()[idx_lon].min()), 4)
            out["london_rango_%"] = round((out["london_hi"] - out["london_lo"]) / out["london_lo"] * 100, 2)
            cl_lon = cerr["cierre"].to_numpy()
            out["london_dir"] = "alcista" if cl_lon[idx_lon[-1]] > cl_lon[idx_lon[0]] else "bajista"
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
    # RESPALDO ses_ant desde 1h: en TF altos (4h) una sesión tiene 1-2 velas y el bloque de
    # arriba no llega a >=3. Recalcular con los datos de 1h (granularidad suficiente SIEMPRE)
    # garantiza contexto completo en TODA temporalidad. Aditivo: solo si faltaba.
    if "ses_ant_dir" not in out:
        try:
            d1h_ctx = cache.get(("1h_data", coin))
            if d1h_ctx is None:
                d1h_ctx = velas_cached(ex, coin, "1h", cache)
                cache[("1h_data", coin)] = d1h_ctx
            recent = d1h_ctx.tail(30)                         # últimas ~30h cubren la sesión previa
            h_sig = int(pd.to_datetime(int(cerr["t"].iloc[-1]), unit="ms").hour)
            if 7 <= h_sig < 13:   rng, nom = (0, 7),  "asia"
            elif 13 <= h_sig < 21: rng, nom = (7, 13), "londres"
            else:                  rng, nom = (13, 21), "ny"
            tt = recent["t"].to_numpy(); cl1 = recent["cierre"].to_numpy()
            hh = pd.to_datetime(tt, unit="ms").hour
            idx2 = np.where((hh >= rng[0]) & (hh < rng[1]))[0]
            if len(idx2) >= 2:
                bloque = idx2[idx2 >= idx2.max() - 12]        # la ocurrencia más reciente de esa sesión
                o_ = cl1[bloque[0]]; c_ = cl1[bloque[-1]]
                hi1 = recent["maximo"].to_numpy()[bloque].max(); lo1 = recent["minimo"].to_numpy()[bloque].min()
                out["ses_ant"] = nom
                out["ses_ant_dir"] = "alcista" if c_ > o_ else "bajista"
                out["ses_ant_rango_%"] = round((hi1 - lo1) / o_ * 100, 2)
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
                    elif estr == "smc_asia":
                        s, L = det_smc_asia(ex, coin, tf, vcache)
                        if L is None:
                            L = velas_cached(ex, coin, tf, vcache)
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
                        for p in range(max(0, len(closed) - 200), len(closed)):
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
                             fecha=str(pd.to_datetime(ts_p, unit="ms")),
                             sesion=sesion_de(ts_p), sub_sesion=sub_sesion_de(ts_p))
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
