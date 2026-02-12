#!/bin/bash
# bench_cpu_exec.sh — Mide overhead de CPU *sin* startup usando docker exec
# Uso: bash bench_cpu_exec.sh [repeticiones]
# Salida: results/cpu_exec.csv
#
# A diferencia de bench_cpu.sh (que usa docker run e incluye startup),
# aquí pre-arrancamos el contenedor y medimos solo la ejecución vía exec.
# Esto aísla el overhead real de CPU del contenedor.
set -e

REPS=${1:-3}
OUTFILE="results/cpu_exec.csv"
mkdir -p results

echo "runtime,metric,value" > "$OUTFILE"

# Tarea CPU-bound: contar hasta 1M (más rápido que 10M del benchmark original)
CPU_CMD='i=0; while [ $i -lt 1000000 ]; do i=$((i+1)); done'

echo "=== CPU Exec Benchmark ($REPS repeticiones) ==="
echo "Contando hasta 1,000,000 en un loop de bash (vía exec, sin startup)..."

# Bare metal
echo "Midiendo bare metal..."
for r in $(seq 1 "$REPS"); do
    start_ns=$(date +%s%N)
    bash -c "$CPU_CMD"
    end_ns=$(date +%s%N)
    secs=$(echo "scale=4; ($end_ns - $start_ns) / 1000000000" | bc)
    echo "bare,cpu_exec_seconds,$secs" >> "$OUTFILE"
    echo "  bare metal intento $r: ${secs}s"
done

# Docker
if command -v docker &>/dev/null; then
    echo "Midiendo Docker (pre-arrancando contenedor)..."
    docker pull -q ubuntu > /dev/null 2>&1 || true
    # Pre-arrancar contenedor
    docker rm -f cpu_exec_docker > /dev/null 2>&1 || true
    docker run -d --name cpu_exec_docker ubuntu sleep 300 > /dev/null 2>&1
    sleep 1  # Estabilizar

    for r in $(seq 1 "$REPS"); do
        start_ns=$(date +%s%N)
        docker exec cpu_exec_docker bash -c "$CPU_CMD"
        end_ns=$(date +%s%N)
        secs=$(echo "scale=4; ($end_ns - $start_ns) / 1000000000" | bc)
        echo "docker,cpu_exec_seconds,$secs" >> "$OUTFILE"
        echo "  docker exec intento $r: ${secs}s"
    done

    # Cleanup
    docker rm -f cpu_exec_docker > /dev/null 2>&1 || true
else
    echo "  docker: no disponible, saltando"
fi

# Podman
if command -v podman &>/dev/null; then
    echo "Midiendo Podman (pre-arrancando contenedor)..."
    podman pull -q ubuntu > /dev/null 2>&1 || podman pull -q docker.io/library/ubuntu > /dev/null 2>&1 || true
    # Pre-arrancar contenedor
    podman rm -f cpu_exec_podman > /dev/null 2>&1 || true
    podman run -d --name cpu_exec_podman ubuntu sleep 300 > /dev/null 2>&1
    sleep 1  # Estabilizar

    for r in $(seq 1 "$REPS"); do
        start_ns=$(date +%s%N)
        podman exec cpu_exec_podman bash -c "$CPU_CMD"
        end_ns=$(date +%s%N)
        secs=$(echo "scale=4; ($end_ns - $start_ns) / 1000000000" | bc)
        echo "podman,cpu_exec_seconds,$secs" >> "$OUTFILE"
        echo "  podman exec intento $r: ${secs}s"
    done

    # Cleanup
    podman rm -f cpu_exec_podman > /dev/null 2>&1 || true
else
    echo "  podman: no disponible, saltando"
fi

echo "Resultados guardados en $OUTFILE"
