#!/usr/bin/env python3
"""
analyze.py — Lee los CSVs de benchmarks y genera gráficas PNG.

Uso: python3 analyze.py
Requiere: matplotlib (pip install matplotlib)
Lee de: results/exp1_startup.csv, results/exp2_scale.csv, results/exp3_runtime.csv
Escribe en: results/*.png e images/*.png
"""

import csv
import statistics
import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
except ImportError:
    print("Error: matplotlib no está instalado.")
    print("Instálalo con: pip install matplotlib")
    sys.exit(1)

RESULTS_DIR = Path(__file__).parent / "results"
IMAGES_DIR = Path(__file__).parent.parent / "images"

# Colores consistentes
COLORS = {
    "bare": "#6c757d",
    "docker": "#0db7ed",
    "podman": "#892ca0",
    "dind": "#0a8ab5",
    "podman-nested": "#6b1f80",
}

LABELS = {
    "bare": "Bare Metal",
    "docker": "Docker",
    "podman": "Podman",
    "dind": "Docker-in-Docker",
    "podman-nested": "Podman-in-Podman",
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
    """Guarda una figura como PNG en results/ y en images/."""
    path = RESULTS_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
    print(f"  Guardado: {path}")
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


def median_iqr(values):
    """Retorna mediana, Q1, Q3."""
    if not values:
        return 0, 0, 0
    med = statistics.median(values)
    q1 = statistics.median(sorted(values)[:len(values) // 2]) if len(values) > 1 else med
    q3 = statistics.median(sorted(values)[-(len(values) // 2):]) if len(values) > 1 else med
    return med, q1, q3


def plot_exp1_startup():
    """Exp 1: Grouped bar chart — 5 bars (bare, docker/ubuntu, docker/alpine,
    podman/ubuntu, podman/alpine), median + IQR whiskers."""
    rows = read_csv("exp1_startup.csv")
    if not rows:
        return

    # Group by (runtime, image)
    data = {}
    for row in rows:
        key = (row["runtime"], row["image"])
        try:
            data.setdefault(key, []).append(float(row["startup_ms"]))
        except (ValueError, KeyError):
            continue

    if not data:
        return

    # Order: bare, docker/ubuntu, docker/alpine, podman/ubuntu, podman/alpine
    order = [
        ("bare", "none"),
        ("docker", "ubuntu"), ("docker", "alpine"),
        ("podman", "ubuntu"), ("podman", "alpine"),
    ]
    keys = [k for k in order if k in data]
    labels = []
    for rt, img in keys:
        if rt == "bare":
            labels.append("Bare Metal")
        else:
            labels.append(f"{rt.title()}\n{img.title()}")

    medians = []
    q1s = []
    q3s = []
    colors = []
    for k in keys:
        med, q1, q3 = median_iqr(data[k])
        medians.append(med)
        q1s.append(q1)
        q3s.append(q3)
        colors.append(COLORS.get(k[0], "#aaa"))

    # Whisker errors: lower = med - q1, upper = q3 - med
    yerr_low = [m - q for m, q in zip(medians, q1s)]
    yerr_high = [q - m for m, q in zip(medians, q3s)]

    fig, ax = plt.subplots(figsize=(10, 5), facecolor="#1a1a2e")
    bars = ax.bar(range(len(keys)), medians, color=colors,
                  edgecolor="#333", linewidth=0.5,
                  yerr=[yerr_low, yerr_high], capsize=5,
                  error_kw={"color": "white", "linewidth": 1.2})

    for bar, med in zip(bars, medians):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(medians) * 0.04,
                f"{med:.1f} ms", ha="center", va="bottom",
                color="white", fontsize=10)

    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels(labels, fontsize=10, color="white")
    style_ax(ax, "Exp 1: Startup Latency (mediana + IQR)", "Tiempo (ms)")

    save_fig(fig, "exp1_startup.png")


def plot_exp2_scale():
    """Exp 2: 2 panels — launch time vs N (lines), per-container KB + daemon RSS."""
    rows = read_csv("exp2_scale.csv")
    if not rows:
        return

    data = {}
    for row in rows:
        rt = row["runtime"]
        try:
            count = int(row["count"])
            launch = float(row["launch_time_s"])
            per_kb = float(row["per_container_kb"])
            daemon_kb = float(row["daemon_rss_kb"])
        except (ValueError, KeyError):
            continue
        data.setdefault(rt, {"counts": [], "launch": [], "per_kb": [], "daemon_kb": []})
        data[rt]["counts"].append(count)
        data[rt]["launch"].append(launch)
        data[rt]["per_kb"].append(per_kb)
        data[rt]["daemon_kb"].append(daemon_kb)

    if not data:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), facecolor="#1a1a2e")

    # Panel 1: Launch time vs N
    for rt in ["docker", "podman"]:
        if rt not in data:
            continue
        d = data[rt]
        ax1.plot(d["counts"], d["launch"], "o-",
                 color=COLORS.get(rt), label=LABELS.get(rt),
                 linewidth=2, markersize=8)
        for x, y in zip(d["counts"], d["launch"]):
            ax1.text(x, y + max(d["launch"]) * 0.04,
                     f"{y:.2f}s", ha="center", va="bottom",
                     color="white", fontsize=9)

    style_ax(ax1, "Launch Time vs Contenedores", "Tiempo (s)")
    ax1.set_xlabel("Contenedores", color="white", fontsize=11)
    ax1.legend(facecolor="#16213e", edgecolor="#333", labelcolor="white")

    # Panel 2: Per-container KB (bars) + daemon RSS (line)
    all_counts = sorted({c for d in data.values() for c in d["counts"]})
    width = 0.35
    x = list(range(len(all_counts)))

    for i, rt in enumerate(["docker", "podman"]):
        if rt not in data:
            continue
        d = data[rt]
        count_to_kb = dict(zip(d["counts"], d["per_kb"]))
        vals = [count_to_kb.get(c, 0) for c in all_counts]
        offset = (i - 0.5) * width
        bars = ax2.bar([xi + offset for xi in x], vals,
                       width=width, label=f"{LABELS[rt]} /cont",
                       color=COLORS.get(rt), edgecolor="#333", linewidth=0.5,
                       alpha=0.8)
        for bar, val in zip(bars, vals):
            if val > 0:
                ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10,
                         f"{val:.0f}", ha="center", va="bottom",
                         color="white", fontsize=8)

    # Daemon RSS as secondary y-axis
    ax2b = ax2.twinx()
    for rt in ["docker", "podman"]:
        if rt not in data:
            continue
        d = data[rt]
        count_to_daemon = dict(zip(d["counts"], d["daemon_kb"]))
        daemon_vals = [count_to_daemon.get(c, 0) / 1024 for c in all_counts]  # MB
        ax2b.plot(x, daemon_vals, "s--",
                  color=COLORS.get(rt), label=f"{LABELS[rt]} daemon RSS",
                  linewidth=1.5, markersize=6, alpha=0.7)

    ax2.set_xticks(x)
    ax2.set_xticklabels([str(c) for c in all_counts], color="white")
    ax2.set_xlabel("Contenedores", color="white", fontsize=11)
    style_ax(ax2, "Memoria: cgroup + daemon RSS", "KB por contenedor")
    ax2b.set_ylabel("Daemon/Conmon RSS (MB)", color="white", fontsize=10)
    ax2b.tick_params(colors="white")

    # Combined legend
    h1, l1 = ax2.get_legend_handles_labels()
    h2, l2 = ax2b.get_legend_handles_labels()
    ax2.legend(h1 + h2, l1 + l2, facecolor="#16213e", edgecolor="#333",
               labelcolor="white", fontsize=8, loc="upper left")

    save_fig(fig, "exp2_scale.png")


def plot_exp3_runtime():
    """Exp 3: 2 panels — grouped bars per workload + overhead % comparison."""
    rows = read_csv("exp3_runtime.csv")
    if not rows:
        return

    # Group by (runtime, workload)
    data = {}
    for row in rows:
        key = (row["runtime"], row["workload"])
        try:
            data.setdefault(key, []).append(float(row["time_s"]))
        except (ValueError, KeyError):
            continue

    if not data:
        return

    workloads = ["hash", "sort"]
    runtimes = ["bare", "docker", "podman"]
    workload_labels = {"hash": "Hash (SHA-256)", "sort": "Sort (1M ints)"}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), facecolor="#1a1a2e")

    # Panel 1: Grouped bars — median time per workload
    width = 0.25
    for wi, wl in enumerate(workloads):
        ax = ax1
        x_base = wi * (len(runtimes) + 1)
        for ri, rt in enumerate(runtimes):
            key = (rt, wl)
            vals = data.get(key, [])
            if not vals:
                continue
            med = statistics.median(vals)
            x_pos = x_base + ri
            bar = ax.bar(x_pos, med, width=0.7,
                         color=COLORS.get(rt, "#aaa"),
                         edgecolor="#333", linewidth=0.5)
            ax.text(x_pos, med + 0.03,
                    f"{med:.3f}s", ha="center", va="bottom",
                    color="white", fontsize=9)

    # X-axis labels
    tick_positions = []
    tick_labels = []
    for wi, wl in enumerate(workloads):
        x_base = wi * (len(runtimes) + 1)
        tick_positions.append(x_base + 1)  # center of 3 bars
        tick_labels.append(workload_labels[wl])

    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels(tick_labels, color="white", fontsize=11)
    style_ax(ax1, "Tiempo de Ejecución (mediana)", "Tiempo (s)")

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=COLORS[rt], edgecolor="#333",
                             label=LABELS[rt]) for rt in runtimes]
    ax1.legend(handles=legend_elements, facecolor="#16213e",
               edgecolor="#333", labelcolor="white")

    # Panel 2: Overhead % per workload
    overhead_data = {}
    for wl in workloads:
        bare_vals = data.get(("bare", wl), [])
        if not bare_vals:
            continue
        bare_med = statistics.median(bare_vals)
        for rt in ["docker", "podman"]:
            vals = data.get((rt, wl), [])
            if not vals:
                continue
            med = statistics.median(vals)
            pct = ((med - bare_med) / bare_med) * 100
            overhead_data.setdefault(rt, {})[wl] = pct

    x = list(range(len(workloads)))
    for ri, rt in enumerate(["docker", "podman"]):
        if rt not in overhead_data:
            continue
        vals = [overhead_data[rt].get(wl, 0) for wl in workloads]
        offset = (ri - 0.5) * width * 2
        bars = ax2.bar([xi + offset for xi in x], vals,
                       width=width * 2, label=LABELS[rt],
                       color=COLORS.get(rt), edgecolor="#333", linewidth=0.5)
        for bar, val in zip(bars, vals):
            y_pos = bar.get_height() if val >= 0 else bar.get_height() - 1.5
            ax2.text(bar.get_x() + bar.get_width() / 2, y_pos + 0.5,
                     f"{val:+.1f}%", ha="center", va="bottom",
                     color="white", fontsize=10, fontweight="bold")

    ax2.axhline(y=0, color="#666", linewidth=0.8, linestyle="--")
    ax2.set_xticks(x)
    ax2.set_xticklabels([workload_labels[wl] for wl in workloads],
                        color="white", fontsize=11)
    ax2.legend(facecolor="#16213e", edgecolor="#333", labelcolor="white")
    style_ax(ax2, "Overhead vs Bare Metal (%)", "Overhead (%)")

    save_fig(fig, "exp3_runtime.png")


def plot_exp4_nested():
    """Exp 4: 2 panels — startup latency (bars) + CPU overhead (bars) at nesting levels."""
    rows = read_csv("exp4_nested.csv")
    if not rows:
        return

    # Group by (method, metric)
    data = {}
    for row in rows:
        key = (row["method"], row["metric"])
        try:
            data.setdefault(key, []).append(float(row["value"]))
        except (ValueError, KeyError):
            continue

    if not data:
        return

    methods = ["bare", "docker", "dind", "podman", "podman-nested"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), facecolor="#1a1a2e")

    # Panel 1: Startup latency
    startup_meds = []
    startup_colors = []
    startup_labels = []
    startup_yerr_lo = []
    startup_yerr_hi = []
    for m in methods:
        vals = data.get((m, "startup_ms"), [])
        if vals:
            med, q1, q3 = median_iqr(vals)
            startup_meds.append(med)
            startup_yerr_lo.append(med - q1)
            startup_yerr_hi.append(q3 - med)
        else:
            startup_meds.append(0)
            startup_yerr_lo.append(0)
            startup_yerr_hi.append(0)
        startup_colors.append(COLORS.get(m, "#aaa"))
        label = LABELS.get(m, m)
        # Line break for long labels
        if "-" in m or " " in label:
            parts = label.split("-") if "-" in label else label.split(" ", 1)
            label = "\n".join(parts) if len(parts) == 2 else label
        startup_labels.append(label)

    bars1 = ax1.bar(range(len(methods)), startup_meds, color=startup_colors,
                    edgecolor="#333", linewidth=0.5,
                    yerr=[startup_yerr_lo, startup_yerr_hi], capsize=5,
                    error_kw={"color": "white", "linewidth": 1.2})
    for bar, med in zip(bars1, startup_meds):
        ax1.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + max(startup_meds) * 0.03,
                 f"{med:.0f} ms", ha="center", va="bottom",
                 color="white", fontsize=9)

    ax1.set_xticks(range(len(methods)))
    ax1.set_xticklabels(startup_labels, fontsize=9, color="white")
    style_ax(ax1, "Startup Latency por Nivel de Nesting", "Tiempo (ms)")

    # Panel 2: CPU overhead
    cpu_meds = []
    cpu_colors = []
    cpu_labels = []
    cpu_yerr_lo = []
    cpu_yerr_hi = []
    for m in methods:
        vals = data.get((m, "cpu_s"), [])
        if vals:
            med, q1, q3 = median_iqr(vals)
            cpu_meds.append(med)
            cpu_yerr_lo.append(med - q1)
            cpu_yerr_hi.append(q3 - med)
        else:
            cpu_meds.append(0)
            cpu_yerr_lo.append(0)
            cpu_yerr_hi.append(0)
        cpu_colors.append(COLORS.get(m, "#aaa"))
        label = LABELS.get(m, m)
        if "-" in m or " " in label:
            parts = label.split("-") if "-" in label else label.split(" ", 1)
            label = "\n".join(parts) if len(parts) == 2 else label
        cpu_labels.append(label)

    bars2 = ax2.bar(range(len(methods)), cpu_meds, color=cpu_colors,
                    edgecolor="#333", linewidth=0.5,
                    yerr=[cpu_yerr_lo, cpu_yerr_hi], capsize=5,
                    error_kw={"color": "white", "linewidth": 1.2})

    bare_med = cpu_meds[0] if cpu_meds[0] > 0 else 1
    for bar, med in zip(bars2, cpu_meds):
        pct = ((med - bare_med) / bare_med) * 100
        label = f"{med:.3f}s" if med == bare_med else f"{med:.3f}s\n({pct:+.0f}%)"
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + max(cpu_meds) * 0.03,
                 label, ha="center", va="bottom",
                 color="white", fontsize=9)

    ax2.set_xticks(range(len(methods)))
    ax2.set_xticklabels(cpu_labels, fontsize=9, color="white")
    style_ax(ax2, "CPU Overhead (sha256sum 50MB, exec)", "Tiempo (s)")

    fig.suptitle("Exp 4: Nested Container Performance", color="white",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, "exp4_nested.png")


def print_summary():
    """Imprime una tabla resumen en texto."""
    print("\n" + "=" * 60)
    print("  RESUMEN DE BENCHMARKS")
    print("=" * 60)

    # Exp 1
    rows = read_csv("exp1_startup.csv")
    if rows:
        data = {}
        for row in rows:
            key = f"{row['runtime']}/{row['image']}"
            try:
                data.setdefault(key, []).append(float(row["startup_ms"]))
            except (ValueError, KeyError):
                pass
        print("\nExp 1 — Startup Latency (mediana):")
        for key in ["bare/none", "docker/ubuntu", "docker/alpine",
                     "podman/ubuntu", "podman/alpine"]:
            if key in data:
                med = statistics.median(data[key])
                print(f"  {key:20s} {med:8.1f} ms")

    # Exp 2
    rows = read_csv("exp2_scale.csv")
    if rows:
        print("\nExp 2 — Scale (launch time + memory):")
        for row in rows:
            try:
                rt = row["runtime"]
                count = row["count"]
                launch = float(row["launch_time_s"])
                per_kb = float(row["per_container_kb"])
                daemon_kb = float(row["daemon_rss_kb"])
                print(f"  {LABELS.get(rt, rt):10s} {count:>2s} cont: "
                      f"{launch:6.2f}s, {per_kb:.0f} KB/cont, "
                      f"daemon={daemon_kb:.0f} KB")
            except (ValueError, KeyError):
                pass

    # Exp 3
    rows = read_csv("exp3_runtime.csv")
    if rows:
        data = {}
        for row in rows:
            key = (row["runtime"], row["workload"])
            try:
                data.setdefault(key, []).append(float(row["time_s"]))
            except (ValueError, KeyError):
                pass
        print("\nExp 3 — Runtime Overhead (mediana):")
        for wl in ["hash", "sort"]:
            print(f"  {wl}:")
            bare_med = statistics.median(data.get(("bare", wl), [1]))
            for rt in ["bare", "docker", "podman"]:
                vals = data.get((rt, wl), [])
                if vals:
                    med = statistics.median(vals)
                    if rt == "bare":
                        print(f"    {LABELS.get(rt, rt):15s} {med:.4f}s")
                    else:
                        pct = ((med - bare_med) / bare_med) * 100
                        print(f"    {LABELS.get(rt, rt):15s} {med:.4f}s ({pct:+.1f}%)")

    # Exp 4
    rows = read_csv("exp4_nested.csv")
    if rows:
        data = {}
        for row in rows:
            key = (row["method"], row["metric"])
            try:
                data.setdefault(key, []).append(float(row["value"]))
            except (ValueError, KeyError):
                pass
        methods = ["bare", "docker", "dind", "podman", "podman-nested"]
        print("\nExp 4 — Nested Containers:")
        print("  Startup (mediana):")
        for m in methods:
            vals = data.get((m, "startup_ms"), [])
            if vals:
                med = statistics.median(vals)
                print(f"    {LABELS.get(m, m):22s} {med:8.1f} ms")
        print("  CPU sha256sum 50MB (mediana):")
        bare_cpu = statistics.median(data.get(("bare", "cpu_s"), [1]))
        for m in methods:
            vals = data.get((m, "cpu_s"), [])
            if vals:
                med = statistics.median(vals)
                if m == "bare":
                    print(f"    {LABELS.get(m, m):22s} {med:.3f}s")
                else:
                    pct = ((med - bare_cpu) / bare_cpu) * 100
                    print(f"    {LABELS.get(m, m):22s} {med:.3f}s ({pct:+.1f}%)")

    print("\n" + "=" * 60)


def main():
    print("Generando gráficas de benchmarks...")
    print(f"Directorio de resultados: {RESULTS_DIR}")
    print()

    plot_exp1_startup()
    plot_exp2_scale()
    plot_exp3_runtime()
    plot_exp4_nested()

    print_summary()

    print("\nGráficas generadas:")
    for png in sorted(RESULTS_DIR.glob("exp*.png")):
        print(f"  {png}")


if __name__ == "__main__":
    main()
