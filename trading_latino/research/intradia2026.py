"""
Juego intradía en 2026 (flat al cierre cada día). Comparamos:
- TECHO con hindsight (timing perfecto: comprar mínimo / vender máximo del día) = irreal.
- Reglas intradía REALES (sin mirar el futuro): comprar y mantener el día, momentum, reversión.
Para ver la diferencia brutal entre "decidir con el futuro a la vista" y lo de verdad alcanzable.

Uso:  python -m trading_latino.research.intradia2026
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from trading_latino.data.download import cargar


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    h1 = cargar("binance", "BTC", "1h")
    h1.index = pd.DatetimeIndex(h1["timestamp"]).tz_localize(None)
    d26 = h1[h1.index.year == 2026]
    dias = d26.groupby(d26.index.date)
    print(f"BTC 2026 intradía (1h), {len(dias)} días. Coste por operación ~0.07% (taker+slippage).")

    cap_perf = cap_bh = cap_mom = cap_rev = 1.0
    for _, g in dias:
        o, h, l, c = g["apertura"].iloc[0], g["maximo"].max(), g["minimo"].min(), g["cierre"].iloc[-1]
        # TECHO hindsight long: comprar en el mínimo, vender en el máximo del día
        cap_perf *= (h / l) * (1 - 0.0014)
        # REAL 1: comprar en la apertura, vender al cierre (mantener el día)
        cap_bh *= (c / o) * (1 - 0.0014)
        # REAL 2: momentum -> si a media sesión va por encima de la apertura, largo hasta el cierre
        mid = g["cierre"].iloc[len(g) // 2]
        cap_mom *= ((c / mid) if mid > o else 1.0) * (1 - 0.0014 if mid > o else 1)
        # REAL 3: reversión -> si a media sesión cae bajo la apertura, comprar hasta el cierre
        cap_rev *= ((c / mid) if mid < o else 1.0) * (1 - 0.0014 if mid < o else 1)

    print(f"  TECHO timing PERFECTO (hindsight, IRREAL): {(cap_perf-1)*100:+.0f}%   <- la 'trampa' del juego")
    print(f"  REAL comprar apertura/vender cierre:       {(cap_bh-1)*100:+.1f}%")
    print(f"  REAL momentum intradía (flat EOD):         {(cap_mom-1)*100:+.1f}%")
    print(f"  REAL reversión intradía (flat EOD):        {(cap_rev-1)*100:+.1f}%")


if __name__ == "__main__":
    main()
