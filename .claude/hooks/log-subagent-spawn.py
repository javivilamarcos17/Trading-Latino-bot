#!/usr/bin/env python3
"""
log-subagent-spawn.py — Registra cuándo Claude lanza un subagente.
Proporciona trazabilidad de qué agente especialista hizo qué.
(Patrón tomado de Rialsa Innovation Hub)
"""
import json
import os
import sys
from datetime import datetime, timezone

LOG_PATH = ".claude/audit/subagent-spawns.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

try:
    payload = json.load(sys.stdin)
    agent_name = payload.get("subagent_type", "unknown")
    prompt_preview = str(payload.get("prompt", ""))[:120].replace("\n", " ")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{ts} | SPAWN | {agent_name} | {prompt_preview}\n")

except Exception:
    pass  # Nunca fallar silenciosamente en hooks

sys.exit(0)
