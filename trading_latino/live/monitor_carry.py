"""
MONITOR DEL MOTOR 3 (carry delta-neutral) — puente semáforo → cesta.
NO opera: informa. Dice si procede montar/mantener/desmontar la cesta y con qué composición.

Reglas (validadas en STATUS 2026-07-19e/j/l):
  - ENCENDIDO solo si: funding medio cesta > 5% APR (4ª luz ON) — el carry duerme en oso.
  - Timing de apertura/rebalanceo: dial de PERSISTENCIA — funding del venue de la cesta en
    percentil >= 75 de sus 180d (auditoría r6: la autocorrelación propia es la señal efectiva;
    el lead-lag cross-venue existe pero no añade nada incremental).
  - Composición: top monedas líquidas por funding APR actual (equiponderada, delta-neutral
    corto perp + largo spot), máx. 15.
  - TRIGGERS DE DESMONTAJE (manual carry, informe investigador 2026-07-19j):
      * funding medio cesta < 0 durante >= 3 días seguidos → DESMONTAR
      * de-peg del colateral estable > 1% → DESMONTAR YA (no esperar)
      * tope duro por exchange: nunca > 50% de la cesta en un solo venue
      * colateral SIEMPRE en stables, nunca coin-margin (convexidad negativa)

  DIMENSIONADO POR RIESGO DE COLA (2026-07-19q — aritmetica retail sin custodia off-exchange):
    perdida en muerte subita de un venue ~ 0.5*manga*(1/apalancamiento + 0.3)
      [0.5 = tope por venue; 1/lev = margen depositado; 0.3 = gap direccional estimado de la
       pata spot sin cobertura durante el desmontaje forzoso]
    con lev=3: cola ~ 0.32*manga → presupuesto de cola 3% del capital ⇒ MANGA MAXIMA ~9-10%.
    A +11.7% CAGR del carry, eso aporta ~1.0-1.2%/año al portfolio: motor MODESTO por diseño.
    Subir la manga = subir la cola linealmente. No hay comida gratis.

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
    media = sum(a for _, a in filas) / len(filas)          # luz de régimen: universo completo
    cesta = [(c, a) for c, a in filas if a > 2.0][:TOP_N]  # cesta: solo monedas que PAGAN (>2% APR)

    # dial de persistencia: percentil del funding BTC del venue (Binance) vs sus 180d
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
    print(f"funding medio del universo ({len(filas)}): {media:+.1f}% APR → "
          f"{'🟢 ZONA ON' if media > UMBRAL_ON else ('🟡 marginal' if media > 0 else '🔴 OFF (oso)')}")
    print(f"cesta candidata (solo pagan >2% APR): {len(cesta)} monedas")
    if pct is not None:
        print(f"dial persistencia: funding del venue percentil {pct:.0f}/180d → "
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
