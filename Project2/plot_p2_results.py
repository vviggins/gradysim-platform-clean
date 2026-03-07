#!/usr/bin/env python3
"""
Plot aggregate metrics for Project2 (interference, no optimization).
Reads node50/100/150/200 CSVs under results/, aggregates mean/std, and saves bar charts.
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_DIR = os.path.join(BASE_DIR, "results")
PLOT_DIR = os.path.join(BASE_DIR, "plots")
os.makedirs(PLOT_DIR, exist_ok=True)

COLOR = "#FC9E79"  # soft orange


def load_all():
    records = []
    for scale in [50, 100, 150, 200]:
        path = os.path.join(RESULT_DIR, f"node{scale}.csv")
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        # normalize percent strings to float
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
    ax.set_xlabel("Scenario Scale (nodes)", fontsize=12)
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
    plot_metric(df, "Total_Data_Packets", "Total Data Packets", "Data Collected vs Scale", "data_collected.png", fmt="{:.0f}")
    plot_metric(df, "Success_Rate", "Success Rate", "Success Rate vs Scale", "success_rate.png", fmt="{:.2f}")
    plot_metric(df, "Total_Energy_Consumed", "Energy Consumed", "Energy vs Scale", "energy.png", fmt="{:.2f}")
    plot_metric(df, "Efficiency", "Efficiency (data/time or data/energy)", "Efficiency vs Scale", "efficiency.png", fmt="{:.2f}")
    plot_metric(df, "Average_Communication_Latency", "Avg Comm Latency", "Comm Latency vs Scale", "latency.png", fmt="{:.3f}")


if __name__ == "__main__":
    main()
