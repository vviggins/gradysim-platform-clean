#!/usr/bin/env python3
"""
Plot time to reach data milestones (Project3, baseline vs Lyapunov).
Focus on node100 to keep the figure clean for the paper.
Input: results/lya_trajectory.csv
Output: plots_final/time_to_data_node100.png
"""
import os
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAJ_FILE = os.path.join(BASE_DIR, "results", "lya_trajectory.csv")
PLOT_DIR = os.path.join(BASE_DIR, "plots_final")
os.makedirs(PLOT_DIR, exist_ok=True)

COLOR = {
    "baseline": "#FC9E79",
    "lya": "#7DCBB2",
}

MILESTONES_KB = [500, 1500, 3000, 4000]  # ~0.5, 1.5, 3.0, 4.0 MB


def compute_time_to_milestones(df):
    rows = []
    for (strategy, node_file), sub in df.groupby(["Strategy", "Node_File"]):
        sub = sub.sort_values("Time")
        for m in MILESTONES_KB:
            reached = sub[sub["Data_Collected_KB"] >= m]
            if reached.empty:
                continue
            t = reached["Time"].iloc[0]
            rows.append({"Strategy": strategy, "Node_File": node_file, "Milestone_KB": m, "Time": t})
    return pd.DataFrame(rows)


def main():
    df = pd.read_csv(TRAJ_FILE)
    df = df[df["Num_Nodes"] == 100]  # focus on node100 for clarity
    data = compute_time_to_milestones(df)
    if data.empty:
        print("No milestones reached; check data.")
        return

    agg = data.groupby(["Strategy", "Milestone_KB"])["Time"].agg(["mean", "std"]).reset_index()

    # --- Classic errorbar plot ---
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(8.5, 5.3))
    for strategy in ["baseline", "lya"]:
        sub = agg[agg["Strategy"] == strategy]
        ax.errorbar(
            sub["Milestone_KB"] / 1024.0,  # convert to MB for axis
            sub["mean"],
            yerr=sub["std"].fillna(0),
            fmt="-o",
            linewidth=2.2,
            capsize=6,
            markeredgecolor="black",
            color=COLOR[strategy],
            label="Baseline" if strategy == "baseline" else "Lyapunov"
        )
        for x, y in zip(sub["Milestone_KB"] / 1024.0, sub["mean"]):
            ax.text(x, y + 0.02 * agg["mean"].max(), f"{y:.1f}s", ha="center", va="bottom", fontsize=10, color="black")

    ax.set_xlabel("Data Milestone (MB)", fontsize=12)
    ax.set_ylabel("Time to Collect (s)", fontsize=12)
    ax.set_title("Time to Reach Data Milestones (node100)", fontsize=14, fontweight="bold")
    ax.legend(frameon=True, facecolor="white", framealpha=0.9, edgecolor="#333")
    ax.grid(True, axis="both", linestyle="--", linewidth=0.6)
    fig.tight_layout()

    out = os.path.join(PLOT_DIR, "time_to_data_node100.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # --- Creative filled-gap plot highlighting time savings ---
    fig, ax = plt.subplots(figsize=(8.8, 5.5))
    base = agg[agg["Strategy"] == "baseline"].sort_values("Milestone_KB")
    lya = agg[agg["Strategy"] == "lya"].sort_values("Milestone_KB")
    # align on milestone axis
    merged = pd.merge(base, lya, on="Milestone_KB", suffixes=("_base", "_lya"))
    x_mb = merged["Milestone_KB"] / 1024.0
    ax.plot(x_mb, base["mean"], "-o", color=COLOR["baseline"], linewidth=2.2, markeredgecolor="black", label="Baseline")
    ax.plot(x_mb, lya["mean"], "-o", color=COLOR["lya"], linewidth=2.2, markeredgecolor="black", label="Lyapunov")
    ax.fill_between(x_mb, merged["mean_lya"], merged["mean_base"], where=(merged["mean_base"] > merged["mean_lya"]), color="#cfe9e2", alpha=0.6, label="Time saved")

    # annotate % savings
    for xb, tb, tl in zip(x_mb, merged["mean_base"], merged["mean_lya"]):
        if tb > 0:
            delta = (tb - tl) / tb * 100
            ax.text(xb, (tb + tl) / 2, f"-{delta:.1f}%", ha="center", va="center", fontsize=10, color="#1e6855", fontweight="bold")

    ax.set_xlabel("Data Milestone (MB)", fontsize=12)
    ax.set_ylabel("Time to Collect (s)", fontsize=12)
    ax.set_title("Time Saved to Reach Data Milestones (node100)", fontsize=14, fontweight="bold")
    ax.legend(frameon=True, facecolor="white", framealpha=0.9, edgecolor="#333")
    ax.grid(True, axis="both", linestyle="--", linewidth=0.6)
    fig.tight_layout()
    out2 = os.path.join(PLOT_DIR, "time_to_data_gain_node100.png")
    plt.savefig(out2, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out2}")


if __name__ == "__main__":
    main()
