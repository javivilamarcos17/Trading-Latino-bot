#!/bin/bash
# PreToolUse.sh — Se ejecuta ANTES de cada comando
# Bloquea operaciones peligrosas que no tienen vuelta atrás

TOOL="$CLAUDE_TOOL_NAME"
INPUT="$CLAUDE_TOOL_INPUT"

# ── Comandos absolutamente bloqueados (nadie puede ejecutarlos) ──────────────

ALWAYS_BLOCKED=(
  "DROP DATABASE"
  "DROP TABLE"
  "TRUNCATE TABLE"
  "rm -rf /"
  "rm -rf ~"
  "format c:"
  "git push --force"
  "git reset --hard HEAD~"
  "git clean -fd"
)

for cmd in "${ALWAYS_BLOCKED[@]}"; do
  if echo "$INPUT" | grep -qi "$cmd"; then
    echo "🛑 BLOQUEADO: '$cmd' es una operación destructiva irreversible."
    echo "   Si realmente necesitas esto, pídelo explícitamente y explica por qué."
    exit 1
  fi
done

# ── Archivos sensibles — nunca leer ni editar ────────────────────────────────

SENSITIVE_PATTERNS=(
  "\.env$"
  "\.env\."
  "secrets/"
  "credentials"
  "private_key"
  "\.pem$"
  "\.key$"
)

for pattern in "${SENSITIVE_PATTERNS[@]}"; do
  if echo "$INPUT" | grep -qiE "$pattern"; then
    echo "🔐 BLOQUEADO: Intento de acceder a archivo sensible."
    echo "   Los archivos .env y credenciales nunca se leen ni editan por Claude."
    exit 1
  fi
done

exit 0
