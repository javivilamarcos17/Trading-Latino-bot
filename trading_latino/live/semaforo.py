"""
SEMÁFORO DIARIO — qué operar HOY y con qué riesgo. Integra todas las reglas validadas:
  1. CICLO (Plan BTC): días desde ATH / caída — enciende la familia Asia y planbtc.
  2. FINDE OFF solo cluster Asia (sab/dom -0.33R en vivo); la tendencia 1D opera en finde por NEUTRALIDAD (auditor: dif no significativa, p=0.55).
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
            "trend_rider", "trend_rider_f", "atr_break_trend", "atr_break", "scalp_break", "planbtc",
            "turtle_ciclo", "ichimoku"]

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
    mom7 = bool(cl[-1] > cl[-8])          # momentum 7d ahora
    mom7_hace10 = bool(cl[-11] > cl[-18]) # momentum 7d hace 10 dias
    return dias, dd * 100, (dias > 200 or dd > 0.50), (dias > 250 and dd > 0.40), mom7, mom7_hace10


def carry_hoy():
    """4a luz: motor CARRY. Funding medio anualizado de la cesta (muestra de 6 monedas liquidas).
    >5% APR = ON (toro/lateral pagando el alquiler); <0 = OFF (oso, funding negativo)."""
    ex = ccxt.binance({"options": {"defaultType": "future"}})
    aprs = []
    for c in ["BTC", "ETH", "XRP", "LINK", "DOGE", "AVAX"]:
        try:
            fr = ex.fetch_funding_rate(f"{c}/USDT:USDT").get("fundingRate")
            if fr is not None: aprs.append(fr * 3 * 365 * 100)
        except Exception:
            pass
    if not aprs: return None, "sin datos", None
    m = sum(aprs) / len(aprs)
    estado = "ON (cesta pagando)" if m > 5 else ("neutral (marginal)" if m > 0 else "OFF (funding negativo = oso)")
    # dial de PERSISTENCIA de funding (recalificado en auditoria r6): el funding es autocorrelado,
    # percentil alto del funding PROPIO del venue predice funding alto proximo (el lead-lag
    # cross-venue existe pero no añade nada sobre esto). Cesta en Binance -> percentil de Binance.
    pct = None
    try:
        import time as _t
        since = int((_t.time() - 180 * 86400) * 1000)
        hist = []
        s = since
        for _ in range(3):
            h = ex.fetch_funding_rate_history("BTC/USDT:USDT", since=s, limit=500)
            if not h: break
            hist += [x["fundingRate"] for x in h]
            s = h[-1]["timestamp"] + 1
        if len(hist) > 100:
            actual = ex.fetch_funding_rate("BTC/USDT:USDT").get("fundingRate")
            if actual is not None:
                pct = 100 * sum(1 for x in hist if x < actual) / len(hist)
    except Exception:
        pass
    # media 7d del funding y dias desde el ultimo cruce negativo->positivo (para el dial de fase)
    f7_apr = None; dias_cruce = None
    if len(hist) > 42:
        import numpy as _np
        arr = _np.array(hist, dtype=float)
        m7 = _np.convolve(arr, _np.ones(21) / 21, mode="valid")  # 21 periodos de 8h = 7d
        f7_apr = m7[-1] * 3 * 365 * 100
        neg = _np.where(m7 <= 0)[0]
        if len(neg) and neg[-1] < len(m7) - 1:
            dias_cruce = (len(m7) - 1 - neg[-1]) / 3.0
    return m, estado, pct, f7_apr, dias_cruce

def main():
    hoy = dt.datetime.now(dt.timezone.utc)
    ahora_ms = time.time() * 1000
    df = ops_vivas()
    dias_ath, dd_pct, ciclo_or, ciclo_strict, mom7, mom7_hace10 = ciclo_hoy()
    finde = hoy.weekday() >= 5

    print(f"🚦 SEMÁFORO — {hoy:%Y-%m-%d %H:%M} UTC")
    print(f"CICLO BTC: {dias_ath}d desde ATH · caída {dd_pct:.0f}%  → "
          f"{'PROFUNDO (Asia/planbtc habilitadas)' if ciclo_or else 'NO profundo (Asia OFF)'}"
          f"{' [estricto: SÍ]' if ciclo_strict else ' [estricto: NO]'}")
    apr, carry_est, pct_lider, f7_apr, dias_cruce = carry_hoy()
    if apr is not None:
        print(f"CARRY (4a luz): funding cesta {apr:+.1f}% APR -> {carry_est}")
        if pct_lider is not None:
            dial = "FAVORABLE para abrir/rebalancear" if pct_lider >= 75 else ("neutro" if pct_lider >= 25 else "desfavorable (esperar)")
            print(f"  dial persistencia: funding del venue en percentil {pct_lider:.0f} de sus 180d -> {dial}")
    # DIAL DE FASE (contexto historico, SIN regla de disparo — auditoria r6): triple convergencia
    if f7_apr is not None:
        c1 = "SÍ" if ciclo_or else "no"
        c2 = f"+{f7_apr:.1f}% APR" + (f" (cruzó a + hace {dias_cruce:.0f}d)" if dias_cruce is not None and f7_apr > 0 else "")
        c3 = "LARGO" if mom7 else "corto"
        n_conv = sum([ciclo_or, f7_apr > 0, mom7])
        print(f"DIAL DE FASE (contexto): ciclo maduro {c1} · funding7d {c2} · momentum7d {c3}"
              f" -> convergencia {n_conv}/3" + (" ⚡" if n_conv == 3 else ""))
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
            elif finde and req_ciclo:
                estado = "🟠 OFF HOY (finde: solo aplica al cluster Asia)"
            else:
                estado = "🟢 ON (riesgo 0.25%)"
        ex_s = f"{exp:+.2f}R" if exp is not None and n else "—"
        print(f"{e:<17}{ex_s:>9}{n:>5}   {estado}")
    print("\nReglas: ciclo>200d|dd>50% · finde OFF · kill-switch exp14d<=0 (14d calibrado) · tope 2/día/estrategia · tope clúster Asia 3/día")

if __name__ == "__main__":
    main()
