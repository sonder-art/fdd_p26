#!/bin/bash
# bench_scale.sh — Mide escalamiento: tiempo y memoria al lanzar muchos contenedores
# Uso: bash bench_scale.sh
# Salida: results/scale.csv
set -e

OUTFILE="results/scale.csv"
mkdir -p results

COUNTS=(10 20 50)

echo "runtime,count,time_seconds,memory_mb" > "$OUTFILE"

get_used_mb() {
    free -m | awk '/^Mem:/ {print $3}'
}

cleanup_containers() {
    local runtime=$1
    local prefix=$2
    local ids
    ids=$($runtime ps -aq --filter "name=$prefix" 2>/dev/null || true)
    if [ -n "$ids" ]; then
        $runtime stop $ids > /dev/null 2>&1 || true
        $runtime rm $ids > /dev/null 2>&1 || true
    fi
}

echo "=== Scaling Benchmark ==="

for runtime in docker podman; do
    if ! command -v "$runtime" &>/dev/null; then
        echo "$runtime: no disponible, saltando"
        continue
    fi

    echo "Midiendo $runtime..."
    $runtime pull -q ubuntu > /dev/null 2>&1 || $runtime pull -q docker.io/library/ubuntu > /dev/null 2>&1 || true

    for count in "${COUNTS[@]}"; do
        prefix="scale_${runtime}_${count}"

        # Asegurar limpieza previa
        cleanup_containers "$runtime" "$prefix"
        sleep 1

        pre_mem=$(get_used_mb)
        start_ns=$(date +%s%N)

        for i in $(seq 1 "$count"); do
            $runtime run -d --name "${prefix}_${i}" ubuntu sleep 300 > /dev/null 2>&1
        done

        end_ns=$(date +%s%N)
        sleep 2
        post_mem=$(get_used_mb)

        elapsed=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        mem_used=$((post_mem - pre_mem))

        echo "${runtime},${count},${elapsed},${mem_used}" >> "$OUTFILE"
        echo "  ${count} contenedores: ${elapsed}s, +${mem_used} MB"

        # Cleanup
        cleanup_containers "$runtime" "$prefix"
        sleep 2
    done
done

echo "Resultados guardados en $OUTFILE"
