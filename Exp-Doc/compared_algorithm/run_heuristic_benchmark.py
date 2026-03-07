"""
Run GA/SA/ACO on prepared TSP npz datasets and log time/length results.

Usage (from repo root):
    python Exp-Doc/compared_algorithm/run_heuristic_benchmark.py

Outputs:
    - Exp-Doc/compared_algorithm/result/heuristic_times.csv
    - Exp-Doc/compared_algorithm/heuristic_time_comparison.png
"""

import csv
import os
import random
import sys
import time
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np

# Ensure local algorithm modules are importable when run from repo root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from GA_refactored import GA
from SA_refactored import SA
from ACO_refactored import ACO


# Default datasets: 50/100/150-city instances prepared earlier.
# If you want to benchmark different files, edit this mapping.
DATASETS = {
    50: os.path.join(SCRIPT_DIR, "node50", "data344.npz"),
    100: os.path.join(SCRIPT_DIR, "node100", "data345.npz"),
    150: os.path.join(SCRIPT_DIR, "node150", "data346.npz"),
}

# Algorithm hyperparameters (aligned with run_experiment.py defaults)
GA_PARAMS = {"iteration": 500, "num_total": 50}
SA_PARAMS = {"T0": 2000, "rate": 0.95, "size": 100}
ACO_PARAMS = {"iter_max": 200, "m": 50}


def load_coords(npz_path: str) -> np.ndarray:
    """Load coordinates from npz and drop the duplicated start node at the end."""
    data = np.load(npz_path, allow_pickle=True)
    coords = data["coords"][0][:-1]  # shape (n, 2)
    return coords


def run_one_size(size: int, npz_path: str) -> List[Dict]:
    """Run GA/SA/ACO on a single dataset and return result rows."""
    coords = load_coords(npz_path)
    num_city = coords.shape[0]

    # Fix seeds per run for repeatability
    np.random.seed(42)
    random.seed(42)

    rows = []

    start = time.perf_counter()
    ga_solver = GA(num_city=num_city, data=coords.copy(), **GA_PARAMS)
    ga_len, _ = ga_solver.run()
    ga_time = time.perf_counter() - start
    rows.append(
        {
            "dataset": os.path.basename(npz_path),
            "size": size,
            "algorithm": "GA",
            "length": ga_len,
            "time_seconds": ga_time,
        }
    )

    start = time.perf_counter()
    sa_solver = SA(num_city=num_city, data=coords.copy(), **SA_PARAMS)
    sa_len, _ = sa_solver.run()
    sa_time = time.perf_counter() - start
    rows.append(
        {
            "dataset": os.path.basename(npz_path),
            "size": size,
            "algorithm": "SA",
            "length": sa_len,
            "time_seconds": sa_time,
        }
    )

    start = time.perf_counter()
    aco_solver = ACO(num_city=num_city, data=coords.copy(), **ACO_PARAMS)
    aco_len, _ = aco_solver.run()
    aco_time = time.perf_counter() - start
    rows.append(
        {
            "dataset": os.path.basename(npz_path),
            "size": size,
            "algorithm": "ACO",
            "length": aco_len,
            "time_seconds": aco_time,
        }
    )

    return rows


def save_csv(rows: List[Dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = ["dataset", "size", "algorithm", "length", "time_seconds"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def plot_times(rows: List[Dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.figure(figsize=(8, 5))
    algos = ["GA", "SA", "ACO"]
    markers = {"GA": "o", "SA": "s", "ACO": "^"}

    for algo in algos:
        algo_rows = sorted(
            [r for r in rows if r["algorithm"] == algo], key=lambda x: x["size"]
        )
        sizes = [r["size"] for r in algo_rows]
        times = [r["time_seconds"] for r in algo_rows]
        plt.plot(sizes, times, marker=markers[algo], label=algo)

    plt.title("Heuristic Algorithms Time Comparison")
    plt.xlabel("Problem Size (Number of Cities)")
    plt.ylabel("Computation Time (seconds)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=200)


def main() -> None:
    all_rows: List[Dict] = []
    for size, npz_path in DATASETS.items():
        all_rows.extend(run_one_size(size, npz_path))

    csv_path = os.path.join(SCRIPT_DIR, "result", "heuristic_times.csv")
    save_csv(all_rows, csv_path)
    print(f"Saved CSV to {csv_path}")

    plot_path = os.path.join(SCRIPT_DIR, "heuristic_time_comparison.png")
    plot_times(all_rows, plot_path)
    print(f"Saved plot to {plot_path}")


if __name__ == "__main__":
    main()
