"""
generar_graficas.py  (v2 — rewrite-module-16-pedagogy)
Genera todas las imágenes del módulo 16 de computo.

Requiere: matplotlib, numpy
Uso:
  python3 clase/16_computo/scripts/generar_graficas.py

Las imágenes se guardan en:
  clase/16_computo/images/
"""

import csv
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
except ImportError as e:
    raise SystemExit(f"Falta dependencia: {e}. Instala con: pip install matplotlib numpy")

SCRIPT_DIR  = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR / "results"
IMAGES_DIR  = SCRIPT_DIR.parent / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# ── Tema Eva01 ────────────────────────────────────────────────────────────────
BG       = "#1a1a2e"
FG       = "#e0e0e0"
ACCENT1  = "#7b2d8b"   # violeta
ACCENT2  = "#00a8cc"   # cian
ACCENT3  = "#e94560"   # rojo coral
ACCENT4  = "#f5a623"   # naranja
ACCENT5  = "#43b581"   # verde
GRID_CLR = "#2a2a4e"
WAIT_CLR = "#2e3060"   # azul oscuro para wait (diferente al BG pero discreto)

# Parámetros estándar de tareas I/O-bound (usados en M1, M2, M4, comparación)
E1     = 0.3    # duración primer exec
W      = 1.2    # duración wait
E2     = 0.2    # duración segundo exec
T_TASK = E1 + W + E2   # 1.7s por tarea


# ── Helpers ───────────────────────────────────────────────────────────────────
def apply_theme(fig, ax_list):
    fig.patch.set_facecolor(BG)
    for ax in ax_list:
        ax.set_facecolor(BG)
        ax.tick_params(colors=FG, labelsize=9)
        ax.xaxis.label.set_color(FG)
        ax.yaxis.label.set_color(FG)
        ax.title.set_color(FG)
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID_CLR)
        ax.grid(color=GRID_CLR, linestyle="--", linewidth=0.5, alpha=0.5, axis="x")


def hbar(ax, y, s, e, color, alpha=0.9, hatch=None, height=0.5):
    """Barra horizontal de Gantt."""
    ax.barh(y, e - s, left=s, height=height, color=color, alpha=alpha,
            linewidth=0, hatch=hatch, edgecolor=FG if hatch else None)


def save(fig, name):
    out = IMAGES_DIR / name
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out}")


def legend_exec_wait(ax, extra=None, loc="upper right"):
    handles = [
        mpatches.Patch(color=ACCENT2, alpha=0.9, label="exec(τᵢ) — CPU activa"),
        mpatches.Patch(facecolor=WAIT_CLR, alpha=0.9, hatch="///",
                       edgecolor=FG, label="wait(τᵢ) — I/O en progreso"),
    ]
    if extra:
        handles += extra
    ax.legend(handles=handles, facecolor=BG, labelcolor=FG, fontsize=8, loc=loc)


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


# ─────────────────────────────────────────────────────────────────────────────
# gantt_m1.png — Secuencial
# ─────────────────────────────────────────────────────────────────────────────
def gantt_m1():
    offsets = [0, T_TASK, 2 * T_TASK]
    T_total = 3 * T_TASK        # 5.1s
    idle_total = 3 * W           # 3.6s

    fig, ax = plt.subplots(figsize=(11, 3.8))
    apply_theme(fig, [ax])

    task_ys = [2, 1, 0]
    colors   = [ACCENT2, ACCENT3, ACCENT4]
    labels   = ["τ₁", "τ₂", "τ₃"]

    for off, y, color, label in zip(offsets, task_ys, colors, labels):
        hbar(ax, y, off,           off + E1,         color)
        hbar(ax, y, off + E1,      off + E1 + W,     WAIT_CLR, 0.9, "///")
        hbar(ax, y, off + E1 + W,  off + T_TASK,     color)
        ax.text(-0.12, y, label, ha="right", va="center", color=FG, fontsize=10)

    # CPU row
    cpu_y = -1
    ax.text(-0.12, cpu_y, "CPU", ha="right", va="center",
            color=FG, fontsize=9, fontweight="bold")
    for off in offsets:
        hbar(ax, cpu_y, off,          off + E1,         ACCENT5, height=0.4)
        hbar(ax, cpu_y, off + E1,     off + E1 + W,     "#1e1e3a", 0.9, height=0.4)
        hbar(ax, cpu_y, off + E1 + W, off + T_TASK,     ACCENT5, height=0.4)
        ax.text(off + E1 + W / 2, cpu_y, "idle", ha="center", va="center",
                color=FG, fontsize=7, alpha=0.7)

    ax.set_xlim(-0.25, T_total + 0.3)
    ax.set_ylim(-1.6, 2.9)
    ax.set_xlabel("Tiempo (s)", color=FG)
    ax.set_title(
        f"M1 — Secuencial: una tarea a la vez  "
        f"(T_total = {T_total:.1f}s,  CPU idle = {idle_total:.1f}s = {idle_total/T_total*100:.0f}%)",
        color=FG, fontsize=11)
    ax.set_yticks([])

    cpu_p = mpatches.Patch(color=ACCENT5, alpha=0.9, label="CPU ocupada")
    legend_exec_wait(ax, extra=[cpu_p])
    fig.tight_layout()
    save(fig, "gantt_m1.png")


# ─────────────────────────────────────────────────────────────────────────────
# gantt_m2.png — Async no concurrent (await secuencial)
# ─────────────────────────────────────────────────────────────────────────────
def gantt_m2():
    """M2: infraestructura async existe, pero await-amos una tarea a la vez."""
    offsets = [0, T_TASK, 2 * T_TASK]
    T_total = 3 * T_TASK

    fig, ax = plt.subplots(figsize=(11, 3.8))
    apply_theme(fig, [ax])

    for off, y, color, label in zip(offsets, [2, 1, 0], [ACCENT2, ACCENT3, ACCENT4], ["τ₁", "τ₂", "τ₃"]):
        hbar(ax, y, off,           off + E1,         color)
        hbar(ax, y, off + E1,      off + E1 + W,     WAIT_CLR, 0.9, "///")
        hbar(ax, y, off + E1 + W,  off + T_TASK,     color)
        ax.text(-0.12, y, label, ha="right", va="center", color=FG, fontsize=10)

    cpu_y = -1
    ax.text(-0.12, cpu_y, "CPU", ha="right", va="center",
            color=FG, fontsize=9, fontweight="bold")
    for off in offsets:
        hbar(ax, cpu_y, off,          off + E1,         ACCENT5, height=0.4)
        hbar(ax, cpu_y, off + E1,     off + E1 + W,     "#1e1e3a", 0.9, height=0.4)
        hbar(ax, cpu_y, off + E1 + W, off + T_TASK,     ACCENT5, height=0.4)
        ax.text(off + E1 + W / 2, cpu_y, "idle", ha="center", va="center",
                color=FG, fontsize=7, alpha=0.7)

    # Annotación: el problema de M2
    ax.annotate(
        "exec(τⱼ) ∩ wait(τᵢ) = ∅\nawait secuencial desperdicia\nlas esperas I/O",
        xy=(T_TASK + E1/2, 0.0), xytext=(T_TASK + 0.8, 1.6),
        color=ACCENT3, fontsize=8,
        arrowprops=dict(arrowstyle="->", color=ACCENT3, lw=1.0),
        bbox=dict(facecolor=BG, edgecolor=ACCENT3, boxstyle="round,pad=0.3", alpha=0.85))

    ax.set_xlim(-0.25, T_total + 0.3)
    ax.set_ylim(-1.6, 2.9)
    ax.set_xlabel("Tiempo (s)", color=FG)
    ax.set_title(
        f"M2 — Async no concurrent: await secuencial = igual que M1  (T_total = {T_total:.1f}s)",
        color=FG, fontsize=11)
    ax.set_yticks([])
    legend_exec_wait(ax)
    fig.tight_layout()
    save(fig, "gantt_m2.png")


# ─────────────────────────────────────────────────────────────────────────────
# gantt_m3.png — Concurrent no async (time-slicing CPU-bound, GIL)
# ─────────────────────────────────────────────────────────────────────────────
def gantt_m3():
    """M3: 2 hilos CPU-bound rondando con quantum q en 1 core — GIL → sin speedup."""
    q         = 0.25
    T_cpu     = 1.5      # CPU real por tarea
    n_quanta  = int(T_cpu / q)   # 6
    T_total   = 2 * T_cpu        # 3.0s (sin speedup)

    fig, ax = plt.subplots(figsize=(11, 3.2))
    apply_theme(fig, [ax])

    for task_i, (color, label) in enumerate(zip([ACCENT2, ACCENT3], ["τ₁ (CPU-bound)", "τ₂ (CPU-bound)"])):
        y = 1 - task_i
        t = task_i * q
        for _ in range(n_quanta):
            hbar(ax, y, t, t + q - 0.01, color, 0.85)
            t += 2 * q
        ax.text(-0.12, y, label, ha="right", va="center", color=FG, fontsize=9)

    # CPU row — 100% ocupada
    cpu_y = -1
    ax.text(-0.12, cpu_y, "CPU", ha="right", va="center",
            color=FG, fontsize=9, fontweight="bold")
    hbar(ax, cpu_y, 0, T_total, ACCENT5, 0.85, height=0.4)
    ax.text(T_total / 2, cpu_y, "100% ocupada  (GIL: solo 1 hilo ejecuta bytecode a la vez)",
            ha="center", va="center", color=BG, fontsize=8, fontweight="bold")

    # Marcas de context switch
    for t in np.arange(q, T_total, q):
        ax.axvline(t, color=FG, alpha=0.12, linewidth=0.8, linestyle=":")

    ax.annotate(
        f"T_total = {T_total:.1f}s = T secuencial\n"
        "overhead de contexto +\nsin paralelismo real (GIL)",
        xy=(T_total - 0.1, 0.5), xytext=(T_total - 1.4, 1.2),
        ha="center", color=FG, fontsize=8,
        arrowprops=dict(arrowstyle="->", color=FG, lw=0.8),
        bbox=dict(facecolor=BG, edgecolor=GRID_CLR, boxstyle="round,pad=0.3"))

    ax.set_xlim(-0.25, T_total + 0.3)
    ax.set_ylim(-1.5, 1.9)
    ax.set_xlabel("Tiempo (s)", color=FG)
    ax.set_title(
        "M3 — Concurrent no async: time-slicing CPU-bound  "
        "(sin wait real, GIL → Speedup ≈ 1×)",
        color=FG, fontsize=11)
    ax.set_yticks([])

    h1 = mpatches.Patch(color=ACCENT2, alpha=0.85, label="τ₁ exec (quantum q=0.25s)")
    h2 = mpatches.Patch(color=ACCENT3, alpha=0.85, label="τ₂ exec (quantum q=0.25s)")
    ax.legend(handles=[h1, h2], facecolor=BG, labelcolor=FG, fontsize=8, loc="upper right")
    fig.tight_layout()
    save(fig, "gantt_m3.png")


# ─────────────────────────────────────────────────────────────────────────────
# gantt_m4.png — Concurrent + async (event loop), idle correcto
# ─────────────────────────────────────────────────────────────────────────────
def gantt_m4():
    """M4: asyncio.gather — tareas I/O-bound escalonadas. Idle principal anotado."""
    # τᵢ empieza su exec cuando la anterior hace await
    # τ₁: exec=[0,    0.3],  wait=[0.3, 1.5],  exec=[1.5, 1.7]
    # τ₂: exec=[0.3,  0.6],  wait=[0.6, 1.8],  exec=[1.8, 2.0]
    # τ₃: exec=[0.6,  0.9],  wait=[0.9, 2.1],  exec=[2.1, 2.3]
    tasks_m4 = [
        ("τ₁", 0.0,   E1,   E1,    E1+W,    E1+W,    T_TASK,      ACCENT2),
        ("τ₂", E1,   2*E1,  2*E1,  2*E1+W,  2*E1+W,  2*E1+W+E2,  ACCENT3),
        ("τ₃", 2*E1, 3*E1,  3*E1,  3*E1+W,  3*E1+W,  3*E1+W+E2,  ACCENT4),
    ]
    T_m4       = 3*E1 + W + E2   # 2.3s
    idle_main  = E1 + W - 3*E1   # = W - 2*E1 = 0.6s  ([0.9, 1.5])
    idle_total_m1 = 3 * W        # 3.6s

    fig, ax = plt.subplots(figsize=(11, 3.8))
    apply_theme(fig, [ax])

    task_ys = [2, 1, 0]
    for i, (label, e1s, e1e, ws, we, e2s, e2e, color) in enumerate(tasks_m4):
        y = task_ys[i]
        hbar(ax, y, e1s, e1e, color)
        hbar(ax, y, ws,  we,  WAIT_CLR, 0.9, "///")
        hbar(ax, y, e2s, e2e, color)
        ax.text(-0.08, y, label, ha="right", va="center", color=FG, fontsize=10)

    # CPU row
    cpu_y = -1
    ax.text(-0.08, cpu_y, "CPU", ha="right", va="center",
            color=FG, fontsize=9, fontweight="bold")
    # Exec escalonados iniciales
    hbar(ax, cpu_y, 0, 3*E1, ACCENT5, height=0.4)
    # Idle principal (todas en wait simultáneamente)
    hbar(ax, cpu_y, 3*E1, E1+W, "#1e1e3a", 0.9, height=0.4)
    ax.text((3*E1 + E1+W)/2, cpu_y, f"idle\n{idle_main:.1f}s",
            ha="center", va="center", color=FG, fontsize=7)
    # Execs finales (uno a la vez, con pequeños idle entre ellos)
    hbar(ax, cpu_y, E1+W,    T_TASK,       ACCENT5, height=0.4)   # τ₁
    hbar(ax, cpu_y, T_TASK,  2*E1+W,       "#1e1e3a", 0.5, height=0.4)
    hbar(ax, cpu_y, 2*E1+W,  2*E1+W+E2,   ACCENT5, height=0.4)   # τ₂
    hbar(ax, cpu_y, 2*E1+W+E2, 3*E1+W,    "#1e1e3a", 0.5, height=0.4)
    hbar(ax, cpu_y, 3*E1+W,  3*E1+W+E2,   ACCENT5, height=0.4)   # τ₃

    # Resaltar ventana de idle principal
    ax.axvspan(3*E1, E1+W, alpha=0.07, color=ACCENT3, ymin=0.0, ymax=0.97)
    ax.annotate("", xy=(E1+W, 2.15), xytext=(3*E1, 2.15),
                arrowprops=dict(arrowstyle="<->", color=ACCENT3, lw=1.5))
    ax.text((3*E1 + E1+W)/2, 2.32,
            f"idle principal: {idle_main:.1f}s\n(M1 idle total: {idle_total_m1:.1f}s → 6× menor)",
            ha="center", va="bottom", color=ACCENT3, fontsize=8,
            bbox=dict(facecolor=BG, edgecolor=ACCENT3, boxstyle="round,pad=0.2", alpha=0.85))

    ax.set_xlim(-0.15, T_m4 + 0.3)
    ax.set_ylim(-1.6, 2.95)
    ax.set_xlabel("Tiempo (s)", color=FG)
    ax.set_title(
        f"M4 — Concurrent + async: T_total = {T_m4:.1f}s  (vs M1: {3*T_TASK:.1f}s)",
        color=FG, fontsize=11)
    ax.set_yticks([])

    cpu_p = mpatches.Patch(color=ACCENT5, alpha=0.9, label="CPU ocupada")
    legend_exec_wait(ax, extra=[cpu_p])
    fig.tight_layout()
    save(fig, "gantt_m4.png")


# ─────────────────────────────────────────────────────────────────────────────
# gantt_m5a.png — Paralelo puro (2 cores, CPU-bound)
# ─────────────────────────────────────────────────────────────────────────────
def gantt_m5a():
    """M5a: 2 procesos CPU-bound ejecutando simultáneamente en 2 cores."""
    T_exec = 1.5

    fig, ax = plt.subplots(figsize=(8, 2.8))
    apply_theme(fig, [ax])

    for y, color, label in zip([1, 0], [ACCENT2, ACCENT3],
                                ["τ₁ (CPU-bound)", "τ₂ (CPU-bound)"]):
        hbar(ax, y, 0, T_exec, color)
        ax.text(-0.08, y, label, ha="right", va="center", color=FG, fontsize=9)

    # Marca de simultaneidad
    t_mid = T_exec / 2
    ax.axvline(t_mid, color=ACCENT4, linewidth=1.5, linestyle="--", alpha=0.8)
    ax.text(t_mid + 0.05, 1.55,
            "|ExecutandoEn(t)| = 2\n(paralelismo real — 2 cores)",
            color=ACCENT4, fontsize=9,
            bbox=dict(facecolor=BG, edgecolor=ACCENT4, boxstyle="round,pad=0.3", alpha=0.85))

    ax.set_xlim(-0.2, T_exec + 0.8)
    ax.set_ylim(-0.5, 2.2)
    ax.set_xlabel("Tiempo (s)", color=FG)
    ax.set_title(
        f"M5a — Paralelo: T_total = {T_exec:.1f}s  "
        f"(vs secuencial: {2*T_exec:.1f}s → speedup 2×, P=2)",
        color=FG, fontsize=11)
    ax.set_yticks([])

    h1 = mpatches.Patch(color=ACCENT2, alpha=0.9, label="τ₁ en Core 1")
    h2 = mpatches.Patch(color=ACCENT3, alpha=0.9, label="τ₂ en Core 2")
    ax.legend(handles=[h1, h2], facecolor=BG, labelcolor=FG, fontsize=8, loc="upper right")
    fig.tight_layout()
    save(fig, "gantt_m5a.png")


# ─────────────────────────────────────────────────────────────────────────────
# gantt_m5b.png — asyncio + ProcessPoolExecutor (Chatbot Scenario B)
# ─────────────────────────────────────────────────────────────────────────────
def gantt_m5b():
    """M5b: event loop maneja I/O; workers paralelos hacen inferencia CPU-bound.

    Tiempos representativos (proporcionales, no a escala exacta) para que
    todos los segmentos sean visibles:
      recv+BD+schedule ≈ 0.5 unidades de display
      inference LLM    ≈ 4.0 unidades de display  (dominante)
    """
    # Unidades de display (≈proporcionales al tiempo real)
    D_recv  = 0.15   # recv+parse (~1ms)
    D_bd    = 0.35   # BD query wait (~50ms)
    D_sched = 0.08   # schedule run_in_executor (~instantáneo)
    D_infer = 4.0    # inferencia LLM local (~2s)  — domina
    D_send  = 0.10   # send response (~5ms)

    # 3 solicitudes llegan escalonadas
    req_gap  = D_recv   # gap entre solicitudes

    fig, ax = plt.subplots(figsize=(12, 4.2))
    apply_theme(fig, [ax])

    el_y = 3   # event loop row
    ax.text(-0.15, el_y, "Event\nloop", ha="right", va="center",
            color=FG, fontsize=8, fontweight="bold")

    colors_req = [ACCENT2, ACCENT3, ACCENT4]
    infer_starts = []

    for i, color in enumerate(colors_req):
        off = i * req_gap
        # recv
        hbar(ax, el_y, off, off + D_recv, color, height=0.45)
        # BD wait
        hbar(ax, el_y, off + D_recv, off + D_recv + D_bd, WAIT_CLR, 0.9, "///", height=0.45)
        # schedule
        s_sched = off + D_recv + D_bd
        hbar(ax, el_y, s_sched, s_sched + D_sched, color, height=0.45)
        # waiting for future (hatched gray, event loop libre para otras cosas)
        s_infer = s_sched + D_sched
        infer_starts.append(s_infer)
        hbar(ax, el_y, s_infer, s_infer + D_infer, "#252540", 0.7, height=0.45)
        ax.text((s_infer + s_infer + D_infer) / 2, el_y,
                "espera\nfuture", ha="center", va="center", color=FG, fontsize=6.5, alpha=0.6)
        # send
        hbar(ax, el_y, s_infer + D_infer, s_infer + D_infer + D_send, color, height=0.45)
        # Request label
        ax.text(off + D_recv / 2, el_y + 0.3, f"req{i+1}",
                ha="center", va="bottom", color=color, fontsize=7)

    # Worker rows
    worker_ys     = [2, 1, 0]
    worker_labels = ["Worker 1\n(proceso)", "Worker 2\n(proceso)", "Worker 3\n(proceso)"]

    for wy, wlabel, color, infer_s in zip(worker_ys, worker_labels, colors_req, infer_starts):
        ax.text(-0.15, wy, wlabel, ha="right", va="center", color=FG, fontsize=8)
        hbar(ax, wy, infer_s, infer_s + D_infer, color, 0.9, height=0.45)
        ax.text(infer_s + D_infer / 2, wy,
                "inferencia LLM local  (~2s CPU)",
                ha="center", va="center", color=BG, fontsize=8, fontweight="bold")

    # Flechas event loop → workers
    for color, infer_s, wy in zip(colors_req, infer_starts, worker_ys):
        ax.annotate("", xy=(infer_s, wy + 0.25), xytext=(infer_s, el_y - 0.25),
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.0, alpha=0.6))

    T_total = infer_starts[0] + D_infer + D_send

    ax.annotate(
        f"3 inferencias paralelas:\nT_total ≈ 1× T_infer\n(no 3× T_infer)",
        xy=(infer_starts[2] + D_infer * 0.5, 0.5),
        xytext=(infer_starts[2] + D_infer * 0.5, -0.45),
        ha="center", color=FG, fontsize=8,
        arrowprops=dict(arrowstyle="->", color=FG, lw=0.8),
        bbox=dict(facecolor=BG, edgecolor=GRID_CLR, boxstyle="round,pad=0.3"))

    ax.set_xlim(-0.25, T_total + 0.2)
    ax.set_ylim(-0.9, 4.1)
    ax.set_xlabel("Tiempo (representativo — no a escala exacta)", color=FG)
    ax.set_title(
        "M5b — asyncio + ProcessPoolExecutor: I/O en event loop, inferencia en workers paralelos",
        color=FG, fontsize=11)
    ax.set_yticks([])

    exec_p  = mpatches.Patch(color=ACCENT2, alpha=0.9, label="exec(τᵢ) — CPU")
    wait_p  = mpatches.Patch(facecolor=WAIT_CLR, alpha=0.9, hatch="///",
                              edgecolor=FG, label="wait — I/O (event loop libre)")
    infer_p = mpatches.Patch(color=ACCENT4, alpha=0.9, label="inferencia CPU en worker")
    ax.legend(handles=[exec_p, wait_p, infer_p], facecolor=BG, labelcolor=FG,
              fontsize=8, loc="upper left")
    fig.tight_layout()
    save(fig, "gantt_m5b.png")


# ─────────────────────────────────────────────────────────────────────────────
# gantt_comparison.png — M1–M4 apilados (mismas tareas I/O-bound)
# ─────────────────────────────────────────────────────────────────────────────
def gantt_comparison():
    """4 paneles: M1, M2, M3, M4 con el mismo conjunto de tareas I/O-bound."""
    T_m1 = 3 * T_TASK          # 5.1s
    T_m4 = 3*E1 + W + E2       # 2.3s

    fig, axes = plt.subplots(4, 1, figsize=(13, 10))
    apply_theme(fig, axes)

    offsets_seq = [0, T_TASK, 2*T_TASK]
    colors3     = [ACCENT2, ACCENT3, ACCENT4]

    def draw_seq(ax, title, annotate_fn=None):
        for off, y, color, label in zip(offsets_seq, [2,1,0], colors3, ["τ₁","τ₂","τ₃"]):
            hbar(ax, y, off,          off + E1,    color)
            hbar(ax, y, off + E1,     off + E1+W,  WAIT_CLR, 0.9, "///")
            hbar(ax, y, off + E1+W,   off + T_TASK, color)
            ax.text(-0.15, y, label, ha="right", va="center", color=FG, fontsize=9)
        if annotate_fn:
            annotate_fn(ax)
        ax.set_xlim(-0.25, T_m1 + 0.3)
        ax.set_ylim(-0.5, 2.8)
        ax.set_yticks([])
        ax.set_title(title, color=FG, fontsize=9)

    # ── M1
    draw_seq(axes[0],
             f"M1 — Secuencial   T_total = {T_m1:.1f}s  |  CPU idle = {3*W:.1f}s  ({3*W/T_m1*100:.0f}%)")

    # ── M2 (idéntico visual a M1)
    draw_seq(axes[1],
             f"M2 — Async no concurrent   T_total = {T_m1:.1f}s  "
             f"(await secuencial ≡ M1, exec ∩ wait = ∅ entre tareas)")

    # ── M3 — CPU-bound time-slicing (diferente tipo de tarea, CPU siempre ocupada)
    ax3 = axes[2]
    q = 0.25; T_m3 = 3.0; n_q = 6
    for task_i, (color, label) in enumerate(zip([ACCENT2, ACCENT3], ["τ₁ cpu", "τ₂ cpu"])):
        y = 1 - task_i
        t = task_i * q
        for _ in range(n_q):
            hbar(ax3, y, t, t + q - 0.01, color, 0.85)
            t += 2 * q
        ax3.text(-0.15, y, label, ha="right", va="center", color=FG, fontsize=9)
    ax3.set_xlim(-0.25, T_m1 + 0.3)
    ax3.set_ylim(-0.5, 1.9)
    ax3.set_yticks([])
    ax3.set_title(
        f"M3 — Concurrent no async   T_total = {T_m3:.1f}s  "
        "(CPU 100% ocupada, GIL → speedup ≈ 1×, no hay wait real)",
        color=FG, fontsize=9)

    # ── M4 — event loop
    ax4 = axes[3]
    tasks_m4 = [
        ("τ₁", 0.0,  E1,  E1,   E1+W,   E1+W,   T_TASK,    ACCENT2),
        ("τ₂", E1,  2*E1, 2*E1, 2*E1+W, 2*E1+W, 2*E1+W+E2, ACCENT3),
        ("τ₃", 2*E1,3*E1, 3*E1, 3*E1+W, 3*E1+W, 3*E1+W+E2, ACCENT4),
    ]
    for i, (label, e1s,e1e,ws,we,e2s,e2e,color) in enumerate(tasks_m4):
        y = [2,1,0][i]
        hbar(ax4, y, e1s, e1e, color)
        hbar(ax4, y, ws,  we,  WAIT_CLR, 0.9, "///")
        hbar(ax4, y, e2s, e2e, color)
        ax4.text(-0.15, y, label, ha="right", va="center", color=FG, fontsize=9)

    idle_s, idle_e = 3*E1, E1+W
    ax4.axvspan(idle_s, idle_e, alpha=0.1, color=ACCENT3)
    ax4.annotate("", xy=(idle_e, 2.2), xytext=(idle_s, 2.2),
                 arrowprops=dict(arrowstyle="<->", color=ACCENT3, lw=1.5))
    ax4.text((idle_s+idle_e)/2, 2.38, f"idle {idle_e-idle_s:.1f}s  (6× < M1)",
             ha="center", color=ACCENT3, fontsize=8)
    ax4.set_xlim(-0.25, T_m1 + 0.3)
    ax4.set_ylim(-0.5, 2.8)
    ax4.set_yticks([])
    ax4.set_title(
        f"M4 — Concurrent + async (event loop)   T_total = {T_m4:.1f}s  "
        f"(2.2× más rápido que M1)",
        color=FG, fontsize=9)

    axes[-1].set_xlabel("Tiempo (s)", color=FG)

    exec_p = mpatches.Patch(color=ACCENT2, alpha=0.9, label="exec(τᵢ)")
    wait_p = mpatches.Patch(facecolor=WAIT_CLR, alpha=0.9, hatch="///",
                            edgecolor=FG, label="wait(τᵢ) — I/O")
    axes[0].legend(handles=[exec_p, wait_p], facecolor=BG, labelcolor=FG,
                   fontsize=8, loc="upper right")

    fig.suptitle("Comparación M1–M4: el mismo conjunto de tareas I/O-bound, distinto modelo",
                 color=FG, fontsize=12, y=1.005)
    fig.tight_layout()
    save(fig, "gantt_comparison.png")


# ─────────────────────────────────────────────────────────────────────────────
# chatbot_timeline.png — Escenario A vs Escenario B (% breakdown)
# ─────────────────────────────────────────────────────────────────────────────
def chatbot_timeline():
    """Barra 100% que muestra exec vs wait por escenario del chatbot."""
    # Tiempos reales (segundos)
    A_ops = [
        ("recv\n1ms",       0.001, "exec"),
        ("read BD\n50ms",   0.050, "wait"),
        ("LLM API\n1500ms", 1.500, "wait"),
        ("send\n5ms",       0.005, "wait"),
    ]
    B_ops = [
        ("recv\n1ms",            0.001, "exec"),
        ("read BD\n50ms",        0.050, "wait"),
        ("inferencia\n2000ms",   2.000, "exec"),
        ("send\n5ms",            0.005, "wait"),
    ]

    fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(12, 4.8))
    apply_theme(fig, [ax_a, ax_b])

    def draw(ax, ops, scenario_title):
        T_total = sum(d for _, d, _ in ops)
        T_exec  = sum(d for _, d, t in ops if t == "exec")
        T_wait  = sum(d for _, d, t in ops if t == "wait")

        x = 0.0
        for label, dur, op_type in ops:
            pct   = dur / T_total * 100
            color = ACCENT2 if op_type == "exec" else WAIT_CLR
            hatch = None if op_type == "exec" else "///"
            ax.barh(0, pct, left=x, height=0.55,
                    color=color, alpha=0.9, linewidth=0.5,
                    edgecolor=FG, hatch=hatch)
            mid = x + pct / 2
            if pct >= 8:
                ax.text(mid, 0, label, ha="center", va="center",
                        color=FG if op_type == "wait" else BG,
                        fontsize=9, fontweight="bold")
            elif pct >= 1.5:
                ax.text(mid, 0.38, label, ha="center", va="bottom",
                        color=FG, fontsize=7.5)
            else:
                # Very thin segment: bracket below
                ax.annotate(label, xy=(mid, -0.28), ha="center", va="top",
                            color=FG, fontsize=7,
                            arrowprops=dict(arrowstyle="-", color=FG, lw=0.6))
            x += pct

        ax.set_title(
            f"{scenario_title}\n"
            f"exec = {T_exec*1000:.0f}ms ({T_exec/T_total*100:.1f}%)   "
            f"wait = {T_wait*1000:.0f}ms ({T_wait/T_total*100:.1f}%)",
            color=FG, fontsize=10)
        ax.set_xlim(0, 100)
        ax.set_ylim(-0.6, 0.95)
        ax.set_yticks([])
        ax.set_xlabel("% del tiempo total de la petición", color=FG)

    draw(ax_a, A_ops,
         "Escenario A — LLM como API remota  →  I/O-bound  →  M4 (asyncio) es óptimo")
    draw(ax_b, B_ops,
         "Escenario B — LLM local en hardware propio  →  CPU-bound  →  M5b (asyncio + ProcessPoolExecutor) es óptimo")

    exec_p = mpatches.Patch(color=ACCENT2, alpha=0.9, label="exec — CPU ocupada")
    wait_p = mpatches.Patch(facecolor=WAIT_CLR, alpha=0.9, hatch="///",
                            edgecolor=FG, label="wait — CPU libre (I/O o red)")
    ax_a.legend(handles=[exec_p, wait_p], facecolor=BG, labelcolor=FG,
                fontsize=9, loc="upper right")

    fig.suptitle(
        "Descomposición exec / wait por escenario: misma petición, distinto cuello de botella",
        color=FG, fontsize=11, y=1.01)
    fig.tight_layout()
    save(fig, "chatbot_timeline.png")


# ─────────────────────────────────────────────────────────────────────────────
# Imágenes de benchmarks y análisis (conservadas del v1)
# ─────────────────────────────────────────────────────────────────────────────
def plot_event_loop_trace():
    events = [
        (0.00, 0.10, 1, "exec"), (0.10, 1.40, 1, "wait"),
        (0.10, 0.20, 2, "exec"), (0.20, 1.50, 2, "wait"),
        (0.20, 0.30, 3, "exec"), (0.30, 1.60, 3, "wait"),
        (1.40, 1.55, 1, "exec"),
        (1.50, 1.65, 2, "exec"),
        (1.60, 1.75, 3, "exec"),
    ]
    colors_exec = {1: ACCENT2, 2: ACCENT3, 3: ACCENT4}
    ys = {1: 2, 2: 1, 3: 0}

    fig, ax = plt.subplots(figsize=(10, 3.5))
    apply_theme(fig, [ax])

    for ts, te, cid, typ in events:
        y = ys[cid]
        color = colors_exec[cid] if typ == "exec" else WAIT_CLR
        alpha = 0.9 if typ == "exec" else 0.8
        hatch = None if typ == "exec" else "///"
        ax.barh(y, te-ts, left=ts, height=0.45, color=color, alpha=alpha,
                linewidth=0, hatch=hatch, edgecolor=FG if hatch else None)

    for cid, y in ys.items():
        ax.text(-0.02, y, f"coro {cid}", ha="right", va="center", color=FG, fontsize=9)

    for t in [0.10, 0.20, 0.30, 1.40, 1.50, 1.60]:
        ax.axvline(t, color=FG, alpha=0.18, linewidth=0.8, linestyle=":")

    ax.set_xlim(-0.05, 1.9)
    ax.set_ylim(-0.5, 2.7)
    ax.set_xlabel("Tiempo (s)", color=FG)
    ax.set_title("Event Loop — traza temporal: qué coroutine ejecuta en cada instante",
                 color=FG, fontsize=10)
    ax.set_yticks([])

    legend_exec_wait(ax)
    fig.tight_layout()
    save(fig, "event_loop_trace.png")


def plot_amdahl():
    fig, ax = plt.subplots(figsize=(8, 5))
    apply_theme(fig, [ax])

    P = np.linspace(1, 16, 200)
    for s, color, label in zip(
        [0.1, 0.25, 0.5, 0.9],
        [ACCENT2, ACCENT4, ACCENT3, ACCENT5],
        None,
    ) if False else zip(
        [0.1, 0.25, 0.5, 0.9],
        [ACCENT2, ACCENT4, ACCENT3, ACCENT5],
        [f"S={s} (máx {1/s:.1f}×)" for s in [0.1, 0.25, 0.5, 0.9]],
    ):
        sp = 1 / (s + (1-s) / P)
        ax.plot(P, sp, color=color, linewidth=2, label=label)
        ax.axhline(1/s, color=color, linewidth=0.8, linestyle="--", alpha=0.4)

    measured = {1: 0.93, 2: 1.80, 4: 3.34, 8: 4.52}
    ax.scatter(list(measured.keys()), list(measured.values()),
               color=FG, zorder=5, s=50, label="Medido (ProcessPoolExecutor)")
    ax.annotate("Los puntos medidos quedan\nbajo la curva S=0.1 por\noverhead de serialización",
                xy=(8, 4.52), xytext=(9.5, 3.0), color=FG, fontsize=8,
                arrowprops=dict(arrowstyle="->", color=FG, lw=0.8))

    ax.set_xlabel("Número de cores (P)", color=FG)
    ax.set_ylabel("Speedup", color=FG)
    ax.set_title("Ley de Amdahl: Speedup(P) = 1 / (S + (1−S)/P)", color=FG, fontsize=11)
    ax.set_xlim(1, 16); ax.set_ylim(0.5, 11)
    ax.legend(facecolor=BG, labelcolor=FG, fontsize=8)
    fig.tight_layout()
    save(fig, "amdahl_speedup.png")


def plot_benchmark_io():
    rows    = read_csv(RESULTS_DIR / "io_bound_benchmark.csv")
    methods = ["sequential", "asyncio", "threading"]
    colors  = {"sequential": ACCENT1, "asyncio": ACCENT2, "threading": ACCENT4}
    data    = {m: {"n": [], "speedup": []} for m in methods}
    for row in rows:
        m = row["method"]
        data[m]["n"].append(int(row["n_tasks"]))
        data[m]["speedup"].append(float(row["speedup"]))

    fig, ax = plt.subplots(figsize=(8, 5))
    apply_theme(fig, [ax])
    for m in methods:
        ax.plot(data[m]["n"], data[m]["speedup"],
                color=colors[m], marker="o", markersize=5, linewidth=2, label=m)
    ns = sorted(data["sequential"]["n"])
    ax.plot(ns, ns, color=FG, linewidth=1, linestyle="--", alpha=0.4, label="ideal (N×)")
    ax.set_xlabel("N tareas I/O-bound (cada una: sleep 1s)", color=FG)
    ax.set_ylabel("Speedup vs secuencial", color=FG)
    ax.set_title("I/O-bound: asyncio y threading escalan ~N×, secuencial no", color=FG, fontsize=10)
    ax.legend(facecolor=BG, labelcolor=FG, fontsize=9)
    ax.set_xscale("log", base=2); ax.set_yscale("log", base=2)
    fig.tight_layout()
    save(fig, "benchmark_io_bound.png")


def plot_benchmark_cpu():
    rows    = read_csv(RESULTS_DIR / "cpu_bound_benchmark.csv")
    methods = ["threading", "multiprocessing", "joblib"]
    colors  = {"threading": ACCENT3, "multiprocessing": ACCENT2, "joblib": ACCENT5}
    data    = {m: {"n": [], "speedup": []} for m in methods}
    for row in rows:
        m = row["method"]
        if m == "sequential":
            continue
        data[m]["n"].append(int(row["n_workers"]))
        data[m]["speedup"].append(float(row["speedup"]))

    fig, ax = plt.subplots(figsize=(8, 5))
    apply_theme(fig, [ax])
    for m in methods:
        ax.plot(data[m]["n"], data[m]["speedup"],
                color=colors[m], marker="o", markersize=5, linewidth=2, label=m)
    ax.plot([1,2,4,8], [1,2,4,8], color=FG, linewidth=1, linestyle="--", alpha=0.4, label="ideal (P×)")
    ax.axhline(1.0, color=ACCENT1, linewidth=1, linestyle=":", alpha=0.6, label="threading (GIL ~1×)")
    ax.set_xlabel("N workers", color=FG)
    ax.set_ylabel("Speedup vs secuencial", color=FG)
    ax.set_title("CPU-bound: multiprocessing/joblib escalan, threading ~1× (GIL)", color=FG, fontsize=10)
    ax.legend(facecolor=BG, labelcolor=FG, fontsize=9)
    fig.tight_layout()
    save(fig, "benchmark_cpu_bound.png")


def plot_pool_size():
    rows = read_csv(RESULTS_DIR / "pool_size_benchmark.csv")
    cpu_n, cpu_t, io_n, io_t = [], [], [], []
    for row in rows:
        n = int(row["n_workers"]); t = float(row["throughput_tasks_per_sec"])
        if row["method"] == "cpu_bound":
            cpu_n.append(n); cpu_t.append(t)
        else:
            io_n.append(n); io_t.append(t)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    apply_theme(fig, [ax1, ax2])

    ax1.plot(cpu_n, cpu_t, color=ACCENT2, marker="o", markersize=5, linewidth=2)
    ax1.axvline(8, color=ACCENT3, linewidth=1.5, linestyle="--", alpha=0.8, label="os.cpu_count()=8")
    ax1.set_xlabel("Pool size (workers)", color=FG)
    ax1.set_ylabel("Throughput (tareas/s)", color=FG)
    ax1.set_title("CPU-bound: óptimo en os.cpu_count()", color=FG, fontsize=10)
    ax1.legend(facecolor=BG, labelcolor=FG, fontsize=8)

    ax2.plot(io_n, io_t, color=ACCENT4, marker="o", markersize=5, linewidth=2)
    ax2.set_xlabel("Pool size (workers / coroutines)", color=FG)
    ax2.set_ylabel("Throughput (tareas/s)", color=FG)
    ax2.set_title("I/O-bound: escala mucho más allá de cpu_count()", color=FG, fontsize=10)
    ax2.set_xscale("log", base=2)

    fig.suptitle("Pool size vs Throughput: CPU-bound tiene óptimo, I/O-bound escala más",
                 color=FG, fontsize=10)
    fig.tight_layout()
    save(fig, "pool_size_vs_throughput.png")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Generando imágenes en: {IMAGES_DIR}\n")

    print("── Gantts por modelo ────────────────────────────")
    gantt_m1()
    gantt_m2()
    gantt_m3()
    gantt_m4()
    gantt_m5a()
    gantt_m5b()
    gantt_comparison()

    print("\n── Chatbot timeline ─────────────────────────────")
    chatbot_timeline()

    print("\n── Event loop trace ─────────────────────────────")
    plot_event_loop_trace()

    print("\n── Análisis y benchmarks ────────────────────────")
    plot_amdahl()
    plot_benchmark_io()
    plot_benchmark_cpu()
    plot_pool_size()

    print(f"\nListo. {len(list(IMAGES_DIR.glob('*.png')))} imágenes en {IMAGES_DIR}")
