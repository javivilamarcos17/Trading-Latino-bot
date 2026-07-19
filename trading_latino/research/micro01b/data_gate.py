# -*- coding: utf-8 -*-
"""DATA GATE de MICRO-01B — 7 checks sobre el OI descargado. Imprime DATA_GATE = PASS/FAIL.
No ejecuta el experimento; solo audita el dato antes de pedir RUN_APPROVED."""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd, hashlib, json
from pathlib import Path
OI = Path(r"c:/Users/javiv/Desktop/Trading Jaime Merino/data_store/oi_5m")
MICRO = Path(r"c:/Users/javiv/Desktop/Trading Jaime Merino/data_store/micro01b")
SYMS = {"BTC": "BTCUSDT_oi_5m.parquet", "ETH": "ETHUSDT_oi_5m.parquet", "SOL": "SOLUSDT_oi_5m.parquet"}
PRICE = {"BTC": "BTCUSDT_price_5m_fut.parquet", "ETH": "ETHUSDT_price_5m_fut.parquet", "SOL": "SOLUSDT_price_5m_fut.parquet"}
BIN = 5 * 60 * 1000  # 5min en ms
fails = []

print("=" * 68)
print("DATA GATE — MICRO-01B (OI 5min + precio 5m fut, Binance perp USDT, data.binance.vision)")
print("=" * 68)

# [0] ATOMICIDAD: los 6 datasets finales deben existir (descargas COMPLETAS y consolidadas)
faltan = [str(OI/v) for v in SYMS.values() if not (OI/v).exists()] + [str(MICRO/v) for v in PRICE.values() if not (MICRO/v).exists()]
if faltan:
    print(f"\nDATASETS INCOMPLETOS (descarga no finalizada): faltan {[Path(f).name for f in faltan]}")
    print("DATA_GATE = ABORTADO — esperar a que AMBAS descargas cierren y consoliden. No validar parquets parciales.")
    sys.exit(1)
print("[0] Atomicidad: los 6 datasets (3 OI + 3 precio) existen y están consolidados. OK")

# [UT] INGESTION UNIT TEST reutilizable (fail-fast: evita que un cambio de pandas/pyarrow reintroduzca el bug de 1970)
_ms = pd.to_datetime(pd.Series(["2024-01-01 00:00:00"])).values.astype("datetime64[ms]").astype("int64")[0]
assert _ms == 1704067200000, f"INGESTION UNIT TEST FALLA: {_ms} != 1704067200000 (bug de resolución datetime)"
assert pd.to_datetime(1704067200000, unit="ms").year == 2024
print("[UT] ingestion unit test (1704067200000 ↔ 2024-01-01 00:00:00 UTC): OK")

anomalias = []  # visible, para evaluación humana antes de RUN_APPROVED (no bloquea auto)

def invariantes(t, nombre, anio_min):
    """5 invariantes temporales genéricos (FAIL duro) + cobertura/gaps material (anomalía visible)."""
    tt = pd.Series(np.asarray(t, dtype="int64"))
    y0 = pd.to_datetime(tt.min(), unit="ms").year; y1 = pd.to_datetime(tt.max(), unit="ms").year
    dif = tt.diff().dropna()
    dups = int((dif == 0).sum()); nomono = int((dif < 0).sum())
    cad5 = (dif == 300000).mean() * 100 if len(dif) else 0
    gaps = int((dif > 300000).sum()); maxgap_h = (dif.max()/3600000) if len(dif) else 0; p95_h = (dif.quantile(.95)/3600000) if len(dif) else 0
    off = int((tt % 300000 != 0).sum())
    esperadas = (int(tt.max()) - int(tt.min())) // 300000 + 1
    cov = 100 * tt.nunique() / esperadas
    # 1 RANGE · 2 MONOTONÍA+DUP · 4 UTC/BOUNDARY · cadencia como FAIL duro
    if y0 < anio_min or y0 < 2018 or y1 > 2027: fails.append(f"{nombre}: rango absurdo {y0}-{y1} (esperado ≥{anio_min})")
    if nomono > 0: fails.append(f"{nombre}: {nomono} timestamps NO monótonos")
    if dups > 0: fails.append(f"{nombre}: {dups} timestamps DUPLICADOS")
    if off > 0: fails.append(f"{nombre}: {off} timestamps FUERA de frontera 5m (UTC)")
    if cad5 < 90: fails.append(f"{nombre}: cadencia 5m solo {cad5:.0f}% (<90%)")
    # cobertura y GAP MATERIAL: la cadencia≥90% NO basta; un hueco grande queda VISIBLE
    if cov < 95: anomalias.append(f"{nombre}: cobertura {cov:.1f}% (revisar)")
    if maxgap_h > 24: anomalias.append(f"{nombre}: GAP MATERIAL de {maxgap_h:.1f}h (>1 día) — evaluar origen antes de aprobar")
    print(f"  {nombre}: {y0}-{y1} · cobertura={cov:.1f}% ({tt.nunique():,}/{esperadas:,}) · cadencia5m={cad5:.1f}% · "
          f"gaps>5m={gaps} (max {maxgap_h:.1f}h, p95 {p95_h:.2f}h) · dups={dups} · off-bnd={off}")

# [1] SOURCE MANIFEST + [7] QUALITY
print("\n[1+7] MANIFEST + CALIDAD por moneda:")
data = {}
for coin, fn in SYMS.items():
    f = OI / fn
    raw = pd.read_parquet(f)
    invariantes(raw["t"].to_numpy(), f"{coin} OI ", 2021 if coin == "BTC" else 2022)   # invariantes sobre RAW
    d = raw.drop_duplicates("t").sort_values("t").reset_index(drop=True)
    data[coin] = d
    t0, t1 = int(d.t.min()), int(d.t.max())
    esperadas = (t1 - t0) // BIN + 1
    dif = d.t.diff().dropna()
    gaps = int((dif > BIN).sum()); dups = int((dif == 0).sum())
    max_gap_h = dif.max() / 3600000 if len(dif) else 0
    cov = 100 * len(d) / esperadas
    ceros = int((d.sum_open_interest <= 0).sum())
    print(f"  {coin}: n={len(d):,} · {pd.to_datetime(t0,unit='ms'):%Y-%m-%d}→{pd.to_datetime(t1,unit='ms'):%Y-%m-%d} · "
          f"cobertura={cov:.1f}% · gaps={gaps} (max {max_gap_h:.1f}h) · dups={dups} · OI<=0: {ceros}")
    if cov < 90: fails.append(f"{coin} cobertura {cov:.0f}%<90%")
    if ceros > 0: fails.append(f"{coin} tiene {ceros} OI<=0")

# [1b] INVARIANTES precio 5m (mismos 5 invariantes que OI)
print("\n[1b] INVARIANTES precio 5m fut:")
price_data = {}
for coin, fn in PRICE.items():
    raw = pd.read_parquet(MICRO / fn)
    invariantes(raw["t"].to_numpy(), f"{coin} PRICE", 2021 if coin == "BTC" else 2022)
    price_data[coin] = raw.drop_duplicates("t").sort_values("t").reset_index(drop=True)

# [2] OI VARIABLE
print("\n[2] VARIABLE OI PRIMARIA = Δlog(sum_open_interest) (cantidad, NO nocional):")
for coin, d in data.items():
    dlog = np.log(d.sum_open_interest.replace(0, np.nan)).diff()
    print(f"  {coin}: Δlog(OI) std={dlog.std():.4f} · p1={dlog.quantile(.01):+.4f} · p99={dlog.quantile(.99):+.4f} (sano si finito y sin saltos absurdos)")

# [3] TIMESTAMP CAUSALITY (semántica)
print("\n[3] TIMESTAMP: create_time = instante del snapshot (frontera de 5min). available_at=t.")
print("    merge: OI(t) con vela de precio cerrada en t. forward outcome empieza en t+1. Latencia: sensibilidad same-boundary vs lag-1 en MICRO-01B.")

# [4] BALANCED PANEL
print("\n[4] PANEL BALANCEADO:")
if len(data) == 3:
    comun0 = max(int(d.t.min()) for d in data.values())
    print(f"  periodo COMÚN (primary) = desde {pd.to_datetime(comun0,unit='ms'):%Y-%m-%d} (BTC+ETH+SOL). BTC pre-{pd.to_datetime(comun0,unit='ms'):%Y} = temporal extension separada.")
else:
    fails.append("no están las 3 monedas")

# [5] EXTRA COLUMNS FIREWALL
cols = set()
for d in data.values(): cols |= set(d.columns)
extra = cols - {"t", "sum_open_interest", "sum_open_interest_value"}
print(f"\n[5] FIREWALL columnas extra: descargado solo {sorted(cols)}. Ratios/taker NO presentes: {'OK' if not (extra) else extra}")

# [6] RESAMPLING unit test (OI = STATE)
print("\n[6] RESAMPLING (OI state, no flow) — unit test 5m→15m:")
if "BTC" in data:
    d = data["BTC"].head(6).copy()  # 6 velas de 5m = 2 de 15m
    # nivel 15m = ultimo snapshot; ΔOI 15m = fin - inicio del intervalo
    d["grp"] = (d.t // (15*60*1000))
    lvl = d.groupby("grp").sum_open_interest.last()
    dOI = d.groupby("grp").sum_open_interest.agg(lambda s: s.iloc[-1] - s.iloc[0])
    suma = d.groupby("grp").sum_open_interest.sum()
    ok = (lvl.iloc[0] == d.sum_open_interest.iloc[2]) and (suma.iloc[0] != lvl.iloc[0])
    print(f"    nivel(last)={lvl.iloc[0]:.1f} vs sum(erróneo)={suma.iloc[0]:.1f} → distintos: {'OK (no se suma OI)' if ok else 'REVISAR'}")

# [8] GAP-DROP % al resamplear (no forward-fill: intervalos sin endpoints validos se descartan)
print("\n[8] % intervalos DESCARTADOS por gaps (no forward-fill) por TF:")
for coin, d in data.items():
    linea = f"  {coin}: "
    for tf_ms, nom in [(15*60*1000, "15m"), (60*60*1000, "1h")]:
        g = d.copy(); g["grp"] = g.t // tf_ms
        # un intervalo es valido si tiene al menos el primer y ultimo bin de 5m esperados (aprox: >=2 puntos y span ~tf)
        val = g.groupby("grp").agg(n=("t", "size"), span=("t", lambda s: s.max()-s.min()))
        esperado_bins = tf_ms // BIN
        drop = (val["n"] < max(2, esperado_bins*0.5)).mean() * 100
        linea += f"{nom}={drop:.1f}%  "
    print(linea)

# [9] AUTOCORRELACION de Δlog(OI) (salud pipeline; control de tendencia lenta/leakage)
print("\n[9] Autocorrelación Δlog(OI) (alta a lag grande = riesgo tendencia lenta/leakage):")
for coin, d in data.items():
    dlog = np.log(d.sum_open_interest.replace(0, np.nan)).diff().dropna()
    ac1 = dlog.autocorr(1); ac100 = dlog.autocorr(100)
    print(f"  {coin}: ac(lag1)={ac1:+.3f}  ac(lag100)={ac100:+.3f}  {'(sano: bajo a lag grande)' if abs(ac100)<0.1 else '⚠ revisar'}")
print("  (el control negativo completo OI-alineado vs OI-desplazado se corre DENTRO de MICRO-01B)")

# [10] SOURCE FILE CONTINUITY: archivos fuente no descargados (fail) vs gaps reales de Binance
print("\n[10] Continuidad de archivos fuente (distinguir gap real vs archivo no descargado):")
import re
TASKS = Path(r"C:/Users/javiv/AppData/Local/Temp/claude/c--Users-javiv-Desktop-Trading-Jaime-Merino/aeb0635f-276e-4db5-9caa-7a5b56d6d6e1/tasks")
for log, etq in [("bp57ahb2v.output", "OI"), ("bv3w55h9c.output", "precio")]:
    p = TASKS / log
    if not p.exists(): print(f"  {etq}: log no encontrado"); continue
    for m in re.finditer(r"GUARDADO (\w+):.*?\(fail=(\d+)\)", p.read_text(errors="replace")):
        sym, fail = m.group(1), int(m.group(2))
        nota = "OK (0 archivos perdidos)" if fail == 0 else f"⚠ {fail} archivos fuente NO descargados → posible origen de gaps"
        print(f"  {etq} {sym}: {nota}")
        if fail > 0: anomalias.append(f"{etq} {sym}: {fail} archivos fuente no descargados")

if anomalias:
    print("\n⚠ ANOMALÍAS MATERIALES (visibles, evaluar antes de RUN_APPROVED — NO auto-bloquean):")
    for a in anomalias: print(f"    - {a}")

print("\n" + "=" * 68)
if not fails:
    # DATA FREEZE: hashes de los 6 datasets FINALES (tras consolidación) -> reproducibilidad
    freeze = {}
    for c, v in SYMS.items(): freeze[v] = hashlib.sha256((OI / v).read_bytes()).hexdigest()[:16]
    for c, v in PRICE.items(): freeze[v] = hashlib.sha256((MICRO / v).read_bytes()).hexdigest()[:16]
    MICRO.mkdir(exist_ok=True)
    json.dump(freeze, open(MICRO / "DATA_FREEZE.json", "w"), indent=2)
    (MICRO / "DATA_GATE_PASS.flag").write_text("PASS 2026-07-19")
    print("DATA_FREEZE.json (hashes de los 6 datasets) + DATA_GATE_PASS.flag generados")
    print("  hashes:", freeze)
print(f"DATA_GATE = {'PASS' if not fails else 'FAIL'}" + (f"  motivos: {fails}" if fails else "  → falta solo RUN_APPROVED (crear RUN_APPROVED.flag) para ejecutar MICRO-01B"))
print("=" * 68)
