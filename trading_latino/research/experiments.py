"""
Banco de experimentos de ENTRADA (BTC-longs).

Probamos muchas variantes de la lógica de entrada y juzgamos cada una por su robustez:
rentabilidad neta en ENTRENAMIENTO (2021-23) **y** en TEST (2024-25). Buscamos algo que
gane en AMBOS, no el mejor número suelto (eso sería sobreajuste).

La salida se fija (agotamiento del impulso) para aislar el efecto de la entrada.

Uso:  python -m trading_latino.research.experiments
"""

from __future__ import annotations

import math
import sys

import pandas as pd

from trading_latino.backtest.engine import correr, preparar
from trading_latino.domain.types import Accion, ColorSqueeze, Decision, EstadoMercado, Lado, Posicion
from trading_latino.config import CONFIG
from trading_latino.risk.manager import en_bloqueo_horario
from trading_latino.strategy.brain import _gestionar_corto, _gestionar_largo

_CORTE = pd.Timestamp("2024-01-01", tz="UTC")
_NADA = Decision(Accion.NADA, "no entra")


def _num_ok(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def _entrada(estado: EstadoMercado, p: dict) -> Decision:
    """Entrada parametrizable. `p` activa/desactiva cada filtro."""
    d, h4, h1 = estado.diario, estado.h4, estado.h1
    tendencia = p.get("modo") == "tendencia"

    # semáforo
    if p["semaforo"] == "ema_cross":
        if not (d.ema_rapida > d.ema_lenta):
            return _NADA
    elif p["semaforo"] == "precio_ema55":
        if not (estado.precio > d.ema_lenta):
            return _NADA

    if p.get("usar_poc"):
        if not _num_ok(h4.poc) or abs(estado.precio - h4.poc) / h4.poc > p["proximidad"]:
            return _NADA

    if p.get("usar_squeeze4h"):
        objetivo = ColorSqueeze.VERDE_CLARO if tendencia else ColorSqueeze.ROJO_OSCURO
        if h4.sqz_color is not objetivo:
            return _NADA

    # ADX por PENDIENTE (signo configurable: 'neg' = bajando, 'pos' = subiendo)
    if p.get("usar_adx"):
        if not _num_ok(h4.adx_pendiente):
            return _NADA
        signo = p.get("adx_signo", "neg")
        if signo == "pos" and not (h4.adx_pendiente > 0):
            return _NADA
        if signo == "neg" and not (h4.adx_pendiente < 0):
            return _NADA

    # ADX por NIVEL (fuerza de tendencia, en vez de pendiente)
    if p.get("usar_adx_nivel"):
        if not _num_ok(h4.adx):
            return _NADA
        mayor = p.get("adx_nivel_mayor", True)
        umbral = p.get("adx_umbral", 23)
        if mayor and not (h4.adx > umbral):
            return _NADA
        if not mayor and not (h4.adx < umbral):
            return _NADA

    # Gatillo 1H: por ESTADO (está en ese color) o por GIRO (acaba de cambiar a ese color).
    if p.get("usar_gatillo1h"):
        objetivo = ColorSqueeze.VERDE_CLARO if tendencia else ColorSqueeze.ROJO_OSCURO
        if p.get("gatillo_giro"):
            if not (h1.sqz_color is objetivo and h1.sqz_color_prev is not objetivo):
                return _NADA
        elif h1.sqz_color is not objetivo:
            return _NADA

    # Volumen relativo: confirmación de interés real (volumen por encima de su media).
    if p.get("usar_volumen"):
        if not _num_ok(h4.volumen_rel) or h4.volumen_rel < p.get("vol_factor", 1.0):
            return _NADA

    # RSI (1H): para longs, no entrar sobrecomprado.
    if p.get("usar_rsi"):
        if not _num_ok(h1.rsi) or h1.rsi > p.get("rsi_umbral", 50):
            return _NADA

    # Posición vs EMA55 de 4H: precio cerca de la "media imán" (soporte dinámico).
    if p.get("usar_ema55"):
        if not _num_ok(h4.ema_lenta) or abs(estado.precio - h4.ema_lenta) / h4.ema_lenta > p.get("prox_ema55", 0.02):
            return _NADA

    if p.get("usar_bloqueo", True) and en_bloqueo_horario(estado.timestamp):
        return _NADA
    if not _num_ok(h4.swing_min):
        return _NADA
    return Decision(Accion.ABRIR_LARGO, "experimento", stop_loss=h4.swing_min * (1 - 0.003))


def _hacer_cerebro(p: dict):
    salida = p.get("salida", "agotamiento_impulso")

    def cerebro(estado: EstadoMercado, posicion: Posicion | None) -> Decision:
        if posicion is not None:
            return _gestionar_largo(estado, posicion, salida)
        return _entrada(estado, p)
    return cerebro


def _entrada_corto(estado: EstadoMercado, p: dict) -> Decision:
    """Entrada SHORT parametrizable (para ablación). Espejo de _entrada. Nunca BTC."""
    if estado.simbolo == CONFIG.btc:
        return _NADA
    d, h4, h1 = estado.diario, estado.h4, estado.h1

    if p["semaforo"] == "ema_cross":
        if not (d.ema_rapida < d.ema_lenta):       # activo débil = diario bajista
            return _NADA

    if p.get("usar_poc"):
        if not _num_ok(h4.poc) or abs(estado.precio - h4.poc) / h4.poc > p["proximidad"]:
            return _NADA

    if p.get("usar_squeeze4h"):
        if h4.sqz_color is not ColorSqueeze.VERDE_OSCURO:    # giro bajista
            return _NADA

    if p.get("usar_adx"):
        if not _num_ok(h4.adx_pendiente):
            return _NADA
        signo = p.get("adx_signo", "pos")
        if signo == "pos" and not (h4.adx_pendiente > 0):
            return _NADA
        if signo == "neg" and not (h4.adx_pendiente < 0):
            return _NADA

    if p.get("usar_gatillo1h"):
        if h1.sqz_color is not ColorSqueeze.VERDE_OSCURO:
            return _NADA

    if en_bloqueo_horario(estado.timestamp):
        return _NADA
    if not _num_ok(h4.swing_max):
        return _NADA
    return Decision(Accion.ABRIR_CORTO, "exp short", stop_loss=h4.swing_max * (1 + 0.003))


def _hacer_cerebro_corto(p: dict):
    salida = p.get("salida", "agotamiento_impulso")

    def cerebro(estado: EstadoMercado, posicion: Posicion | None) -> Decision:
        if posicion is not None:
            return _gestionar_corto(estado, posicion, salida)
        return _entrada_corto(estado, p)
    return cerebro


def _hacer_cerebro_combinado(p_long: dict, p_short: dict):
    """Combinado: largo si el diario del activo es alcista, corto si bajista (configs distintas)."""
    sl_l = p_long.get("salida", "agotamiento_impulso")
    sl_s = p_short.get("salida", "agotamiento_impulso")

    def cerebro(estado: EstadoMercado, posicion: Posicion | None) -> Decision:
        if posicion is not None:
            if posicion.lado is Lado.LARGO:
                return _gestionar_largo(estado, posicion, sl_l)
            return _gestionar_corto(estado, posicion, sl_s)
        if estado.diario.ema_rapida > estado.diario.ema_lenta:
            return _entrada(estado, p_long)
        return _entrada_corto(estado, p_short)
    return cerebro


def _rent(curva: pd.Series, ini=None, fin=None) -> float:
    c = curva.loc[ini:fin] if (ini or fin) else curva
    return (c.iloc[-1] / c.iloc[0] - 1) if len(c) > 1 else 0.0


_BASE = dict(semaforo="ema_cross", usar_poc=True, proximidad=0.015, usar_squeeze4h=True, usar_gatillo1h=True)

VARIANTES = [
    ("base: ADX pend. NEG",      {**_BASE, "usar_adx": True, "adx_signo": "neg"}),
    ("sin filtro ADX",           {**_BASE, "usar_adx": False}),
    ("ADX pend. POSITIVA",       {**_BASE, "usar_adx": True, "adx_signo": "pos"}),
    ("ADX nivel >23",            {**_BASE, "usar_adx_nivel": True, "adx_nivel_mayor": True, "adx_umbral": 23}),
    ("ADX nivel <23",            {**_BASE, "usar_adx_nivel": True, "adx_nivel_mayor": False, "adx_umbral": 23}),
    ("sin ADX, POC 1.0%",        {**_BASE, "proximidad": 0.010, "usar_adx": False}),
    ("sin ADX, POC 2.5%",        {**_BASE, "proximidad": 0.025, "usar_adx": False}),
    ("sin ADX + nivel>23",       {**_BASE, "usar_adx": False, "usar_adx_nivel": True, "adx_nivel_mayor": True, "adx_umbral": 23}),
]


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    datos = preparar("BTC")
    h1 = datos["h1"]
    bh = h1["cierre"].iloc[-1] / h1["cierre"].iloc[0] - 1
    print(f"Referencia comprar-y-mantener BTC: total {bh*100:+.1f}%\n")
    print(f"  {'variante':<26} | {'TOTAL':>8} | {'train 21-23':>11} | {'TEST 24-25':>11} | {'ops':>4}")
    print("  " + "-" * 74)

    for nombre, p in VARIANTES:
        r = correr("BTC", "btc_longs", 10000, 1.0, datos=datos, cerebro=_hacer_cerebro(p))
        c = r["curva"]
        total = _rent(c)
        train = _rent(c, fin=_CORTE)
        test = _rent(c.loc[_CORTE:])
        robusto = "  <-- gana en ambos" if (train > 0 and test > 0) else ""
        print(f"  {nombre:<26} | {total*100:>7.2f}% | {train*100:>10.2f}% | {test*100:>10.2f}% | {len(r['operaciones']):>4}{robusto}")


if __name__ == "__main__":
    main()
