#!/usr/bin/env python3
"""
Project1: reference upper bound (no interference).
Produce two charts:
  1) Nodes vs Total Mission Time
  2) Nodes vs Efficiency (data/time or data/energy from 'Efficiency' column)
Input: results/node50/100/150/200.csv
Output: plots_reference/*.png
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_DIR = os.path.join(BASE_DIR, "results")
PLOT_DIR = os.path.join(BASE_DIR, "plots_reference")
os.makedirs(PLOT_DIR, exist_ok=True)

COLOR = "#7DCBB2"


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
        raise FileNotFoundError("No node*.csv files found in results/")
    return pd.concat(records, ignore_index=True)


def plot_metric(df, col, ylabel, title, fname, fmt="{:.2f}"):
    agg = df.groupby("Scale")[col].agg(["mean", "std"]).reset_index()
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(7.5, 5))
    bars = ax.bar(
        agg["Scale"].astype(str),
        agg["mean"],
        yerr=agg["std"].fillna(0),
        color=COLOR,
        edgecolor="black",
        capsize=6,
        alpha=0.9,
        label=title
    )
    for bar in bars:
        y = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            y + 0.01 * agg["mean"].max(),
            fmt.format(y),
            ha="center",
            va="bottom",
            fontsize=10,
            color="black",
        )
    ax.set_xlabel("Nodes", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(frameon=True, facecolor="white", framealpha=0.9, edgecolor="#333")
    ax.grid(True, axis="y", linestyle="--", linewidth=0.6)
    fig.tight_layout()
    out_path = os.path.join(PLOT_DIR, fname)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def main():
    df = load_all()
    # Use Total_Waypoints as a linear proxy for mission length (deterministic across scales)
    plot_metric(df, "Total_Waypoints", "Mission Length (waypoints, ~time)", "Nodes vs Mission Length (reference)", "mission_length_vs_nodes.png", fmt="{:.0f}")
    plot_metric(df, "Efficiency", "Efficiency (data/time)", "Nodes vs Efficiency", "efficiency_vs_nodes.png", fmt="{:.2f}")


if __name__ == "__main__":
    main()
