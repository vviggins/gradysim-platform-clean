#!/usr/bin/env python3
"""
Parameter sweep for Lyapunov control (skip aggressiveness).
We vary LYA_V and measure efficiency (Data/Time) on node100 datasets.
Outputs:
  - results/param_sweep_summary.csv
  - results/param_sweep_trajectory.csv (for possible extra plots)
"""
import os
import random
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "..", "data")
RESULT_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULT_DIR, exist_ok=True)

# Communication / dynamics (moderate cost)
DATA_TRANSFER_RATE = 500.0
UAV_SPEED = 20.0
UAV_BATTERY_CAPACITY = 3000.0
ENERGY_PER_METER_FLIGHT = 0.1
ENERGY_PER_SECOND_HOVER = 1.2
COMM_HANDSHAKE_TIME = 10.0

# Baseline parameters (fixed)
BASELINE_MAX_ATTEMPTS = 20
BASELINE_SUCCESS_FACTOR = 0.6

# Lyapunov fixed bits
LYA_MAX_ATTEMPTS = 5
LYA_MIN_ATTEMPTS_BEFORE_SKIP = 2
LYA_THRESHOLD = 0.0


def load_coords(file_path):
    coords = np.loadtxt(file_path)
    if np.array_equal(coords[0], coords[-1]):
        coords = coords[:-1]
    return coords


def build_env(coords, seed):
    random.seed(seed)
    np.random.seed(seed)
    n = len(coords)
    distances = squareform(pdist(coords, metric="euclidean"))
    values = np.ones(n)
    hi = np.random.choice(n, size=max(1, int(0.1 * n)), replace=False)
    values[hi] = 5.0
    base_q = np.random.uniform(0.7, 0.95, n)
    bad_idx = np.random.choice(n, max(1, int(0.3 * n)), replace=False)
    base_q[bad_idx] *= 0.2
    # small payloads (10x smaller than original project)
    payload = np.random.normal(15.0, 5.0, n)
    payload[payload < 5.0] = 5.0
    critical = np.random.choice(bad_idx, max(1, int(0.5 * len(bad_idx))), replace=False)
    hi_data = np.random.normal(400.0, 80.0, len(critical))
    hi_data[hi_data < 250.0] = 250.0
    payload[critical] = hi_data
    return {"distances": distances, "values": values, "qualities": base_q, "data_payload": payload}


def comm_attempt(env, node_idx, strategy):
    p = 0.9 * env["qualities"][node_idx] + random.uniform(-0.1, 0.1)
    if strategy == "baseline":
        p *= BASELINE_SUCCESS_FACTOR
    p = max(0.0, min(1.0, p))
    t = COMM_HANDSHAKE_TIME
    if random.random() < p:
        data = env["data_payload"][node_idx]
        t += data / DATA_TRANSFER_RATE
        return True, t, data
    return False, t, 0.0


def execute(env, path, strategy, lya_v=None):
    s = {
        "Success_Nodes": 0,
        "Fail_Nodes": 0,
        "Skipped_Nodes": 0,
        "Data_Collected_KB": 0.0,
        "Total_Time": 0.0,
        "Total_Energy": 0.0,
        "Total_Flight_Distance": 0.0,
        "Total_Comm_Latency": 0.0,
        "Attempts": 0,
        "Retry_Sum": 0,
    }
    traj = []
    backlog = 0.0
    seen = set()
    max_attempts = BASELINE_MAX_ATTEMPTS if strategy == "baseline" else LYA_MAX_ATTEMPTS

    for i in range(len(path) - 1):
        cur, nxt = path[i], path[i + 1]
        dist = env["distances"][cur, nxt]
        flight_e = dist * ENERGY_PER_METER_FLIGHT
        flight_t = dist / UAV_SPEED
        if s["Total_Energy"] + flight_e > UAV_BATTERY_CAPACITY:
            break
        s["Total_Energy"] += flight_e
        s["Total_Time"] += flight_t
        s["Total_Flight_Distance"] += dist

        attempts_here = 0
        success = False
        data_col = 0.0
        for att in range(1, max_attempts + 1):
            attempts_here += 1
            ok, comm_t, data = comm_attempt(env, cur, strategy)
            hover_e = comm_t * ENERGY_PER_SECOND_HOVER
            if s["Total_Energy"] + hover_e > UAV_BATTERY_CAPACITY:
                break
            s["Total_Energy"] += hover_e
            s["Total_Time"] += comm_t
            s["Total_Comm_Latency"] += comm_t
            s["Attempts"] += 1
            s["Retry_Sum"] += 1 if att > 1 else 0
            if ok:
                success = True
                data_col = data
                break
            if strategy == "lya":
                # online empirical success (no prior); aggressive skip influenced by lya_v
                p_hat = 1.0 / attempts_here
                penalty = (lya_v or 0.0) * backlog - p_hat
                if attempts_here >= LYA_MIN_ATTEMPTS_BEFORE_SKIP and backlog > 0 and penalty > LYA_THRESHOLD:
                    s["Skipped_Nodes"] += 1
                    traj.append({
                        "Time": s["Total_Time"],
                        "Data_Collected_KB": s["Data_Collected_KB"],
                        "Current_Node": int(cur),
                        "Attempt_Count": attempts_here,
                        "Success_Flag": 0,
                        "Skipped_Flag": 1,
                        "LYA_V": lya_v
                    })
                    break

        if success:
            if cur not in seen:
                s["Success_Nodes"] += 1
                seen.add(cur)
            s["Data_Collected_KB"] += data_col
            backlog = max(0.0, backlog - env["values"][cur])
            traj.append({
                "Time": s["Total_Time"],
                "Data_Collected_KB": s["Data_Collected_KB"],
                "Current_Node": int(cur),
                "Attempt_Count": attempts_here,
                "Success_Flag": 1,
                "Skipped_Flag": 0,
                "LYA_V": lya_v
            })
        else:
            s["Fail_Nodes"] += 1
            backlog += env["values"][cur]

    s["Total_Waypoints"] = len(path) - 1
    s["Success_Rate"] = s["Success_Nodes"] / s["Total_Waypoints"] if s["Total_Waypoints"] else 0
    s["Avg_Comm_Latency"] = s["Total_Comm_Latency"] / s["Attempts"] if s["Attempts"] else 0
    s["Eff_Data_Per_Time"] = s["Data_Collected_KB"] / s["Total_Time"] if s["Total_Time"] else 0
    s["Eff_Data_Per_Energy"] = s["Data_Collected_KB"] / s["Total_Energy"] if s["Total_Energy"] else 0
    s["Avg_Retry_Per_Node"] = s["Retry_Sum"] / max(1, s["Attempts"])
    s["Strategy"] = "baseline" if strategy == "baseline" else f"lya_V{lya_v}"
    s["LYA_V"] = lya_v if strategy == "lya" else None
    return s, traj


def run_scale(scale, lya_v_values):
    folder = os.path.join(DATA_DIR, f"node{scale}")
    files = sorted([f for f in os.listdir(folder) if f.endswith(".txt")])
    summaries, trajectories = [], []
    for fname in files:
        coords = load_coords(os.path.join(folder, fname))
        path = list(range(len(coords))) + [0]
        # deterministic yet different seeds per file for variability
        seed = abs(hash(fname)) % (2**32)
        env = build_env(coords, seed=seed)

        # baseline
        stats, traj = execute(env, path, "baseline", lya_v=None)
        stats["Node_File"] = fname.replace(".txt", "")
        stats["Num_Nodes"] = scale
        summaries.append(stats)
        for t in traj:
            t["Node_File"] = fname.replace(".txt", "")
            t["Num_Nodes"] = scale
        trajectories.extend(traj)

        # lyapunov sweeps
        for v in lya_v_values:
            stats, traj = execute(env, path, "lya", lya_v=v)
            stats["Node_File"] = fname.replace(".txt", "")
            stats["Num_Nodes"] = scale
            summaries.append(stats)
            for t in traj:
                t["Node_File"] = fname.replace(".txt", "")
                t["Num_Nodes"] = scale
            trajectories.extend(traj)
    return summaries, trajectories


def main():
    # vary Lyapunov weight (skip aggressiveness)
    lya_v_values = [0.5, 1.0, 2.0, 3.0, 4.0]
    scales = [50, 100, 150, 200]  # sweep across four scales
    summary_all, traj_all = [], []
    for sc in scales:
        s, t = run_scale(sc, lya_v_values)
        summary_all.extend(s)
        traj_all.extend(t)
    pd.DataFrame(summary_all).to_csv(os.path.join(RESULT_DIR, "param_sweep_summary.csv"), index=False, encoding="utf-8")
    pd.DataFrame(traj_all).to_csv(os.path.join(RESULT_DIR, "param_sweep_trajectory.csv"), index=False, encoding="utf-8")
    print("Saved param sweep results to results/")


if __name__ == "__main__":
    main()
