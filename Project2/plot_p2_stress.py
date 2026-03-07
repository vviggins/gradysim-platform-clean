#!/usr/bin/env python3
"""
Project2 stress profile (interference, no optimization).
Focus: how failure rate impacts latency/coverage/efficiency.
Input: results/node50/100/150/200.csv (per-run Failure_Rate present).
Outputs: plots_stress/*.png
"""
import os
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_DIR = os.path.join(BASE_DIR, "results")
PLOT_DIR = os.path.join(BASE_DIR, "plots_stress")
os.makedirs(PLOT_DIR, exist_ok=True)

PALETTE = {
    50: "#7DCBB2",
    100: "#5FB89F",
    150: "#3FA485",
    200: "#1E8B6D",
}


def load_all():
    records = []
    for scale in [50, 100, 150, 200]:
        path = os.path.join(RESULT_DIR, f"node{scale}.csv")
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        for pct_col in ["Success_Rate", "Failure_Rate"]:
            if pct_col in df.columns and df[pct_col].dtype == object:
                df[pct_col] = df[pct_col].str.rstrip("%").astype(float) / 100.0
        df["Scale"] = scale
        records.append(df)
    if not records:
        raise FileNotFoundError("No node*.csv found in results/")
    return pd.concat(records, ignore_index=True)


def plot_failure_vs(df, y_col, ylabel, title, fname):
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(8.5, 5.3))
    for scale, sub in df.groupby("Scale"):
        sub = sub.sort_values("Failure_Rate")
        ax.plot(
            sub["Failure_Rate"],
            sub[y_col],
            marker="o",
            linewidth=2.0,
            markeredgecolor="black",
            color=PALETTE.get(scale, "#888"),
            label=f"Node{scale}"
        )
    ax.set_xlabel("Failure Rate", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(frameon=True, facecolor="white", framealpha=0.9, edgecolor="#333")
    ax.grid(True, axis="both", linestyle="--", linewidth=0.6)
    fig.tight_layout()
    out_path = os.path.join(PLOT_DIR, fname)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def main():
    df = load_all()
    # Mission time proxy: Total_Data_Packets / Efficiency (since Efficiency = data/time)
    df["Mission_Time"] = df["Total_Data_Packets"] / df["Efficiency"]

    plot_failure_vs(df, "Mission_Time", "Mission Time (proxy, s)", "Failure Rate vs Mission Time (proxy)", "failure_vs_time.png")
    plot_failure_vs(df, "Total_Data_Packets", "Data Collected (packets)", "Failure Rate vs Coverage", "failure_vs_data.png")
    plot_failure_vs(df, "Total_Communication_Latency", "Total Comm Latency", "Failure Rate vs Long-Tail Latency", "failure_vs_latency.png")
    plot_failure_vs(df, "Efficiency", "Efficiency (data/time)", "Failure Rate vs Efficiency", "failure_vs_eff.png")


if __name__ == "__main__":
    main()
