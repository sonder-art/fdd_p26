#!/usr/bin/env python3
"""
simulations.py — Genera gráficas para el Módulo 15: Arquitectura de Computadoras

Uso:
    cd clase/15_arquitectura_de_computadoras/scripts
    python3 simulations.py

Requiere:
    pip install matplotlib numpy
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
import numpy as np
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPTS_DIR = Path(__file__).parent
MODULE_DIR  = SCRIPTS_DIR.parent
RESULTS_DIR = SCRIPTS_DIR / "results"
IMAGES_DIR  = MODULE_DIR / "images"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# ── Tema visual (consistente con el sitio eva01) ────────────────────────────
BG    = "#1a1a2e"
PANEL = "#16213e"
TEXT  = "#e0e0e0"
GRID  = "#2a2a4e"

COLORS = {
    "cpu": "#0db7ed",
    "gpu": "#892ca0",
    "npu": "#f0a500",
    "tpu": "#2ecc71",
    "other": "#95a5a6",
}

MEM_COLORS = [
    "#e74c3c",  # Registros
    "#e67e22",  # L1
    "#f1c40f",  # L2
    "#2ecc71",  # L3
    "#3498db",  # RAM
    "#8e44ad",  # SSD
    "#7f8c8d",  # HDD
]


def _style_ax(ax):
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)
    ax.tick_params(colors=TEXT, which="both")
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.title.set_color(TEXT)
    ax.yaxis.grid(True, color=GRID, alpha=0.4, linewidth=0.6)
    ax.set_axisbelow(True)


def save_fig(fig, name):
    for dest in (RESULTS_DIR / name, IMAGES_DIR / name):
        fig.savefig(dest, dpi=150, bbox_inches="tight", facecolor=BG)
        print(f"  Guardado: {dest}")
    plt.close(fig)


# ── 1. Jerarquía de memoria ────────────────────────────────────────────────
def plot_memoria_jerarquia():
    levels = [
        ("Registros CPU",  "~0.3 ns",  "< 1 KB",       0),
        ("Caché L1",       "~1 ns",    "32–64 KB",      1),
        ("Caché L2",       "~4 ns",    "256 KB–1 MB",   2),
        ("Caché L3",       "~40 ns",   "4–32 MB",       3),
        ("RAM  (DRAM)",    "~100 ns",  "8–64 GB",       4),
        ("SSD NVMe",       "~0.1 ms",  "512 GB–4 TB",   5),
        ("HDD",            "~10 ms",   "1–20 TB",       6),
    ]
    n = len(levels)
    max_w = 10.0

    fig, ax = plt.subplots(figsize=(13, 7), facecolor=BG)
    ax.set_facecolor(BG)
    ax.axis("off")

    for i, (name, latency, size, _) in enumerate(levels):
        width = 2.5 + (max_w - 2.5) * (i / (n - 1))
        x     = (max_w - width) / 2
        y     = (n - 1 - i) * 1.0

        rect = mpatches.FancyBboxPatch(
            (x, y), width, 0.82,
            boxstyle="round,pad=0.04",
            facecolor=MEM_COLORS[i],
            edgecolor=BG, linewidth=2.5, alpha=0.92,
        )
        ax.add_patch(rect)

        ax.text(max_w / 2, y + 0.41, name,
                ha="center", va="center",
                color="white", fontsize=11, fontweight="bold")

        ax.text(x - 0.25, y + 0.41, latency,
                ha="right", va="center", color="#cccccc", fontsize=9)

        ax.text(x + width + 0.25, y + 0.41, size,
                ha="left", va="center", color="#cccccc", fontsize=9)

    # Column headers
    ax.text(1.0,  n + 0.15, "← latencia",  ha="center", color="#cccccc", fontsize=9, style="italic")
    ax.text(max_w - 1.0, n + 0.15, "capacidad →", ha="center", color="#cccccc", fontsize=9, style="italic")

    # Speed arrow (left)
    ax.annotate("", xy=(-1.3, n - 0.1), xytext=(-1.3, 0.1),
                arrowprops=dict(arrowstyle="->", color=MEM_COLORS[0], lw=2))
    ax.text(-1.3, n / 2, "más\nrápido", ha="center", va="center",
            color=MEM_COLORS[0], fontsize=9, rotation=90)

    # Size arrow (right)
    ax.annotate("", xy=(max_w + 1.3, 0.1), xytext=(max_w + 1.3, n - 0.1),
                arrowprops=dict(arrowstyle="->", color=MEM_COLORS[-2], lw=2))
    ax.text(max_w + 1.3, n / 2, "más\ngrande", ha="center", va="center",
            color=MEM_COLORS[-2], fontsize=9, rotation=90)

    ax.set_xlim(-2.2, max_w + 2.5)
    ax.set_ylim(-0.35, n + 0.55)
    ax.set_title("Jerarquía de Memoria: velocidad vs capacidad",
                 color=TEXT, fontsize=14, fontweight="bold", pad=14)

    save_fig(fig, "memoria_jerarquia.png")


# ── 2. Comparación CPU / GPU / NPU ────────────────────────────────────────
def plot_procesadores_comparacion():
    tasks = [
        "Código\nsecuencial",
        "Álgebra\nlineal (ML)",
        "Inferencia\nML",
        "Entrenamiento\nML",
        "I/O +\nbranching",
    ]
    # Scores 0–5 (conceptual, no benchmarks absolutos)
    cpu = [5.0, 2.0, 2.0, 1.0, 5.0]
    gpu = [1.0, 5.0, 4.0, 5.0, 0.5]
    npu = [0.5, 3.0, 5.0, 1.5, 0.0]

    x     = np.arange(len(tasks))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6), facecolor=BG)
    _style_ax(ax)

    ax.bar(x - width, cpu, width, label="CPU",              color=COLORS["cpu"], alpha=0.9)
    ax.bar(x,         gpu, width, label="GPU",              color=COLORS["gpu"], alpha=0.9)
    ax.bar(x + width, npu, width, label="NPU / Neural Eng.", color=COLORS["npu"], alpha=0.9)

    ax.set_xticks(x)
    ax.set_xticklabels(tasks, color=TEXT, fontsize=10)
    ax.set_ylim(0, 6.2)
    ax.set_ylabel("Rendimiento relativo (1–5)", color=TEXT)
    ax.set_title("CPU vs GPU vs NPU: ¿para qué sirve cada uno?",
                 color=TEXT, fontsize=13, fontweight="bold")
    ax.legend(facecolor=PANEL, labelcolor=TEXT, edgecolor=GRID, fontsize=10)

    ax.text(0.5, -0.18,
            "Escala conceptual — no representa benchmarks absolutos. "
            "El mejor chip depende de la tarea.",
            transform=ax.transAxes, ha="center", color="#888888",
            fontsize=8, style="italic")

    save_fig(fig, "procesadores_comparacion.png")


# ── 3. Costo histórico de un GFLOP ────────────────────────────────────────
def plot_flops_historico():
    # (año, nombre, USD por GFLOP)
    data = [
        (1961, "IBM 7090",           1e10),
        (1984, "Cray X-MP",          4.2e7),
        (1994, "Intel Pentium",      3e4),
        (1997, "Intel Pentium II",   1e3),
        (2001, "AMD Athlon XP",      1e2),
        (2006, "PlayStation 3",      1.0),
        (2008, "AMD Radeon HD 4870", 0.065),
        (2013, "NVIDIA GTX 780",     0.002),
        (2017, "NVIDIA GTX 1080",    3.5e-4),
        (2020, "NVIDIA RTX 3090",    4e-5),
        (2022, "NVIDIA RTX 4090",    1.5e-5),
        (2023, "NVIDIA H100",        2e-6),
    ]

    years = [d[0] for d in data]
    costs = [d[2] for d in data]
    names = [d[1] for d in data]

    point_colors = [
        COLORS["cpu"],   # IBM 7090
        COLORS["cpu"],   # Cray X-MP
        COLORS["cpu"],   # Pentium
        COLORS["cpu"],   # Pentium II
        COLORS["cpu"],   # Athlon
        "#2ecc71",       # PlayStation 3
        COLORS["gpu"],   # Radeon HD 4870
        COLORS["gpu"],   # GTX 780
        COLORS["gpu"],   # GTX 1080
        COLORS["gpu"],   # RTX 3090
        COLORS["gpu"],   # RTX 4090
        COLORS["gpu"],   # H100
    ]

    # Manual label offsets (x_points, y_mult) to avoid overlap
    offsets = [
        ( 0, 3),    # IBM 7090       → above
        (-5, 0.1),  # Cray X-MP      → below-left
        ( 2, 3),    # Pentium        → above
        (-6, 0.1),  # Pentium II     → below-left
        ( 2, 3),    # Athlon         → above
        (-6, 0.1),  # PS3            → below-left
        ( 2, 3),    # HD 4870        → above
        ( 2, 0.1),  # GTX 780        → below
        (-7, 3),    # GTX 1080       → above-left
        ( 2, 0.1),  # RTX 3090       → below
        (-7, 3),    # RTX 4090       → above-left
        ( 2, 0.1),  # H100           → below
    ]

    fig, ax = plt.subplots(figsize=(13, 7), facecolor=BG)
    _style_ax(ax)

    ax.plot(years, costs, color="#444466", linewidth=1.2, alpha=0.6, zorder=1)

    for i, (yr, name, cost) in enumerate(data):
        ax.scatter(yr, cost, color=point_colors[i], s=90, zorder=3, edgecolors="white", linewidths=0.5)
        dx, dy_mult = offsets[i]
        y_text = cost * dy_mult if dy_mult != 0 else cost
        ax.annotate(name, (yr, cost),
                    xytext=(dx, 0), textcoords="offset points",
                    color=TEXT, fontsize=8, va="center")

    ax.set_yscale("log")
    ax.set_xlabel("Año", color=TEXT, fontsize=11)
    ax.set_ylabel("USD por GFLOP  (escala logarítmica)", color=TEXT, fontsize=11)
    ax.set_title("Costo histórico de 1 GFLOP — 5,000,000,000,000× más barato en 62 años",
                 color=TEXT, fontsize=12, fontweight="bold")

    # Y-axis: friendly dollar labels
    def fmt_dollar(val, _):
        if val >= 1e9:  return f"${val/1e9:.0f}B"
        if val >= 1e6:  return f"${val/1e6:.0f}M"
        if val >= 1e3:  return f"${val/1e3:.0f}K"
        if val >= 1:    return f"${val:.0f}"
        return f"${val:.5f}".rstrip("0")

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(fmt_dollar))
    ax.xaxis.grid(True, color=GRID, alpha=0.2, linewidth=0.5)

    # Legend
    cpu_p = mpatches.Patch(color=COLORS["cpu"], label="CPU")
    gpu_p = mpatches.Patch(color=COLORS["gpu"], label="GPU")
    oth_p = mpatches.Patch(color="#2ecc71",     label="Consola")
    ax.legend(handles=[cpu_p, gpu_p, oth_p],
              facecolor=PANEL, labelcolor=TEXT, edgecolor=GRID)

    # Callout
    ax.annotate("5 × 10¹²×\nmás barato",
                xy=(2023, 2e-6), xytext=(2005, 1e3),
                color="#f0a500", fontsize=11, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#f0a500", lw=1.5))

    save_fig(fig, "flops_historico.png")


# ── 4. Chips actuales (por tipo de operación) ─────────────────────────────
def plot_chips_actuales():
    # [FP64 TFLOPS, FP32/BF16 TFLOPS, INT8 TOPS]
    # 0 = operación no relevante para ese chip → no se dibuja
    chips = {
        "Intel i9\n14900K":         [0.30,    0.60,    0],
        "AMD Ryzen\n9 7950X":        [0.26,    0.52,    0],
        "Apple M3\nUltra (CPU)":     [0.60,    1.20,    0],
        "NVIDIA\nRTX 4090":          [1.30,   82.60,  660],
        "NVIDIA\nH100 SXM5":         [67.0, 1979.0,  3958],
        "Apple M3\nNeural Engine":   [0,       0,      38],
        "Google\nTPU v4":            [0,     275.0,    0],
    }

    labels = list(chips.keys())
    fp64 = np.array([v[0] for v in chips.values()], dtype=float)
    fp32 = np.array([v[1] for v in chips.values()], dtype=float)
    int8 = np.array([v[2] for v in chips.values()], dtype=float)

    # Replace 0 with NaN (won't render on log scale)
    fp64 = np.where(fp64 == 0, np.nan, fp64)
    fp32 = np.where(fp32 == 0, np.nan, fp32)
    int8 = np.where(int8 == 0, np.nan, int8)

    x     = np.arange(len(labels))
    width = 0.26

    fig, ax = plt.subplots(figsize=(14, 7), facecolor=BG)
    _style_ax(ax)

    ax.bar(x - width, fp64, width, label="FP64  — cálculo científico",   color="#3498db", alpha=0.9)
    ax.bar(x,         fp32, width, label="FP32 / BF16 — entrenamiento ML", color=COLORS["gpu"], alpha=0.9)
    ax.bar(x + width, int8, width, label="INT8 — inferencia",             color=COLORS["npu"], alpha=0.9)

    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=TEXT, fontsize=9)
    ax.set_ylabel("TFLOPS / TOPS  (escala logarítmica)", color=TEXT)
    ax.set_title("Rendimiento por chip y tipo de operación",
                 color=TEXT, fontsize=13, fontweight="bold")
    ax.legend(facecolor=PANEL, labelcolor=TEXT, edgecolor=GRID, fontsize=9)

    ax.text(0.5, -0.14,
            "Barra ausente = operación no optimizada para ese chip. "
            "H100 BF16 incluye sparsity estructurada (×2). "
            "TPU v4 usa BF16 nativo.",
            transform=ax.transAxes, ha="center", color="#888888",
            fontsize=8, style="italic")

    save_fig(fig, "chips_actuales.png")


# ── 5. Escala de entrenamiento de LLMs ────────────────────────────────────
def plot_llm_escala():
    models = [
        {"name": "BERT-Large",        "year": 2018, "params_B": 0.34,  "flops": 1.5e20, "cost_M": 0.007},
        {"name": "GPT-2",             "year": 2019, "params_B": 1.5,   "flops": 5e19,   "cost_M": 0.05},
        {"name": "T5-11B",            "year": 2020, "params_B": 11,    "flops": 5e21,   "cost_M": 0.5},
        {"name": "GPT-3\n175B",       "year": 2020, "params_B": 175,   "flops": 3.1e23, "cost_M": 5},
        {"name": "PaLM\n540B",        "year": 2022, "params_B": 540,   "flops": 2.5e24, "cost_M": 50},
        {"name": "LLaMA 2\n70B",      "year": 2023, "params_B": 70,    "flops": 2.0e24, "cost_M": 20},
        {"name": "Gemini\nUltra",     "year": 2023, "params_B": 1500,  "flops": 1.5e25, "cost_M": 80},
        {"name": "GPT-4\n(est.)",     "year": 2023, "params_B": 1800,  "flops": 2.0e25, "cost_M": 100},
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), facecolor=BG)

    years  = np.array([m["year"]    for m in models])
    flops  = np.array([m["flops"]   for m in models])
    costs  = np.array([m["cost_M"]  for m in models])
    params = np.array([m["params_B"] for m in models])
    names  =          [m["name"]    for m in models]

    # ── Panel 1: FLOPs entrenamiento vs año ──
    _style_ax(ax1)
    sizes = np.sqrt(params) * 8 + 30
    sc = ax1.scatter(years, flops, s=sizes, c=costs,
                     cmap="plasma", alpha=0.85, zorder=3,
                     edgecolors="white", linewidths=0.5)
    for i, name in enumerate(names):
        ax1.annotate(name, (years[i], flops[i]),
                     xytext=(6, 4), textcoords="offset points",
                     color=TEXT, fontsize=8)
    ax1.set_yscale("log")
    ax1.set_xlabel("Año", color=TEXT)
    ax1.set_ylabel("FLOPs de entrenamiento (escala log)", color=TEXT)
    ax1.set_title("FLOPs para entrenar modelos LLM\n(tamaño del punto ∝ parámetros)",
                  color=TEXT, fontsize=11, fontweight="bold")

    cbar = plt.colorbar(sc, ax=ax1)
    cbar.set_label("Costo estimado (millones USD)", color=TEXT)
    cbar.ax.yaxis.set_tick_params(color=TEXT)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=TEXT)
    cbar.ax.set_facecolor(PANEL)

    # Y-axis friendly labels
    def fmt_flops(v, _):
        exp = int(np.log10(v))
        return f"10^{exp}"
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(fmt_flops))
    ax1.xaxis.grid(True, color=GRID, alpha=0.2, linewidth=0.5)

    # ── Panel 2: Parámetros vs costo ──
    _style_ax(ax2)
    cmap_yr = plt.cm.viridis(np.linspace(0.15, 0.9, len(models)))
    for i, m in enumerate(models):
        ax2.scatter(m["params_B"], m["cost_M"], s=90,
                    color=cmap_yr[i], zorder=3,
                    edgecolors="white", linewidths=0.5)
        ax2.annotate(m["name"], (m["params_B"], m["cost_M"]),
                     xytext=(6, 4), textcoords="offset points",
                     color=TEXT, fontsize=8)
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel("Parámetros (billones)", color=TEXT)
    ax2.set_ylabel("Costo de entrenamiento (millones USD)", color=TEXT)
    ax2.set_title("Parámetros vs Costo de entrenamiento",
                  color=TEXT, fontsize=11, fontweight="bold")
    ax2.xaxis.grid(True, color=GRID, alpha=0.2, linewidth=0.5)

    fig.suptitle("La escala del entrenamiento de LLMs",
                 color=TEXT, fontsize=14, fontweight="bold", y=1.01)

    save_fig(fig, "llm_escala.png")


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    print("Generando gráficas — Módulo 15: Arquitectura de Computadoras")
    print(f"Destino: {IMAGES_DIR}\n")

    print("1/5  Jerarquía de memoria...")
    plot_memoria_jerarquia()

    print("2/5  Comparación CPU / GPU / NPU...")
    plot_procesadores_comparacion()

    print("3/5  Costo histórico de FLOPs...")
    plot_flops_historico()

    print("4/5  Chips actuales por tipo de operación...")
    plot_chips_actuales()

    print("5/5  Escala de entrenamiento de LLMs...")
    plot_llm_escala()

    imgs = list(IMAGES_DIR.glob("*.png"))
    print(f"\nListo — {len(imgs)} imágenes generadas.")
    for p in sorted(imgs):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
