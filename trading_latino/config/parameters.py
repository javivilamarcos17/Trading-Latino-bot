"""
Parámetros del bot de Trading Latino — la "biblia" convertida en código.

Cada parámetro lleva una etiqueta de ORIGEN, según el principio de gobierno del proyecto
(ver docs/ESTRATEGIA_TRADING_LATINO.md):

    🟦 NUCLEO  = método de Merino. Sagrado, no se toca.
    🟨 REAL    = realidad técnica neutral (costes, datos). No cambia su método.
    🟥 ADD     = añadido nuestro, OPCIONAL. Desactivado por defecto. No contamina el núcleo.

Backtest y operativa en vivo leen ESTOS mismos valores: una sola fuente de verdad.
"""

from dataclasses import dataclass, field


# ───────────────────────────── Indicadores (🟦 NUCLEO) ─────────────────────────────
@dataclass(frozen=True)
class Indicadores:
    EMA_RAPIDA: int = 10            # 🟦 EMA 10 (inercia a corto)
    EMA_LENTA: int = 55            # 🟦 EMA 55 (tendencia principal / "imán")

    ADX_PERIODO: int = 14          # 🟦 suavizado ADX
    ADX_DI_LONGITUD: int = 14      # 🟦 longitud DI
    ADX_NIVEL_CLAVE: float = 23.0  # 🟦 nivel clave horizontal
    ADX_BARRAS_PENDIENTE: int = 3  # ⚠️ pendiente medida sobre 3 barras (de la versión community Ruckard)

    # Squeeze Momentum (LazyBear)
    BB_LONGITUD: int = 20          # 🟦 Bollinger
    BB_MULT: float = 2.0           # 🟦
    KC_LONGITUD: int = 20          # 🟦 Keltner
    KC_MULT: float = 1.5           # 🟦

    # Perfil de Volumen
    POC_VENTANA_VELAS: int = 100   # 🔎 ventana para calcular el POC (default Ruckard VPVR=100). A validar en directo.


# ───────────────────────────── Temporalidades (🟦 NUCLEO) ─────────────────────────────
@dataclass(frozen=True)
class Temporalidades:
    MACRO: str = "1w"      # 🟦 filtro semanal de BTC (apalancamiento/riesgo)
    SEMAFORO: str = "1d"   # 🟦 semáforo diario de BTC (permiso Long/Short)
    OPERATIVO: str = "4h"  # 🟦 patrón
    GATILLO: str = "1h"    # 🟦 entrada fina


# ───────────────────────────── Gestión de riesgo (🟦 NUCLEO) ─────────────────────────────
@dataclass(frozen=True)
class Riesgo:
    CAPITAL_PARTES: int = 20            # 🟦 capital en 20 partes
    TAMANO_POSICION_PCT: float = 0.05   # 🟦 = 5% del capital por operación, fijo (núcleo Merino)
    INTERES_COMPUESTO: bool = False     # 🟦 interés simple, nunca compuesto

    APALANCAMIENTO_MIN: int = 3         # 🟦 3x-5x
    APALANCAMIENTO_MAX: int = 5         # 🟦
    MARGEN_AISLADO: bool = True         # 🟦 aislado (cruzado prohibido)

    PERMITIR_DCA: bool = False          # 🟦 prohibido promediar a la baja
    SHORT_BTC_PROHIBIDO: bool = True    # 🟦 a Bitcoin jamás se le hace short

    # Break-even: tras 1 vela de 4H ganadora, mover SL al break-even REAL (con costes). Ver §13.
    BREAKEVEN_VELAS_4H: int = 1         # 🟦 (intención de Merino)
    BREAKEVEN_NETO_CON_COSTES: bool = True  # 🟨 el SL de BE cubre comisiones+funding (lo pidió el dueño)

    # Guillotina del tiempo: 6-8 velas de 4H (24-32h) sin avanzar -> cierre a mercado
    GUILLOTINA_VELAS_4H_MIN: int = 6    # 🟦
    GUILLOTINA_VELAS_4H_MAX: int = 8    # 🟦

    # Filtro horario: no abrir entre 15:15 y 15:45 (Madrid) — apertura de Nueva York
    BLOQUEO_HORARIO_INICIO: str = "15:15"   # 🟦
    BLOQUEO_HORARIO_FIN: str = "15:45"      # 🟦
    BLOQUEO_HORARIO_TZ: str = "Europe/Madrid"  # 🟦

    # Bear market estructural (BTC bajo EMA55 semanal) -> reducir Longs a la mitad
    REDUCCION_LONGS_EN_BEAR: float = 0.5    # 🟦


# ───────────────────────────── Costes (🟨 REALIDAD TÉCNICA) ─────────────────────────────
@dataclass(frozen=True)
class Costes:
    # 🔎 Confirmar el esquema de comisiones vigente de Hyperliquid antes de fiarse.
    COMISION_TAKER: float = 0.00045   # 🟨 ~0.045% por lado (órdenes a mercado)
    COMISION_MAKER: float = 0.00015   # 🟨 ~0.015% por lado (órdenes límite)
    SLIPPAGE_ESTIMADO: float = 0.0005 # 🟨 deslizamiento estimado en órdenes a mercado
    FUNDING_CADA_HORAS: int = 1       # 🟨 en Hyperliquid el funding se paga cada hora
    # El funding real por hora se toma del histórico/feed; esto es solo la frecuencia.


# ───────────────────────────── Universo (🟦 lista de vigilancia) ─────────────────────────────
BTC = "BTC"  # 🟦 el rey: solo Longs, nunca short

# 🟦 Lista de vigilancia de altcoins (elegida por criterio profesional, ver §15).
# 🔎 Verificar disponibilidad real en Hyperliquid al conectar.
ALTCOINS = [
    "ETH", "SOL", "BNB", "XRP", "ADA",      # majors / L1 grandes
    "AVAX", "NEAR", "APT", "SUI",            # L1 alternativas
    "ARB", "OP", "POL",                      # L2 / escalado
    "LINK", "UNI", "AAVE",                   # DeFi / oráculos
    "LTC", "BCH",                            # veteranas líquidas
    "DOT",                                   # interoperabilidad
    "TIA",                                   # infra / modular
    "DOGE",                                  # meme líquida
]


# ───────────────────────────── Añadidos OPCIONALES (🟥 ADD) ─────────────────────────────
@dataclass(frozen=True)
class AnadidosOpcionales:
    """Todo aquí está DESACTIVADO por defecto. Solo se activa si el dueño lo aprueba
    y el backtest lo justifica. NUNCA se da por hecho que forma parte del método."""
    USAR_RIESGO_FIJO: bool = False          # 🟥 en vez del 5% fijo de Merino
    RIESGO_FIJO_PCT: float = 0.01           # 🟥 (si se activara)
    FILTRO_ENTRADA_VENTAJA: bool = False    # 🟥 no entrar si objetivo < N x costes
    FILTRO_ENTRADA_RATIO_COSTE: float = 2.0 # 🟥
    USAR_ORDENES_MAKER: bool = False        # 🟥 límite en vez de mercado (Merino entra a mercado)
    TOMA_PARCIAL: bool = False              # 🟥 vender la mitad al entrar en ganancias
    # Cortacircuitos de pérdida: 🟥 a CALIBRAR con el backtest, no a ojo. None = sin tope aún.
    TOPE_PERDIDA_DIARIA: float | None = None
    TOPE_PERDIDA_SEMANAL: float | None = None
    TOPE_PERDIDA_MENSUAL: float | None = None
    # Mejoras de v2 que Merino sí usa:
    USAR_DOMINANCIA: bool = False           # 🟥 USDT.D/BTC.D/TOTAL3 como contexto risk-on/off
    USAR_AREA_VALOR: bool = False           # 🟥 VAH/VAL además del POC


# ───────────────────────────── Backtest (🟨 REALIDAD) ─────────────────────────────
@dataclass(frozen=True)
class Backtest:
    CAPITAL_INICIAL: float = 10_000.0   # 🔎 a confirmar con el dueño
    # 🔎 periodo a confirmar; idealmente cubre alcista y bajista
    FECHA_INICIO: str = "2021-01-01"
    FECHA_FIN: str = "2025-12-31"
    EXCHANGE_DATOS: str = "binance"     # 🟨 fuente de histórico largo (no es donde operamos)


# ───────────────────────────── Configuración global ─────────────────────────────
@dataclass(frozen=True)
class Config:
    indicadores: Indicadores = field(default_factory=Indicadores)
    temporalidades: Temporalidades = field(default_factory=Temporalidades)
    riesgo: Riesgo = field(default_factory=Riesgo)
    costes: Costes = field(default_factory=Costes)
    backtest: Backtest = field(default_factory=Backtest)
    anadidos: AnadidosOpcionales = field(default_factory=AnadidosOpcionales)
    btc: str = BTC
    altcoins: list[str] = field(default_factory=lambda: list(ALTCOINS))


# Instancia por defecto que importa el resto del bot.
CONFIG = Config()
