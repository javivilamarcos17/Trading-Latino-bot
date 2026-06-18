#!/bin/bash
# SessionStart.sh — Se ejecuta automáticamente al abrir una sesión de Claude Code
# Muestra el estado actual del proyecto para que Claude arranque con contexto

echo "═══════════════════════════════════════════════════════════════"
echo "  PROYECTO — Estado al iniciar sesión"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Rama actual
BRANCH=$(git branch --show-current 2>/dev/null || echo "sin-git")
echo "📍 Rama actual: $BRANCH"
echo ""

# Últimos commits
echo "📝 Últimos 3 commits:"
git log --oneline -3 2>/dev/null | sed 's/^/   /' || echo "   (sin historial)"
echo ""

# Archivos modificados
CHANGED=$(git status --short 2>/dev/null | wc -l | tr -d ' ')
if [ "$CHANGED" -gt "0" ]; then
  echo "⚠️  Archivos modificados sin commitear: $CHANGED"
  git status --short 2>/dev/null | head -5 | sed 's/^/    /'
  if [ "$CHANGED" -gt "5" ]; then
    echo "   ... y $((CHANGED - 5)) más"
  fi
else
  echo "✅ Todo commiteado — rama limpia"
fi
echo ""

# Lecciones aprendidas
LOG=".claude/skills/lessons-learned/log.md"
if [ -f "$LOG" ]; then
  COUNT=$(grep -c "^## " "$LOG" 2>/dev/null || echo "0")
  echo "🧠 Lecciones aprendidas registradas: $COUNT"
  echo ""
  echo "   Última lección:"
  grep "^## " "$LOG" 2>/dev/null | tail -1 | sed 's/^/   /'
else
  echo "🧠 Sin lecciones registradas aún"
fi
echo ""

# Estado real del proyecto (PROJECT_STATUS.md)
STATUS="PROJECT_STATUS.md"
if [ -f "$STATUS" ]; then
  # Solo dentro de la sección "1. Estado actual" (hasta la siguiente cabecera "## "),
  # para no coger casillas marcadas de otras secciones (ej. nivel de confianza).
  # Acepta tanto [X] como [x].
  ETAPA=$(awk '/^## 1\./{f=1;next} /^## /{f=0} f' "$STATUS" 2>/dev/null \
    | grep -E '^- \[[Xx]\] ' | head -1 | sed -E 's/^- \[[Xx]\] //')
  if [ -n "$ETAPA" ]; then
    echo "📊 Estado del proyecto: $ETAPA"
  else
    echo "📊 PROJECT_STATUS.md existe — revisa la etapa actual"
  fi
  echo ""
fi

# Recordatorios
echo "📚 Recordatorios:"
echo "   • Lee SYSTEM_VISION.md y PROJECT_STATUS.md si no lo has hecho ya"
echo "   • Lee lessons-learned/log.md antes de empezar"
echo "   • Pushback antes de ejecutar peticiones subóptimas"
echo "   • Registra lecciones inmediatamente tras correcciones"
echo "   • Actualiza PROJECT_STATUS.md cuando cambie qué funciona; no des falso avance"
echo ""
echo "═══════════════════════════════════════════════════════════════"
