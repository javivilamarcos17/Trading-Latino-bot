"""ANALISIS PROFUNDO de la arena (solo lectura). Descompone las operaciones EN VIVO por los factores
INDEPENDIENTES que capturamos, para ver qué condiciones aportan ventaja real (no más osciladores
redundantes). Sirve para DISEÑAR estrategias compuestas con base en datos.

Uso: python -m trading_latino.live._analisis
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

REG = Path(__file__).resolve().parents[2] / "data_store" / "paper_arena"
MIN = 15   # n mínimo para dar un veredicto (debajo = poca muestra)


def cargar():
    ops = []
    for f in REG.glob("*.json"):
        if f.stem.startswith("_"):
            continue
        estr = "_".join(f.stem.split("_")[:-2])
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue
        if isinstance(data, list):
            for o in data:
                if (isinstance(o, dict) and o.get("regimen") is not None
                        and o.get("status") == "cerrada" and isinstance(o.get("exits"), dict)):
                    o["_estr"] = estr
                    ops.append(o)
    return ops


def stat(v):
    n = len(v)
    if not n:
        return 0, 0.0, 0.0
    return n, sum(1 for x in v if x > 0) / n, sum(v) / n


def linea(etq, v):
    n, w, e = stat(v)
    flag = "" if n >= MIN else "  (poca muestra)"
    print(f"    {etq:<26} n={n:>4} win={w * 100:>3.0f}% exp={e:>+.2f}R{flag}")


def R(o):
    return o["exits"]["fixed"]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ops = cargar()
    print(f"ANALISIS PROFUNDO — {len(ops)} operaciones en vivo (cerradas, salida fija en R)")
    print("AVISO: ~1 dia de datos, un solo tramo de mercado. Esto es DIRECCIONAL, no concluyente.\n")

    longs = [o for o in ops if o["dir"] == "largo"]
    shorts = [o for o in ops if o["dir"] == "corto"]
    print(f"Direccion: largos n={len(longs)} exp={stat([R(o) for o in longs])[2]:+.2f}R | "
          f"cortos n={len(shorts)} exp={stat([R(o) for o in shorts])[2]:+.2f}R\n")

    # 1) UBICACION premium/descuento (tesis smart money: comprar barato, vender caro)
    print("1) UBICACION en el rango (smart money: largos en DESCUENTO, cortos en PREMIUM):")
    for et, dirc in [("LARGOS", "largo"), ("CORTOS", "corto")]:
        sub = [o for o in ops if o["dir"] == dirc and o.get("pos_rango") is not None]
        print(f"  {et}:")
        linea("descuento (<0.40)", [R(o) for o in sub if o["pos_rango"] < 0.40])
        linea("medio (0.40-0.60)", [R(o) for o in sub if 0.40 <= o["pos_rango"] <= 0.60])
        linea("premium (>0.60)", [R(o) for o in sub if o["pos_rango"] > 0.60])

    # 2) FUNDING (posicionamiento) — contrario suele pagar
    print("\n2) FUNDING al entrar (posicionamiento de la masa):")
    fn = [o for o in ops if o.get("funding") is not None]
    linea("funding + (largos pagan)", [R(o) for o in fn if o["funding"] > 0])
    linea("funding - (cortos pagan)", [R(o) for o in fn if o["funding"] < 0])

    # 3) SESION (mercado USA, etc.)
    print("\n3) SESION:")
    ses = defaultdict(list)
    for o in ops:
        ses[o.get("sesion", "?")].append(R(o))
    for s in ["asia", "londres", "ny_open", "ny", "cierre"]:
        if s in ses:
            linea(s, ses[s])

    # 4) SENTIMIENTO (Fear & Greed)
    print("\n4) FEAR & GREED (sentimiento):")
    fg = [o for o in ops if o.get("fng") is not None]
    linea("miedo (<30)", [R(o) for o in fg if o["fng"] < 30])
    linea("neutral (30-55)", [R(o) for o in fg if 30 <= o["fng"] <= 55])
    linea("codicia (>55)", [R(o) for o in fg if o["fng"] > 55])

    # 5) REGIMEN x DIRECCION
    print("\n5) REGIMEN (ADX) x DIRECCION:")
    for reg in ["tendencia", "rango"]:
        for dirc in ["largo", "corto"]:
            linea(f"{reg} + {dirc}", [R(o) for o in ops if o.get("regimen") == reg and o["dir"] == dirc])

    # 6) VOLUMEN RELATIVO en la señal
    print("\n6) VOLUMEN relativo en la vela de señal:")
    vr = [o for o in ops if o.get("vol_rel") is not None]
    linea("vol bajo (<0.8)", [R(o) for o in vr if o["vol_rel"] < 0.8])
    linea("vol normal (0.8-1.5)", [R(o) for o in vr if 0.8 <= o["vol_rel"] <= 1.5])
    linea("vol alto (>1.5)", [R(o) for o in vr if o["vol_rel"] > 1.5])

    # 7) ob_trend (la lider) — desglose por TF y por ubicacion
    print("\n7) ob_trend (la lider) — desglose:")
    obt = [o for o in ops if o["_estr"] == "ob_trend"]
    tfs = defaultdict(list)
    for o in obt:
        tfs[o["tf"]].append(R(o))
    for tf in ["5m", "15m", "1h", "4h"]:
        if tf in tfs:
            linea(f"TF {tf}", tfs[tf])
    linea("en descuento (<0.40)", [R(o) for o in obt if o.get("pos_rango", 1) < 0.40])
    linea("en premium (>0.60)", [R(o) for o in obt if o.get("pos_rango", 0) > 0.60])


if __name__ == "__main__":
    main()
