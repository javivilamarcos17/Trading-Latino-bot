#!/bin/bash
# PostToolUse.sh — Se ejecuta DESPUÉS de cada herramienta
# Actualmente solo registra auditoría básica. Ampliar según necesidades del proyecto.

TOOL="$CLAUDE_TOOL_NAME"

# Registrar uso de herramientas de escritura en audit log
if [[ "$TOOL" == "Write" || "$TOOL" == "Edit" ]]; then
  AUDIT_DIR=".claude/audit"
  mkdir -p "$AUDIT_DIR"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | $TOOL | $CLAUDE_TOOL_INPUT" >> "$AUDIT_DIR/edits.log" 2>/dev/null
fi

exit 0
