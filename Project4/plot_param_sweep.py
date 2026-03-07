#!/usr/bin/env python3
"""
Plot Lyapunov parameter sweep results.
- Efficiency (Data/Time) vs LYA_V
- Optional Total_Time and Data_Collected_KB trends
"""
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_FILE = os.path.join(BASE_DIR, "results", "param_sweep_summary.csv")
PLOT_DIR = os.path.join(BASE_DIR, "plots_param")
os.makedirs(PLOT_DIR, exist_ok=True)

COLOR_BASELINE = "#FC9E79"
COLOR_LYA = "#7DCBB2"
PALETTE = {
    50: "#7DCBB2",
    100: "#5FB89F",
    150: "#3FA485",
    200: "#1E8B6D",
}


def load_data():
    if not os.path.exists(RESULT_FILE):
        print(f"Result file not found: {RESULT_FILE}")
        sys.exit(1)
    df = pd.read_csv(RESULT_FILE)
    return df


def plot_efficiency(df):
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(8.5, 5.3))

    lya = df[df["Strategy"].str.startswith("lya_")].copy()
    if lya.empty:
        print("No Lyapunov entries found in data.")
        return
    lya["LYA_V"] = lya["LYA_V"].astype(float)
    agg = lya.groupby("LYA_V")["Eff_Data_Per_Time"].agg(["mean", "std"]).reset_index()
    ax.errorbar(
        agg["LYA_V"],
        agg["mean"],
        yerr=agg["std"].fillna(0),
        fmt="-o",
        color=COLOR_LYA,
        ecolor="black",
        elinewidth=1.2,
        capsize=6,
        linewidth=2.2,
        markeredgecolor="black",
        label="Lyapunov (mean ± std)"
    )
    for x, y in zip(agg["LYA_V"], agg["mean"]):
        ax.text(
            x, y + 0.02 * max(agg["mean"]),
            f"{y:.2f}",
            ha="center", va="bottom", fontsize=10, color="black"
        )

    ax.set_xlabel("Lyapunov weight V (skip aggressiveness)", fontsize=12)
    ax.set_ylabel("Efficiency: Data / Time (KB/s)", fontsize=12)
    ax.set_title("Lyapunov Efficiency vs V", fontsize=14, fontweight="bold")
    ax.legend(frameon=True, facecolor="white", framealpha=0.9, edgecolor="#333")
    ax.grid(True, axis="y", linestyle="--", linewidth=0.6)
    fig.tight_layout()

    out = os.path.join(PLOT_DIR, "eff_vs_v.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


def plot_efficiency_by_scale(df):
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5.5))

    lya = df[df["Strategy"].str.startswith("lya_")].copy()
    if lya.empty:
        print("No Lyapunov entries found in data.")
        return
    lya["LYA_V"] = lya["LYA_V"].astype(float)

    for scale, sub in lya.groupby("Num_Nodes"):
        g = sub.groupby("LYA_V")["Eff_Data_Per_Time"].mean().reset_index()
        ax.plot(
            g["LYA_V"], g["Eff_Data_Per_Time"],
            marker="o", linewidth=2.2, markeredgecolor="black",
            color=PALETTE.get(scale, COLOR_LYA),
            label=f"TSP-{scale}"
        )

    ax.set_xlabel("Lyapunov weight V (skip aggressiveness)", fontsize=12)
    ax.set_ylabel("Efficiency: Data / Time (KB/s)", fontsize=12)
    ax.set_title("Lyapunov Efficiency vs V across scales", fontsize=14, fontweight="bold")
    ax.legend(frameon=True, facecolor="white", framealpha=0.9, edgecolor="#333")
    ax.grid(True, axis="y", linestyle="--", linewidth=0.6)
    fig.tight_layout()

    out = os.path.join(PLOT_DIR, "eff_vs_v_by_scale.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


def plot_time_and_data(df):
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax1 = plt.subplots(figsize=(8.5, 5.3))

    lya = df[df["Strategy"].str.startswith("lya_")].copy()
    lya["LYA_V"] = lya["LYA_V"].astype(float)

    g_time = lya.groupby("LYA_V")["Total_Time"].mean()
    g_data = lya.groupby("LYA_V")["Data_Collected_KB"].mean()
    v_values = g_time.index.tolist()

    ax1.bar(
        [v - 0.12 for v in v_values], g_time.values,
        width=0.24, color=COLOR_LYA, edgecolor="black", alpha=0.85,
        label="Total Time (Lyapunov)"
    )
    ax1.set_xlabel("Lyapunov weight V", fontsize=12)
    ax1.set_ylabel("Total Time (s)", fontsize=12)
    ax1.tick_params(axis="y", labelcolor=COLOR_LYA)

    ax2 = ax1.twinx()
    ax2.plot(
        [v + 0.12 for v in v_values], g_data.values,
        color="#5A5A5A", marker="s", linewidth=2,
        label="Data Collected (Lyapunov)", markeredgecolor="black"
    )
    ax2.set_ylabel("Data Collected (KB)", fontsize=12)
    ax2.tick_params(axis="y", labelcolor="#5A5A5A")

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper center",
               frameon=True, facecolor="white", framealpha=0.9, edgecolor="#333", ncol=2)

    ax1.grid(True, axis="y", linestyle="--", linewidth=0.6)
    fig.tight_layout()
    out = os.path.join(PLOT_DIR, "time_data_vs_v.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


def main():
    df = load_data()
    plot_efficiency(df)
    plot_efficiency_by_scale(df)
    plot_time_and_data(df)


if __name__ == "__main__":
    main()
