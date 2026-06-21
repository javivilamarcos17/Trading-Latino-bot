"""
SNIPER DE LIQUIDEZ EN PAPEL (Hyperliquid). SOLO LECTURA + registro en papel. NO envía órdenes.

Cada vez que se ejecuta:
  1) Reconstruye el mapa de liquidez (pools de stops) con velas de 15m.
  2) Mira la ÚLTIMA vela CERRADA: ¿barrió un pool de liquidez y revirtió, con pico de volumen?
     - Barrido de pool ARRIBA + cierre de vuelta abajo + volumen -> SETUP CORTO.
     - Barrido de pool ABAJO + cierre de vuelta arriba + volumen -> SETUP LARGO.
     Stop tras la mecha; objetivo = pool opuesto más cercano (R variable, a favor del recorrido).
  3) Registra el SETUP como operación EN PAPEL (json en disco) y actualiza las abiertas
     comprobando si tocaron stop u objetivo. Imprime el track record acumulado.

Así, ejecutándolo periódicamente (cron/loop), acumulamos evidencia EN VIVO de si el mapa real da
edge — lo que el backtest no podía decirnos. NADA de dinero real hasta tener track record.

Uso:  python -m trading_latino.live.sniper            # BTC
      python -m trading_latino.live.sniper ETH
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from trading_latino.live.mapa_liquidez import _ex, _simbolo, pools_liquidez

REGISTRO = Path(__file__).resolve().parents[2] / "data_store" / "paper"
VOL_MULT = 1.8        # pico de volumen vs media reciente
BUFFER = 0.0007       # margen del stop tras la mecha


def _cargar(moneda):
    f = REGISTRO / f"sniper_{moneda}.json"
    if f.exists():
        return json.loads(f.read_text())
    return []


def _guardar(moneda, ops):
    REGISTRO.mkdir(parents=True, exist_ok=True)
    (REGISTRO / f"sniper_{moneda}.json").write_text(json.dumps(ops, indent=2))


def _velas(ex, moneda, limite=500):
    v = pd.DataFrame(ex.fetch_ohlcv(_simbolo(moneda), "15m", limit=limite),
                     columns=["t", "apertura", "maximo", "minimo", "cierre", "volumen"])
    return v


def detectar(velas):
    """Mira la última vela CERRADA (índice -2). Devuelve un setup o None."""
    arriba, abajo = pools_liquidez(velas.iloc[:-1])     # pools con lo cerrado
    c = velas.iloc[-2]                                   # última vela cerrada
    mid = float(c["cierre"])
    vol_med = velas["volumen"].iloc[-22:-2].mean()
    if c["volumen"] < VOL_MULT * vol_med:
        return None
    cuerpo = abs(c["cierre"] - c["apertura"]) + 1e-9

    # pools por encima/por debajo del cierre
    pa = arriba[(arriba["c"] < c["maximo"]) & (arriba["c"] > c["apertura"])]
    pb = abajo[(abajo["c"] > c["minimo"]) & (abajo["c"] < c["apertura"])]
    mecha_sup = c["maximo"] - max(c["cierre"], c["apertura"])
    mecha_inf = min(c["cierre"], c["apertura"]) - c["minimo"]

    # CORTO: barrió un pool de arriba (mecha lo pinchó) y cerró por debajo, mecha de rechazo
    if len(pa) and c["cierre"] < c["apertura"] and mecha_sup > cuerpo:
        objetivos = abajo[abajo["c"] < mid].sort_values("c", ascending=False)
        if len(objetivos):
            stop = float(c["maximo"]) * (1 + BUFFER); objetivo = float(objetivos.iloc[0]["c"])
            D = stop - mid
            if objetivo < mid and D > 0:
                return {"dir": "corto", "entry": mid, "stop": stop, "target": objetivo,
                        "R": round((mid - objetivo) / D, 2), "pool": float(pa.iloc[0]["c"])}
    # LARGO: barrió un pool de abajo y cerró por encima
    if len(pb) and c["cierre"] > c["apertura"] and mecha_inf > cuerpo:
        objetivos = arriba[arriba["c"] > mid].sort_values("c")
        if len(objetivos):
            stop = float(c["minimo"]) * (1 - BUFFER); objetivo = float(objetivos.iloc[0]["c"])
            D = mid - stop
            if objetivo > mid and D > 0:
                return {"dir": "largo", "entry": mid, "stop": stop, "target": objetivo,
                        "R": round((objetivo - mid) / D, 2), "pool": float(pb.iloc[0]["c"])}
    return None


def actualizar_abiertas(ops, velas):
    """Comprueba si las operaciones abiertas tocaron stop u objetivo."""
    hi = velas["maximo"].to_numpy(); lo = velas["minimo"].to_numpy(); ts = velas["t"].to_numpy()
    for o in ops:
        if o["status"] != "abierta":
            continue
        for k in range(len(ts)):
            if ts[k] <= o["ts"]:
                continue
            if o["dir"] == "corto":
                if hi[k] >= o["stop"]: o.update(status="perdida", exit=o["stop"], R_real=-1.0); break
                if lo[k] <= o["target"]: o.update(status="ganada", exit=o["target"], R_real=o["R"]); break
            else:
                if lo[k] <= o["stop"]: o.update(status="perdida", exit=o["stop"], R_real=-1.0); break
                if hi[k] >= o["target"]: o.update(status="ganada", exit=o["target"], R_real=o["R"]); break


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    moneda = (sys.argv[1:] or ["BTC"])[0]
    ex = _ex(); ex.load_markets()
    velas = _velas(ex, moneda)
    ops = _cargar(moneda)

    actualizar_abiertas(ops, velas)

    # detectar setup en la última vela cerrada (sin duplicar)
    ts_ultima = int(velas.iloc[-2]["t"])
    ya = any(o["ts"] == ts_ultima for o in ops)
    setup = None if ya else detectar(velas)
    if setup:
        setup.update(ts=ts_ultima, status="abierta",
                     fecha=str(pd.to_datetime(ts_ultima, unit="ms")))
        ops.append(setup)
        print(f"NUEVO SETUP {setup['dir'].upper()} @ {setup['entry']:,.1f} | stop {setup['stop']:,.1f} "
              f"| objetivo {setup['target']:,.1f} | {setup['R']}R (barrió pool {setup['pool']:,.1f})")
    else:
        print("Sin setup nuevo en la última vela cerrada." + (" (ya registrado)" if ya else ""))

    _guardar(moneda, ops)

    # track record en papel
    cerradas = [o for o in ops if o["status"] in ("ganada", "perdida")]
    abiertas = [o for o in ops if o["status"] == "abierta"]
    print(f"\nTrack record EN PAPEL ({moneda}): {len(cerradas)} cerradas, {len(abiertas)} abiertas")
    if cerradas:
        rs = [o["R_real"] for o in cerradas]
        win = sum(1 for r in rs if r > 0) / len(rs)
        print(f"  win {win*100:.0f}% | R total {sum(rs):+.1f} | edge/op {sum(rs)/len(rs):+.3f}R")
    for o in abiertas:
        print(f"  abierta: {o['dir']} @ {o['entry']:,.1f} stop {o['stop']:,.1f} obj {o['target']:,.1f} ({o['fecha']})")


if __name__ == "__main__":
    main()
