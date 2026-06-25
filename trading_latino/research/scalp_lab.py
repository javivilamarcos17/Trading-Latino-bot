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
    n = len(v);
    return (n, sum(1 for x in v if x > 0)/n if n else 0, sum(v)/n if n else 0)

def main():
    print("SCALP LAB — operativas de 5m, costes REALES, honesto con el régimen (oso = cortos mandan)\n")
    for coin in ["BTC", "ETH", "SOL"]:
        d = bajar_5m(coin)
        ini = pd.to_datetime(int(d['t'].iloc[0]), unit='ms').strftime('%m-%d')
        fin = pd.to_datetime(int(d['t'].iloc[-1]), unit='ms').strftime('%m-%d')
        print(f"=== {coin} ({len(d)} velas 5m, {ini}->{fin}) ===")
        for nom, fn in OPERATIVAS.items():
            res = {"largo": [], "corto": []}
            stops = []
            for j in range(25, len(d)-1):
                sig = fn(d, j)
                if not sig: continue
                dirc, entry, stop, target = sig
                r = _salida(d, j, entry, stop, target, dirc == "largo")
                if r is None: continue
                res[dirc].append(r)
                stops.append(abs(entry-stop)/entry*100)
            allr = res["largo"] + res["corto"]
            if len(allr) < 10:
                print(f"  {nom:<13} pocas señales ({len(allr)})"); continue
            n, w, gross = stat(allr)
            # coste en R = comision / distancia_stop_media
            stop_med = np.median(stops) if stops else 0.5
            coste_R = COSTE / (stop_med/100)
            neto = gross - coste_R
            nl, wl, gl = stat(res["largo"]); ns, ws, gs = stat(res["corto"])
            print(f"  {nom:<13} n={n:<4} win={w*100:.0f}%  GROSS={gross:+.3f}R  coste={coste_R:.3f}R  NETO={neto:+.3f}R  "
                  f"[largo {gl:+.2f}({nl}) | corto {gs:+.2f}({ns})]")
        print()
    print("CLAVE: en scalping el coste (comision/stop) es enorme. Si NETO<0, la operativa no sobrevive a costes.")

if __name__ == "__main__":
    main()
