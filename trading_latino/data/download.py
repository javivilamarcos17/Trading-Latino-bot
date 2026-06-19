"""
Descarga de histórico de velas (Fase 1).

Baja velas OHLCV de un exchange (por defecto Binance, vía la librería ccxt) y las guarda
en disco en formato parquet, una tabla por (símbolo, temporalidad).

Decisiones (ver docs/ARQUITECTURA.md):
- Descargamos CADA temporalidad nativa del exchange (1h, 4h, 1d, 1w) en vez de resamplear
  desde 1h. Es más fiel (coincide con TradingView) y evita errores de alineación.
- Para el backtest usamos histórico largo de Binance; para OPERAR usaremos Hyperliquid.
  Validar la estrategia con datos de otro exchange es estándar y aceptable.
- Usamos futuros perpetuos (lo que de verdad operaremos): símbolo unificado "BTC/USDT:USDT".

Uso:
    python -m trading_latino.data.download                 # descarga BTC (todas las TF)
    python -m trading_latino.data.download --simbolos BTC ETH --tf 1h 4h
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import ccxt
import pandas as pd

from trading_latino.config import CONFIG

# Carpeta donde se guardan los datos (ignorada por git).
DATA_STORE = Path(__file__).resolve().parents[2] / "data_store"

COLUMNAS = ["timestamp", "apertura", "maximo", "minimo", "cierre", "volumen"]


def _exchange(exchange_id: str) -> ccxt.Exchange:
    """Crea el cliente del exchange para futuros perpetuos, con rate-limit activado."""
    clase = getattr(ccxt, exchange_id)
    return clase({
        "enableRateLimit": True,                 # respeta los límites de la API automáticamente
        "options": {"defaultType": "future"},    # mercado de futuros perpetuos
    })


def _simbolo_mercado(simbolo: str) -> str:
    """Traduce un símbolo corto del proyecto (p. ej. 'BTC') al unificado de ccxt perpetuo."""
    return f"{simbolo}/USDT:USDT"


def _ruta(exchange_id: str, simbolo: str, temporalidad: str) -> Path:
    return DATA_STORE / exchange_id / simbolo / f"{temporalidad}.parquet"


def _a_ms(fecha_iso: str) -> int:
    """Convierte 'YYYY-MM-DD' a milisegundos UTC."""
    return int(datetime.fromisoformat(fecha_iso).replace(tzinfo=timezone.utc).timestamp() * 1000)


def descargar_ohlcv(
    ex: ccxt.Exchange,
    simbolo: str,
    temporalidad: str,
    desde_ms: int,
    hasta_ms: int,
) -> pd.DataFrame:
    """Descarga velas OHLCV paginando desde `desde_ms` hasta `hasta_ms`.

    Devuelve un DataFrame ordenado por tiempo, sin duplicados, con columnas COLUMNAS.
    """
    mercado = _simbolo_mercado(simbolo)
    tf_ms = ex.parse_timeframe(temporalidad) * 1000
    limite = 1000
    filas: list[list] = []
    cursor = desde_ms

    while cursor < hasta_ms:
        lote = ex.fetch_ohlcv(mercado, timeframe=temporalidad, since=cursor, limit=limite)
        if not lote:
            break
        filas.extend(lote)
        ultimo = lote[-1][0]
        # avanzar el cursor justo después de la última vela recibida
        cursor = ultimo + tf_ms
        # si el exchange devolvió menos de un lote completo, ya estamos al día
        if len(lote) < limite:
            break

    if not filas:
        return pd.DataFrame(columns=COLUMNAS)

    df = pd.DataFrame(filas, columns=["timestamp", "apertura", "maximo", "minimo", "cierre", "volumen"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df[df["timestamp"] < pd.to_datetime(hasta_ms, unit="ms", utc=True)]
    df = df.drop_duplicates(subset="timestamp").sort_values("timestamp").reset_index(drop=True)
    return df


def guardar(df: pd.DataFrame, exchange_id: str, simbolo: str, temporalidad: str) -> Path:
    ruta = _ruta(exchange_id, simbolo, temporalidad)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(ruta, index=False)
    return ruta


def cargar(exchange_id: str, simbolo: str, temporalidad: str) -> pd.DataFrame:
    """Lee del disco las velas guardadas (las usará el Feed del backtest)."""
    ruta = _ruta(exchange_id, simbolo, temporalidad)
    if not ruta.exists():
        raise FileNotFoundError(f"No hay datos en {ruta}. Descárgalos primero.")
    return pd.read_parquet(ruta)


def descargar_simbolo(
    simbolo: str,
    temporalidades: list[str],
    desde: str,
    hasta: str,
    exchange_id: str = "binance",
) -> None:
    """Descarga y guarda todas las temporalidades de un símbolo, informando del resultado."""
    ex = _exchange(exchange_id)
    desde_ms, hasta_ms = _a_ms(desde), _a_ms(hasta)
    for tf in temporalidades:
        t0 = time.time()
        df = descargar_ohlcv(ex, simbolo, tf, desde_ms, hasta_ms)
        if df.empty:
            print(f"  [{simbolo} {tf}] sin datos en el rango pedido")
            continue
        ruta = guardar(df, exchange_id, simbolo, tf)
        ini = df["timestamp"].iloc[0].date()
        fin = df["timestamp"].iloc[-1].date()
        print(f"  [{simbolo} {tf}] {len(df):>6} velas  {ini} → {fin}  ({time.time()-t0:.1f}s)  → {ruta.name}")


def main() -> None:
    # En Windows la consola usa cp1252 y rompe con caracteres como "→". Forzar UTF-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    p = argparse.ArgumentParser(description="Descargar histórico de velas para el backtest.")
    p.add_argument("--simbolos", nargs="+", default=[CONFIG.btc],
                   help="Símbolos a descargar (por defecto solo BTC).")
    p.add_argument("--tf", nargs="+", default=["1h", "4h", "1d", "1w"],
                   help="Temporalidades a descargar.")
    p.add_argument("--desde", default=CONFIG.backtest.FECHA_INICIO)
    p.add_argument("--hasta", default=CONFIG.backtest.FECHA_FIN)
    p.add_argument("--exchange", default=CONFIG.backtest.EXCHANGE_DATOS)
    args = p.parse_args()

    print(f"Descargando de {args.exchange}  ({args.desde} → {args.hasta})")
    for simbolo in args.simbolos:
        print(f"· {simbolo}")
        descargar_simbolo(simbolo, args.tf, args.desde, args.hasta, args.exchange)
    print("Hecho.")


if __name__ == "__main__":
    main()
