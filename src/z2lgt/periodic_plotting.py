"""Matplotlib figures for the periodic conserved-sector benchmark."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


REQUIRED_COLUMNS = {
    "time",
    "ideal_imbalance",
    "wrong_sector_imbalance",
    "absolute_difference",
}


def read_periodic_dynamics_csv(path: Path) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            raise ValueError(f"missing required columns in {path}")
        rows = [
            {key: float(value) for key, value in row.items()}
            for row in reader
        ]
    if len(rows) < 2:
        raise ValueError("periodic dynamics plot requires at least two time points")
    return rows


def plot_periodic_sector_dynamics(
    rows: list[dict[str, float]],
    output_dir: Path = Path("figures"),
) -> list[Path]:
    """Plot sector-resolved matter transport and its absolute corruption."""
    if len(rows) < 2:
        raise ValueError("periodic dynamics plot requires at least two rows")
    time = np.asarray([row["time"] for row in rows], dtype=float)
    ideal = np.asarray([row["ideal_imbalance"] for row in rows], dtype=float)
    wrong = np.asarray([row["wrong_sector_imbalance"] for row in rows], dtype=float)
    difference = np.asarray([row["absolute_difference"] for row in rows], dtype=float)
    if np.any(np.diff(time) <= 0):
        raise ValueError("time points must be strictly increasing")

    plt.rcParams.update(
        {
            "font.size": 12,
            "axes.titlesize": 15,
            "axes.labelsize": 13,
            "legend.fontsize": 11,
        }
    )
    fig, (ax_top, ax_bottom) = plt.subplots(
        2,
        1,
        figsize=(7.6, 6.8),
        sharex=True,
        gridspec_kw={"height_ratios": (2.2, 1.0), "hspace": 0.08},
    )

    ax_top.plot(
        time,
        ideal,
        marker="o",
        color="#1768AC",
        linewidth=2.2,
        markersize=4.5,
        label=r"Target sector $W=+1$",
    )
    ax_top.plot(
        time,
        wrong,
        marker="s",
        color="#D1495B",
        linestyle="--",
        linewidth=2.0,
        markersize=4.2,
        label=r"Wrong sector $W=-1$ (Gauss passes)",
    )
    ax_top.axhline(0.0, color="0.72", linewidth=1.0)
    ax_top.set_ylabel(r"matter imbalance $O_{\rm LR}(t)$")
    ax_top.set_ylim(-1.08, 1.08)
    ax_top.set_title("A hidden Wilson-sector error corrupts physical matter dynamics")
    ax_top.legend(frameon=False, loc="lower left")
    ax_top.grid(alpha=0.22)
    ax_top.text(
        0.98,
        0.94,
        r"$\langle G_s\rangle=+1$ for both trajectories",
        transform=ax_top.transAxes,
        ha="right",
        va="top",
        fontsize=10.5,
        color="0.28",
    )

    ax_bottom.fill_between(time, 0.0, difference, color="#E9A23B", alpha=0.3)
    ax_bottom.plot(time, difference, color="#B66A00", linewidth=2.0)
    maximum = int(np.argmax(difference))
    ax_bottom.scatter(time[maximum], difference[maximum], color="#7A4500", zorder=3)
    ax_bottom.annotate(
        f"max {difference[maximum]:.2f}",
        (time[maximum], difference[maximum]),
        xytext=(-8, 8),
        textcoords="offset points",
        ha="right",
        fontsize=10,
    )
    ax_bottom.set(
        xlabel="dimensionless evolution time",
        ylabel=r"$|\Delta O_{\rm LR}|$",
        xlim=(time[0], time[-1]),
        ylim=(0.0, max(0.1, 1.12 * difference.max())),
    )
    ax_bottom.grid(alpha=0.22)

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        output_dir / "fig06_periodic_sector_dynamics.pdf",
        output_dir / "fig06_periodic_sector_dynamics.png",
    ]
    fig.savefig(paths[0], bbox_inches="tight")
    fig.savefig(paths[1], dpi=220, bbox_inches="tight")
    plt.close(fig)
    return paths
