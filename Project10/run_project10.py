"""
Project10: Lyapunov V sweep focusing on time vs skips (smooth curves).

Outputs (Project10/result/):
  - project10_raw.csv : per-run metrics
  - project10_agg.csv : aggregated mean/std over seeds
  - project10_v_tradeoff.png : dual-axis plot (total time ↑ vs skipped per node ↓)
"""

import os
import sys
import glob
import csv
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from matplotlib.ticker import LogLocator, ScalarFormatter, AutoMinorLocator

# Import simulation engine and shared plotting utils
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
MY_LYA_DIR = os.path.join(ROOT, "Exp-Doc", "My_Lya")
COMMON_DIR = os.path.join(ROOT, "ProjectCommon")
sys.path.insert(0, MY_LYA_DIR)
sys.path.insert(0, COMMON_DIR)

from simulation import Config, SimulationEnvironment, LyapunovStrategyV4  # type: ignore
from plot_utils import apply_ieee_style

# Experiment settings
SCALE = 100
# Dense log grid for smooth curves (up to ~20)
V_VALUES = list(np.logspace(-1, np.log10(20), 12))  # 0.1 to 20
SEEDS_PER_V = 5
RESULT_DIR = os.path.join(os.path.dirname(__file__), "result")
os.makedirs(RESULT_DIR, exist_ok=True)


def pick_coord_file(scale: int) -> str:
    folder = os.path.join(ROOT, "data", f"node{scale}")
    files = sorted(glob.glob(os.path.join(folder, "*.txt")))
    if not files:
        raise FileNotFoundError(f"No coord txt found for scale={scale} in {folder}")
    return files[0]


def run_once(v_value: float, seed: int):
    coord_file = pick_coord_file(SCALE)
    cfg = Config(seed=seed)
    cfg.COORDS_FILE_PATH = coord_file
    cfg.LYAPUNOV_V = v_value
    env = SimulationEnvironment(cfg)
    path = env.get_initial_tsp_path()

    strat = LyapunovStrategyV4(env)
    stats = strat.execute(path)

    row = {
        "V": v_value,
        "seed": seed,
        "total_time": stats["total_time"],
        "energy": stats["energy_consumed"],
        "success_nodes": stats["success_nodes"],
        "fail_nodes": stats["fail_nodes"],
        "skipped_nodes": stats["skipped_nodes"],
        "skipped_per_node": stats["skipped_nodes"] / SCALE,
    }
    return row


def aggregate(rows):
    agg = []
    keyed = defaultdict(list)
    for r in rows:
        keyed[r["V"]].append(r)
    for v, items in keyed.items():
        def mean_std(field):
            vals = [it[field] for it in items]
            return float(np.mean(vals)), float(np.std(vals))

        t_mean, t_std = mean_std("total_time")
        s_mean, s_std = mean_std("skipped_per_node")
        agg.append(
            {
                "V": v,
                "total_time_mean": t_mean,
                "total_time_std": t_std,
                "skipped_per_node_mean": s_mean,
                "skipped_per_node_std": s_std,
            }
        )
    return agg


def save_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def plot_tradeoff(agg_rows):
    apply_ieee_style()
    fig, ax1 = plt.subplots(figsize=(7.2, 4.0))  # single-column friendly

    agg_rows = sorted(agg_rows, key=lambda x: x["V"])
    x = np.array([r["V"] for r in agg_rows])
    time_y = np.array([r["total_time_mean"] for r in agg_rows])
    skip_y = np.array([r["skipped_per_node_mean"] for r in agg_rows])

    # Smooth curves in log(V) domain
    x_log = np.log10(x)
    smooth_x_log = np.linspace(x_log.min(), x_log.max(), 200)

    def smooth_curve(y_vals):
        if len(y_vals) >= 4:
            spline = make_interp_spline(x_log, y_vals, k=3)
            return 10 ** smooth_x_log, spline(smooth_x_log)
        return x, y_vals

    smooth_x_time, smooth_time = smooth_curve(time_y)
    smooth_x_skip, smooth_skip = smooth_curve(skip_y)

    # Left axis: total time (blue), solid + square markers
    line1 = ax1.plot(
        smooth_x_time, smooth_time,
        color="#1f77b4", linestyle="-",
        linewidth=2.0, label="Total time (s)"
    )
    ax1.plot(x, time_y, color="#1f77b4", marker="s", linestyle="none", markersize=6)
    ax1.set_xscale("log")
    ax1.set_xlabel("Lyapunov V (log scale)")
    ax1.set_ylabel("Total time (s)")
    ax1.margins(x=0.05, y=0.1)

    # Right axis: skipped per node (red), dashed + circle markers
    ax2 = ax1.twinx()
    line2 = ax2.plot(
        smooth_x_skip, smooth_skip,
        color="#d62728", linestyle="--",
        linewidth=2.0, label="Skipped per node"
    )
    ax2.plot(x, skip_y, color="#d62728", marker="o", linestyle="none", markersize=6)
    ax2.set_ylabel("Skipped per node")
    ax2.margins(x=0.05, y=0.1)

    # Ticks and grid (rectangular grid, consistent spacing markers)
    # Ticks (uniform style) and grid (square-like, consistent)
    ax1.set_xticks(V_VALUES)
    ax1.get_xaxis().set_major_locator(LogLocator(base=10.0, subs=(1.0, 2.0, 5.0)))
    ax1.get_xaxis().set_major_formatter(ScalarFormatter())
    ax1.minorticks_on()
    ax1.yaxis.set_minor_locator(AutoMinorLocator())
    # Use major grid for solid reference, minor grid for finer squares
    ax1.grid(True, which="major", linestyle="--", color="#c0c0c0", alpha=0.7)
    ax1.grid(True, which="minor", linestyle=":", color="#d8d8d8", alpha=0.6)
    ax1.set_axisbelow(True)
    # black boxed frame, slightly thicker
    for spine in ["top", "right", "left", "bottom"]:
        ax1.spines[spine].set_visible(True)
        ax1.spines[spine].set_linewidth(1.2)
    for spine in ["top", "right", "left", "bottom"]:
        if spine in ax2.spines:
            ax2.spines[spine].set_visible(True)
            ax2.spines[spine].set_linewidth(1.2)

    # Note at bottom-right
    ax1.text(0.98, 0.02, "log scale", ha="right", va="bottom", transform=ax1.transAxes, fontsize=9, color="#444")

    # Legend (upper-left)
    handles = [line1[0], line2[0]]
    labels = ["Total time (s)", "Skipped per node"]
    ax1.legend(handles, labels, loc="upper left", frameon=False)

    fig.tight_layout()
    out_path = os.path.join(RESULT_DIR, "project10_v_tradeoff.png")
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f"Saved plot to {out_path}")


def main():
    all_rows = []
    for v in V_VALUES:
        for rep in range(SEEDS_PER_V):
            seed = 5000 + rep
            all_rows.append(run_once(v, seed))

    raw_path = os.path.join(RESULT_DIR, "project10_raw.csv")
    save_csv(raw_path, all_rows, fieldnames=list(all_rows[0].keys()))
    print(f"Saved raw to {raw_path}")

    agg_rows = aggregate(all_rows)
    agg_path = os.path.join(RESULT_DIR, "project10_agg.csv")
    save_csv(agg_path, agg_rows, fieldnames=list(agg_rows[0].keys()))
    print(f"Saved agg to {agg_path}")

    plot_tradeoff(agg_rows)


if __name__ == "__main__":
    main()
