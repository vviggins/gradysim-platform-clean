import matplotlib.pyplot as plt


# Color palette aligned with Project3 (Baseline vs Lyapunov)
PALETTE = {
    "Baseline": "#FC9E79",
    "Lyapunov": "#7DCBB2",
}


def apply_ieee_style():
    """Apply a clean, publication-friendly style."""
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.linestyle": "--",
            "grid.alpha": 0.35,
            "axes.labelsize": 12,
            "axes.titlesize": 13,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "font.family": "DejaVu Sans",
            "lines.linewidth": 2.0,
        }
    )


def line_with_error(ax, x, y, yerr=None, label=None, color=None, marker="o", linestyle="-"):
    """Plot a line with optional error bars."""
    return ax.errorbar(
        x,
        y,
        yerr=yerr,
        label=label,
        color=color,
        marker=marker,
        linestyle=linestyle,
        linewidth=2.0,
        capsize=3,
        markersize=6,
    )


def dual_axis(
    ax,
    x,
    left_series,
    right_series,
    xlabel,
    left_label,
    right_label,
    xscale="linear",
    title=None,
):
    """
    Plot two metrics sharing x but different y-axes.
    left/right series: list of dicts with keys y, yerr, label, color, marker, linestyle.
    """
    ax.set_xscale(xscale)
    for s in left_series:
        line_with_error(
            ax,
            x,
            s["y"],
            yerr=s.get("yerr"),
            label=s.get("label"),
            color=s.get("color"),
            marker=s.get("marker", "o"),
            linestyle=s.get("linestyle", "-"),
        )
    ax.set_xlabel(xlabel)
    ax.set_ylabel(left_label)

    ax2 = ax.twinx()
    for s in right_series:
        line_with_error(
            ax2,
            x,
            s["y"],
            yerr=s.get("yerr"),
            label=s.get("label"),
            color=s.get("color"),
            marker=s.get("marker", "s"),
            linestyle=s.get("linestyle", "--"),
        )
    ax2.set_ylabel(right_label)

    if title:
        ax.set_title(title, fontweight="bold")

    return ax, ax2


def collect_legend(fig, axes):
    """Collect legends from all axes (including twins) into one figure-level legend."""
    handles, labels = [], []
    for ax in fig.axes:
        hlist, llist = ax.get_legend_handles_labels()
        for h, l in zip(hlist, llist):
            if l not in labels:
                handles.append(h)
                labels.append(l)
    if handles:
        fig.legend(handles, labels, loc="upper center", ncol=min(4, len(labels)), bbox_to_anchor=(0.5, 1.02))
