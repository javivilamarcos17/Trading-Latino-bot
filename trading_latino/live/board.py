"""
BOARD de la ARENA — vista de solo lectura del paper-trading acumulado. NO llama a la API (instantáneo).
Lee los registros JSON y muestra: ranking por estrategia, ranking detallado, abiertas y última actualización.

Uso:  python -m trading_latino.live.board
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REG = Path(__file__).resolve().parents[2] / "data_store" / "paper_arena"


def _cum(pnls):
    eq = 1.0
    for p in pnls:
        eq *= (1 + p)
    return eq - 1


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    files = sorted(REG.glob("*.json"))
    if not files:
        print("Aún no hay datos. Lanza la arena o espera a la tarea programada."); return

    comp = []           # por competidor
    por_estr = {}       # agregado por estrategia
    ult = 0
    abiertas_total = 0
    for f in files:
        partes = f.stem.split("_")
        # nombre tipo  scalp_sqz_BTC_15m  -> estrategia puede llevar guion bajo
        tf = partes[-1]; coin = partes[-2]; estr = "_".join(partes[:-2])
        ops = json.loads(f.read_text())
        cerr = [o for o in ops if o["status"] == "cerrada"]
        ab = [o for o in ops if o["status"] == "abierta"]
        abiertas_total += len(ab)
        pnls = [o["pnl"] for o in cerr]
        comp.append({"estr": estr, "coin": coin, "tf": tf, "n": len(cerr), "ab": len(ab),
                     "win": (sum(1 for p in pnls if p > 0) / len(pnls)) if pnls else None,
                     "ret": _cum(pnls)})
        d = por_estr.setdefault(estr, [])
        d.extend(pnls)
        ult = max(ult, f.stat().st_mtime)

    print("=" * 64)
    print(f"  BOARD ARENA (paper)   ·   actualizado hace {int((time.time()-ult)/60)} min")
    print("=" * 64)

    print("\n  RANKING POR ESTRATEGIA (todas las monedas/TF juntas)")
    print(f"  {'estrategia':<12} {'ops':>5} {'win':>6} {'retorno':>10}")
    fila = [(e, len(p), (sum(1 for x in p if x > 0) / len(p) if p else None), _cum(p)) for e, p in por_estr.items()]
    for e, n, win, ret in sorted(fila, key=lambda x: -x[3]):
        w = f"{win*100:4.0f}%" if win is not None else "  - "
        print(f"  {e:<12} {n:>5} {w:>6} {ret*100:>+9.2f}%")

    print("\n  DETALLE POR COMPETIDOR (top y bottom por retorno)")
    print(f"  {'estrategia':<12} {'coin':<5} {'tf':<4} {'ops':>4} {'ab':>3} {'win':>6} {'retorno':>9}")
    orden = sorted(comp, key=lambda x: -x["ret"])
    activos = [c for c in orden if c["n"] > 0]
    muestra = activos[:8] + (["..."] if len(activos) > 12 else []) + activos[-4:] if len(activos) > 12 else activos
    for c in muestra:
        if c == "...":
            print("  ..."); continue
        w = f"{c['win']*100:4.0f}%" if c["win"] is not None else "  - "
        print(f"  {c['estr']:<12} {c['coin']:<5} {c['tf']:<4} {c['n']:>4} {c['ab']:>3} {w:>6} {c['ret']*100:>+8.2f}%")

    tot = sum(c["n"] for c in comp)
    print(f"\n  TOTAL: {tot} operaciones cerradas | {abiertas_total} abiertas | {len(files)} competidores")
    print("  (recuerda: muestra pequeña al principio = sin conclusiones todavía)")


if __name__ == "__main__":
    main()
