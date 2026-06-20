"""
El cerebro de la estrategia (🟦 método de Merino).

Función PURA: recibe el estado del mercado (las 4 temporalidades ya calculadas) y la
posición actual, y devuelve una Decisión. No conoce el mundo (backtest o real): solo
decide. El motor es quien ejecuta.

De momento implementa el módulo **BTC solo-Longs** (lo primero que backtesteamos, 5a).
Los Shorts de altcoins (5b) y las otras reglas de salida se añaden en su fase.
"""

from __future__ import annotations

from trading_latino.config import CONFIG
from trading_latino.domain.types import (
    Accion,
    ColorSqueeze,
    Decision,
    EstadoMercado,
    Lado,
    Posicion,
)
from trading_latino.risk.manager import (
    break_even_neto,
    en_bloqueo_horario,
    semaforo_diario,
)

_NADA = Decision(Accion.NADA, "sin cambios")


def decidir(estado: EstadoMercado, posicion: Posicion | None, modo: str | None = None,
            regla_salida: str | None = None) -> Decision:
    """Decide qué hacer con `estado` dada la `posicion` actual (o None).

    `regla_salida` permite forzar una regla concreta (para comparar en el backtest); si es
    None se usa la de la configuración.
    """
    modo = modo or CONFIG.backtest.MODO
    regla_salida = regla_salida or CONFIG.estrategia.REGLA_SALIDA
    if modo == "btc_longs":
        return _gestionar_largo(estado, posicion, regla_salida) if posicion else _entrada_largo(estado)
    if modo == "alt_shorts":
        raise NotImplementedError("El módulo de alt-shorts (5b) se implementa más adelante.")
    if modo == "combinado":
        raise NotImplementedError("El módulo combinado (5c) se implementa tras validar 5a y 5b.")
    raise ValueError(f"Modo de backtest desconocido: {modo}")


# ───────────────────────── Entrada (Long) ─────────────────────────
def _entrada_largo(estado: EstadoMercado) -> Decision:
    """Patrón de compra de Trading Latino. Todas las condiciones deben cumplirse."""
    e = CONFIG.estrategia

    # 1) Semáforo diario de BTC alcista (EMA10 > EMA55 diaria).
    if semaforo_diario(estado.diario.ema_rapida, estado.diario.ema_lenta) != "alcista":
        return Decision(Accion.NADA, "semáforo diario bajista: no se buscan Longs")

    # 2) 4H: el precio ha corregido a una zona de soporte de volumen (cerca del POC).
    poc4 = estado.h4.poc
    if poc4 is None or abs(estado.precio - poc4) / poc4 > e.PROXIMIDAD_POC:
        return Decision(Accion.NADA, "precio fuera de la zona de soporte (POC 4H)")

    # 3) 4H: giro alcista del Squeeze (rojo oscuro = se agota la bajada).
    if estado.h4.sqz_color is not ColorSqueeze.ROJO_OSCURO:
        return Decision(Accion.NADA, "Squeeze 4H no confirma giro alcista (no es rojo oscuro)")

    # 4) 4H: ADX con pendiente POSITIVA (el impulso de fondo se reactiva en el retroceso).
    #    [Corregido 2026-06-19] Antes exigíamos pendiente NEGATIVA y rompía la robustez
    #    fuera de muestra (ver lessons-learned y docs/RIESGOS_RENTABILIDAD.md).
    if estado.h4.adx_pendiente <= 0:
        return Decision(Accion.NADA, "ADX 4H sin pendiente positiva")

    # 5) Gatillo 1H: el monitor de 1H completa su corrección menor (rojo oscuro).
    if estado.h1.sqz_color is not ColorSqueeze.ROJO_OSCURO:
        return Decision(Accion.NADA, "gatillo 1H no confirma (Squeeze 1H no es rojo oscuro)")

    # 6) Filtro horario (apertura de Nueva York).
    if en_bloqueo_horario(estado.timestamp):
        return Decision(Accion.NADA, "ventana de bloqueo horario (15:15-15:45 Madrid)")

    # 7) Stop estructural: bajo el mínimo reciente de 4H, con holgura.
    if estado.h4.swing_min is None:
        return Decision(Accion.NADA, "sin mínimo estructural para colocar el stop")
    stop = estado.h4.swing_min * (1 - 0.003)

    return Decision(
        Accion.ABRIR_LARGO,
        "patrón Trading Latino confirmado (semáforo + POC 4H + Squeeze rojo oscuro + ADX bajando + gatillo 1H)",
        stop_loss=stop,
    )


# ───────────────────────── Gestión de la posición (Long) ─────────────────────────
def _gestionar_largo(estado: EstadoMercado, posicion: Posicion, regla_salida: str) -> Decision:
    """Mientras hay un Long abierto: salida, guillotina y break-even."""
    e = CONFIG.estrategia
    r = CONFIG.riesgo

    # 1) Salida en beneficio (según la regla elegida).
    salida = _salida(estado, posicion, regla_salida)
    if salida is not None:
        return salida

    # 2) Guillotina del tiempo: tiempo agotado y precio plano.
    if posicion.velas_4h_transcurridas >= r.GUILLOTINA_VELAS_4H_MAX:
        plano = abs(estado.precio - posicion.precio_entrada) / posicion.precio_entrada <= e.GUILLOTINA_PLANITUD
        if plano:
            return Decision(Accion.CERRAR, "guillotina del tiempo: ciclo agotado y precio plano")

    # 3) Break-even neto: tras una vela de 4H ganadora, mover el SL al break-even real.
    if not posicion.break_even_aplicado and posicion.velas_4h_transcurridas >= r.BREAKEVEN_VELAS_4H:
        if estado.precio > posicion.precio_entrada:
            be = break_even_neto(posicion.precio_entrada, Lado.LARGO)
            return Decision(Accion.MOVER_BREAKEVEN, "break-even neto tras vela de 4H ganadora", stop_loss=be)

    return _NADA


def _salida(estado: EstadoMercado, posicion: Posicion, regla: str) -> Decision | None:
    """Despacha la regla de salida. Devuelve Decision(CERRAR) o None. (Para Longs.)"""
    e = CONFIG.estrategia

    if regla == "agotamiento_impulso":
        # El impulso alcista se agota cuando el Squeeze de 4H pasa a verde oscuro.
        if estado.h4.sqz_color is ColorSqueeze.VERDE_OSCURO:
            return Decision(Accion.CERRAR, "agotamiento del impulso: Squeeze 4H giró a verde oscuro")
        return None

    if regla == "trailing":
        # Salir si el precio retrocede X% desde el máximo alcanzado a favor.
        if posicion.max_favorable is not None:
            if estado.precio <= posicion.max_favorable * (1 - e.TRAILING_RETROCESO):
                return Decision(Accion.CERRAR, f"trailing: retroceso {e.TRAILING_RETROCESO*100:.0f}% desde el máximo")
        return None

    if regla == "siguiente_poc":
        # Tomar beneficio al llegar a la resistencia más cercana (swing alto de 4H).
        objetivo = estado.h4.swing_max
        if objetivo is not None and estado.precio >= objetivo:
            return Decision(Accion.CERRAR, "llegó a la resistencia (muralla de volumen / swing alto 4H)")
        return None

    if regla == "multiplo_r":
        # Objetivo = N veces el riesgo inicial (entrada - stop inicial).
        if posicion.stop_inicial is not None:
            objetivo = posicion.precio_entrada + e.MULTIPLO_R * (posicion.precio_entrada - posicion.stop_inicial)
            if estado.precio >= objetivo:
                return Decision(Accion.CERRAR, f"objetivo {e.MULTIPLO_R:.0f}R alcanzado")
        return None

    if regla == "ciclo_1h":
        # Operar el ciclo de 1H: cerrar cuando el Squeeze de 1H se agota al alza
        # (pasa a verde oscuro = techo del micro-impulso). Permite varias operaciones
        # dentro de una misma tendencia de 4H.
        if estado.h1.sqz_color is ColorSqueeze.VERDE_OSCURO:
            return Decision(Accion.CERRAR, "ciclo 1H agotado: Squeeze 1H giró a verde oscuro")
        return None

    raise ValueError(f"Regla de salida desconocida: {regla}")
