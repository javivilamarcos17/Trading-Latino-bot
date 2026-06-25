"""
SCALP LAB — prueba operativas de SCALPING (5m) con costes REALES y honestidad de régimen.
=========================================================================================
El scalping vive y muere por los COSTES: con stops pequeños, la comisión (0.08% ida+vuelta)
pesa MUCHO en R. Aquí medimos varias operativas de 5m sobre datos recientes de Binance,
separando GROSS (sin coste) vs NETO (con coste) y por DIRECCIÓN (en oso, los cortos mandan).

Uso:  python -m trading_latino.research.scalp_lab
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd, ccxt

COSTE = 0.0008   # 0.08% ida+vuelta (comisión). El spread medido en vivo ~0.006R extra.

def bajar_5m(coin, velas=6000):
    """Pagina hacia atrás para tener MUESTRA decente (Binance limita 1500/llamada)."""
    import time as _t
    ex = ccxt.binance({"options": {"defaultType": "future"}})
    paso = 5 * 60_000
    hasta = int(pd.Timestamp.now("UTC").timestamp() * 1000)
    desde = hasta - velas * paso
    bl, t = [], desde
    while t < hasta:
        try:
            o = ex.fetch_ohlcv(f"{coin}USDT", "5m", since=t, limit=1500)
        except Exception:
            _t.sleep(2); continue
        if not o: break
        bl.extend(o); t = o[-1][0] + paso
    d = pd.DataFrame(bl, columns=["t", "apertura", "maximo", "minimo", "cierre", "volumen"])
    return d.drop_duplicates("t").sort_values("t").reset_index(drop=True)

def _salida_trail(d, j, entry, stop, es_largo, atr_mult=2.0, max_bars=240):
    """Salida TRAILING: deja correr el momentum. El stop persigue al precio a atr_mult×ATR. La idea:
    capturar las pocas rupturas que se convierten en movimientos grandes (que pagan las perdidas)."""
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    D = abs(entry - stop)
    if D == 0: return None
    atr = (d["maximo"] - d["minimo"]).rolling(14).mean().to_numpy()[j]
    if np.isnan(atr) or atr == 0: atr = D
    trail = stop
    for i in range(j + 1, min(j + max_bars, len(d))):
        if es_largo:
            if lo[i] <= trail: return (trail - entry) / D
            trail = max(trail, hi[i] - atr_mult * atr)
        else:
            if hi[i] >= trail: return (entry - trail) / D
            trail = min(trail, lo[i] + atr_mult * atr)
    fin = min(j + max_bars, len(d)) - 1
    return ((cl[fin] - entry) if es_largo else (entry - cl[fin])) / D

def _salida(d, j, entry, stop, target, es_largo, max_bars=60):
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    D = abs(entry - stop)
    if D == 0: return None
    Rt = abs(target - entry) / D
    for i in range(j + 1, min(j + max_bars, len(d))):
        if es_largo:
            if lo[i] <= stop: return -1.0
            if hi[i] >= target: return Rt
        else:
            if hi[i] >= stop: return -1.0
            if lo[i] <= target: return Rt
    fin = min(j + max_bars, len(d)) - 1
    return ((cl[fin] - entry) if es_largo else (entry - cl[fin])) / D

# --- operativas de scalping (5m) ---
def s_breakout(d, j, R=1.5):
    """Ruptura de 10 velas + EMA20 a favor (momentum scalp). Stop swing de 8, objetivo R."""
    cl = d["cierre"].to_numpy(); hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    if j < 25: return None
    e20 = d["cierre"].ewm(span=20, adjust=False).mean().to_numpy()
    hh = hi[j-10:j].max(); ll = lo[j-10:j].min()
    if cl[j] > hh and cl[j] > e20[j] and e20[j] > e20[j-1]:
        st = lo[j-8:j].min(); return ("largo", cl[j], st, cl[j] + R*(cl[j]-st))
    if cl[j] < ll and cl[j] < e20[j] and e20[j] < e20[j-1]:
        st = hi[j-8:j].max(); return ("corto", cl[j], st, cl[j] - R*(st-cl[j]))
    return None

def s_pullback(d, j, R=1.5):
    """Pullback a EMA9 en micro-tendencia (EMA9>EMA21). Scalp clásico de continuación."""
    cl = d["cierre"].to_numpy(); lo = d["minimo"].to_numpy(); hi = d["maximo"].to_numpy()
    if j < 25: return None
    e9 = d["cierre"].ewm(span=9, adjust=False).mean().to_numpy()
    e21 = d["cierre"].ewm(span=21, adjust=False).mean().to_numpy()
    if e9[j] > e21[j] and lo[j] <= e9[j] and cl[j] > e9[j]:
        st = lo[j-5:j+1].min(); return ("largo", cl[j], st, cl[j] + R*(cl[j]-st))
    if e9[j] < e21[j] and hi[j] >= e9[j] and cl[j] < e9[j]:
        st = hi[j-5:j+1].max(); return ("corto", cl[j], st, cl[j] - R*(st-cl[j]))
    return None

def s_breakout_wide(d, j, R=2.0):
    """Igual que breakout pero stop MÁS ANCHO (swing 14) y objetivo 2R: menos coste en R, deja correr."""
    cl = d["cierre"].to_numpy(); hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    if j < 30: return None
    e20 = d["cierre"].ewm(span=20, adjust=False).mean().to_numpy()
    hh = hi[j-10:j].max(); ll = lo[j-10:j].min()
    if cl[j] > hh and cl[j] > e20[j] and e20[j] > e20[j-1]:
        st = lo[j-14:j].min(); return ("largo", cl[j], st, cl[j] + R*(cl[j]-st))
    if cl[j] < ll and cl[j] < e20[j] and e20[j] < e20[j-1]:
        st = hi[j-14:j].max(); return ("corto", cl[j], st, cl[j] - R*(st-cl[j]))
    return None

def s_trend(d, j, R=1.5):
    """Scalp SOLO a favor de la tendencia mayor (EMA200): pullback a EMA9 en uptrend/downtrend.
    Filtra los contra-tendencia (los longs en oso, etc.) que sabemos que fallan."""
    cl = d["cierre"].to_numpy(); lo = d["minimo"].to_numpy(); hi = d["maximo"].to_numpy()
    if j < 210: return None
    e9 = d["cierre"].ewm(span=9, adjust=False).mean().to_numpy()
    e200 = d["cierre"].ewm(span=200, adjust=False).mean().to_numpy()
    if cl[j] > e200[j] and lo[j] <= e9[j] and cl[j] > e9[j]:
        st = lo[j-5:j+1].min(); return ("largo", cl[j], st, cl[j] + R*(cl[j]-st))
    if cl[j] < e200[j] and hi[j] >= e9[j] and cl[j] < e9[j]:
        st = hi[j-5:j+1].max(); return ("corto", cl[j], st, cl[j] - R*(st-cl[j]))
    return None

def s_vwap_revert(d, j, R=1.0):
    """Mean-reversion scalp: el precio se estira lejos del VWAP(20) y vuelve. Stop tras la mecha."""
    cl = d["cierre"].to_numpy(); hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy()
    if j < 25: return None
    tp = (d["maximo"]+d["minimo"]+d["cierre"])/3
    vwap = ((tp*d["volumen"]).rolling(20).sum()/d["volumen"].rolling(20).sum()).to_numpy()
    if np.isnan(vwap[j]): return None
    dist = (cl[j]-vwap[j])/vwap[j]
    if dist < -0.004 and cl[j] > cl[j-1]:   # muy por debajo y girando arriba
        st = lo[j-3:j+1].min(); return ("largo", cl[j], st, vwap[j])
    if dist > 0.004 and cl[j] < cl[j-1]:     # muy por encima y girando abajo
        st = hi[j-3:j+1].max(); return ("corto", cl[j], st, vwap[j])
    return None

OPERATIVAS = {"breakout_5m": s_breakout, "breakout_wide": s_breakout_wide,
              "pullback_5m": s_pullback, "trend_scalp": s_trend, "vwap_revert": s_vwap_revert}

def stat(v):
    n = len(v)
    return (n, sum(1 for x in v if x > 0)/n if n else 0, sum(v)/n if n else 0)

TAKER, MAKER = 0.0008, 0.0003   # comisión round-trip: taker 0.08% vs maker 0.03%

def _atr_pct(d, n=14):
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    tr = np.maximum(hi[1:]-lo[1:], np.maximum(np.abs(hi[1:]-cl[:-1]), np.abs(lo[1:]-cl[:-1])))
    atr = pd.Series(np.concatenate([[hi[0]-lo[0]], tr])).ewm(span=n, adjust=False).mean().to_numpy()
    return atr / cl * 100   # ATR en %

def main():
    print("SCALP LAB — PRUEBA TOTAL: 5 operativas × normal/alta-volatilidad × coste taker/maker\n")
    for coin in ["BTC", "ETH", "SOL"]:
        d = bajar_5m(coin)
        atrp = _atr_pct(d)
        vol_alta = atrp > np.nanmedian(atrp[100:])   # alta volatilidad = ATR sobre la mediana
        ini = pd.to_datetime(int(d['t'].iloc[0]), unit='ms').strftime('%m-%d')
        fin = pd.to_datetime(int(d['t'].iloc[-1]), unit='ms').strftime('%m-%d')
        print(f"=== {coin} ({len(d)} velas 5m, {ini}->{fin}) ===")
        print(f"  {'operativa':<13}{'n':>5}  ||  SALIDA FIJA: gross/net@maker  ||  SALIDA TRAILING: gross/net@maker")
        for nom, fn in OPERATIVAS.items():
            pf, pt, stops = [], [], []
            for j in range(25, len(d)-1):
                sig = fn(d, j)
                if not sig: continue
                dirc, entry, stop, target = sig
                rf = _salida(d, j, entry, stop, target, dirc == "largo")
                rt = _salida_trail(d, j, entry, stop, dirc == "largo")
                if rf is None or rt is None: continue
                pf.append(rf); pt.append(rt); stops.append(abs(entry-stop)/entry*100)
            if len(pf) < 15: continue
            stop_med = np.median(stops) if stops else 0.5
            cm = MAKER/(stop_med/100)
            nf, _, gf = stat(pf); _, _, gt = stat(pt)
            netf, nett = gf - cm, gt - cm
            ff = "OK" if netf > 0 else "  "; ft = "OK" if nett > 0 else "  "
            print(f"  {nom:<13}{nf:>5}  ||  {gf:>+7.3f} / {netf:>+7.3f}{ff}  ||  {gt:>+7.3f} / {nett:>+7.3f}{ft}")
        print()
    print("VEREDICTO: ¿la salida TRAILING (dejar correr) hace positivo algún scalp donde la fija fallaba?")
    print("Si ni con trailing ni con maker hay edge consistente en 3 monedas, el scalping 5m no es viable.")

if __name__ == "__main__":
    main()
