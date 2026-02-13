#!/bin/bash
# run_all.sh — Ejecuta los 3 experimentos de benchmark y genera gráficas
# Uso: bash run_all.sh
# Requiere: docker y/o podman instalados, Python 3 con matplotlib para gráficas
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p results

echo "============================================"
echo "  Benchmarks de Contenedores"
echo "  4 Experimentos: LAUNCH + CAPACITY + RUNNING + NESTED"
echo "============================================"
echo ""

# Verificar qué runtimes están disponibles
echo "Runtimes disponibles:"
if command -v docker &>/dev/null; then
    echo "  ✓ Docker $(docker --version 2>/dev/null | head -1)"
else
    echo "  ✗ Docker no encontrado"
fi
if command -v podman &>/dev/null; then
    echo "  ✓ Podman $(podman --version 2>/dev/null | head -1)"
else
    echo "  ✗ Podman no encontrado"
fi
echo ""

# Ejecutar cada benchmark
BENCHMARKS=(
    "bench_startup.sh:Exp 1 — Startup Latency (LAUNCH cost)"
    "bench_scale.sh:Exp 2 — Resource Footprint at Scale (LAUNCH + CAPACITY)"
    "bench_runtime.sh:Exp 3 — Runtime Overhead (RUNNING cost)"
    "exp4_nested.sh:Exp 4 — Nested Container Performance"
)

for entry in "${BENCHMARKS[@]}"; do
    script="${entry%%:*}"
    name="${entry##*:}"

    echo "--------------------------------------------"
    echo "  $name"
    echo "  ($script)"
    echo "--------------------------------------------"

    if [ -f "$script" ]; then
        bash "$script" || echo "⚠ $script terminó con errores (continuando...)"
    else
        echo "⚠ $script no encontrado, saltando"
    fi
    echo ""
done

echo "============================================"
echo "  Todos los benchmarks completados"
echo "============================================"
echo ""

# Generar gráficas si Python y matplotlib están disponibles
if command -v python3 &>/dev/null; then
    if python3 -c "import matplotlib" 2>/dev/null; then
        echo "Generando gráficas con analyze.py..."
        python3 analyze.py
        echo ""
        echo "Gráficas generadas en results/ e images/"
    else
        echo "matplotlib no encontrado. Para generar gráficas:"
        echo "  pip install -r requirements.txt"
        echo "  python3 analyze.py"
    fi
else
    echo "Python 3 no encontrado. Para generar gráficas instala Python y matplotlib."
fi

echo ""
echo "Resultados CSV en: $SCRIPT_DIR/results/"
ls -la results/exp*.csv 2>/dev/null || echo "(no se generaron CSVs)"
