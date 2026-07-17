"""
PLAN BTC CORE — esqueleto MECANIZABLE del sistema de Plan BTC (Carlos), testeado a años vista.
=============================================================================================
No podemos replicar su discreción (Elliott subjetivo); SÍ su esqueleto objetivo:
  GATILLO:  barrido de liquidez (mecha limpia el mín/máx de 20 días) + RECLAIM (cierre de vuelta).
  FILTRO 1: contrarian F&G REAL (alternative.me desde 2018): miedo extremo -> prohibido short;
            codicia extrema -> prohibido long.  [regla literal del sistema]
  FILTRO 2: CICLO (su métrica estrella, nunca probada por nosotros): días desde ATH y % de caída.
            <200 días desde ATH en bajista = "tramo de engaño" -> sin compras de fondo.
  STOP: tras la mecha del barrido. SALIDAS: 2R fijo (comparable) y runner 4R (su estilo asimétrico).
Datos: BTC/ETH/SOL DIARIO spot Binance (2018->hoy: cubre 2 ciclos completos). Neto de costes.

Uso:  python -m trading_latino.research.planbtc_core
"""
from __future__ import annotations
import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd, ccxt, requests

COSTE = 0.002   # 0.1% por lado spot/derivado retail + margen

def bajar_diario(coin):
    ex = ccxt.binance()
    bl, t = [], int(pd.Timestamp("2018-02-01", tz="UTC").timestamp()*1000)
    while True:
        try: o = ex.fetch_ohlcv(f"{coin}/USDT", "1d", since=t, limit=1000)
        except Exception: time.sleep(3); continue
        if not o: break
        bl.extend(o); nt = o[-1][0] + 86400_000
        if nt <= t or len(o) < 1000: break
        t = nt
    d = pd.DataFrame(bl, columns=["t","apertura","maximo","minimo","cierre","volumen"])
    return d.drop_duplicates("t").sort_values("t").reset_index(drop=True)

def bajar_fng():
    """Historial COMPLETO de Fear&Greed (alternative.me, desde feb-2018)."""
    r = requests.get("https://api.alternative.me/fng/?limit=0&format=json", timeout=30).json()
    rows = [(int(x["timestamp"])*1000, int(x["value"])) for x in r["data"]]
    f = pd.DataFrame(rows, columns=["t","fng"]).sort_values("t").reset_index(drop=True)
    return f

def salida(d, i, entry, stop, target, es_largo, max_d=60):
    hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
    D = abs(entry-stop)
    if D == 0: return None
    Rt = abs(target-entry)/D
    for k in range(i+1, min(i+max_d, len(d))):
        if es_largo:
            if lo[k] <= stop: return -1.0-COSTE/ (D/entry)
            if hi[k] >= target: return Rt-COSTE/(D/entry)
        else:
            if hi[k] >= stop: return -1.0-COSTE/(D/entry)
            if lo[k] <= target: return Rt-COSTE/(D/entry)
    fin = min(i+max_d, len(d))-1
    return ((cl[fin]-entry) if es_largo else (entry-cl[fin]))/D - COSTE/(D/entry)

def stat(v):
    n=len(v); return n,(sum(1 for x in v if x>0)/n if n else 0),(sum(v)/n if n else 0)

def main():
    print("PLAN BTC CORE — esqueleto mecanizable, DIARIO 2018-2026 (2 ciclos), neto\n")
    fng = bajar_fng()
    print(f"F&G histórico: {len(fng):,} días ({pd.to_datetime(fng['t'].iloc[0],unit='ms'):%Y-%m} -> hoy)")
    for coin in ["BTC","ETH","SOL"]:
        d = bajar_diario(coin)
        if len(d) < 400: print(f"{coin}: pocos datos"); continue
        # F&G alineado por día (el de AYER: sin lookahead)
        farr = pd.merge_asof(d[["t"]], fng, on="t", direction="backward")["fng"].shift(1).to_numpy()
        hi = d["maximo"].to_numpy(); lo = d["minimo"].to_numpy(); cl = d["cierre"].to_numpy()
        # ciclo: ATH rolling y días desde ATH (sin lookahead)
        ath = np.maximum.accumulate(hi)
        dias_ath = np.zeros(len(d)); last = 0
        for i in range(len(d)):
            if hi[i] >= ath[i]: last = i
            dias_ath[i] = i - last
        dd_ath = (ath - cl)/ath
        N = 20
        variantes = {
            "A_barrido_solo": [], "B_+FG_contrarian": [], "C_+FG_+ciclo": [], "C_runner4R": [],
        }
        for i in range(N+5, len(d)-1):
            ll = lo[i-N:i].min(); hh = hi[i-N:i].max()
            fg = farr[i]
            # LONG: mecha limpia el mínimo de 20d y CIERRA de vuelta encima (reclaim)
            if lo[i] < ll and cl[i] > ll:
                entry = cl[i]; stop = lo[i]*0.995
                if entry > stop:
                    tgt2 = entry + 2*(entry-stop); tgt4 = entry + 4*(entry-stop)
                    r2 = salida(d,i,entry,stop,tgt2,True); r4 = salida(d,i,entry,stop,tgt4,True)
                    if r2 is not None:
                        variantes["A_barrido_solo"].append(r2)
                        if not (fg==fg and fg>75):                       # no long en euforia
                            variantes["B_+FG_contrarian"].append(r2)
                            # ciclo: comprar fondo solo si >200d desde ATH o caída >50% (su regla)
                            if dias_ath[i] > 200 or dd_ath[i] > 0.50:
                                variantes["C_+FG_+ciclo"].append(r2)
                                if r4 is not None: variantes["C_runner4R"].append(r4)
            # SHORT: mecha limpia el máximo de 20d y CIERRA de vuelta debajo
            if hi[i] > hh and cl[i] < hh:
                entry = cl[i]; stop = hi[i]*1.005
                if stop > entry:
                    tgt2 = entry - 2*(stop-entry)
                    r2 = salida(d,i,entry,stop,tgt2,False)
                    if r2 is not None:
                        variantes["A_barrido_solo"].append(r2)
                        if not (fg==fg and fg<25):                       # no short en miedo extremo
                            variantes["B_+FG_contrarian"].append(r2)
                            if dias_ath[i] < 100:                        # shorts solo cerca de ATH (distribución)
                                variantes["C_+FG_+ciclo"].append(r2)
        print(f"\n=== {coin} (diario, {len(d):,} días) ===")
        for nom, v in variantes.items():
            n,w,ex = stat(v)
            if n: print(f"  {nom:<18} n={n:<4} win={w*100:.0f}%  exp={ex:+.3f}R")
    print("\nLEER: A=gatillo desnudo (ya sabíamos que solo, es débil). B=+su filtro contrarian.")
    print("C=+su métrica de ciclo (días desde ATH). Si C >> A, la INTELIGENCIA del sistema está en los filtros.")

if __name__ == "__main__":
    main()
