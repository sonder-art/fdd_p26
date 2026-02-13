#!/bin/bash
# Exp 4: Nested Container Performance
# Measures startup latency and CPU overhead at different nesting levels:
#   Level 0 (bare) — host
#   Level 1         — docker/podman run
#   Level 2         — Docker-in-Docker / Podman-in-Podman
#
# Startup: docker run --rm alpine echo ok (includes container creation)
# CPU:     sha256sum 50MB via exec in PRE-STARTED containers (no startup cost)
#
# Uso: bash exp4_nested.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CSV="$SCRIPT_DIR/results/exp4_nested.csv"
REPS=5
WARMUP=1

mkdir -p "$SCRIPT_DIR/results"
echo "method,metric,rep,value" > "$CSV"

now_ns() { date +%s%N; }
ms_diff() { echo "scale=1; ($2 - $1) / 1000000" | bc; }
s_diff()  { echo "scale=3; ($2 - $1) / 1000000000" | bc; }

record() {
    local method=$1 metric=$2 rep=$3 value=$4
    if [ "$rep" -ge 1 ]; then
        echo "$method,$metric,$rep,$value" >> "$CSV"
    fi
}

echo "============================================"
echo "  Exp 4: Nested Container Performance"
echo "============================================"
echo ""

# ======== SETUP ========
echo "--- Setup ---"

# Pre-pull images
echo "Verifying images..."
docker pull alpine > /dev/null 2>&1
podman pull alpine > /dev/null 2>&1

# Docker L1: pre-start container for CPU tests
docker rm -f exp4-docker-l1 > /dev/null 2>&1 || true
docker run -d --name exp4-docker-l1 alpine sleep 3600 > /dev/null

# Podman L1: pre-start container for CPU tests
podman rm -f exp4-podman-l1 > /dev/null 2>&1 || true
podman run -d --name exp4-podman-l1 alpine sleep 3600 > /dev/null

# Docker-in-Docker
echo "Starting Docker-in-Docker (DinD)..."
docker rm -f exp4-dind > /dev/null 2>&1 || true
docker run -d --privileged --name exp4-dind docker:dind > /dev/null
echo "  Waiting for nested dockerd..."
for _ in $(seq 1 20); do
    docker exec exp4-dind docker info > /dev/null 2>&1 && break
    sleep 1
done
docker exec exp4-dind docker pull alpine > /dev/null 2>&1
# Pre-start inner container for CPU tests
docker exec exp4-dind docker rm -f inner > /dev/null 2>&1 || true
docker exec exp4-dind docker run -d --name inner alpine sleep 3600 > /dev/null
echo "  DinD ready."

# Podman-in-Podman
echo "Starting Podman-in-Podman..."
podman rm -f exp4-podman-nest > /dev/null 2>&1 || true
podman run -d --privileged --name exp4-podman-nest quay.io/podman/stable sleep 3600 > /dev/null
sleep 3
podman exec exp4-podman-nest podman pull alpine > /dev/null 2>&1
# Pre-start inner container for CPU tests
podman exec exp4-podman-nest podman rm -f inner > /dev/null 2>&1 || true
podman exec exp4-podman-nest podman run -d --name inner alpine sleep 3600 > /dev/null
echo "  Podman nested ready."
echo ""

# ======== STARTUP BENCHMARK ========
echo "--- Startup Latency (run --rm alpine echo ok) ---"

for i in $(seq 0 $((REPS + WARMUP - 1))); do
    rep=$((i - WARMUP))

    # bare
    s=$(now_ns); echo ok > /dev/null; e=$(now_ns)
    record "bare" "startup_ms" "$rep" "$(ms_diff $s $e)"

    # docker L1
    s=$(now_ns); docker run --rm alpine echo ok > /dev/null; e=$(now_ns)
    record "docker" "startup_ms" "$rep" "$(ms_diff $s $e)"

    # docker L2 (DinD)
    s=$(now_ns)
    docker exec exp4-dind docker run --rm alpine echo ok > /dev/null
    e=$(now_ns)
    record "dind" "startup_ms" "$rep" "$(ms_diff $s $e)"

    # podman L1
    s=$(now_ns); podman run --rm alpine echo ok > /dev/null; e=$(now_ns)
    record "podman" "startup_ms" "$rep" "$(ms_diff $s $e)"

    # podman L2 (nested)
    s=$(now_ns)
    podman exec exp4-podman-nest podman run --rm alpine echo ok > /dev/null
    e=$(now_ns)
    record "podman-nested" "startup_ms" "$rep" "$(ms_diff $s $e)"

    if [ "$rep" -ge 1 ]; then echo "  startup rep $rep done"; fi
done
echo ""

# ======== CPU BENCHMARK ========
echo "--- CPU Overhead (sha256sum 50MB via exec, pre-started containers) ---"

CPU_CMD='dd if=/dev/urandom bs=1M count=50 2>/dev/null | sha256sum > /dev/null'

for i in $(seq 0 $((REPS + WARMUP - 1))); do
    rep=$((i - WARMUP))

    # bare
    s=$(now_ns); bash -c "$CPU_CMD"; e=$(now_ns)
    record "bare" "cpu_s" "$rep" "$(s_diff $s $e)"

    # docker L1 (exec into pre-started container)
    s=$(now_ns)
    docker exec exp4-docker-l1 sh -c "$CPU_CMD"
    e=$(now_ns)
    record "docker" "cpu_s" "$rep" "$(s_diff $s $e)"

    # docker L2 (exec into inner container inside DinD)
    s=$(now_ns)
    docker exec exp4-dind docker exec inner sh -c "$CPU_CMD"
    e=$(now_ns)
    record "dind" "cpu_s" "$rep" "$(s_diff $s $e)"

    # podman L1 (exec into pre-started container)
    s=$(now_ns)
    podman exec exp4-podman-l1 sh -c "$CPU_CMD"
    e=$(now_ns)
    record "podman" "cpu_s" "$rep" "$(s_diff $s $e)"

    # podman L2 (exec into inner container inside podman)
    s=$(now_ns)
    podman exec exp4-podman-nest podman exec inner sh -c "$CPU_CMD"
    e=$(now_ns)
    record "podman-nested" "cpu_s" "$rep" "$(s_diff $s $e)"

    if [ "$rep" -ge 1 ]; then echo "  cpu rep $rep done"; fi
done
echo ""

# ======== CLEANUP ========
echo "--- Cleanup ---"
docker rm -f exp4-docker-l1 exp4-dind > /dev/null 2>&1 || true
podman rm -f exp4-podman-l1 exp4-podman-nest > /dev/null 2>&1 || true
echo "Done. Results: $CSV"
