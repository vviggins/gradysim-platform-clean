#!/usr/bin/env python3
"""
Publication-style plots for baseline vs Lyapunov (scales: 50/100/150/200).
Palette: baseline #FC9E79, Lyapunov #7DCBB2.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
try:
    import seaborn as sns
    _HAS_SEABORN = True
except ImportError:
    _HAS_SEABORN = False

ROOT = os.path.dirname(os.path.abspath(__file__))
RESULT_DIR = os.path.join(ROOT, "results")
PLOT_DIR = os.path.join(ROOT, "plots_final")
os.makedirs(PLOT_DIR, exist_ok=True)

SUMMARY_CSV = os.path.join(RESULT_DIR, "lya_summary.csv")
TRAJ_CSV = os.path.join(RESULT_DIR, "lya_trajectory.csv")

COLORS = {"baseline": "#FC9E79", "lya": "#7DCBB2"}
LABELS = {"baseline": "Baseline", "lya": "Lyapunov"}


def bar_with_error(df, metric, title, ylabel, fname):
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(7.2, 5.0))

    # 统计均值和标准差
    grouped = df.groupby(["Num_Nodes", "Strategy"])[metric]
    stats = grouped.agg(["mean", "std"]).reset_index()
    stats["Color"] = stats["Strategy"].map(COLORS)
    stats["Label"] = stats["Strategy"].map(LABELS)

    # 保证顺序
    scales = sorted(stats["Num_Nodes"].unique())
    strategies = ["baseline", "lya"]
    bar_width = 0.8 / len(strategies)
    positions = np.arange(len(scales))

    for i, strat in enumerate(strategies):
        subset = stats[stats["Strategy"] == strat]
        means = subset["mean"].values
        stds = subset["std"].fillna(0).values
        xpos = positions + i * bar_width - (len(strategies) - 1) / 2 * bar_width
        bars = ax.bar(
            xpos,
            means,
            width=bar_width,
            yerr=stds,
            capsize=5,
            color=COLORS[strat],
            edgecolor="black",
            linewidth=1.0,
            alpha=0.92,
            label=LABELS[strat],
        )
        # 标注数值
        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + max(means) * 0.03,
                f"{h:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    ax.set_xticks(positions)
    ax.set_xticklabels([f"Node{n}" for n in scales], fontsize=12)
    ax.set_ylabel(ylabel, fontsize=13, labelpad=8)
    ax.set_title(title, fontsize=15, fontweight="bold", pad=12)
    ax.tick_params(axis="y", labelsize=11)
    ax.yaxis.grid(True, linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.legend(frameon=True, facecolor="white", framealpha=0.85, fontsize=11, title="Strategy", title_fontsize=11)

    fig.tight_layout(pad=1.6)
    out_path = os.path.join(PLOT_DIR, fname)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_trajectory(df, scale=100):
    if df.empty:
        return
    df_scale = df[df["Num_Nodes"] == scale].copy()
    if df_scale.empty:
        return
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(7.0, 4.8))
    for strat, group in df_scale.groupby("Strategy"):
        g = group.sort_values("Time").copy()
        g["Data_Collected_KB"] = g["Data_Collected_KB"].cummax()
        if _HAS_SEABORN:
            sns.lineplot(
                x=g["Time"],
                y=g["Data_Collected_KB"],
                ax=ax,
                label=LABELS.get(strat, strat),
                color=COLORS.get(strat, "#333"),
                linewidth=2.6,
            )
        else:
            ax.plot(
                g["Time"],
                g["Data_Collected_KB"],
                label=LABELS.get(strat, strat),
                color=COLORS.get(strat, "#333"),
                linewidth=2.6,
            )
    ax.set_xlabel("Time (s)", fontsize=13)
    ax.set_ylabel("Cumulative Data (KB)", fontsize=13)
    ax.set_title(f"Trajectory (Node{scale})", fontsize=15, fontweight="bold", pad=10)
    ax.tick_params(axis="both", labelsize=11)
    ax.yaxis.grid(True, linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.legend(frameon=True, facecolor="white", framealpha=0.85, fontsize=11, title="Strategy", title_fontsize=11)
    fig.tight_layout(pad=1.6)
    out_path = os.path.join(PLOT_DIR, "trajectory_node100.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def main():
    summary = pd.read_csv(SUMMARY_CSV)
    traj = pd.read_csv(TRAJ_CSV) if os.path.exists(TRAJ_CSV) else pd.DataFrame()

    metrics = {
        "Total_Time": ("Total Mission Time", "Average Time (s)", "total_time.png"),
        "Data_Collected_KB": ("Total Data Collected", "Average Data (KB)", "data_collected.png"),
        "Eff_Data_Per_Time": ("Time Efficiency", "Avg Efficiency (KB/s)", "eff_time.png"),
        "Eff_Data_Per_Energy": ("Energy Efficiency", "Avg Efficiency (KB/Energy)", "eff_energy.png"),
        "Skipped_Nodes": ("Skipped Nodes", "Average Skipped Nodes", "skipped_nodes.png"),
    }
    for col, (title, ylabel, fname) in metrics.items():
        if col in summary.columns:
            bar_with_error(summary, col, title, ylabel, fname)

    plot_trajectory(traj, scale=100)

    # Additional plots (do not overwrite existing ones)
    if not summary.empty:
        from plotting_extra import (
            plot_violin_latency_retry,
            plot_stacked_coverage,
            plot_efficiency_tradeoff,
            plot_eff_cdf,
            plot_tail_nodes,
        )
        plot_violin_latency_retry(summary, PLOT_DIR, COLORS, LABELS)
        plot_stacked_coverage(summary, PLOT_DIR, COLORS, LABELS)
        plot_efficiency_tradeoff(summary, PLOT_DIR, COLORS, LABELS)
        plot_eff_cdf(summary, PLOT_DIR, COLORS, LABELS)
        plot_tail_nodes(summary, PLOT_DIR, COLORS, LABELS)


if __name__ == "__main__":
    main()
