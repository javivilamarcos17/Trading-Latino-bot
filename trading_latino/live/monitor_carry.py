"""
MONITOR DEL MOTOR 3 (carry delta-neutral) — puente semáforo → cesta.
NO opera: informa. Dice si procede montar/mantener/desmontar la cesta y con qué composición.

Reglas (validadas en STATUS 2026-07-19e/j/l):
  - ENCENDIDO solo si: funding medio cesta > 5% APR (4ª luz ON) — el carry duerme en oso.
  - Timing de apertura/rebalanceo: dial lead-lag — Binance (líder) en percentil >= 75 de sus 180d.
  - Composición: top monedas líquidas por funding APR actual (equiponderada, delta-neutral
    corto perp + largo spot), máx. 15.
  - TRIGGERS DE DESMONTAJE (manual carry, informe investigador 2026-07-19j):
      * funding medio cesta < 0 durante >= 3 días seguidos → DESMONTAR
      * de-peg del colateral estable > 1% → DESMONTAR YA (no esperar)
      * tope duro por exchange: nunca > 50% de la cesta en un solo venue
      * colateral SIEMPRE en stables, nunca coin-margin (convexidad negativa)

Uso:  python -m trading_latino.live.monitor_carry
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import time
import ccxt

UNIVERSO = ["BTC", "ETH", "XRP", "LINK", "DOGE", "AVAX", "ADA", "DOT", "LTC", "BCH",
            "SOL", "SUI", "NEAR", "APT", "ARB"]
TOP_N = 15
UMBRAL_ON = 5.0       # % APR medio de cesta para encender
PCT_DIAL = 75         # percentil 180d de Binance para abrir/rebalancear


def main():
    ex = ccxt.binance({"options": {"defaultType": "future"}})
    filas = []
    for c in UNIVERSO:
        try:
            fr = ex.fetch_funding_rate(f"{c}/USDT:USDT").get("fundingRate")
            if fr is not None:
                filas.append((c, fr * 3 * 365 * 100))
        except Exception:
            pass
        time.sleep(0.05)
    if not filas:
        print("sin datos de funding"); return
    filas.sort(key=lambda x: -x[1])
    cesta = filas[:TOP_N]
    media = sum(a for _, a in cesta) / len(cesta)

    # dial lead-lag: percentil del funding BTC de Binance vs 180d
    pct = None
    try:
        since = int((time.time() - 180 * 86400) * 1000)
        hist, s = [], since
        for _ in range(3):
            h = ex.fetch_funding_rate_history("BTC/USDT:USDT", since=s, limit=500)
            if not h: break
            hist += [x["fundingRate"] for x in h]
            s = h[-1]["timestamp"] + 1
        actual = ex.fetch_funding_rate("BTC/USDT:USDT").get("fundingRate")
        if len(hist) > 100 and actual is not None:
            pct = 100 * sum(1 for x in hist if x < actual) / len(hist)
    except Exception:
        pass

    print("🧺 MONITOR MOTOR 3 — carry delta-neutral (informativo, NO opera)")
    print(f"funding medio cesta top-{len(cesta)}: {media:+.1f}% APR → "
          f"{'🟢 ZONA ON' if media > UMBRAL_ON else ('🟡 marginal' if media > 0 else '🔴 OFF (oso)')}")
    if pct is not None:
        print(f"dial lead-lag: Binance percentil {pct:.0f}/180d → "
              f"{'🟢 abrir/rebalancear' if pct >= PCT_DIAL else '⏳ esperar mejor momento'}")
    print(f"\n{'moneda':<8}{'APR%':>8}   (corto perp + largo spot, equiponderada)")
    for c, a in cesta:
        print(f"{c:<8}{a:>+8.1f}")
    print("\nTRIGGERS DE DESMONTAJE: funding cesta <0 3 días → desmontar · de-peg stable >1% → YA")
    print("LÍMITES: máx 50% de cesta por exchange · colateral solo stables · PnL barrido a diario")
    veredicto = ("MONTAR/MANTENER" if media > UMBRAL_ON and (pct is None or pct >= PCT_DIAL)
                 else ("MANTENER si ya está, no ampliar" if media > UMBRAL_ON else "NO MONTAR (dormir)"))
    print(f"\nVEREDICTO HOY: {veredicto}")


if __name__ == "__main__":
    main()
