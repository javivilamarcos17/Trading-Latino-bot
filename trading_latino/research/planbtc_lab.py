"""
PLAN BTC LAB — banco de pruebas para la operativa SPOT "2 RSI" de Plan BTC (youtuber).
=====================================================================================
Una operativa SPOT se mide contra el HODL (comprar y aguantar), no en R por trade:
¿gana más? ¿o lo mismo con caídas MUCHO menores? Ese es el listón.

El harness es PARAMETRIZABLE: cuando el dueño traiga las reglas exactas del video
(periodos RSI, umbrales, temporalidades, tramos de compra/venta) se enchufan aquí.
Mientras, corre la CLASE DE REFERENCIA (variantes RSI-spot razonables) + benchmarks:
  - HODL BTC
  - DCA semanal (compra fija cada lunes)
  - RSI spot genérico: comprar cuando RSI_diario < X, vender cuando > Y (varias X/Y)
  - 2-RSI dual: RSI semanal (régimen) + RSI diario (timing) — la forma más probable del método

Uso:  python -m trading_latino.research.planbtc_lab [desde=2021-01-01]
"""
from __future__ import annotations
import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd, ccxt

COMISION = 0.001   # 0.1% spot por lado (Binance spot estándar)

def bajar_diario(coin, desde_ts):
    ex = ccxt.binance()   # spot
    bl, t = [], desde_ts
    while True:
        try: o = ex.fetch_ohlcv(f"{coin}/USDT", "1d", since=t, limit=1000)
        except Exception: time.sleep(3); continue
        if not o: break
        bl.extend(o); nt = o[-1][0] + 86400_000
        if nt <= t or len(o) < 1000: break
        t = nt
    d = pd.DataFrame(bl, columns=["t","apertura","maximo","minimo","cierre","volumen"])
    return d.drop_duplicates("t").sort_values("t").reset_index(drop=True)

def rsi(c, n):
    dif = c.diff()
    up = dif.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn = (-dif).clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    return (100 - 100/(1 + up/dn.replace(0, np.nan)))

def metricas(equity, dias):
    eq = np.array(equity)
    pk = np.maximum.accumulate(eq)
    dd = ((pk - eq)/pk).max()*100
    total = (eq[-1]/eq[0]-1)*100
    cagr = ((eq[-1]/eq[0])**(365/dias)-1)*100
    return total, cagr, dd

def sim_spot(d, señal_compra, señal_venta, tramos=1):
    """Simulador spot: entra/sale por señales (posición 0..1 en `tramos` escalones).
    señal_compra/venta: arrays booleanos por día (sin lookahead: se ejecuta al cierre del día señal)."""
    cl = d["cierre"].to_numpy()
    pos = 0.0; cash = 1.0; btc = 0.0
    equity = []
    n_ops = 0
    paso = 1.0/tramos
    for i in range(len(cl)):
        if señal_compra[i] and pos < 1.0:
            objetivo = min(1.0, pos + paso)
            delta = objetivo - pos
            gasto = cash * (delta/(1-pos)) if pos < 1 else 0
            btc += gasto*(1-COMISION)/cl[i]; cash -= gasto; pos = objetivo; n_ops += 1
        elif señal_venta[i] and pos > 0.0:
            objetivo = max(0.0, pos - paso)
            delta = pos - objetivo
            venta_btc = btc*(delta/pos)
            cash += venta_btc*cl[i]*(1-COMISION); btc -= venta_btc; pos = objetivo; n_ops += 1
        equity.append(cash + btc*cl[i])
    return equity, n_ops

def main():
    desde = sys.argv[1] if len(sys.argv) > 1 else "2021-01-01"
    desde_ts = int(pd.Timestamp(desde, tz="UTC").timestamp()*1000)
    print(f"PLAN BTC LAB — spot BTC, {desde} -> hoy. Listón = batir al HODL (retorno o caída).\n")
    d = bajar_diario("BTC", desde_ts)
    dias = (d["t"].iloc[-1]-d["t"].iloc[0])/86400_000
    cl = d["cierre"]
    r_d = rsi(cl, 14).to_numpy()
    # RSI semanal calculado sobre cierres de semana, reindexado a diario (ffill, sin lookahead: solo semanas CERRADAS)
    dsem = d.set_index(pd.to_datetime(d["t"], unit="ms"))["cierre"].resample("W-SUN").last()
    r_w_sem = rsi(dsem, 14)
    r_w = r_w_sem.reindex(pd.to_datetime(d["t"], unit="ms"), method="ffill").shift(1).to_numpy()  # shift: semana cerrada

    print(f"{'variante':<34}{'ops':>5}{'TOTAL':>10}{'CAGR':>8}{'peor caída':>12}")
    # benchmarks
    eq_hodl = (cl/cl.iloc[0]).tolist()
    t_, c_, dd_ = metricas(eq_hodl, dias)
    print(f"{'HODL (comprar y aguantar)':<34}{1:>5}{t_:>+9.0f}%{c_:>+7.1f}%{('-'+format(dd_,'.0f')+'%'):>12}")
    # DCA semanal
    lunes = pd.to_datetime(d["t"], unit="ms").dayofweek.to_numpy() == 0
    cash = 0.0; btc = 0.0; apor = 0.0; eq = []
    for i in range(len(cl)):
        if lunes[i]: btc += (1*(1-COMISION))/cl.iloc[i]; apor += 1
        eq.append(btc*cl.iloc[i])
    ret_dca = (eq[-1]/apor-1)*100 if apor else 0
    print(f"{'DCA semanal (ref aportaciones)':<34}{int(apor):>5}{ret_dca:>+9.0f}%{'':>8}{'—':>12}")
    # clase de referencia RSI spot
    variantes = [
        ("RSI14d <30 compra / >70 vende", r_d < 30, r_d > 70, 1),
        ("RSI14d <35 / >75, 3 tramos",    r_d < 35, r_d > 75, 3),
        ("2-RSI: sem<45 y d<35 / sem>65", (r_w < 45) & (r_d < 35), (r_w > 65) & (r_d > 60), 3),
        ("2-RSI: sem<50 y d<30 / d>75",   (r_w < 50) & (r_d < 30), r_d > 75, 3),
    ]
    for nom, sc, sv, tr in variantes:
        sc = np.nan_to_num(sc, nan=False).astype(bool); sv = np.nan_to_num(sv, nan=False).astype(bool)
        eq, nops = sim_spot(d, sc, sv, tramos=tr)
        t_, c_, dd_ = metricas(eq, dias)
        print(f"{nom:<34}{nops:>5}{t_:>+9.0f}%{c_:>+7.1f}%{('-'+format(dd_,'.0f')+'%'):>12}")
    print("\nLEER ASÍ: una variante SOLO interesa si supera al HODL en retorno, o lo iguala con caída")
    print("mucho menor. Cuando el dueño traiga las reglas EXACTAS de Plan BTC, se enchufan al harness.")

if __name__ == "__main__":
    main()
