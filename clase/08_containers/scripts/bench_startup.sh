#!/bin/bash
# bench_startup.sh — Mide latencia de arranque de contenedores
# Uso: bash bench_startup.sh [repeticiones]
# Salida: results/startup.csv
set -e

REPS=${1:-10}
OUTFILE="results/startup.csv"
mkdir -p results

echo "runtime,metric,value" > "$OUTFILE"

echo "=== Startup Latency ($REPS repeticiones) ==="

# Bare metal
echo "Midiendo bare metal..."
for i in $(seq 1 "$REPS"); do
    start_ns=$(date +%s%N)
    echo ok > /dev/null
    end_ns=$(date +%s%N)
    ms=$(echo "scale=1; ($end_ns - $start_ns) / 1000000" | bc)
    echo "bare,startup_ms,$ms" >> "$OUTFILE"
done
echo "  bare metal: listo"

# Docker
if command -v docker &>/dev/null; then
    echo "Midiendo Docker..."
    docker pull -q ubuntu > /dev/null 2>&1 || true
    # Warm-up run (primera ejecución siempre es más lenta)
    docker run --rm ubuntu echo ok > /dev/null 2>&1
    for i in $(seq 1 "$REPS"); do
        start_ns=$(date +%s%N)
        docker run --rm ubuntu echo ok > /dev/null 2>&1
        end_ns=$(date +%s%N)
        ms=$(echo "scale=1; ($end_ns - $start_ns) / 1000000" | bc)
        echo "docker,startup_ms,$ms" >> "$OUTFILE"
    done
    echo "  docker: listo"
else
    echo "  docker: no disponible, saltando"
fi

# Podman
if command -v podman &>/dev/null; then
    echo "Midiendo Podman..."
    podman pull -q ubuntu > /dev/null 2>&1 || podman pull -q docker.io/library/ubuntu > /dev/null 2>&1 || true
    # Warm-up run
    podman run --rm ubuntu echo ok > /dev/null 2>&1
    for i in $(seq 1 "$REPS"); do
        start_ns=$(date +%s%N)
        podman run --rm ubuntu echo ok > /dev/null 2>&1
        end_ns=$(date +%s%N)
        ms=$(echo "scale=1; ($end_ns - $start_ns) / 1000000" | bc)
        echo "podman,startup_ms,$ms" >> "$OUTFILE"
    done
    echo "  podman: listo"
else
    echo "  podman: no disponible, saltando"
fi

echo "Resultados guardados en $OUTFILE"
