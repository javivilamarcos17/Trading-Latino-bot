#!/bin/bash
# Stop.sh — Se ejecuta al finalizar una sesión de Claude Code
# Recuerda registrar lecciones si hubo correcciones

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Fin de sesión"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  Antes de cerrar, comprueba:"
echo "  ✓ ¿Hubo correcciones en esta sesión? → Registra la lección"
echo "    /nueva-leccion"
echo ""
echo "  ✓ ¿Hay cambios sin commitear?"
git status --short 2>/dev/null | head -5 | sed 's/^/    /'
echo ""
echo "  ✓ ¿Hay decisiones nuevas que añadir a SYSTEM_VISION.md?"
echo ""
echo "═══════════════════════════════════════════════════════════════"
