"""
LAB DE SALIDAS (solo lectura) — datos REALES. Lee el resultado neto en R de cada política de salida,
MEDIDO sobre el camino real de 1m (orden correcto stop-vs-objetivo), no estimado.
Políticas: fixed (fijo) · be05/be10 (break-even a 0.5R/1R) · t125 (objetivo 1.25R) · trail (trailing 1R).

Uso:  python -m trading_latino.live.salidas
"""

from __future__ import annotations

import glob
import json
import sys

POL = ("fixed", "be05", "be10", "t125", "trail")
NOMBRE = {"fixed": "objetivo fijo", "be05": "break-even 0.5R", "be10": "break-even 1R",
          "t125": "objetivo 1.25R", "trail": "trailing 1R"}


def cargar():
    ops = []
    for f in glob.glob("data_store/paper_arena/*.json"):
        try:
            for o in json.load(open(f, encoding="utf-8")):
                if o.get("status") == "cerrada" and isinstance(o.get("exits"), dict):
                    ops.append(o)
        except Exception:
            pass
    return ops


def _stats(vals):
    n = len(vals)
    return n, (sum(1 for v in vals if v > 0) / n if n else 0), (sum(vals) / n if n else 0)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ops = cargar()
    print(f"LAB DE SALIDAS (datos reales, resueltos con 1m) — {len(ops)} operaciones cerradas\n")
    if len(ops) < 20:
        print("  Muestra aún pequeña; se llena sola al acumular. Vuelve a mirar mañana."); return

    print("1) COMPARATIVA DE SALIDAS (todas las estrategias juntas) — exp/op NETO en R:")
    print(f"   {'salida':<18}{'n':>6}{'win':>7}{'exp/op':>10}")
    res = {}
    for p in POL:
        vals = [o["exits"][p] for o in ops if p in o["exits"]]
        n, win, exp = _stats(vals); res[p] = exp
        print(f"   {NOMBRE[p]:<18}{n:>6}{win*100:>6.0f}%{exp:>+9.3f}R")
    mejor = max(res, key=res.get)
    print(f"   -> mejor salida global: {NOMBRE[mejor]} (exp {res[mejor]:+.3f}R)")

    print("\n2) MEJOR SALIDA POR ESTRATEGIA (n>=15):")
    porestr = {}
    for o in ops:
        porestr.setdefault(o.get("estr", "?"), []).append(o)
    print(f"   {'estrategia':<12}{'n':>5}  mejor salida (exp/op)")
    for e, v in sorted(porestr.items()):
        if len(v) < 15:
            continue
        exps = {p: sum(o["exits"][p] for o in v if p in o["exits"]) / len(v) for p in POL}
        b = max(exps, key=exps.get)
        print(f"   {e:<12}{len(v):>5}  {NOMBRE[b]:<16} {exps[b]:+.3f}R   (fijo: {exps['fixed']:+.3f}R)")

    print("\n3) ¿Qué estrategia + salida da exp/op POSITIVA? (lo que buscamos)")
    hay = False
    for e, v in sorted(porestr.items()):
        if len(v) < 15:
            continue
        for p in POL:
            exp = sum(o["exits"][p] for o in v if p in o["exits"]) / len(v)
            if exp > 0.05:
                print(f"   {e} + {NOMBRE[p]}: {exp:+.3f}R (n={len(v)})"); hay = True
    if not hay:
        print("   Ninguna supera +0.05R todavía (o falta muestra). Seguimos midiendo.")


if __name__ == "__main__":
    main()
