#!/bin/bash
# bench_memory.sh — Mide consumo de memoria de contenedores
# Uso: bash bench_memory.sh
# Salida: results/memory.csv
set -e

OUTFILE="results/memory.csv"
mkdir -p results

echo "runtime,metric,value" > "$OUTFILE"

COUNTS=(1 5 10 20)

get_used_mb() {
    free -m | awk '/^Mem:/ {print $3}'
}

cleanup_containers() {
    local runtime=$1
    local prefix=$2
    for name in $($runtime ps -a --format '{{.Names}}' 2>/dev/null | grep "^${prefix}" || true); do
        $runtime stop "$name" > /dev/null 2>&1 || true
        $runtime rm "$name" > /dev/null 2>&1 || true
    done
}

echo "=== Memory Consumption ==="

baseline=$(get_used_mb)
echo "baseline,used_mb,$baseline" >> "$OUTFILE"
echo "Memoria base: ${baseline} MB"

for runtime in docker podman; do
    if ! command -v "$runtime" &>/dev/null; then
        echo "$runtime: no disponible, saltando"
        continue
    fi

    echo "Midiendo $runtime..."
    $runtime pull -q ubuntu > /dev/null 2>&1 || $runtime pull -q docker.io/library/ubuntu > /dev/null 2>&1 || true

    for count in "${COUNTS[@]}"; do
        # Asegurar limpieza previa
        cleanup_containers "$runtime" "mem_${runtime}"
        sleep 1

        pre_mem=$(get_used_mb)

        for i in $(seq 1 "$count"); do
            $runtime run -d --name "mem_${runtime}_${i}" ubuntu sleep 3600 > /dev/null 2>&1
        done
        sleep 3

        post_mem=$(get_used_mb)
        overhead=$((post_mem - pre_mem))
        echo "${runtime},containers_${count}_overhead_mb,$overhead" >> "$OUTFILE"
        echo "  ${runtime} con ${count} contenedores: +${overhead} MB"

        # Cleanup
        cleanup_containers "$runtime" "mem_${runtime}"
        sleep 2
    done
done

echo "Resultados guardados en $OUTFILE"
