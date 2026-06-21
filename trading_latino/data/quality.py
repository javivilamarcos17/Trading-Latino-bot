"""
Control de calidad de los datos descargados (Fase 1).

Un backtest solo vale si los datos son buenos. Aquí comprobamos lo esencial:
- que las velas estén ordenadas y sin duplicados,
- que no falten velas (huecos en el tiempo),
- que cada vela tenga sentido (máximo >= mínimo, precios y volumen positivos, sin NaN).

Uso:
    python -m trading_latino.data.quality                 # revisa BTC (todas las TF)
    python -m trading_latino.data.quality --simbolos BTC ETH --tf 1h 4h
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from trading_latino.config import CONFIG
from trading_latino.data.download import cargar

# Duración de cada vela, en milisegundos, para detectar huecos.
PASO_MS = {
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
    "1w": 604_800_000,
}


def revisar(df: pd.DataFrame, temporalidad: str) -> dict:
    """Devuelve un informe con los problemas encontrados (vacío = todo bien)."""
    informe: dict = {"filas": len(df)}

    if df.empty:
        informe["error"] = "sin datos"
        return informe

    ts = df["timestamp"]
    informe["rango"] = f"{ts.iloc[0]} → {ts.iloc[-1]}"
    informe["duplicados"] = int(ts.duplicated().sum())
    informe["ordenado"] = bool(ts.is_monotonic_increasing)

    # Huecos: diferencias entre velas mayores que el paso esperado.
    paso = PASO_MS.get(temporalidad)
    if paso is not None:
        difs = ts.astype("int64").div(1_000_000).diff().dropna()  # ns -> ms
        huecos = difs[difs > paso]
        informe["huecos"] = int(len(huecos))
        velas_perdidas = int(((huecos / paso) - 1).round().sum()) if len(huecos) else 0
        informe["velas_perdidas_aprox"] = velas_perdidas

    # Integridad de cada vela.
    o, h, l, c, v = (df[x] for x in ["apertura", "maximo", "minimo", "cierre", "volumen"])
    malas = (
        (h < l) | (h < o) | (h < c) | (l > o) | (l > c)
        | (o <= 0) | (c <= 0) | (v < 0)
        | df[["apertura", "maximo", "minimo", "cierre", "volumen"]].isna().any(axis=1)
    )
    informe["velas_invalidas"] = int(malas.sum())

    problemas = (
        informe["duplicados"] > 0
        or not informe["ordenado"]
        or informe.get("huecos", 0) > 0
        or informe["velas_invalidas"] > 0
    )
    informe["ok"] = not problemas
    return informe


def _imprimir(simbolo: str, tf: str, informe: dict) -> None:
    estado = "OK ✅" if informe.get("ok") else "REVISAR ⚠️"
    if "error" in informe:
        print(f"  [{simbolo} {tf}] {informe['error']}  ⚠️")
        return
    print(
        f"  [{simbolo} {tf}] {estado}  {informe['filas']} velas  {informe['rango']}\n"
        f"      duplicados={informe['duplicados']}  ordenado={informe['ordenado']}  "
        f"huecos={informe.get('huecos', '-')} (≈{informe.get('velas_perdidas_aprox', 0)} velas)  "
        f"invalidas={informe['velas_invalidas']}"
    )


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    p = argparse.ArgumentParser(description="Revisar la calidad de los datos descargados.")
    p.add_argument("--simbolos", nargs="+", default=[CONFIG.btc])
    p.add_argument("--tf", nargs="+", default=["1h", "4h", "1d", "1w"])
    p.add_argument("--exchange", default=CONFIG.backtest.EXCHANGE_DATOS)
    args = p.parse_args()

    for simbolo in args.simbolos:
        print(f"· {simbolo}")
        for tf in args.tf:
            try:
                df = cargar(args.exchange, simbolo, tf)
            except FileNotFoundError as e:
                print(f"  [{simbolo} {tf}] {e}")
                continue
            _imprimir(simbolo, tf, revisar(df, tf))


if __name__ == "__main__":
    main()
