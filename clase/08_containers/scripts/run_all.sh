#!/bin/bash
# run_all.sh — Ejecuta todos los benchmarks y genera gráficas
# Uso: bash run_all.sh
# Requiere: docker y/o podman instalados, Python 3 con matplotlib para gráficas
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p results

echo "============================================"
echo "  Benchmarks de Contenedores"
echo "  Docker vs Podman vs Bare Metal"
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
    "bench_startup.sh:Startup Latency"
    "bench_memory.sh:Memory Consumption"
    "bench_cpu.sh:CPU Overhead"
    "bench_io.sh:Disk I/O"
    "bench_nested.sh:Nested Containers"
    "bench_scale.sh:Scaling"
    "bench_cpu_exec.sh:CPU Puro (exec)"
    "bench_memory_cgroup.sh:Memory Cgroup"
    "bench_nested_v2.sh:Nested Containers v2"
)

for entry in "${BENCHMARKS[@]}"; do
    script="${entry%%:*}"
    name="${entry##*:}"

    echo "--------------------------------------------"
    echo "  $name ($script)"
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
        echo "Gráficas generadas en results/"
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
ls -la results/*.csv 2>/dev/null || echo "(no se generaron CSVs)"
