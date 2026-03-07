import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
try:
    import seaborn as sns
    _HAS_SEABORN = True
except ImportError:
    _HAS_SEABORN = False


def _prep_style():
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams["axes.titleweight"] = "bold"
    plt.rcParams["axes.labelsize"] = 11
    plt.rcParams["xtick.labelsize"] = 10
    plt.rcParams["ytick.labelsize"] = 10


def plot_violin_latency_retry(summary, out_dir, colors, labels):
    """Violin + box for Avg_Comm_Latency and Avg_Retry_Per_Node."""
    _prep_style()
    metrics = [
        ("Avg_Comm_Latency", "Avg Comm Latency (s)", "violin_latency.png"),
        ("Avg_Retry_Per_Node", "Avg Retry Per Node", "violin_retry.png"),
    ]
    for col, ylabel, fname in metrics:
        if col not in summary.columns:
            continue
        plt.figure(figsize=(7.2, 4.6))
        if _HAS_SEABORN:
            sns.violinplot(
                data=summary,
                x="Num_Nodes",
                y=col,
                hue="Strategy",
                palette=colors,
                cut=0,
                inner=None,
                linewidth=1.0,
            )
            sns.boxplot(
                data=summary,
                x="Num_Nodes",
                y=col,
                hue="Strategy",
                palette=colors,
                showcaps=True,
                boxprops={"facecolor": "none", "edgecolor": "black"},
                showfliers=False,
                linewidth=1.0,
                dodge=True,
            )
        else:
            # fallback: grouped boxplot
            grouped = summary.groupby(["Num_Nodes", "Strategy"])[col].apply(list)
            nodes = sorted(summary["Num_Nodes"].unique())
            strategies = ["baseline", "lya"]
            width = 0.35
            for i, strat in enumerate(strategies):
                data = [grouped.get((n, strat), []) for n in nodes]
                positions = np.arange(len(nodes)) + (i - 0.5) * width
                plt.boxplot(
                    data,
                    positions=positions,
                    widths=width * 0.9,
                    patch_artist=True,
                    boxprops={"facecolor": colors.get(strat, "#ccc"), "edgecolor": "black"},
                    medianprops={"color": "black"},
                )
            plt.xticks(np.arange(len(nodes)), [f"Node{n}" for n in nodes])
        plt.xlabel("Num Nodes", fontsize=11)
        plt.ylabel(ylabel, fontsize=11)
        plt.title(ylabel, fontsize=14, fontweight="bold", pad=10)
        plt.grid(axis="y", linestyle="--", alpha=0.35)
        plt.legend(frameon=True, facecolor="white", framealpha=0.9, edgecolor="#999")
        plt.tight_layout()
        out_path = os.path.join(out_dir, fname)
        plt.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Saved: {out_path}")


def plot_stacked_coverage(summary, out_dir, colors, labels):
    """Stacked percent bars for Success/Fail/Skipped."""
    _prep_style()
    plt.figure(figsize=(7.5, 4.8))
    nodes = sorted(summary["Num_Nodes"].unique())
    strategies = ["baseline", "lya"]
    bar_width = 0.35
    x = np.arange(len(nodes))

    for i, strat in enumerate(strategies):
        subset = summary[summary["Strategy"] == strat]
        success = []
        fail = []
        skip = []
        for n in nodes:
            df_n = subset[subset["Num_Nodes"] == n]
            s = df_n["Success_Nodes"].mean()
            f = df_n["Fail_Nodes"].mean()
            sk = df_n["Skipped_Nodes"].mean()
            total = s + f + sk if (s + f + sk) > 0 else 1
            success.append(s / total * 100)
            fail.append(f / total * 100)
            skip.append(sk / total * 100)
        xpos = x + (i - 0.5) * bar_width
        plt.bar(xpos, success, width=bar_width, color=colors[strat], edgecolor="black", linewidth=1.0, label=f"{labels[strat]}-Success")
        plt.bar(xpos, fail, width=bar_width, bottom=success, color="#bbbbbb", edgecolor="black", linewidth=1.0, label=f"{labels[strat]}-Fail")
        plt.bar(xpos, skip, width=bar_width, bottom=np.array(success) + np.array(fail), color="#888888", edgecolor="black", linewidth=1.0, label=f"{labels[strat]}-Skip")

    plt.xticks(x, [f"Node{n}" for n in nodes])
    plt.ylabel("Proportion (%)", fontsize=11)
    plt.title("Coverage (Success/Fail/Skip)", fontsize=14, fontweight="bold", pad=10)
    plt.grid(axis="y", linestyle="--", alpha=0.35)
    plt.legend(frameon=True, facecolor="white", framealpha=0.9, edgecolor="#999", fontsize=9, ncol=2)
    plt.tight_layout()
    out_path = os.path.join(out_dir, "coverage_stacked.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def plot_efficiency_tradeoff(summary, out_dir, colors, labels):
    """Scatter: Total_Time vs Eff_Data_Per_Energy (color=strategy, marker=num_nodes)."""
    _prep_style()
    plt.figure(figsize=(7.5, 5.0))
    markers = {50: "o", 100: "s", 150: "D", 200: "^"}
    for strat in ["baseline", "lya"]:
        df = summary[summary["Strategy"] == strat]
        for n in sorted(df["Num_Nodes"].unique()):
            df_n = df[df["Num_Nodes"] == n]
            plt.scatter(
                df_n["Total_Time"],
                df_n["Eff_Data_Per_Energy"],
                color=colors.get(strat, "#333"),
                edgecolor="black",
                linewidth=0.8,
                marker=markers.get(n, "o"),
                s=50,
                alpha=0.85,
                label=f"{labels[strat]}-{n}",
            )
    plt.xlabel("Total Time (s)", fontsize=11)
    plt.ylabel("Efficiency (KB / Energy)", fontsize=11)
    plt.title("Time vs Energy Efficiency", fontsize=14, fontweight="bold", pad=10)
    plt.grid(True, linestyle="--", alpha=0.35)
    plt.legend(frameon=True, facecolor="white", framealpha=0.9, edgecolor="#999", fontsize=9, ncol=2)
    plt.tight_layout()
    out_path = os.path.join(out_dir, "eff_tradeoff.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def plot_eff_cdf(summary, out_dir, colors, labels):
    """CDF of Eff_Data_Per_Time, grouped by strategy."""
    _prep_style()
    plt.figure(figsize=(7.0, 4.8))
    for strat in ["baseline", "lya"]:
        data = summary[summary["Strategy"] == strat]["Eff_Data_Per_Time"].dropna().sort_values()
        if data.empty:
            continue
        y = np.linspace(0, 1, len(data), endpoint=False)
        plt.step(data, y, where="post", label=labels[strat], color=colors.get(strat, "#333"), linewidth=2.2)
    plt.xlabel("Efficiency (KB / s)", fontsize=11)
    plt.ylabel("CDF", fontsize=11)
    plt.title("Efficiency CDF (All scales)", fontsize=14, fontweight="bold", pad=8)
    plt.grid(True, linestyle="--", alpha=0.35)
    plt.legend(frameon=True, facecolor="white", framealpha=0.9, edgecolor="#999", fontsize=10)
    plt.tight_layout()
    out_path = os.path.join(out_dir, "eff_cdf.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def plot_tail_nodes(summary, out_dir, colors, labels, top_k=5):
    """Worst-case nodes by Avg_Comm_Latency (top K) per scale & strategy."""
    _prep_style()
    plt.figure(figsize=(8.0, 5.2))
    records = []
    for strat in ["baseline", "lya"]:
        for n in sorted(summary["Num_Nodes"].unique()):
            df = summary[(summary["Strategy"] == strat) & (summary["Num_Nodes"] == n)]
            # 使用 Avg_Comm_Latency 最高的若干样本（这里是 per-file 汇总; 如需 per-node 需更细粒度）
            worst = df.nlargest(top_k, "Avg_Comm_Latency")
            for val in worst["Avg_Comm_Latency"]:
                records.append({"Num_Nodes": n, "Strategy": strat, "Latency": val})
    if not records:
        return
    df_plot = pd.DataFrame(records)
    if _HAS_SEABORN:
        sns.boxplot(
            data=df_plot,
            x="Num_Nodes",
            y="Latency",
            hue="Strategy",
            palette=colors,
            showcaps=True,
            boxprops={"edgecolor": "black"},
            showfliers=False,
            linewidth=1.0,
        )
    else:
        markers = {"baseline": "o", "lya": "s"}
        for strat in ["baseline", "lya"]:
            subset = df_plot[df_plot["Strategy"] == strat]
            plt.scatter(
                subset["Num_Nodes"],
                subset["Latency"],
                label=labels[strat],
                color=colors.get(strat, "#333"),
                edgecolor="black",
                marker=markers.get(strat, "o"),
                alpha=0.8,
            )
    plt.xlabel("Num Nodes", fontsize=11)
    plt.ylabel("Worst-case Latency (s)", fontsize=11)
    plt.title(f"Worst {top_k} Latency (per scale & strategy)", fontsize=14, fontweight="bold", pad=8)
    plt.grid(True, linestyle="--", alpha=0.35)
    plt.legend(frameon=True, facecolor="white", framealpha=0.9, edgecolor="#999", fontsize=10)
    plt.tight_layout()
    out_path = os.path.join(out_dir, "tail_latency.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")
