"""
Project7: Scalability test — vary number of nodes and observe per-user metrics.

Outputs (Project7/result/):
- project7_raw.csv   : per run metrics (scale, seed, strategy, total_time, energy, success_nodes, fail_nodes, skipped_nodes, collected_value)
- project7_agg.csv   : aggregated per scale (means/stds)
- project7_scalability.png : plots of per-user time/energy and per-user skipped nodes vs scale
"""

import os
import sys
import glob
import csv
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
MY_LYA_DIR = os.path.join(ROOT, "Exp-Doc", "My_Lya")
COMMON_DIR = os.path.join(ROOT, "ProjectCommon")
sys.path.insert(0, MY_LYA_DIR)
sys.path.insert(0, COMMON_DIR)

from simulation import Config, SimulationEnvironment, BaselineStrategy, LyapunovStrategyV4  # type: ignore
from plot_utils import apply_ieee_style, line_with_error, collect_legend, PALETTE

# Settings
SCALES = [50, 100, 150, 200]
SEEDS_PER = 5
V_FIXED = 1e4
RESULT_DIR = os.path.join(os.path.dirname(__file__), "result")
os.makedirs(RESULT_DIR, exist_ok=True)


def pick_coord_file(scale: int) -> str:
    folder = os.path.join(ROOT, "data", f"node{scale}")
    files = sorted(glob.glob(os.path.join(folder, "*.txt")))
    if not files:
        raise FileNotFoundError(f"No coord txt found for scale={scale} in {folder}")
    return files[0]


def run_once(scale: int, seed: int):
    coord_file = pick_coord_file(scale)
    cfg = Config(seed=seed)
    cfg.COORDS_FILE_PATH = coord_file
    cfg.LYAPUNOV_V = V_FIXED
    env = SimulationEnvironment(cfg)
    path = env.get_initial_tsp_path()

    strategies = {"Baseline": BaselineStrategy(env), "Lyapunov": LyapunovStrategyV4(env)}
    rows = []
    for name, inst in strategies.items():
        stats = inst.execute(path)
        rows.append(
            {
                "scale": scale,
                "seed": seed,
                "strategy": name,
                "total_time": stats["total_time"],
                "energy": stats["energy_consumed"],
                "success_nodes": stats["success_nodes"],
                "fail_nodes": stats["fail_nodes"],
                "skipped_nodes": stats["skipped_nodes"],
                "collected_value": stats["collected_value"],
            }
        )
    return rows


def aggregate(rows):
    agg = []
    keyed = defaultdict(list)
    for r in rows:
        key = (r["scale"], r["strategy"])
        keyed[key].append(r)
    for (scale, strat), items in keyed.items():
        def mean_std(field):
            vals = [it[field] for it in items]
            return float(np.mean(vals)), float(np.std(vals))

        t_mean, t_std = mean_std("total_time")
        e_mean, e_std = mean_std("energy")
        s_mean, s_std = mean_std("skipped_nodes")
        agg.append(
            {
                "scale": scale,
                "strategy": strat,
                "total_time_mean": t_mean,
                "total_time_std": t_std,
                "energy_mean": e_mean,
                "energy_std": e_std,
                "skipped_mean": s_mean,
                "skipped_std": s_std,
            }
        )
    return agg


def save_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def plot_scalability(agg_rows):
    apply_ieee_style()
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # Per-user total time
    ax = axes[0]
    for strat in ["Baseline", "Lyapunov"]:
        subset = sorted([r for r in agg_rows if r["strategy"] == strat], key=lambda x: x["scale"])
        x = [r["scale"] for r in subset]
        y = [r["total_time_mean"] / r["scale"] for r in subset]
        yerr = [r["total_time_std"] / r["scale"] for r in subset]
        line_with_error(ax, x, y, yerr=yerr, label=f"{strat} time per node", color=PALETTE.get(strat))
    ax.set_xlabel("Number of nodes")
    ax.set_ylabel("Time per node (s)")
    ax.set_title("Per-node time", fontweight="bold")

    # Per-user energy
    ax = axes[1]
    for strat in ["Baseline", "Lyapunov"]:
        subset = sorted([r for r in agg_rows if r["strategy"] == strat], key=lambda x: x["scale"])
        x = [r["scale"] for r in subset]
        y = [r["energy_mean"] / r["scale"] for r in subset]
        yerr = [r["energy_std"] / r["scale"] for r in subset]
        line_with_error(ax, x, y, yerr=yerr, label=f"{strat} energy per node", color=PALETTE.get(strat), marker="D")
    ax.set_xlabel("Number of nodes")
    ax.set_ylabel("Energy per node")
    ax.set_title("Per-node energy", fontweight="bold")

    # Per-user skipped
    ax = axes[2]
    for strat in ["Baseline", "Lyapunov"]:
        subset = sorted([r for r in agg_rows if r["strategy"] == strat], key=lambda x: x["scale"])
        x = [r["scale"] for r in subset]
        y = [r["skipped_mean"] / r["scale"] for r in subset]
        yerr = [r["skipped_std"] / r["scale"] for r in subset]
        line_with_error(ax, x, y, yerr=yerr, label=f"{strat} skipped per node", color=PALETTE.get(strat), marker="s", linestyle="--")
    ax.set_xlabel("Number of nodes")
    ax.set_ylabel("Skipped per node")
    ax.set_title("Per-node skips", fontweight="bold")

    collect_legend(fig, axes)
    fig.suptitle("Scalability: per-node metrics", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out_path = os.path.join(RESULT_DIR, "project7_scalability.png")
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Saved plot to {out_path}")


def main():
    all_rows = []
    for scale in SCALES:
        for rep in range(SEEDS_PER):
            seed = 3000 + rep
            all_rows.extend(run_once(scale, seed))
    raw_path = os.path.join(RESULT_DIR, "project7_raw.csv")
    save_csv(raw_path, all_rows, fieldnames=list(all_rows[0].keys()))
    print(f"Saved raw to {raw_path}")

    agg_rows = aggregate(all_rows)
    agg_path = os.path.join(RESULT_DIR, "project7_agg.csv")
    save_csv(agg_path, agg_rows, fieldnames=list(agg_rows[0].keys()))
    print(f"Saved agg to {agg_path}")

    plot_scalability(agg_rows)


if __name__ == "__main__":
    main()
