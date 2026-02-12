#!/bin/bash
# bench_nested_v2.sh — Prueba 6 enfoques de contenedores anidados
# Uso: bash bench_nested_v2.sh
# Salida: results/nested_v2.csv
#
# A diferencia de bench_nested.sh (que solo probó 2 enfoques y ambos fallaron),
# este script prueba 6 enfoques diferentes y documenta cuáles funcionan.
set -e

OUTFILE="results/nested_v2.csv"
mkdir -p results

TIMEOUT=45

echo "runtime,approach,result,time_seconds,error_msg" > "$OUTFILE"

record() {
    local runtime="$1" approach="$2" result="$3" time_s="$4" error_msg="$5"
    # Limpiar error_msg: remover comas y newlines para CSV
    error_msg=$(echo "$error_msg" | tr ',' ';' | tr '\n' ' ' | head -c 200)
    echo "${runtime},${approach},${result},${time_s},${error_msg}" >> "$OUTFILE"
}

echo "=== Nested Containers v2 (6 enfoques) ==="
echo "Timeout por enfoque: ${TIMEOUT}s"
echo ""

# -------------------------------------------------------
# 1. Docker: DinD con --privileged (clásico)
# -------------------------------------------------------
if command -v docker &>/dev/null; then
    echo "1/6 Docker: dind_privileged..."
    docker rm -f dind_test > /dev/null 2>&1 || true
    docker pull -q docker:dind > /dev/null 2>&1 || true

    start_ns=$(date +%s%N)
    error_out=$(mktemp)
    if timeout "$TIMEOUT" bash -c '
        docker run --rm --privileged --name dind_test docker:dind sh -c "
            dockerd > /dev/null 2>&1 &
            timeout 30 sh -c \"until docker info > /dev/null 2>&1; do sleep 0.5; done\"
            docker run --rm alpine echo nested-ok
        "
    ' > /dev/null 2>"$error_out"; then
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        echo "  ✓ success (${secs}s)"
        record "docker" "dind_privileged" "success" "$secs" ""
    else
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        err=$(cat "$error_out" | tail -3)
        echo "  ✗ error (${secs}s): $err"
        record "docker" "dind_privileged" "error" "$secs" "$err"
    fi
    rm -f "$error_out"
    docker rm -f dind_test > /dev/null 2>&1 || true

    # -------------------------------------------------------
    # 2. Docker: Socket mount (patrón CI/CD)
    # -------------------------------------------------------
    echo "2/6 Docker: socket_mount..."
    start_ns=$(date +%s%N)
    error_out=$(mktemp)
    if timeout "$TIMEOUT" docker run --rm \
        -v /var/run/docker.sock:/var/run/docker.sock \
        docker:cli docker run --rm alpine echo nested-ok \
        > /dev/null 2>"$error_out"; then
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        echo "  ✓ success (${secs}s)"
        record "docker" "socket_mount" "success" "$secs" ""
    else
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        err=$(cat "$error_out" | tail -3)
        echo "  ✗ error (${secs}s): $err"
        record "docker" "socket_mount" "error" "$secs" "$err"
    fi
    rm -f "$error_out"

    # -------------------------------------------------------
    # 3. Docker: DinD con seguridad relajada (sin privileged)
    # -------------------------------------------------------
    echo "3/6 Docker: dind_relaxed_security..."
    docker rm -f dind_relaxed > /dev/null 2>&1 || true
    start_ns=$(date +%s%N)
    error_out=$(mktemp)
    if timeout "$TIMEOUT" bash -c '
        docker run --rm --name dind_relaxed \
            --security-opt apparmor=unconfined \
            --security-opt seccomp=unconfined \
            --cap-add SYS_ADMIN \
            docker:dind sh -c "
                dockerd > /dev/null 2>&1 &
                timeout 30 sh -c \"until docker info > /dev/null 2>&1; do sleep 0.5; done\"
                docker run --rm alpine echo nested-ok
            "
    ' > /dev/null 2>"$error_out"; then
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        echo "  ✓ success (${secs}s)"
        record "docker" "dind_relaxed_security" "success" "$secs" ""
    else
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        err=$(cat "$error_out" | tail -3)
        echo "  ✗ error (${secs}s): $err"
        record "docker" "dind_relaxed_security" "error" "$secs" "$err"
    fi
    rm -f "$error_out"
    docker rm -f dind_relaxed > /dev/null 2>&1 || true
else
    echo "Docker no disponible, saltando enfoques 1-3"
    record "docker" "dind_privileged" "skipped" "0" "docker not available"
    record "docker" "socket_mount" "skipped" "0" "docker not available"
    record "docker" "dind_relaxed_security" "skipped" "0" "docker not available"
fi

# -------------------------------------------------------
# 4. Podman: PinP básico (label=disable + /dev/fuse)
# -------------------------------------------------------
if command -v podman &>/dev/null; then
    echo "4/6 Podman: pinp_basic..."
    podman pull -q quay.io/podman/stable > /dev/null 2>&1 || true

    start_ns=$(date +%s%N)
    error_out=$(mktemp)
    if timeout "$TIMEOUT" podman run --rm \
        --security-opt label=disable \
        --device /dev/fuse \
        quay.io/podman/stable podman run --rm alpine echo nested-ok \
        > /dev/null 2>"$error_out"; then
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        echo "  ✓ success (${secs}s)"
        record "podman" "pinp_basic" "success" "$secs" ""
    else
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        err=$(cat "$error_out" | tail -3)
        echo "  ✗ error (${secs}s): $err"
        record "podman" "pinp_basic" "error" "$secs" "$err"
    fi
    rm -f "$error_out"

    # -------------------------------------------------------
    # 5. Podman: PinP con --privileged
    # -------------------------------------------------------
    echo "5/6 Podman: pinp_privileged..."
    start_ns=$(date +%s%N)
    error_out=$(mktemp)
    if timeout "$TIMEOUT" podman run --rm --privileged \
        quay.io/podman/stable podman run --rm alpine echo nested-ok \
        > /dev/null 2>"$error_out"; then
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        echo "  ✓ success (${secs}s)"
        record "podman" "pinp_privileged" "success" "$secs" ""
    else
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        err=$(cat "$error_out" | tail -3)
        echo "  ✗ error (${secs}s): $err"
        record "podman" "pinp_privileged" "error" "$secs" "$err"
    fi
    rm -f "$error_out"

    # -------------------------------------------------------
    # 6. Podman: PinP con VFS storage driver
    # -------------------------------------------------------
    echo "6/6 Podman: pinp_vfs..."
    start_ns=$(date +%s%N)
    error_out=$(mktemp)
    if timeout "$TIMEOUT" podman run --rm \
        --security-opt label=disable \
        --device /dev/fuse \
        quay.io/podman/stable \
        podman --storage-driver vfs run --rm alpine echo nested-ok \
        > /dev/null 2>"$error_out"; then
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        echo "  ✓ success (${secs}s)"
        record "podman" "pinp_vfs" "success" "$secs" ""
    else
        end_ns=$(date +%s%N)
        secs=$(echo "scale=2; ($end_ns - $start_ns) / 1000000000" | bc)
        err=$(cat "$error_out" | tail -3)
        echo "  ✗ error (${secs}s): $err"
        record "podman" "pinp_vfs" "error" "$secs" "$err"
    fi
    rm -f "$error_out"
else
    echo "Podman no disponible, saltando enfoques 4-6"
    record "podman" "pinp_basic" "skipped" "0" "podman not available"
    record "podman" "pinp_privileged" "skipped" "0" "podman not available"
    record "podman" "pinp_vfs" "skipped" "0" "podman not available"
fi

echo ""
echo "Resultados guardados en $OUTFILE"

# Mostrar resumen
echo ""
echo "Resumen:"
while IFS=',' read -r runtime approach result time_s error_msg; do
    [ "$runtime" = "runtime" ] && continue  # skip header
    if [ "$result" = "success" ]; then
        echo "  ✓ ${runtime}/${approach}: ${time_s}s"
    else
        echo "  ✗ ${runtime}/${approach}: ${result}"
    fi
done < "$OUTFILE"
