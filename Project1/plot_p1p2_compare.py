#!/usr/bin/env python3
"""
Cross-project comparison: Project1 (no interference) vs Project2 (interference, no optimization).
Aggregates node50/100/150/200 CSVs and draws side-by-side bars with deltas.
Outputs -> plots_compare/*.png
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
P1_RESULTS = os.path.join(BASE_DIR, "results")
P2_RESULTS = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "Project2", "Project5_CollectData", "results"))
PLOT_DIR = os.path.join(BASE_DIR, "plots_compare")
os.makedirs(PLOT_DIR, exist_ok=True)

COLOR_P1 = "#7DCBB2"  # baseline: no interference
COLOR_P2 = "#FC9E79"  # interference: no optimization


def load_project(results_dir, label):
    records = []
    for scale in [50, 100, 150, 200]:
        path = os.path.join(results_dir, f"node{scale}.csv")
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        for pct_col in ["Success_Rate", "Failure_Rate"]:
            if pct_col in df.columns and df[pct_col].dtype == object:
                df[pct_col] = df[pct_col].str.rstrip("%").astype(float) / 100.0
        df["Scale"] = scale
        df["Project"] = label
        records.append(df)
    if not records:
        raise FileNotFoundError(f"No node*.csv found in {results_dir}")
    return pd.concat(records, ignore_index=True)


def grouped_bars(df, metric, ylabel, title, fname, higher_better=True):
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    color_map = {"P1": COLOR_P1, "P2": COLOR_P2}

    df_ag = df.groupby(["Scale", "Project"])[metric].agg(["mean", "std"]).reset_index()
    scales = sorted(df_ag["Scale"].unique())
    bar_width = 0.35
    positions = np.arange(len(scales))

    for idx, proj in enumerate(["P1", "P2"]):
        sub = df_ag[df_ag["Project"] == proj]
        # align by scale
        means = [sub[sub["Scale"] == s]["mean"].iloc[0] for s in scales]
        stds = [sub[sub["Scale"] == s]["std"].iloc[0] if not sub[sub["Scale"] == s]["std"].isna().all() else 0 for s in scales]
        x_pos = positions + (idx - 0.5) * bar_width
        bars = ax.bar(
            x_pos,
            means,
            width=bar_width,
            color=color_map[proj],
            edgecolor="black",
            yerr=stds,
            capsize=6,
            alpha=0.9,
            label="No interference (P1)" if proj == "P1" else "Interference (P2)"
        )
        for bar, val in zip(bars, means):
            ax.text(bar.get_x() + bar.get_width() / 2, val + 0.01 * max(means + [max(stds, default=0)]),
                    f"{val:.2f}", ha="center", va="bottom", fontsize=10, color="black")

    ax.set_xticks(positions)
    ax.set_xticklabels([f"Node{s}" for s in scales])
    ax.set_xlabel("Scenario Scale", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(frameon=True, facecolor="white", framealpha=0.9, edgecolor="#333")
    ax.grid(True, axis="y", linestyle="--", linewidth=0.6)
    fig.tight_layout()
    out_path = os.path.join(PLOT_DIR, fname)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def delta_plot(df, metric, title, fname, higher_better=True):
    """
    Plot relative gap (P1 vs P2) in percent for each scale.
    """
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    df_ag = df.groupby(["Scale", "Project"])[metric].mean().unstack()
    scales = sorted(df_ag.index)
    # higher_better: (P1 - P2)/P2; lower_better: (P2 - P1)/P2
    deltas = []
    for s in scales:
        v1 = df_ag.loc[s, "P1"]
        v2 = df_ag.loc[s, "P2"]
        if higher_better:
            delta = (v1 - v2) / v2 * 100 if v2 != 0 else 0
        else:
            delta = (v2 - v1) / v2 * 100 if v2 != 0 else 0
        deltas.append(delta)

    bars = ax.bar([str(s) for s in scales], deltas, color="#5A6ACF", edgecolor="black", alpha=0.9)
    for bar, val in zip(bars, deltas):
        ax.text(bar.get_x() + bar.get_width() / 2, val + (2 if val >= 0 else -2),
                f"{val:.1f}%", ha="center", va="bottom" if val >= 0 else "top", fontsize=10, color="black")

    ax.set_xlabel("Scenario Scale", fontsize=12)
    ax.set_ylabel("Relative gap (P1 vs P2) [%]", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axhline(0, color="#444", linewidth=1)
    ax.grid(True, axis="y", linestyle="--", linewidth=0.6)
    fig.tight_layout()
    out_path = os.path.join(PLOT_DIR, fname)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def main():
    p1 = load_project(P1_RESULTS, "P1")
    p2 = load_project(P2_RESULTS, "P2")
    df = pd.concat([p1, p2], ignore_index=True)

    grouped_bars(df, "Total_Data_Packets", "Total Data Packets", "Data Collected (P1 vs P2)", "data_compare.png")
    grouped_bars(df, "Success_Rate", "Success Rate", "Success Rate (P1 vs P2)", "success_compare.png")
    grouped_bars(df, "Total_Energy_Consumed", "Energy Consumed", "Energy (P1 vs P2)", "energy_compare.png")
    grouped_bars(df, "Efficiency", "Efficiency (data/time or data/energy)", "Efficiency (P1 vs P2)", "efficiency_compare.png")
    grouped_bars(df, "Average_Communication_Latency", "Avg Comm Latency", "Latency (P1 vs P2)", "latency_compare.png", higher_better=False)

    # delta plots to highlight gap
    delta_plot(df, "Total_Data_Packets", "Data advantage of P1 over P2", "delta_data.png", higher_better=True)
    delta_plot(df, "Success_Rate", "Success rate advantage (P1 vs P2)", "delta_success.png", higher_better=True)
    delta_plot(df, "Total_Energy_Consumed", "Energy saving of P1 vs P2", "delta_energy.png", higher_better=False)
    delta_plot(df, "Efficiency", "Efficiency gain (P1 vs P2)", "delta_efficiency.png", higher_better=True)
    delta_plot(df, "Average_Communication_Latency", "Latency reduction (P1 vs P2)", "delta_latency.png", higher_better=False)


if __name__ == "__main__":
    main()
