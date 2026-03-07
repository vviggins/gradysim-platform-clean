"""
Project6: Load-disturbance robustness test (fixed V, vary load multiplier).

Outputs (Project6/result/):
- project6_raw.csv   : per run metrics (load_scale, seed, strategy, total_time, energy, success_nodes, fail_nodes, skipped_nodes, collected_value)
- project6_agg.csv   : aggregated mean/std per load_scale
- project6_load_sweep.png : performance vs load plot
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
LOAD_SCALES = [0.6, 0.8, 1.0, 1.2, 1.4]
SEEDS_PER = 5
V_FIXED = 1e4
SCALE_FOR_TEST = 100  # use node100 dataset as baseline workload
RESULT_DIR = os.path.join(os.path.dirname(__file__), "result")
os.makedirs(RESULT_DIR, exist_ok=True)


def pick_coord_file(scale: int) -> str:
    folder = os.path.join(ROOT, "data", f"node{scale}")
    files = sorted(glob.glob(os.path.join(folder, "*.txt")))
    if not files:
        raise FileNotFoundError(f"No coord txt found for scale={scale} in {folder}")
    return files[0]


def run_once(load_scale: float, seed: int):
    coord_file = pick_coord_file(SCALE_FOR_TEST)
    cfg = Config(seed=seed)
    cfg.COORDS_FILE_PATH = coord_file
    cfg.LYAPUNOV_V = V_FIXED
    env = SimulationEnvironment(cfg)
    # scale payloads to emulate heavier/lighter load
    env.node_data_payloads = {k: v * load_scale for k, v in env.node_data_payloads.items()}

    path = env.get_initial_tsp_path()
    strategies = {"Baseline": BaselineStrategy(env), "Lyapunov": LyapunovStrategyV4(env)}

    rows = []
    for name, inst in strategies.items():
        stats = inst.execute(path)
        rows.append(
            {
                "load_scale": load_scale,
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
        key = (r["load_scale"], r["strategy"])
        keyed[key].append(r)
    for (load_scale, strat), items in keyed.items():
        def mean_std(field):
            vals = [it[field] for it in items]
            return float(np.mean(vals)), float(np.std(vals))

        t_mean, t_std = mean_std("total_time")
        s_mean, s_std = mean_std("skipped_nodes")
        agg.append(
            {
                "load_scale": load_scale,
                "strategy": strat,
                "total_time_mean": t_mean,
                "total_time_std": t_std,
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


def plot_load(agg_rows):
    apply_ieee_style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Total time
    ax = axes[0]
    for strat in ["Baseline", "Lyapunov"]:
        subset = sorted([r for r in agg_rows if r["strategy"] == strat], key=lambda x: x["load_scale"])
        x = [r["load_scale"] for r in subset]
        y = [r["total_time_mean"] for r in subset]
        yerr = [r["total_time_std"] for r in subset]
        line_with_error(ax, x, y, yerr=yerr, label=f"{strat} total time", color=PALETTE.get(strat))
    ax.set_xlabel("Load multiplier")
    ax.set_ylabel("Total time (s)")
    ax.set_title("Performance vs load", fontweight="bold")

    # Skipped nodes
    ax = axes[1]
    for strat in ["Baseline", "Lyapunov"]:
        subset = sorted([r for r in agg_rows if r["strategy"] == strat], key=lambda x: x["load_scale"])
        x = [r["load_scale"] for r in subset]
        y = [r["skipped_mean"] for r in subset]
        yerr = [r["skipped_std"] for r in subset]
        line_with_error(ax, x, y, yerr=yerr, label=f"{strat} skipped", color=PALETTE.get(strat), marker="s", linestyle="--")
    ax.set_xlabel("Load multiplier")
    ax.set_ylabel("Skipped nodes")
    ax.set_title("Backlog proxy vs load", fontweight="bold")

    collect_legend(fig, axes)
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    out_path = os.path.join(RESULT_DIR, "project6_load_sweep.png")
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Saved plot to {out_path}")


def main():
    all_rows = []
    for load_scale in LOAD_SCALES:
        for rep in range(SEEDS_PER):
            seed = 2000 + rep
            all_rows.extend(run_once(load_scale, seed))
    raw_path = os.path.join(RESULT_DIR, "project6_raw.csv")
    save_csv(raw_path, all_rows, fieldnames=list(all_rows[0].keys()))
    print(f"Saved raw to {raw_path}")

    agg_rows = aggregate(all_rows)
    agg_path = os.path.join(RESULT_DIR, "project6_agg.csv")
    save_csv(agg_path, agg_rows, fieldnames=list(agg_rows[0].keys()))
    print(f"Saved agg to {agg_path}")

    plot_load(agg_rows)


if __name__ == "__main__":
    main()
