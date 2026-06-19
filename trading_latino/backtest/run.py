"""
Correr el backtest e imprimir el informe (Fase 5).

Uso:
    python -m trading_latino.backtest.run                  # BTC, modo de la config, barrido de costes
    python -m trading_latino.backtest.run --simbolo BTC --modo btc_longs
"""

from __future__ import annotations

import argparse
import sys

from trading_latino.config import CONFIG
from trading_latino.backtest.engine import correr, preparar
from trading_latino.reports.metrics import formatear, resumen


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    p = argparse.ArgumentParser(description="Backtest de la estrategia Trading Latino.")
    p.add_argument("--simbolo", default="BTC")
    p.add_argument("--modo", default=CONFIG.backtest.MODO)
    p.add_argument("--capital", type=float, default=CONFIG.backtest.CAPITAL_INICIAL)
    args = p.parse_args()

    print(f"== Backtest {args.simbolo} · modo '{args.modo}' · capital {args.capital:.0f} ==")
    print("Preparando datos e indicadores...")
    datos = preparar(args.simbolo)

    # Referencia honesta: ¿cuánto habría hecho simplemente comprar y mantener BTC?
    h1 = datos["h1"]
    buy_hold = h1["cierre"].iloc[-1] / h1["cierre"].iloc[0] - 1
    print(f"\n[Referencia] Comprar y mantener {args.simbolo}: {buy_hold*100:+.2f}%")

    # Caso base (costes reales 1x) con informe detallado
    base = correr(args.simbolo, args.modo, args.capital, multiplicador_costes=1.0, datos=datos)
    r = resumen(base)
    print("\n-- Costes reales (1x) --")
    print(formatear(base, r))

    # Barrido de sensibilidad a costes (¿cuánto margen sobre el muro de costes?)
    print("\n-- Sensibilidad a costes (rentabilidad neta) --")
    print(f"  {'costes':>8} | {'rent.':>9} | {'profit f.':>9} | {'ops':>5}")
    for mult in CONFIG.backtest.BARRIDO_COSTES:
        res = correr(args.simbolo, args.modo, args.capital, multiplicador_costes=mult, datos=datos)
        rr = resumen(res)
        pf = rr["profit_factor"]
        pf_txt = "inf" if pf == float("inf") else f"{pf:.2f}"
        print(f"  {mult:>7.1f}x | {rr['rentabilidad']*100:>8.2f}% | {pf_txt:>9} | {rr['operaciones']:>5}")

    print("\nNota: en neto (comisiones + funding + slippage). Resultado a interpretar con los gates de")
    print("docs/RIESGOS_RENTABILIDAD.md (verde/ámbar/rojo). NO es una recomendación de inversión.")


if __name__ == "__main__":
    main()
