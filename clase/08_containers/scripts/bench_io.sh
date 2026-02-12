#!/bin/bash
# bench_io.sh — Mide rendimiento de escritura en disco
# Uso: bash bench_io.sh [repeticiones]
# Salida: results/io.csv
set -e

REPS=${1:-3}
OUTFILE="results/io.csv"
mkdir -p results

echo "runtime,mode,rep,mb_per_sec" > "$OUTFILE"

BS="1M"
COUNT=100

extract_speed() {
    # dd output: "100+0 records out, 104857600 bytes (105 MB, 100 MiB) copied, 0.123 s, 854 MB/s"
    local output="$1"
    # Intentar extraer MB/s o GB/s
    echo "$output" | grep -oP '[\d.]+ [MG]B/s' | head -1 || echo "0 MB/s"
}

echo "=== Disk I/O Benchmark ($REPS repeticiones, ${COUNT}MB) ==="

# Bare metal
echo "Midiendo bare metal..."
for r in $(seq 1 "$REPS"); do
    result=$(dd if=/dev/zero of=/tmp/bench_io_test bs=$BS count=$COUNT conv=fdatasync 2>&1 || true)
    speed=$(extract_speed "$result")
    # Convertir a número
    num=$(echo "$speed" | grep -oP '[\d.]+' | head -1)
    unit=$(echo "$speed" | grep -oP '[MG]B/s' | head -1)
    if [ "$unit" = "GB/s" ]; then
        num=$(echo "$num * 1000" | bc)
    fi
    echo "bare,direct,$r,$num" >> "$OUTFILE"
    echo "  bare metal intento $r: $speed"
    rm -f /tmp/bench_io_test
done

for runtime in docker podman; do
    if ! command -v "$runtime" &>/dev/null; then
        echo "$runtime: no disponible, saltando"
        continue
    fi

    $runtime pull -q ubuntu > /dev/null 2>&1 || $runtime pull -q docker.io/library/ubuntu > /dev/null 2>&1 || true

    # Overlay (escritura dentro del contenedor)
    echo "Midiendo $runtime overlay..."
    for r in $(seq 1 "$REPS"); do
        result=$($runtime run --rm ubuntu bash -c \
            "dd if=/dev/zero of=/tmp/testfile bs=$BS count=$COUNT conv=fdatasync 2>&1" 2>&1 || true)
        speed=$(extract_speed "$result")
        num=$(echo "$speed" | grep -oP '[\d.]+' | head -1)
        unit=$(echo "$speed" | grep -oP '[MG]B/s' | head -1)
        if [ "$unit" = "GB/s" ]; then
            num=$(echo "$num * 1000" | bc)
        fi
        echo "${runtime},overlay,$r,${num:-0}" >> "$OUTFILE"
        echo "  $runtime overlay intento $r: $speed"
    done

    # Volume mount
    echo "Midiendo $runtime volume..."
    tmpdir=$(mktemp -d)
    for r in $(seq 1 "$REPS"); do
        result=$($runtime run --rm -v "$tmpdir":/mnt ubuntu bash -c \
            "dd if=/dev/zero of=/mnt/testfile bs=$BS count=$COUNT conv=fdatasync 2>&1" 2>&1 || true)
        speed=$(extract_speed "$result")
        num=$(echo "$speed" | grep -oP '[\d.]+' | head -1)
        unit=$(echo "$speed" | grep -oP '[MG]B/s' | head -1)
        if [ "$unit" = "GB/s" ]; then
            num=$(echo "$num * 1000" | bc)
        fi
        echo "${runtime},volume,$r,${num:-0}" >> "$OUTFILE"
        echo "  $runtime volume intento $r: $speed"
        rm -f "$tmpdir/testfile"
    done
    rm -rf "$tmpdir"
done

echo "Resultados guardados en $OUTFILE"
