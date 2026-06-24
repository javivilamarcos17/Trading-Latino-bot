"""
ESTUDIO POR CONDICIONES — ¿qué estrategia funciona CUÁNDO y CÓMO?
=================================================================
La arena guarda ~17 dimensiones de contexto por operación (sesión, régimen,
funding, OI, Fear&Greed, EMA200, MFE/MAE...) pero ningún tool las analizaba.
Este script lee TODAS las ops cerradas y descompone el resultado por cada
condición, surfaceando dónde se CONCENTRA el edge y dónde hay FUGAS (= filtros
candidatos). Convierte datos crudos en "esta estrategia gana en ESTA condición".

GUARDA-RAÍLES ANTI-AUTOENGAÑO (críticos — leer):
  - Solo se muestran slices con n >= MIN_N. Pocos datos = ruido, no edge.
  - Son HIPÓTESIS, no verdades. Al cortar por muchas condiciones aparecen
    "edges" por puro azar (data-mining). Validar en Binance antes de fiarse.
  - La CONSISTENCIA (misma condición gana en varias monedas/estrategias) es
    mucho más fiable que un slice aislado espectacular.
  - Métrica = salida 'fixed' (2R), para comparar todo en igualdad de condiciones.

Uso:
  python -m trading_latino.research.estudio                 # resumen global
  python -m trading_latino.research.estudio ob_trend        # foco en una estrategia
  python -m trading_latino.research.estudio --pockets       # ranking de bolsas de edge
  python -m trading_latino.research.estudio --leaks         # ranking de fugas (filtros)
  python -m trading_latino.research.estudio --exits         # estudio de salidas (MFE/MAE)
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import json
from pathlib import Path
from collections import defaultdict

REG = Path(__file__).resolve().parents[2] / "data_store" / "paper_arena"
MIN_N = 20            # mínimo de ops para que un slice cuente (anti-ruido)
MIN_N_POCKET = 25     # más estricto para el ranking de bolsas/fugas

# ------------------------------------------------------------------ bucketización de cada dimensión
def _b_funding(v):
    if v is None: return None
    if v > 0.00005: return "fund+alto"
    if v > 0: return "fund+"
    if v < -0.00005: return "fund-alto"
    if v < 0: return "fund-"
    return "fund~0"

def _b_doi(v):
    if v is None: return None
    if v > 0.3: return "OI_sube"
    if v < -0.3: return "OI_baja"
    return "OI_plano"

def _b_fng(v):
    if v is None: return None
    if v < 20: return "fng<20"
    if v < 25: return "fng20-25"
    if v < 30: return "fng25-30"
    if v < 50: return "fng30-50"
    return "fng50+"

def _b_pos(v):
    if v is None: return None
    if v < 0.33: return "rango_bajo"
    if v < 0.66: return "rango_medio"
    return "rango_alto"

def _b_adx(v):
    if v is None: return None
    if v < 20: return "adx<20"
    if v < 25: return "adx20-25"
    return "adx25+"

# (etiqueta_dimension, funcion_que_extrae_el_bucket_de_la_op)
DIMENSIONES = [
    ("direccion",   lambda o: o.get("dir")),
    ("sesion",      lambda o: o.get("sesion")),
    ("sub_sesion",  lambda o: o.get("sub_sesion")),
    ("regimen",     lambda o: o.get("regimen")),
    ("adx_dir",     lambda o: o.get("adx_dir")),
    ("adx_nivel",   lambda o: _b_adx(o.get("adx"))),
    ("sobre_ema200",lambda o: None if o.get("sobre_ema200") is None else ("sobre_ema200" if o.get("sobre_ema200") else "bajo_ema200")),
    ("funding",     lambda o: _b_funding(o.get("funding"))),
    ("oi_delta",    lambda o: _b_doi(o.get("d_oi_%"))),
    ("fear_greed",  lambda o: _b_fng(o.get("fng"))),
    ("pos_rango",   lambda o: _b_pos(o.get("pos_rango"))),
    ("ses_ant_dir", lambda o: o.get("ses_ant_dir")),
    ("m5_trend",    lambda o: o.get("m5_trend")),                 # micro-tendencia 5m (informativo)
    ("m5_alineado", lambda o: None if o.get("m5_trend") is None else
                    ("5m_a_favor" if (o.get("m5_trend") == "up") == (o.get("dir") == "largo") else "5m_en_contra")),
    ("coin",        lambda o: o.get("coin")),
    ("tf",          lambda o: o.get("tf")),
]

# ------------------------------------------------------------------ carga
def cargar():
    """Lista de ops cerradas con su contexto y pnl 'fixed'. Añade campo 'pnl_fixed'."""
    ops = []
    for f in sorted(REG.glob("*.json")):
        if f.stem.startswith("_"):
            continue
        try:
            arr = json.loads(f.read_text())
        except Exception:
            continue
        for o in arr:
            if o.get("status") != "cerrada" or not isinstance(o.get("exits"), dict):
                continue
            if "fixed" not in o["exits"]:
                continue
            o["pnl_fixed"] = o["exits"]["fixed"]
            ops.append(o)
    return ops

def _stat(vals):
    n = len(vals)
    if not n: return 0, 0.0, 0.0
    return n, sum(1 for v in vals if v > 0) / n, sum(vals) / n

# ------------------------------------------------------------------ vistas
def desglose_estrategia(ops, estr):
    """Para UNA estrategia, exp por cada dimensión y bucket."""
    sub = [o for o in ops if o.get("estr") == estr]
    n, win, exp = _stat([o["pnl_fixed"] for o in sub])
    print(f"\n=== {estr} — global: n={n} win={win*100:.0f}% exp={exp:+.3f}R ===")
    if n < 5:
        print("  (muy pocos datos)"); return
    for dim, fn in DIMENSIONES:
        grupos = defaultdict(list)
        for o in sub:
            b = fn(o)
            if b is not None:
                grupos[b].append(o["pnl_fixed"])
        filas = [(b, *_stat(v)) for b, v in grupos.items() if len(v) >= 5]
        if len(filas) < 2:   # solo interesa si la dimensión DISCRIMINA (≥2 buckets)
            continue
        filas.sort(key=lambda x: x[3], reverse=True)
        print(f"  · {dim:<13}: " + "  ".join(f"{b}={ex:+.2f}R(n{n})" for b, n, w, ex in filas))

def ranking_pockets(ops, leaks=False):
    """Escanea TODOS los (estrategia × dimensión × bucket) y rankea por exp."""
    res = []
    estrs = sorted({o.get("estr") for o in ops})
    for estr in estrs:
        sub = [o for o in ops if o.get("estr") == estr]
        base_n, _, base_exp = _stat([o["pnl_fixed"] for o in sub])
        if base_n < MIN_N:
            continue
        for dim, fn in DIMENSIONES:
            grupos = defaultdict(list)
            for o in sub:
                b = fn(o)
                if b is not None:
                    grupos[b].append(o["pnl_fixed"])
            for b, v in grupos.items():
                n, w, ex = _stat(v)
                if n >= MIN_N_POCKET:
                    res.append((ex, estr, dim, b, n, w, base_exp))
    res.sort(key=lambda x: x[0], reverse=not leaks)
    titulo = "FUGAS (condiciones donde la estrategia PIERDE → filtros candidatos)" if leaks else \
             "BOLSAS DE EDGE (condiciones donde la estrategia GANA más)"
    print(f"\n=== {titulo} — top 25, n>={MIN_N_POCKET} ===")
    print(f"  {'exp':>7} {'(vs base)':>10}  {'n':>4}  {'win':>4}  estrategia / condición")
    for ex, estr, dim, b, n, w, base in res[:25]:
        delta = ex - base
        print(f"  {ex:>+6.2f}R {delta:>+9.2f}  {n:>4}  {w*100:>3.0f}%  {estr} | {dim}={b}")
    print("  ⚠️ HIPÓTESIS, no verdades: validar en Binance. Fíjate en lo que se REPITE entre estrategias.")

def mapa_router(ops):
    """ROUTER: para cada momento del mercado (sesión × régimen), QUÉ estrategia usar.
    Esta es la tesis profesional: no una estrategia, sino la MEJOR para cada condición."""
    print(f"\n=== MAPA ROUTER — la MEJOR estrategia para cada momento del mercado (n>={MIN_N}) ===")
    # Eje 1: sesión. Eje 2: régimen (tendencia/rango). Celda: top estrategia por exp.
    sesiones = ["asia", "londres", "ny"]
    regimenes = ["tendencia", "rango"]
    for ses in sesiones:
        print(f"\n  ── Sesión {ses.upper()} ──")
        for reg in regimenes:
            cand = defaultdict(list)
            for o in ops:
                if o.get("sesion") == ses and o.get("regimen") == reg:
                    cand[o["estr"]].append(o["pnl_fixed"])
            filas = []
            for e, v in cand.items():
                n, w, ex = _stat(v)
                if n >= MIN_N:
                    filas.append((ex, w, n, e))
            filas.sort(reverse=True)
            if not filas:
                print(f"     {reg:<10}: (sin estrategias con n>={MIN_N})"); continue
            top = filas[:3]
            txt = "  ".join(f"{e}={ex:+.2f}R(n{n},{w*100:.0f}%)" for ex, w, n, e in top)
            print(f"     {reg:<10}: {txt}")
    print("\n  ⚠️ Todo régimen actual = bajista/miedo. El router REAL necesita datos de toro/euforia")
    print("     (de ahí el multi-año de Binance). Esto es el esqueleto; se rellena al validar.")

def _curva(cerr, risk_pct):
    """Devuelve (retorno_total_%, max_drawdown_%) de una curva de capital compuesta."""
    cap = pico = 1.0; maxdd = 0.0
    for o in cerr:
        cap *= (1 + (risk_pct / 100.0) * o["pnl_fixed"])
        pico = max(pico, cap)
        maxdd = max(maxdd, (pico - cap) / pico)
    return (cap - 1) * 100, maxdd * 100

def riesgo_ruina(ops, risk_pct=1.0):
    """SEGURIDAD: ¿puede un mal momento reventar el trabajo de muchos días?
    Compara la curva de capital de TODAS las estrategias vs SOLO LAS CURADAS (las
    ganadoras), demostrando que la curación recorta el drawdown. Mide también la
    CONCENTRACIÓN (posiciones simultáneas correlacionadas = riesgo real oculto)."""
    import datetime as dt
    from collections import Counter
    cerr = sorted([o for o in ops if o.get("ts")], key=lambda o: o["ts"])
    if not cerr:
        print("  (sin ops)"); return
    # Tier "curado": estrategias con exp>0.25 y n>=MIN_N (la cima validada)
    by_estr = defaultdict(list)
    for o in cerr: by_estr[o.get("estr")].append(o["pnl_fixed"])
    curadas = {e for e, v in by_estr.items() if len(v) >= MIN_N and _stat(v)[2] > 0.25}
    cur = [o for o in cerr if o.get("estr") in curadas]

    print(f"\n=== RIESGO DE RUINA — curva de capital a {risk_pct:.0f}% de riesgo por operación ===")
    rt_all, dd_all = _curva(cerr, risk_pct)
    rt_cur, dd_cur = _curva(cur, risk_pct) if cur else (0, 0)
    print(f"  TODAS ({len({o.get('estr') for o in cerr})} estr, {len(cerr):,} ops): retorno {rt_all:+.0f}%  ·  PEOR caída -{dd_all:.1f}%")
    print(f"  CURADAS ({len(curadas)} estr, {len(cur):,} ops):  retorno {rt_cur:+.0f}%  ·  PEOR caída -{dd_cur:.1f}%")
    if dd_all > 0:
        print(f"  → Curar recorta la caída de -{dd_all:.0f}% a -{dd_cur:.0f}%. ESTO es 'no tener todas activas'.")
    # Concentración
    por_ts = defaultdict(lambda: Counter())
    for o in cerr: por_ts[o["ts"]][o.get("dir")] += 1
    peor = max(por_ts.items(), key=lambda kv: sum(kv[1].values()))
    n_simult = sum(peor[1].values())
    cuando = dt.datetime.fromtimestamp(peor[0]/1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
    print(f"  Concentración máx: {n_simult} posiciones a la vez ({dict(peor[1])}) el {cuando} UTC")
    print(f"  Regla de oro: riesgo/trade × posiciones simultáneas correlacionadas = tu riesgo REAL.")
    print(f"  Con {n_simult} a la vez y {risk_pct:.0f}%/trade, un giro brusco arriesga ~{n_simult*risk_pct:.0f}% DE GOLPE.")
    print(f"  → Solución: límite duro de posiciones correlacionadas + activar solo las del momento (router).")

def estudio_salidas(ops):
    """Usa MFE/MAE para estudiar CÓMO salir: ¿el target 2R deja dinero en la mesa o es too lejos?"""
    print(f"\n=== ESTUDIO DE SALIDAS (MFE = cuánto corre el precio a favor; MAE = cuánto sufre antes) ===")
    print(f"  {'estrategia':<18}{'n':>5}{'MFE_medio':>11}{'MAE_medio':>11}  lectura")
    por = defaultdict(lambda: {"mfe": [], "mae": []})
    for o in ops:
        if o.get("mfe_R") is not None and o.get("mae_R") is not None:
            por[o["estr"]]["mfe"].append(o["mfe_R"]); por[o["estr"]]["mae"].append(o["mae_R"])
    filas = []
    for estr, d in por.items():
        if len(d["mfe"]) < MIN_N: continue
        mfe = sum(d["mfe"]) / len(d["mfe"]); mae = sum(d["mae"]) / len(d["mae"])
        filas.append((mfe, estr, len(d["mfe"]), mae))
    filas.sort(reverse=True)
    for mfe, estr, n, mae in filas:
        if mfe > 2.3:    lect = "el precio corre >2.3R → el target 2R deja dinero (probar trail/3R)"
        elif mfe < 1.6:  lect = "rara vez llega a 2R → target 2R quizá too lejos (probar 1.25R/BE)"
        else:            lect = "MFE cerca de 2R → el target 2R está bien calibrado"
        print(f"  {estr:<18}{n:>5}{mfe:>+10.2f}R{mae:>+10.2f}R  {lect}")

def main():
    args = sys.argv[1:]
    ops = cargar()
    if not ops:
        print("No hay ops cerradas con salidas. ¿La arena ha corrido?"); return
    print(f"ESTUDIO POR CONDICIONES — {len(ops):,} ops cerradas, "
          f"{len({o.get('estr') for o in ops})} estrategias. Métrica: salida 'fixed' (2R).")

    if "--pockets" in args:
        ranking_pockets(ops, leaks=False)
    elif "--leaks" in args:
        ranking_pockets(ops, leaks=True)
    elif "--exits" in args:
        estudio_salidas(ops)
    elif "--mapa" in args:
        mapa_router(ops)
    elif "--riesgo" in args:
        riesgo_ruina(ops)
    elif args and not args[0].startswith("--"):
        desglose_estrategia(ops, args[0])
    else:
        # resumen por defecto: las 3 vistas clave, compactas
        ranking_pockets(ops, leaks=False)
        ranking_pockets(ops, leaks=True)
        estudio_salidas(ops)

if __name__ == "__main__":
    main()
