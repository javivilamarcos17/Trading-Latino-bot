"""Inventario + estado de la arena (solo lectura). Uso: python -m trading_latino.live._inventario"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

REG = Path(__file__).resolve().parents[2] / "data_store" / "paper_arena"


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    ops = []
    comp, estrs = set(), set()
    for f in REG.glob("*.json"):
        if f.stem.startswith("_"):
            continue
        partes = f.stem.split("_")
        tf, coin, estr = partes[-1], partes[-2], "_".join(partes[:-2])
        comp.add((estr, coin, tf)); estrs.add(estr)
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue
        if isinstance(data, list):
            for o in data:
                if isinstance(o, dict):
                    o["_estr"] = estr
                    ops.append(o)

    print(f"INVENTARIO: {len(estrs)} estrategias | {len(comp)} competidores (estrategia x moneda x TF)")
    print(f"Estrategias: {sorted(estrs)}\n")

    live = [o for o in ops if o.get("regimen") is not None
            and o.get("status") == "cerrada" and isinstance(o.get("exits"), dict)]
    print(f"Ops cerradas con contexto + salida medida (en vivo): {len(live)}\n")

    agg = defaultdict(list)
    for o in live:
        agg[o["_estr"]].append(o["exits"]["fixed"])
    print("COMO VA CADA ESTRATEGIA (R con salida fija):")
    print(f"  {'estrategia':<12}{'n':>5}{'win':>7}{'exp/op':>9}")
    for e, v in sorted(agg.items(), key=lambda x: -sum(x[1]) / len(x[1])):
        n = len(v); w = sum(1 for x in v if x > 0) / n; ex = sum(v) / n
        print(f"  {e:<12}{n:>5}{w * 100:>6.0f}%{ex:>+8.2f}R")

    cand = [e for e, v in agg.items() if len(v) >= 15 and sum(v) / len(v) > 0.05]
    print(f"\nCandidatas reales (exp/op > +0.05R y n>=15): {cand if cand else 'NINGUNA todavia'}")


if __name__ == "__main__":
    main()
