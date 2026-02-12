#!/bin/bash
# bench_cpu.sh — Mide overhead de CPU en contenedores
# Uso: bash bench_cpu.sh [repeticiones]
# Salida: results/cpu.csv
set -e

REPS=${1:-3}
OUTFILE="results/cpu.csv"
mkdir -p results

echo "runtime,metric,value" > "$OUTFILE"

# Tarea CPU-bound: contar hasta 10M en un loop de bash
CPU_CMD='i=0; while [ $i -lt 10000000 ]; do i=$((i+1)); done'

echo "=== CPU Benchmark ($REPS repeticiones) ==="
echo "Contando hasta 10,000,000 en un loop de bash..."

# Bare metal
echo "Midiendo bare metal..."
for r in $(seq 1 "$REPS"); do
    start_ns=$(date +%s%N)
    bash -c "$CPU_CMD"
    end_ns=$(date +%s%N)
    secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
    echo "bare,cpu_seconds,$secs" >> "$OUTFILE"
    echo "  bare metal intento $r: ${secs}s"
done

# Docker
if command -v docker &>/dev/null; then
    echo "Midiendo Docker..."
    docker pull -q ubuntu > /dev/null 2>&1 || true
    for r in $(seq 1 "$REPS"); do
        start_ns=$(date +%s%N)
        docker run --rm ubuntu bash -c "$CPU_CMD"
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        echo "docker,cpu_seconds,$secs" >> "$OUTFILE"
        echo "  docker intento $r: ${secs}s"
    done
else
    echo "  docker: no disponible, saltando"
fi

# Podman
if command -v podman &>/dev/null; then
    echo "Midiendo Podman..."
    podman pull -q ubuntu > /dev/null 2>&1 || podman pull -q docker.io/library/ubuntu > /dev/null 2>&1 || true
    for r in $(seq 1 "$REPS"); do
        start_ns=$(date +%s%N)
        podman run --rm ubuntu bash -c "$CPU_CMD"
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        echo "podman,cpu_seconds,$secs" >> "$OUTFILE"
        echo "  podman intento $r: ${secs}s"
    done
else
    echo "  podman: no disponible, saltando"
fi

echo "Resultados guardados en $OUTFILE"
