#!/usr/bin/env python3
"""
analyze.py — Lee los CSVs de benchmarks y genera gráficas PNG.

Uso: python3 analyze.py
Requiere: matplotlib (pip install matplotlib)
Lee de: results/*.csv
Escribe en: results/*.png
"""

import csv
import os
import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")  # Backend sin GUI
    import matplotlib.pyplot as plt
except ImportError:
    print("Error: matplotlib no está instalado.")
    print("Instálalo con: pip install matplotlib")
    sys.exit(1)

RESULTS_DIR = Path(__file__).parent / "results"
IMAGES_DIR = Path(__file__).parent.parent / "images"

# Colores consistentes para cada runtime
COLORS = {
    "bare": "#6c757d",
    "docker": "#0db7ed",
    "podman": "#892ca0",
}

LABELS = {
    "bare": "Bare Metal",
    "docker": "Docker",
    "podman": "Podman",
}


def read_csv(filename):
    """Lee un CSV y retorna una lista de diccionarios."""
    filepath = RESULTS_DIR / filename
    if not filepath.exists():
        print(f"  Archivo no encontrado: {filepath}")
        return []
    with open(filepath) as f:
        return list(csv.DictReader(f))


def save_fig(fig, name):
    """Guarda una figura como PNG en results/ y en images/ (para el sitio web)."""
    path = RESULTS_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
    print(f"  Guardado: {path}")
    # También guardar en images/ para que Eleventy lo copie al sitio
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    img_path = IMAGES_DIR / name
    fig.savefig(img_path, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
    print(f"  Guardado: {img_path}")
    plt.close(fig)


def style_ax(ax, title, ylabel):
    """Aplica estilo consistente a un eje."""
    ax.set_title(title, color="white", fontsize=14, fontweight="bold", pad=12)
    ax.set_ylabel(ylabel, color="white", fontsize=11)
    ax.tick_params(colors="white")
    ax.set_facecolor("#16213e")
    for spine in ax.spines.values():
        spine.set_color("#333")


def plot_startup():
    """Gráfica 1: Comparación de tiempos de startup."""
    rows = read_csv("startup.csv")
    if not rows:
        return

    # Agrupar por runtime y calcular promedios
    data = {}
    for row in rows:
        rt = row["runtime"]
        try:
            val = float(row["value"])
        except (ValueError, KeyError):
            continue
        data.setdefault(rt, []).append(val)

    if not data:
        return

    runtimes = sorted(data.keys(), key=lambda x: {"bare": 0, "docker": 1, "podman": 2}.get(x, 9))
    means = [sum(data[r]) / len(data[r]) for r in runtimes]
    colors = [COLORS.get(r, "#aaa") for r in runtimes]
    labels = [LABELS.get(r, r) for r in runtimes]

    fig, ax = plt.subplots(figsize=(8, 5), facecolor="#1a1a2e")
    bars = ax.bar(labels, means, color=colors, edgecolor="#333", linewidth=0.5)
    style_ax(ax, "Startup Latency", "Tiempo (ms)")

    for bar, val in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(means) * 0.02,
                f"{val:.1f} ms", ha="center", va="bottom", color="white", fontsize=10)

    save_fig(fig, "startup_comparison.png")


def plot_memory():
    """Gráfica 2: Comparación de memoria."""
    rows = read_csv("memory.csv")
    if not rows:
        return

    # Extraer overhead por runtime y count
    data = {}
    for row in rows:
        rt = row["runtime"]
        metric = row["metric"]
        if "overhead" not in metric:
            continue
        try:
            val = float(row["value"])
        except (ValueError, KeyError):
            continue
        # Extraer count del metric name: containers_5_overhead_mb -> 5
        parts = metric.split("_")
        count = parts[1] if len(parts) >= 3 else "?"
        data.setdefault(rt, {})[count] = val

    if not data:
        return

    fig, ax = plt.subplots(figsize=(10, 5), facecolor="#1a1a2e")
    x_labels = sorted({c for d in data.values() for c in d}, key=lambda c: int(c) if c.isdigit() else 0)
    width = 0.35
    x = range(len(x_labels))

    for i, rt in enumerate(["docker", "podman"]):
        if rt not in data:
            continue
        vals = [data[rt].get(c, 0) for c in x_labels]
        offset = (i - 0.5) * width
        bars = ax.bar([xi + offset for xi in x], vals,
                      width=width, label=LABELS.get(rt, rt),
                      color=COLORS.get(rt, "#aaa"), edgecolor="#333", linewidth=0.5)
        for bar, val in zip(bars, vals):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                        f"{val:.0f}", ha="center", va="bottom", color="white", fontsize=9)

    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{c} cont." for c in x_labels])
    ax.legend(facecolor="#16213e", edgecolor="#333", labelcolor="white")
    style_ax(ax, "Memory Overhead por Número de Contenedores", "Overhead (MB)")

    save_fig(fig, "memory_comparison.png")


def plot_cpu():
    """Gráfica 3: Comparación de CPU."""
    rows = read_csv("cpu.csv")
    if not rows:
        return

    data = {}
    for row in rows:
        rt = row["runtime"]
        try:
            val = float(row["value"])
        except (ValueError, KeyError):
            continue
        data.setdefault(rt, []).append(val)

    if not data:
        return

    runtimes = sorted(data.keys(), key=lambda x: {"bare": 0, "docker": 1, "podman": 2}.get(x, 9))
    means = [sum(data[r]) / len(data[r]) for r in runtimes]
    colors = [COLORS.get(r, "#aaa") for r in runtimes]
    labels = [LABELS.get(r, r) for r in runtimes]

    fig, ax = plt.subplots(figsize=(8, 5), facecolor="#1a1a2e")
    bars = ax.bar(labels, means, color=colors, edgecolor="#333", linewidth=0.5)
    style_ax(ax, "CPU Benchmark (contar hasta 10M)", "Tiempo (segundos)")

    for bar, val in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(means) * 0.02,
                f"{val:.2f}s", ha="center", va="bottom", color="white", fontsize=10)

    save_fig(fig, "cpu_comparison.png")


def plot_io():
    """Gráfica 4: Comparación de I/O."""
    rows = read_csv("io.csv")
    if not rows:
        return

    data = {}
    for row in rows:
        rt = row["runtime"]
        mode = row["mode"]
        try:
            val = float(row["mb_per_sec"])
        except (ValueError, KeyError):
            continue
        key = f"{rt}_{mode}"
        data.setdefault(key, []).append(val)

    if not data:
        return

    fig, ax = plt.subplots(figsize=(10, 5), facecolor="#1a1a2e")

    # Agrupar por modo
    modes = ["direct", "overlay", "volume"]
    mode_labels = {"direct": "Directo", "overlay": "Overlay FS", "volume": "Volume Mount"}
    runtimes = ["bare", "docker", "podman"]
    width = 0.25

    for i, rt in enumerate(runtimes):
        vals = []
        x_positions = []
        for j, mode in enumerate(modes):
            key = f"{rt}_{mode}"
            if key in data:
                vals.append(sum(data[key]) / len(data[key]))
                x_positions.append(j + (i - 1) * width)
        if vals:
            ax.bar(x_positions, vals, width=width,
                   label=LABELS.get(rt, rt), color=COLORS.get(rt, "#aaa"),
                   edgecolor="#333", linewidth=0.5)

    ax.set_xticks(range(len(modes)))
    ax.set_xticklabels([mode_labels.get(m, m) for m in modes])
    ax.legend(facecolor="#16213e", edgecolor="#333", labelcolor="white")
    style_ax(ax, "Disk I/O: Escritura de 100MB", "Velocidad (MB/s)")

    save_fig(fig, "io_comparison.png")


def plot_scale():
    """Gráfica 5: Escalamiento de memoria."""
    rows = read_csv("scale.csv")
    if not rows:
        return

    data = {}
    for row in rows:
        rt = row["runtime"]
        try:
            count = int(row["count"])
            mem = float(row["memory_mb"])
            time_s = float(row["time_seconds"])
        except (ValueError, KeyError):
            continue
        data.setdefault(rt, {"counts": [], "memory": [], "time": []})
        data[rt]["counts"].append(count)
        data[rt]["memory"].append(mem)
        data[rt]["time"].append(time_s)

    if not data:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), facecolor="#1a1a2e")

    for rt in ["docker", "podman"]:
        if rt not in data:
            continue
        d = data[rt]
        ax1.plot(d["counts"], d["memory"], "o-",
                 color=COLORS.get(rt, "#aaa"), label=LABELS.get(rt, rt),
                 linewidth=2, markersize=8)
        ax2.plot(d["counts"], d["time"], "o-",
                 color=COLORS.get(rt, "#aaa"), label=LABELS.get(rt, rt),
                 linewidth=2, markersize=8)

    style_ax(ax1, "Memoria vs Contenedores", "Overhead Memoria (MB)")
    ax1.set_xlabel("Número de contenedores", color="white", fontsize=11)
    ax1.legend(facecolor="#16213e", edgecolor="#333", labelcolor="white")

    style_ax(ax2, "Tiempo de Arranque vs Contenedores", "Tiempo Total (s)")
    ax2.set_xlabel("Número de contenedores", color="white", fontsize=11)
    ax2.legend(facecolor="#16213e", edgecolor="#333", labelcolor="white")

    save_fig(fig, "scale_memory.png")


def plot_cpu_exec():
    """Gráfica 7: CPU puro (exec) — comparación con/sin startup."""
    rows = read_csv("cpu_exec.csv")
    if not rows:
        return

    # Datos de exec
    exec_data = {}
    for row in rows:
        rt = row["runtime"]
        try:
            val = float(row["value"])
        except (ValueError, KeyError):
            continue
        exec_data.setdefault(rt, []).append(val)

    if not exec_data:
        return

    # También leer datos originales de cpu.csv para comparación
    run_data = {}
    run_rows = read_csv("cpu.csv")
    for row in run_rows:
        rt = row["runtime"]
        try:
            val = float(row["value"])
        except (ValueError, KeyError):
            continue
        run_data.setdefault(rt, []).append(val)

    runtimes = sorted(exec_data.keys(), key=lambda x: {"bare": 0, "docker": 1, "podman": 2}.get(x, 9))
    exec_means = {r: sum(exec_data[r]) / len(exec_data[r]) for r in runtimes}
    colors = [COLORS.get(r, "#aaa") for r in runtimes]
    labels = [LABELS.get(r, r) for r in runtimes]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), facecolor="#1a1a2e")

    # Panel 1: Tiempos exec
    means_list = [exec_means[r] for r in runtimes]
    bars = ax1.bar(labels, means_list, color=colors, edgecolor="#333", linewidth=0.5)
    style_ax(ax1, "CPU Puro (exec, contar hasta 1M)", "Tiempo (segundos)")
    for bar, val in zip(bars, means_list):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(means_list) * 0.02,
                 f"{val:.2f}s", ha="center", va="bottom", color="white", fontsize=10)

    # Panel 2: Comparación overhead % (run vs exec)
    if run_data:
        run_means = {r: sum(run_data[r]) / len(run_data[r]) for r in run_data}
        comparison_runtimes = [r for r in ["docker", "podman"] if r in exec_means and r in run_means]
        if comparison_runtimes:
            bare_run = run_means.get("bare", 1)
            bare_exec = exec_means.get("bare", 1)

            x = range(len(comparison_runtimes))
            width = 0.35
            run_overheads = [((run_means[r] - bare_run) / bare_run) * 100 for r in comparison_runtimes]
            exec_overheads = [((exec_means[r] - bare_exec) / bare_exec) * 100 for r in comparison_runtimes]

            bars1 = ax2.bar([xi - width / 2 for xi in x], run_overheads,
                            width=width, label="docker run (con startup)",
                            color="#e74c3c", edgecolor="#333", linewidth=0.5)
            bars2 = ax2.bar([xi + width / 2 for xi in x], exec_overheads,
                            width=width, label="docker exec (sin startup)",
                            color="#2ecc71", edgecolor="#333", linewidth=0.5)

            ax2.set_xticks(list(x))
            ax2.set_xticklabels([LABELS.get(r, r) for r in comparison_runtimes])
            ax2.legend(facecolor="#16213e", edgecolor="#333", labelcolor="white")
            style_ax(ax2, "Overhead CPU: run vs exec", "Overhead (%)")

            for bar, val in zip(bars1, run_overheads):
                ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                         f"{val:.1f}%", ha="center", va="bottom", color="white", fontsize=9)
            for bar, val in zip(bars2, exec_overheads):
                y_pos = bar.get_height() if bar.get_height() >= 0 else bar.get_height() - 1.5
                ax2.text(bar.get_x() + bar.get_width() / 2, y_pos + 0.5,
                         f"{val:.1f}%", ha="center", va="bottom", color="white", fontsize=9)

    save_fig(fig, "cpu_exec_comparison.png")


def plot_memory_cgroup():
    """Gráfica 8: Memoria cgroup — per-container y daemon RSS."""
    rows = read_csv("memory_cgroup.csv")
    if not rows:
        return

    per_container = {}  # {runtime: {count: kb}}
    daemon_rss = {}     # {runtime: {count: kb}}

    for row in rows:
        rt = row["runtime"]
        metric = row["metric"]
        try:
            count = int(row["count"])
            val = float(row["value"])
        except (ValueError, KeyError):
            continue

        if metric == "per_container_kb":
            per_container.setdefault(rt, {})[count] = val
        elif metric in ("daemon_rss_kb", "conmon_rss_kb"):
            daemon_rss.setdefault(rt, {})[count] = val

    if not per_container:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), facecolor="#1a1a2e")

    # Panel 1: Per-container KB bars grouped by runtime
    counts = sorted({c for d in per_container.values() for c in d})
    width = 0.35
    x = range(len(counts))

    for i, rt in enumerate(["docker", "podman"]):
        if rt not in per_container:
            continue
        vals = [per_container[rt].get(c, 0) for c in counts]
        offset = (i - 0.5) * width
        bars = ax1.bar([xi + offset for xi in x], vals,
                       width=width, label=LABELS.get(rt, rt),
                       color=COLORS.get(rt, "#aaa"), edgecolor="#333", linewidth=0.5)
        for bar, val in zip(bars, vals):
            if val > 0:
                ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10,
                         f"{val:.0f}", ha="center", va="bottom", color="white", fontsize=9)

    ax1.set_xticks(list(x))
    ax1.set_xticklabels([f"{c} cont." for c in counts])
    ax1.legend(facecolor="#16213e", edgecolor="#333", labelcolor="white")
    style_ax(ax1, "Memoria por Contenedor (cgroup)", "KB por contenedor")

    # Panel 2: Daemon/conmon RSS line chart vs container count
    for rt in ["docker", "podman"]:
        if rt not in daemon_rss:
            continue
        d = daemon_rss[rt]
        x_vals = sorted(d.keys())
        y_vals = [d[c] / 1024 for c in x_vals]  # Convert KB to MB
        label = "dockerd RSS" if rt == "docker" else "conmon RSS"
        ax2.plot(x_vals, y_vals, "o-",
                 color=COLORS.get(rt, "#aaa"), label=label,
                 linewidth=2, markersize=8)
        for xv, yv in zip(x_vals, y_vals):
            ax2.text(xv, yv + max(y_vals) * 0.03,
                     f"{yv:.1f}", ha="center", va="bottom", color="white", fontsize=9)

    style_ax(ax2, "Daemon/Conmon RSS vs Contenedores", "RSS (MB)")
    ax2.set_xlabel("Número de contenedores", color="white", fontsize=11)
    ax2.legend(facecolor="#16213e", edgecolor="#333", labelcolor="white")

    save_fig(fig, "memory_cgroup_comparison.png")


def plot_nested_v2():
    """Gráfica 9: Nested v2 — 6 enfoques con resultado."""
    rows = read_csv("nested_v2.csv")
    if not rows:
        return

    approaches = []
    times = []
    colors_list = []
    results = []

    for row in rows:
        rt = row["runtime"]
        approach = row["approach"]
        result = row["result"]
        try:
            time_s = float(row["time_seconds"])
        except (ValueError, KeyError):
            time_s = 0

        label = f"{rt}\n{approach}"
        approaches.append(label)
        results.append(result)

        if result == "success":
            times.append(time_s)
            colors_list.append("#2ecc71")  # green
        else:
            times.append(0.5)  # small bar for visibility
            colors_list.append("#e74c3c")  # red

    if not approaches:
        return

    fig, ax = plt.subplots(figsize=(12, 5), facecolor="#1a1a2e")
    bars = ax.bar(range(len(approaches)), times, color=colors_list,
                  edgecolor="#333", linewidth=0.5)

    for bar, result, time_s, orig_row in zip(bars, results, times, rows):
        if result == "success":
            try:
                real_time = float(orig_row["time_seconds"])
            except (ValueError, KeyError):
                real_time = time_s
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    f"{real_time:.1f}s", ha="center", va="bottom", color="#2ecc71",
                    fontsize=10, fontweight="bold")
        else:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    result.upper(), ha="center", va="bottom", color="#e74c3c",
                    fontsize=10, fontweight="bold")

    ax.set_xticks(range(len(approaches)))
    ax.set_xticklabels(approaches, fontsize=8, color="white")
    style_ax(ax, "Nested Containers: 6 Enfoques", "Tiempo (segundos)")

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor="#2ecc71", edgecolor="#333", label="Success"),
                       Patch(facecolor="#e74c3c", edgecolor="#333", label="Error/Skipped")]
    ax.legend(handles=legend_elements, facecolor="#16213e", edgecolor="#333", labelcolor="white")

    save_fig(fig, "nested_v2_comparison.png")


def plot_summary():
    """Gráfica 6: Resumen general combinado."""
    # Recolectar métricas principales
    metrics = {}

    # Startup
    rows = read_csv("startup.csv")
    for row in rows:
        rt = row["runtime"]
        try:
            val = float(row["value"])
        except (ValueError, KeyError):
            continue
        metrics.setdefault("startup", {}).setdefault(rt, []).append(val)

    # CPU
    rows = read_csv("cpu.csv")
    for row in rows:
        rt = row["runtime"]
        try:
            val = float(row["value"])
        except (ValueError, KeyError):
            continue
        metrics.setdefault("cpu", {}).setdefault(rt, []).append(val)

    if not metrics:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor="#1a1a2e")

    # Panel 1: Startup
    if "startup" in metrics:
        ax = axes[0]
        d = metrics["startup"]
        runtimes = sorted(d.keys(), key=lambda x: {"bare": 0, "docker": 1, "podman": 2}.get(x, 9))
        means = [sum(d[r]) / len(d[r]) for r in runtimes]
        colors = [COLORS.get(r, "#aaa") for r in runtimes]
        labels = [LABELS.get(r, r) for r in runtimes]
        bars = ax.bar(labels, means, color=colors, edgecolor="#333", linewidth=0.5)
        style_ax(ax, "Startup Latency", "Tiempo (ms)")
        for bar, val in zip(bars, means):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(means) * 0.02,
                    f"{val:.0f}", ha="center", va="bottom", color="white", fontsize=10)

    # Panel 2: CPU
    if "cpu" in metrics:
        ax = axes[1]
        d = metrics["cpu"]
        runtimes = sorted(d.keys(), key=lambda x: {"bare": 0, "docker": 1, "podman": 2}.get(x, 9))
        means = [sum(d[r]) / len(d[r]) for r in runtimes]
        colors = [COLORS.get(r, "#aaa") for r in runtimes]
        labels = [LABELS.get(r, r) for r in runtimes]
        bars = ax.bar(labels, means, color=colors, edgecolor="#333", linewidth=0.5)
        style_ax(ax, "CPU Benchmark", "Tiempo (s)")
        for bar, val in zip(bars, means):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(means) * 0.02,
                    f"{val:.1f}", ha="center", va="bottom", color="white", fontsize=10)

    save_fig(fig, "summary.png")


def print_summary():
    """Imprime una tabla resumen en texto."""
    print("\n" + "=" * 60)
    print("  RESUMEN DE BENCHMARKS")
    print("=" * 60)

    # Startup
    rows = read_csv("startup.csv")
    if rows:
        data = {}
        for row in rows:
            rt = row["runtime"]
            try:
                data.setdefault(rt, []).append(float(row["value"]))
            except (ValueError, KeyError):
                pass
        print("\nStartup Latency:")
        for rt in ["bare", "docker", "podman"]:
            if rt in data:
                mean = sum(data[rt]) / len(data[rt])
                print(f"  {LABELS.get(rt, rt):15s} {mean:8.1f} ms")

    # CPU
    rows = read_csv("cpu.csv")
    if rows:
        data = {}
        for row in rows:
            rt = row["runtime"]
            try:
                data.setdefault(rt, []).append(float(row["value"]))
            except (ValueError, KeyError):
                pass
        print("\nCPU (contar hasta 10M):")
        for rt in ["bare", "docker", "podman"]:
            if rt in data:
                mean = sum(data[rt]) / len(data[rt])
                print(f"  {LABELS.get(rt, rt):15s} {mean:8.2f} s")

    # Scale
    rows = read_csv("scale.csv")
    if rows:
        print("\nEscalamiento:")
        for row in rows:
            try:
                rt = row["runtime"]
                count = row["count"]
                time_s = float(row["time_seconds"])
                mem = float(row["memory_mb"])
                print(f"  {LABELS.get(rt, rt):15s} {count:>3s} contenedores: {time_s:6.1f}s, +{mem:.0f} MB")
            except (ValueError, KeyError):
                pass

    # CPU Exec
    rows = read_csv("cpu_exec.csv")
    if rows:
        data = {}
        for row in rows:
            rt = row["runtime"]
            try:
                data.setdefault(rt, []).append(float(row["value"]))
            except (ValueError, KeyError):
                pass
        print("\nCPU Exec (contar hasta 1M, sin startup):")
        for rt in ["bare", "docker", "podman"]:
            if rt in data:
                mean = sum(data[rt]) / len(data[rt])
                print(f"  {LABELS.get(rt, rt):15s} {mean:8.4f} s")

    # Memory Cgroup
    rows = read_csv("memory_cgroup.csv")
    if rows:
        print("\nMemoria Cgroup (por contenedor):")
        for row in rows:
            if row["metric"] == "per_container_kb":
                rt = row["runtime"]
                count = row["count"]
                val = row["value"]
                print(f"  {LABELS.get(rt, rt):15s} {count:>2s} cont: {val:>8s} KB/cont")

    # Nested v2
    rows = read_csv("nested_v2.csv")
    if rows:
        print("\nNested v2:")
        for row in rows:
            rt = row["runtime"]
            approach = row["approach"]
            result = row["result"]
            time_s = row["time_seconds"]
            symbol = "✓" if result == "success" else "✗"
            print(f"  {symbol} {rt}/{approach}: {result} ({time_s}s)")

    print("\n" + "=" * 60)


def main():
    print("Generando gráficas de benchmarks...")
    print(f"Directorio de resultados: {RESULTS_DIR}")
    print()

    plot_startup()
    plot_memory()
    plot_cpu()
    plot_io()
    plot_scale()
    plot_cpu_exec()
    plot_memory_cgroup()
    plot_nested_v2()
    plot_summary()

    print_summary()

    print("\nGráficas generadas:")
    for png in sorted(RESULTS_DIR.glob("*.png")):
        print(f"  {png}")


if __name__ == "__main__":
    main()
