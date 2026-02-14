#!/bin/bash
# bench_startup.sh — Mide latencia de arranque de contenedores (LAUNCH cost)
# Prueba: Docker vs Podman x Ubuntu vs Alpine + bare metal baseline
# Uso: bash bench_startup.sh [repeticiones]
# Salida: results/exp1_startup.csv
set -e

REPS=${1:-10}
OUTFILE="results/exp1_startup.csv"
mkdir -p results

echo "runtime,image,rep,startup_ms" > "$OUTFILE"

echo "=== Exp 1: Startup Latency ($REPS reps + 1 warm-up) ==="

# --- Bare metal baseline ---
echo "Midiendo bare metal..."
# Warm-up (descartado)
echo ok > /dev/null
for i in $(seq 1 "$REPS"); do
    start_ns=$(date +%s%N)
    echo ok > /dev/null
    end_ns=$(date +%s%N)
    ms=$(echo "scale=2; ($end_ns - $start_ns) / 1000000" | bc)
    echo "bare,none,$i,$ms" >> "$OUTFILE"
done
echo "  bare metal: listo"

# --- Docker ---
if command -v docker &>/dev/null; then
    for image in ubuntu alpine; do
        echo "Midiendo Docker + $image..."
        docker pull -q "$image" > /dev/null 2>&1 || true
        # Warm-up (descartado)
        docker run --rm "$image" echo ok > /dev/null 2>&1
        for i in $(seq 1 "$REPS"); do
            start_ns=$(date +%s%N)
            docker run --rm "$image" echo ok > /dev/null 2>&1
            end_ns=$(date +%s%N)
            ms=$(echo "scale=2; ($end_ns - $start_ns) / 1000000" | bc)
            echo "docker,$image,$i,$ms" >> "$OUTFILE"
        done
        echo "  docker/$image: listo"
    done
else
    echo "  docker: no disponible, saltando"
fi

# --- Podman ---
if command -v podman &>/dev/null; then
    for image in ubuntu alpine; do
        echo "Midiendo Podman + $image..."
        podman pull -q "$image" > /dev/null 2>&1 \
            || podman pull -q "docker.io/library/$image" > /dev/null 2>&1 || true
        # Warm-up (descartado)
        podman run --rm "$image" echo ok > /dev/null 2>&1
        for i in $(seq 1 "$REPS"); do
            start_ns=$(date +%s%N)
            podman run --rm "$image" echo ok > /dev/null 2>&1
            end_ns=$(date +%s%N)
            ms=$(echo "scale=2; ($end_ns - $start_ns) / 1000000" | bc)
            echo "podman,$image,$i,$ms" >> "$OUTFILE"
        done
        echo "  podman/$image: listo"
    done
else
    echo "  podman: no disponible, saltando"
fi

echo "Resultados guardados en $OUTFILE"
