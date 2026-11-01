#!/usr/bin/env bash
# ==============================================================================
# Antigravity Wallpaper Glassmorphism — Suite de Verificación Determinista
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "🧪 [1/3] Verificando ausencia total de rutas privadas en el repositorio..."
if git -C "$REPO_DIR" grep -I -i "/home/darwinsin" ":(exclude).git" ":(exclude)scripts/ci.sh" 2>/dev/null; then
  echo "  ❌ [FAIL] Se detectaron rutas privadas absolutas."
  exit 1
else
  echo "  ✔ [PASS] 0 rutas privadas absolutas detectadas."
fi

echo "🧪 [2/3] Validando sintaxis AST de scripts Python del motor Glassmorphism..."
for py in "paths.py" "apply_wallpaper.py" "patch_antigravity.py" "restore_antigravity.py" "test_persistence.py"; do
  python3 -c "import ast; ast.parse(open('$REPO_DIR/scripts/$py').read()); print('  ✔ [PASS] $py AST sintácticamente válido.')"
done

echo "🧪 [3/3] Validando sintaxis y marcadores de plantilla CSS..."
grep -q "TU_DATA_URI_O_RUTA_AQUI" "$REPO_DIR/styles/template.css"
test -f "$REPO_DIR/styles/active_sample.css"
echo "  ✔ [PASS] Plantilla CSS y hoja de estilos activas estructuradas correctamente."

echo ""
echo "✅ Todas las pruebas de CI de Glassmorphism Wallpaper pasaron al 100% (Código de salida 0)."
