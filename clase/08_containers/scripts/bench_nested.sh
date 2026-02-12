#!/bin/bash
# bench_nested.sh — Mide contenedores anidados (Docker-in-Docker, Podman-in-Podman)
# Uso: bash bench_nested.sh
# Salida: results/nested.csv
# NOTA: Docker-in-Docker requiere --privileged
set -e

OUTFILE="results/nested.csv"
mkdir -p results

echo "runtime,metric,value" > "$OUTFILE"

echo "=== Nested Containers ==="

# Docker-in-Docker
if command -v docker &>/dev/null; then
    echo "Docker-in-Docker (requiere --privileged)..."
    docker pull -q docker:dind > /dev/null 2>&1 || true

    start_ns=$(date +%s%N)
    if docker run --rm --privileged docker:dind sh -c '
        # Esperar a que el daemon interno arranque
        dockerd > /dev/null 2>&1 &
        timeout 30 sh -c "until docker info > /dev/null 2>&1; do sleep 0.5; done"
        docker run --rm alpine echo ok
    ' > /dev/null 2>&1; then
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        echo "docker,nested_seconds,$secs" >> "$OUTFILE"
        echo "  Docker-in-Docker: ${secs}s"
    else
        echo "  Docker-in-Docker: falló (puede requerir permisos adicionales)"
        echo "docker,nested_seconds,error" >> "$OUTFILE"
    fi
else
    echo "  docker: no disponible, saltando"
fi

# Podman-in-Podman
if command -v podman &>/dev/null; then
    echo "Podman-in-Podman..."
    podman pull -q quay.io/podman/stable > /dev/null 2>&1 || true

    start_ns=$(date +%s%N)
    if podman run --rm --security-opt label=disable \
        --device /dev/fuse \
        quay.io/podman/stable podman run --rm alpine echo ok > /dev/null 2>&1; then
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        echo "podman,nested_seconds,$secs" >> "$OUTFILE"
        echo "  Podman-in-Podman: ${secs}s"
    else
        echo "  Podman-in-Podman: falló (puede requerir configuración adicional)"
        echo "podman,nested_seconds,error" >> "$OUTFILE"
    fi
else
    echo "  podman: no disponible, saltando"
fi

echo "Resultados guardados en $OUTFILE"
