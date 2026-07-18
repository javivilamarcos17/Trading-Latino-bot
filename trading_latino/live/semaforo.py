"""
SEMÁFORO DIARIO — qué operar HOY y con qué riesgo. Integra todas las reglas validadas:
  1. CICLO (Plan BTC): días desde ATH / caída — enciende la familia Asia y planbtc.
  2. FINDE OFF: sáb/dom −0.33R en vivo (3/3 monedas) → intradía apagado.
  3. ROLLING 21d por estrategia (kill-switch de decay): exp vivo reciente <0 → banquillo.
  4. DIRECCIÓN rolling 7d (calibrado: reacciona en 2-4 dias vs 2 semanas, mismos cambios de bando).
Solo datos EN VIVO (costes reales correctos) + diario Binance para el ciclo.

Uso:  python -m trading_latino.live.semaforo
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import json, glob, os, time
import datetime as dt
import numpy as np, pandas as pd, ccxt

REG = "data_store/paper_arena"
# universo desplegable: ganadoras vivas + columna alta + planbtc
UNIVERSO = ["fvg_ob_asia", "ob_asia_close", "ob_asia_close_L", "fvg_ob", "ob_regime_asia",
            "trend_rider", "trend_rider_f", "atr_break_trend", "atr_break", "scalp_break", "planbtc"]

def ops_vivas():
    rows = []
    for f in glob.glob(os.path.join(REG, "*.json")):
        b = os.path.basename(f)
        if b.startswith("_"): continue
        e = "_".join(b[:-5].split("_")[:-2])
        try: ops = json.load(open(f))
        except Exception: continue
        for o in ops:
            if o.get("status") == "cerrada" and isinstance(o.get("exits"), dict) and o.get("ts"):
                rows.append((e, o["ts"], o["exits"]["fixed"], o.get("dir")))
    return pd.DataFrame(rows, columns=["estr", "ts", "r", "dir"])

def ciclo_hoy():
    ex = ccxt.binance()
    o = ex.fetch_ohlcv("BTC/USDT", "1d", limit=1000)
    d = pd.DataFrame(o, columns=["t","o","h","l","c","v"])
    hi = d["h"].to_numpy(); cl = d["c"].to_numpy()
    ath = hi.max(); i_ath = int(np.argmax(hi))
    dias = len(d) - 1 - i_ath
    dd = (ath - cl[-1]) / ath
    return dias, dd * 100, (dias > 200 or dd > 0.50), (dias > 250 and dd > 0.40)

def main():
    hoy = dt.datetime.now(dt.timezone.utc)
    ahora_ms = time.time() * 1000
    df = ops_vivas()
    dias_ath, dd_pct, ciclo_or, ciclo_strict = ciclo_hoy()
    finde = hoy.weekday() >= 5

    print(f"🚦 SEMÁFORO — {hoy:%Y-%m-%d %H:%M} UTC")
    print(f"CICLO BTC: {dias_ath}d desde ATH · caída {dd_pct:.0f}%  → "
          f"{'PROFUNDO (Asia/planbtc habilitadas)' if ciclo_or else 'NO profundo (Asia OFF)'}"
          f"{' [estricto: SÍ]' if ciclo_strict else ' [estricto: NO]'}")
    print(f"FINDE: {'SÍ → intradía OFF hoy' if finde else 'no (laborable)'}")

    # dirección rolling 30d (ganadoras)
    v30 = df[(df.ts >= ahora_ms - 7 * 86400_000) & (df.estr.isin(UNIVERSO))]
    gl = v30[v30.dir == "largo"]["r"]; gc = v30[v30.dir == "corto"]["r"]
    if len(gl) >= 40 and len(gc) >= 40:
        print(f"DIRECCIÓN 7d: largos {gl.mean():+.2f}R (n={len(gl)}) · cortos {gc.mean():+.2f}R (n={len(gc)})"
              f" → sesgo {'LARGO' if gl.mean() > gc.mean() else 'CORTO'}")

    print(f"\n{'estrategia':<17}{'exp14d':>9}{'n':>5}   estado")
    for e in UNIVERSO:
        s = df[(df.estr == e) & (df.ts >= ahora_ms - 14 * 86400_000)]
        n = len(s); exp = s.r.mean() if n else None
        # gates
        if e == "planbtc":
            estado = "🟢 EN GUARDIA (arma de ciclo, 1%)" if ciclo_or else "⚪ ciclo no profundo"
        elif n < 10:
            estado = "⚪ sin muestra 14d (banquillo)"
        elif exp is None or exp <= 0:
            estado = "🔴 BANQUILLO (kill-switch: exp14d<=0)"
        else:
            req_ciclo = e in ("fvg_ob_asia", "ob_asia_close", "ob_asia_close_L", "fvg_ob", "ob_regime_asia")
            if req_ciclo and not ciclo_or:
                estado = "🟠 OFF (fuera de ciclo profundo)"
            elif finde:
                estado = "🟠 OFF HOY (finde)"
            else:
                estado = "🟢 ON (riesgo 0.25%)"
        ex_s = f"{exp:+.2f}R" if exp is not None and n else "—"
        print(f"{e:<17}{ex_s:>9}{n:>5}   {estado}")
    print("\nReglas: ciclo>200d|dd>50% · finde OFF · kill-switch exp14d<=0 (14d calibrado) · tope 2/día/estrategia · tope clúster Asia 3/día")

if __name__ == "__main__":
    main()
