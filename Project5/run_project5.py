"""
Project5: Sweep Lyapunov V to study performance–stability trade-off.

Outputs (created under Project5/result/):
- project5_raw.csv   : per run metrics (scale, V, seed, strategy, total_time, energy, success_nodes, fail_nodes, skipped_nodes, collected_value)
- project5_agg.csv   : aggregated mean/std over seeds (per scale, per V)
- project5_v_tradeoff.png : dual-axis plot (total_time vs V, skipped_nodes vs V) for each scale

Notes:
- Uses existing simulation engine in Exp-Doc/My_Lya/simulation.py without modifying it.
- Uses the first .txt file found in data/node{scale}/ as the coordinate source.
"""

import os
import sys
import glob
import csv
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np

# Make simulation module importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
MY_LYA_DIR = os.path.join(ROOT, "Exp-Doc", "My_Lya")
COMMON_DIR = os.path.join(ROOT, "ProjectCommon")
sys.path.insert(0, MY_LYA_DIR)
sys.path.insert(0, COMMON_DIR)

from simulation import Config, SimulationEnvironment, BaselineStrategy, LyapunovStrategyV4  # type: ignore
from plot_utils import apply_ieee_style, dual_axis, collect_legend, PALETTE


# Experiment settings
SCALES = [50, 100, 150]
V_VALUES = [1e2, 5e2, 1e3, 5e3, 1e4, 5e4, 1e5]
SEEDS_PER_SETTING = 5  # more repetitions for smoother curves
RESULT_DIR = os.path.join(os.path.dirname(__file__), "result")
os.makedirs(RESULT_DIR, exist_ok=True)


def pick_coord_file(scale: int) -> str:
    folder = os.path.join(ROOT, "data", f"node{scale}")
    files = sorted(glob.glob(os.path.join(folder, "*.txt")))
    if not files:
        raise FileNotFoundError(f"No coord txt found for scale={scale} in {folder}")
    return files[0]


def run_once(scale: int, v_value: float, seed: int):
    coord_file = pick_coord_file(scale)
    cfg = Config(seed=seed)
    cfg.COORDS_FILE_PATH = coord_file
    cfg.LYAPUNOV_V = v_value
    env = SimulationEnvironment(cfg)
    path = env.get_initial_tsp_path()

    strategies = {
        "Baseline": BaselineStrategy(env),
        "Lyapunov": LyapunovStrategyV4(env),
    }

    rows = []
    for name, inst in strategies.items():
        stats = inst.execute(path)
        rows.append(
            {
                "scale": scale,
                "V": v_value,
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
        key = (r["scale"], r["V"], r["strategy"])
        keyed[key].append(r)
    for (scale, v, strat), items in keyed.items():
        def mean_std(field):
            vals = [it[field] for it in items]
            return float(np.mean(vals)), float(np.std(vals))

        t_mean, t_std = mean_std("total_time")
        s_mean, s_std = mean_std("skipped_nodes")
        agg.append(
            {
                "scale": scale,
                "V": v,
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


def plot_tradeoff(agg_rows):
    apply_ieee_style()
    fig, axes = plt.subplots(1, len(SCALES), figsize=(14, 4), sharey=False, sharex=False)
    if len(SCALES) == 1:
        axes = [axes]

    for ax, scale in zip(axes, SCALES):
        subset_all = [r for r in agg_rows if r["scale"] == scale]
        v_vals = sorted({r["V"] for r in subset_all})

        left_series = []
        right_series = []
        for strat in ["Baseline", "Lyapunov"]:
            subset = [r for r in subset_all if r["strategy"] == strat]
            subset = sorted(subset, key=lambda x: x["V"])
            color = PALETTE.get(strat, None)
            left_series.append(
                {
                    "y": [r["total_time_mean"] for r in subset],
                    "yerr": [r["total_time_std"] for r in subset],
                    "label": f"{strat} total time",
                    "color": color,
                    "marker": "o",
                    "linestyle": "-",
                }
            )
            right_series.append(
                {
                    "y": [r["skipped_mean"] for r in subset],
                    "yerr": [r["skipped_std"] for r in subset],
                    "label": f"{strat} skipped",
                    "color": color,
                    "marker": "s",
                    "linestyle": "--",
                }
            )

        dual_axis(
            ax,
            v_vals,
            left_series,
            right_series,
            xlabel="Lyapunov V (log scale)",
            left_label="Total time (s)",
            right_label="Skipped nodes",
            xscale="log",
            title=f"Scale={scale} nodes",
        )

    collect_legend(fig, axes)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out_path = os.path.join(RESULT_DIR, "project5_v_tradeoff.png")
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Saved plot to {out_path}")


def main():
    all_rows = []
    for scale in SCALES:
        for v in V_VALUES:
            for rep in range(SEEDS_PER_SETTING):
                seed = 1000 + rep  # deterministic but varied
                all_rows.extend(run_once(scale, v, seed))
    raw_path = os.path.join(RESULT_DIR, "project5_raw.csv")
    save_csv(raw_path, all_rows, fieldnames=list(all_rows[0].keys()))
    print(f"Saved raw to {raw_path}")

    agg_rows = aggregate(all_rows)
    agg_path = os.path.join(RESULT_DIR, "project5_agg.csv")
    save_csv(agg_path, agg_rows, fieldnames=list(agg_rows[0].keys()))
    print(f"Saved agg to {agg_path}")

    plot_tradeoff(agg_rows)


if __name__ == "__main__":
    main()
