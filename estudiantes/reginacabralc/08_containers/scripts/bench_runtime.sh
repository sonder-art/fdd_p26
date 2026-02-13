#!/bin/bash
# bench_runtime.sh — Mide RUNNING cost (overhead en contenedores ya corriendo)
# Pre-inicia contenedores, luego ejecuta workloads via exec
# Workloads: hash (CPU puro) y sort (CPU + memoria + pipes)
# Uso: bash bench_runtime.sh [repeticiones]
# Salida: results/exp3_runtime.csv
set -e

REPS=${1:-5}
OUTFILE="results/exp3_runtime.csv"
mkdir -p results

echo "runtime,workload,rep,time_s" > "$OUTFILE"

# --- Workload commands ---
# hash: pure CPU integer arithmetic (~0.9s)
HASH_CMD='dd if=/dev/urandom bs=1M count=100 2>/dev/null | sha256sum > /dev/null'
# sort: CPU + memory allocation + pipes (~1.3s)
SORT_CMD='seq 1 1000000 | shuf | sort -n > /dev/null'

run_workload() {
    local cmd="$1"
    local start_ns end_ns
    start_ns=$(date +%s%N)
    bash -c "$cmd" 2>/dev/null
    end_ns=$(date +%s%N)
    echo "scale=4; ($end_ns - $start_ns) / 1000000000" | bc
}

echo "=== Exp 3: Runtime Overhead ($REPS reps + 1 warm-up) ==="

# --- Pre-start containers ---
DOCKER_CONTAINER="exp3_docker"
PODMAN_CONTAINER="exp3_podman"

docker_available=false
podman_available=false

if command -v docker &>/dev/null; then
    echo "Pre-iniciando contenedor Docker..."
    docker rm -f "$DOCKER_CONTAINER" > /dev/null 2>&1 || true
    docker run -d --name "$DOCKER_CONTAINER" ubuntu sleep 3600 > /dev/null 2>&1
    sleep 1
    docker_available=true
fi

if command -v podman &>/dev/null; then
    echo "Pre-iniciando contenedor Podman..."
    podman rm -f "$PODMAN_CONTAINER" > /dev/null 2>&1 || true
    podman run -d --name "$PODMAN_CONTAINER" ubuntu sleep 3600 > /dev/null 2>&1
    sleep 1
    podman_available=true
fi

# --- Run benchmarks ---
for workload_name in hash sort; do
    if [ "$workload_name" = "hash" ]; then
        CMD="$HASH_CMD"
    else
        CMD="$SORT_CMD"
    fi

    echo ""
    echo "--- Workload: $workload_name ---"

    # Bare metal
    echo "  bare metal..."
    # Warm-up
    bash -c "$CMD" 2>/dev/null
    for i in $(seq 1 "$REPS"); do
        t=$(run_workload "$CMD")
        echo "bare,$workload_name,$i,$t" >> "$OUTFILE"
    done

    # Docker exec
    if [ "$docker_available" = true ]; then
        echo "  docker exec..."
        # Warm-up
        docker exec "$DOCKER_CONTAINER" bash -c "$CMD" 2>/dev/null
        for i in $(seq 1 "$REPS"); do
            start_ns=$(date +%s%N)
            docker exec "$DOCKER_CONTAINER" bash -c "$CMD" 2>/dev/null
            end_ns=$(date +%s%N)
            t=$(echo "scale=4; ($end_ns - $start_ns) / 1000000000" | bc)
            echo "docker,$workload_name,$i,$t" >> "$OUTFILE"
        done
    fi

    # Podman exec
    if [ "$podman_available" = true ]; then
        echo "  podman exec..."
        # Warm-up
        podman exec "$PODMAN_CONTAINER" bash -c "$CMD" 2>/dev/null
        for i in $(seq 1 "$REPS"); do
            start_ns=$(date +%s%N)
            podman exec "$PODMAN_CONTAINER" bash -c "$CMD" 2>/dev/null
            end_ns=$(date +%s%N)
            t=$(echo "scale=4; ($end_ns - $start_ns) / 1000000000" | bc)
            echo "podman,$workload_name,$i,$t" >> "$OUTFILE"
        done
    fi
done

# --- Cleanup ---
echo ""
echo "Limpiando contenedores..."
if [ "$docker_available" = true ]; then
    docker rm -f "$DOCKER_CONTAINER" > /dev/null 2>&1 || true
fi
if [ "$podman_available" = true ]; then
    podman rm -f "$PODMAN_CONTAINER" > /dev/null 2>&1 || true
fi

echo "Resultados guardados en $OUTFILE"
