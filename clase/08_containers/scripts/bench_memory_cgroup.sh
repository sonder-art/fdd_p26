#!/bin/bash
# bench_memory_cgroup.sh — Mide memoria por contenedor vía docker stats (cgroup)
# Uso: bash bench_memory_cgroup.sh
# Salida: results/memory_cgroup.csv
#
# A diferencia de bench_memory.sh (que usa free -m y sufre de ruido del sistema),
# este script usa docker stats / podman stats que leen memory.current del cgroup,
# dando una medición exacta por contenedor.
set -e

OUTFILE="results/memory_cgroup.csv"
mkdir -p results

echo "runtime,metric,count,value" > "$OUTFILE"

COUNTS=(1 3 5)

# Parsear strings de memoria a KB
# Docker usa KiB/MiB/GiB, Podman usa kB/MB/GB
parse_mem_to_kb() {
    local mem_str="$1"
    # Remover espacios
    mem_str=$(echo "$mem_str" | tr -d ' ')

    local num unit
    num=$(echo "$mem_str" | grep -oP '[\d.]+')
    unit=$(echo "$mem_str" | grep -oP '[A-Za-z]+')

    if [ -z "$num" ]; then
        echo "0"
        return
    fi

    case "$unit" in
        B|b)       echo "$num" | awk '{printf "%.0f", $1 / 1024}' ;;
        KiB|kB|KB) echo "$num" | awk '{printf "%.0f", $1}' ;;
        MiB|MB)    echo "$num" | awk '{printf "%.0f", $1 * 1024}' ;;
        GiB|GB)    echo "$num" | awk '{printf "%.0f", $1 * 1024 * 1024}' ;;
        *)         echo "$num" | awk '{printf "%.0f", $1}' ;;
    esac
}

cleanup_containers() {
    local runtime=$1
    local prefix=$2
    for name in $($runtime ps -a --format '{{.Names}}' 2>/dev/null | grep "^${prefix}" || true); do
        $runtime rm -f "$name" > /dev/null 2>&1 || true
    done
}

echo "=== Memory Cgroup Benchmark ==="
echo "Usando docker/podman stats (cgroup memory.current) para medición exacta"
echo ""

for runtime in docker podman; do
    if ! command -v "$runtime" &>/dev/null; then
        echo "$runtime: no disponible, saltando"
        continue
    fi

    echo "Midiendo $runtime..."
    $runtime pull -q ubuntu > /dev/null 2>&1 || $runtime pull -q docker.io/library/ubuntu > /dev/null 2>&1 || true

    # Medir daemon/conmon RSS sin contenedores (baseline)
    if [ "$runtime" = "docker" ]; then
        daemon_pid=$(pgrep -x dockerd 2>/dev/null || echo "")
        if [ -n "$daemon_pid" ]; then
            daemon_rss=$(ps -p "$daemon_pid" -o rss= 2>/dev/null | tr -d ' ')
            echo "${runtime},daemon_rss_kb,0,$daemon_rss" >> "$OUTFILE"
            echo "  daemon RSS (0 contenedores): ${daemon_rss} KB"
        fi
    else
        # Conmon: sin contenedores no hay conmon
        echo "${runtime},conmon_rss_kb,0,0" >> "$OUTFILE"
        echo "  conmon RSS (0 contenedores): 0 KB"
    fi

    for count in "${COUNTS[@]}"; do
        # Limpiar antes
        cleanup_containers "$runtime" "memcg_${runtime}"
        sleep 1

        # Lanzar contenedores
        for i in $(seq 1 "$count"); do
            $runtime run -d --name "memcg_${runtime}_${i}" ubuntu sleep 3600 > /dev/null 2>&1
        done
        sleep 2  # Estabilizar

        # Medir memoria por contenedor vía stats
        total_kb=0
        container_count=0
        while IFS=',' read -r name mem_usage; do
            # mem_usage tiene formato "X MiB / Y MiB" — tomar solo el uso actual
            current_mem=$(echo "$mem_usage" | cut -d'/' -f1)
            kb=$(parse_mem_to_kb "$current_mem")
            total_kb=$((total_kb + kb))
            container_count=$((container_count + 1))
        done < <($runtime stats --no-stream --format '{{.Name}},{{.MemUsage}}' 2>/dev/null | grep "^memcg_${runtime}" || true)

        if [ "$container_count" -gt 0 ]; then
            per_container_kb=$((total_kb / container_count))
            echo "${runtime},per_container_kb,${count},${per_container_kb}" >> "$OUTFILE"
            echo "${runtime},total_containers_kb,${count},${total_kb}" >> "$OUTFILE"
            echo "  ${count} contenedores: ${per_container_kb} KB/cont, ${total_kb} KB total"
        else
            echo "  ${count} contenedores: no se pudo obtener stats"
        fi

        # Medir daemon/conmon RSS con contenedores corriendo
        if [ "$runtime" = "docker" ]; then
            daemon_pid=$(pgrep -x dockerd 2>/dev/null || echo "")
            if [ -n "$daemon_pid" ]; then
                daemon_rss=$(ps -p "$daemon_pid" -o rss= 2>/dev/null | tr -d ' ')
                echo "${runtime},daemon_rss_kb,${count},${daemon_rss}" >> "$OUTFILE"
                echo "  daemon RSS (${count} contenedores): ${daemon_rss} KB"
            fi
        else
            # Sumar RSS de todos los procesos conmon
            conmon_rss=$(ps aux 2>/dev/null | grep '[c]onmon' | awk '{sum += $6} END {print sum+0}')
            echo "${runtime},conmon_rss_kb,${count},${conmon_rss}" >> "$OUTFILE"
            echo "  conmon RSS (${count} contenedores): ${conmon_rss} KB"
        fi

        # Cleanup
        cleanup_containers "$runtime" "memcg_${runtime}"
        sleep 2
    done
    echo ""
done

echo "Resultados guardados en $OUTFILE"
