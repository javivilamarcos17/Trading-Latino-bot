"""ANALISIS MULTI-TEMPORALIDAD (solo lectura). Para cada estrategia, compara su resultado entre
temporalidades (¿hay una TF claramente mejor?) y cruza el resultado con el régimen del momento.
Objetivo: entender cómo se relacionan las temporalidades, que es donde puede estar la ventaja.

Uso: python -m trading_latino.live._mtf
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

REG = Path(__file__).resolve().parents[2] / "data_store" / "paper_arena"
TFS = ["1m", "5m", "15m", "1h", "4h"]


def cargar():
    ops = []
    for f in REG.glob("*.json"):
        if f.stem.startswith("_"):
            continue
        partes = f.stem.split("_")
        tf, estr = partes[-1], "_".join(partes[:-2])
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue
        if isinstance(data, list):
            for o in data:
                if (isinstance(o, dict) and o.get("status") == "cerrada"
                        and isinstance(o.get("exits"), dict)):
                    o["_estr"], o["_tf"] = estr, tf
                    ops.append(o)
    return ops


def cel(v):
    if len(v) < 5:
        return f"{'·':>15}"
    n = len(v); w = sum(1 for x in v if x > 0) / n * 100; e = sum(v) / len(v)
    return f"{n:>3} {w:>3.0f}% {e:>+5.2f}R"   # ancho fijo 15 para que la tabla quede alineada


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ops = cargar()
    print(f"ANALISIS MULTI-TEMPORALIDAD — {len(ops)} operaciones cerradas (salida fija en R)")
    print("'·' = menos de 5 ops (sin dato). Solo cuentan las que tienen salida medida.\n")

    por = defaultdict(lambda: defaultdict(list))
    for o in ops:
        por[o["_estr"]][o["_tf"]].append(o["exits"]["fixed"])

    print(f"{'estrategia':<12}" + "".join(f"{tf:>15}" for tf in TFS))
    for estr in sorted(por):
        fila = f"{estr:<12}"
        for tf in TFS:
            fila += f"{cel(por[estr][tf]):>15}"
        print(fila)

    print("\nMEJOR temporalidad por estrategia (n>=15):")
    for estr in sorted(por):
        cand = [(tf, sum(v) / len(v), len(v)) for tf, v in por[estr].items() if len(v) >= 15]
        if cand:
            tf, e, n = max(cand, key=lambda x: x[1])
            print(f"  {estr:<12} -> {tf:<4} (exp {e:+.2f}R, n={n})")


if __name__ == "__main__":
    main()
