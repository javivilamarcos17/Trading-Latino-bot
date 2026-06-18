#!/usr/bin/env python3
"""
block-subagent-external.py — Impide que los subagentes ejecuten operaciones
externas peligrosas (push, deploy, acciones irreversibles).
Solo el agente principal (Claude en conversación directa con el usuario)
puede ejecutar estas operaciones.
(Patrón tomado de Rialsa Innovation Hub)
"""
import json
import os
import sys

# Operaciones bloqueadas SIEMPRE (ni el agente principal ni subagentes)
ALWAYS_BLOCKED = (
    "DROP DATABASE",
    "TRUNCATE TABLE",
    "rm -rf /",
    "format c:",
)

# Operaciones bloqueadas SOLO para subagentes
SUBAGENT_BLOCKED = (
    "git push",
    "gh pr create",
    "gh pr merge",
    "gh release",
    "deploy.sh",
    "deploy.ps1",
    "npm run deploy",
    "vercel --prod",
    "ALTER DATABASE",
    "DROP TABLE",
)

try:
    payload = json.load(sys.stdin)
    tool = payload.get("tool_name", "")
    tool_input = json.dumps(payload.get("tool_input", {}))
    is_subagent = os.environ.get("CLAUDE_SUBAGENT", "false").lower() == "true"

    # Bloqueos absolutos
    for blocked in ALWAYS_BLOCKED:
        if blocked.lower() in tool_input.lower():
            print(f"🛑 BLOQUEADO SIEMPRE: '{blocked}' — operación destructiva irreversible.")
            sys.exit(1)

    # Bloqueos solo para subagentes
    if is_subagent:
        for blocked in SUBAGENT_BLOCKED:
            if blocked.lower() in tool_input.lower():
                print(f"🛑 BLOQUEADO EN SUBAGENTE: '{blocked}'")
                print("   Los subagentes no pueden ejecutar operaciones externas.")
                print("   El agente principal debe hacerlo con supervisión del usuario.")
                sys.exit(1)

except Exception:
    pass

sys.exit(0)
