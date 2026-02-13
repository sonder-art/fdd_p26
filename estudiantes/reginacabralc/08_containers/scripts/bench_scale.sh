#!/bin/bash
# bench_scale.sh — Mide LAUNCH time + CAPACITY (memoria) al escalar contenedores
# Usa docker/podman stats (cgroup memory.current) en vez de free -m
# Uso: bash bench_scale.sh
# Salida: results/exp2_scale.csv
set -e

OUTFILE="results/exp2_scale.csv"
mkdir -p results

COUNTS=(1 5 10 20)

echo "runtime,count,launch_time_s,per_container_kb,total_container_kb,daemon_rss_kb" > "$OUTFILE"

# --- Helper: parse docker/podman stats memory to KB ---
# Docker reports: "1.5MiB / 7.5GiB" (binary units)
# Podman reports: "1.5MB / 7.5GB" (decimal units) or sometimes MiB
parse_mem_to_kb() {
    local mem_str="$1"
    # Extract the first number+unit (usage, not limit)
    local usage
    usage=$(echo "$mem_str" | sed 's/ \/.*//' | xargs)
    local num unit
    num=$(echo "$usage" | grep -oP '[\d.]+')
    unit=$(echo "$usage" | grep -oP '[A-Za-z]+')
    case "$unit" in
        B)    echo "$num" | awk '{printf "%.1f", $1 / 1024}' ;;
        kB|KB) echo "$num" | awk '{printf "%.1f", $1}' ;;
        KiB)  echo "$num" | awk '{printf "%.1f", $1 * 1.024}' ;;
        MB)   echo "$num" | awk '{printf "%.1f", $1 * 1000}' ;;
        MiB)  echo "$num" | awk '{printf "%.1f", $1 * 1024}' ;;
        GB)   echo "$num" | awk '{printf "%.1f", $1 * 1000000}' ;;
        GiB)  echo "$num" | awk '{printf "%.1f", $1 * 1048576}' ;;
        *)    echo "0" ;;
    esac
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

get_daemon_rss_kb() {
    local runtime=$1
    if [ "$runtime" = "docker" ]; then
        # RSS of dockerd in KB
        local pid
        pid=$(pgrep -x dockerd 2>/dev/null || echo "")
        if [ -n "$pid" ]; then
            ps -p "$pid" -o rss= 2>/dev/null | xargs
        else
            echo "0"
        fi
    else
        # Sum of all conmon processes RSS in KB
        local total
        total=$(ps -C conmon -o rss= 2>/dev/null | awk '{s+=$1} END {print s+0}')
        echo "$total"
    fi
}

echo "=== Exp 2: Resource Footprint at Scale ==="

for runtime in docker podman; do
    if ! command -v "$runtime" &>/dev/null; then
        echo "$runtime: no disponible, saltando"
        continue
    fi

    echo "Midiendo $runtime..."
    $runtime pull -q ubuntu > /dev/null 2>&1 \
        || $runtime pull -q docker.io/library/ubuntu > /dev/null 2>&1 || true

    for count in "${COUNTS[@]}"; do
        prefix="exp2_${runtime}_${count}"

        # Ensure clean state
        cleanup_containers "$runtime" "$prefix"
        sleep 1

        # --- Launch time ---
        start_ns=$(date +%s%N)
        for i in $(seq 1 "$count"); do
            $runtime run -d --name "${prefix}_${i}" ubuntu sleep 3600 > /dev/null 2>&1
        done
        end_ns=$(date +%s%N)
        launch_s=$(echo "scale=3; ($end_ns - $start_ns) / 1000000000" | bc)

        sleep 2  # let cgroups settle

        # --- Per-container memory via stats ---
        total_kb=0
        n_containers=0
        while IFS= read -r line; do
            # line format: "name,mem_usage"
            mem_field=$(echo "$line" | cut -d',' -f2)
            kb=$(parse_mem_to_kb "$mem_field")
            total_kb=$(echo "$total_kb + $kb" | bc)
            n_containers=$((n_containers + 1))
        done < <($runtime stats --no-stream --format "{{.Name}},{{.MemUsage}}" 2>/dev/null \
                 | grep "^${prefix}_")

        if [ "$n_containers" -gt 0 ]; then
            per_container_kb=$(echo "scale=1; $total_kb / $n_containers" | bc)
        else
            per_container_kb=0
        fi

        # --- Daemon/conmon RSS ---
        daemon_rss_kb=$(get_daemon_rss_kb "$runtime")

        echo "${runtime},${count},${launch_s},${per_container_kb},${total_kb},${daemon_rss_kb}" >> "$OUTFILE"
        echo "  ${count} cont: ${launch_s}s, ${per_container_kb} KB/cont, daemon=${daemon_rss_kb} KB"

        # Cleanup
        cleanup_containers "$runtime" "$prefix"
        sleep 2
    done
done

echo "Resultados guardados en $OUTFILE"
