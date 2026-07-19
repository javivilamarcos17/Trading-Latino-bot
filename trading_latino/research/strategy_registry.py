"""
REGISTRO CANÓNICO DE ESTRATEGIAS — única fuente de verdad de identidad (2026-07-19).

Nace del bug tr/abt: el funding falló porque los joins se hacían por strings libres ("tr" vs
"trend_rider"). A partir de ahora TODO merge/atribución de PnL se resuelve por strategy_id
canónico o vía resolve(alias). Nunca por string libre.

Uso:
    from trading_latino.research.strategy_registry import resolve, canonical, validar
    resolve("tr")            -> "trend_rider"
    canonical("abt")         -> {"id": "STRAT-DAILY-ABT", "name": "atr_break_trend", ...}
    validar([...aliases...]) -> lanza si hay alias desconocido o canónico duplicado
"""
from __future__ import annotations

# Cada entrada: id único, nombre canónico, aliases (todas las formas vistas en el código/datos),
# horizonte típico y su COST PROFILE (enemigo económico principal — lección del funding 2026-07-19).
REGISTRO = [
    {"id": "STRAT-DAILY-TR",      "name": "trend_rider",     "aliases": ["tr", "trend_rider", "trend_rider_f"],
     "horizonte": "1D (~66d hold)", "cost_driver": "funding/holding", "estado": "validado"},
    {"id": "STRAT-DAILY-ABT",     "name": "atr_break_trend", "aliases": ["abt", "atr_break_trend", "atr_breakout"],
     "horizonte": "1D (~66d hold)", "cost_driver": "funding/holding", "estado": "validado"},
    {"id": "STRAT-CYCLE-TURTLE",  "name": "turtle_ciclo",    "aliases": ["turtle", "turtle_ciclo"],
     "horizonte": "1D ciclo (~78d hold)", "cost_driver": "funding/holding + concentración episódica", "estado": "validado (inflado-pero-real)"},
    {"id": "STRAT-CYCLE-PLANBTC", "name": "planbtc",         "aliases": ["planbtc", "plan_btc"],
     "horizonte": "1D ciclo", "cost_driver": "funding/holding", "estado": "arma de ciclo (en guardia)"},
    {"id": "STRAT-4H-ICHIMOKU",   "name": "ichimoku",        "aliases": ["ichimoku"],
     "horizonte": "4H (~4d hold)", "cost_driver": "fees/slippage (funding bajo, 6%)", "estado": "desplegada ETH/SOL"},
    {"id": "STRAT-CARRY",         "name": "carry",           "aliases": ["carry", "carry_pro"],
     "horizonte": "días/semanas", "cost_driver": "tail/event/exchange risk", "estado": "dormido (motor 3)"},
    {"id": "STRAT-15M-OBASIA",    "name": "ob_asia",         "aliases": ["ob_asia", "ob_regime_asia", "fvg_ob_asia",
        "ob_asia_close", "ob_plus_asia", "ob_plus_asia_r3", "ob_trend_r3"],
     "horizonte": "15m", "cost_driver": "fees/slippage", "estado": "FALSIFICADO (holdout 2018) — experimento forward"},
]

_ALIAS = {}
for _e in REGISTRO:
    for _a in _e["aliases"]:
        _ALIAS[_a.lower()] = _e


def canonical(alias: str) -> dict:
    """Devuelve la entrada canónica de un alias. Lanza KeyError si es desconocido (nunca silencioso)."""
    e = _ALIAS.get(str(alias).lower())
    if e is None:
        raise KeyError(f"estrategia desconocida: {alias!r} — añádela al REGISTRO antes de usarla")
    return e


def resolve(alias: str) -> str:
    """alias -> nombre canónico."""
    return canonical(alias)["name"]


def resolve_id(alias: str) -> str:
    """alias -> strategy_id (para joins)."""
    return canonical(alias)["id"]


def validar(aliases) -> None:
    """Chequeo de integridad para runners: 0 aliases desconocidos, 0 canónicos duplicados."""
    desconocidos = [a for a in set(aliases) if str(a).lower() not in _ALIAS]
    if desconocidos:
        raise ValueError(f"aliases desconocidos (join silencioso evitado): {desconocidos}")
    nombres = [e["name"] for e in REGISTRO]
    dups = {n for n in nombres if nombres.count(n) > 1}
    if dups:
        raise ValueError(f"nombres canónicos duplicados en el REGISTRO: {dups}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    validar([a for e in REGISTRO for a in e["aliases"]])
    print(f"REGISTRO OK — {len(REGISTRO)} estrategias, {len(_ALIAS)} aliases, sin duplicados.")
    print(f"  ejemplo: resolve('tr')={resolve('tr')} · resolve('abt')={resolve('abt')} · resolve_id('tr')={resolve_id('tr')}")
    for e in REGISTRO:
        print(f"  {e['id']:<20} {e['name']:<16} aliases={e['aliases']}")
