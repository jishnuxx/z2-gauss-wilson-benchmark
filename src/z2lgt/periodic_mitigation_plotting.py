"""Plots for exact Gauss- versus Wilson-aware mitigation."""

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
    "raw_imbalance",
    "gauss_only_imbalance",
    "gauss_plus_wilson_imbalance",
    "raw_abs_error",
    "gauss_only_abs_error",
    "gauss_plus_wilson_abs_error",
    "raw_acceptance",
    "gauss_only_acceptance",
    "gauss_plus_wilson_acceptance",
}


def read_periodic_mitigation_csv(path: Path) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            raise ValueError(f"missing required columns in {path}")
        rows = [{key: float(value) for key, value in row.items()} for row in reader]
    if len(rows) < 2:
        raise ValueError("mitigation figure requires at least two rows")
    return rows


def plot_periodic_exact_mitigation(
    rows: list[dict[str, float]],
    output_dir: Path = Path("figures"),
) -> list[Path]:
    if len(rows) < 2:
        raise ValueError("mitigation figure requires at least two rows")
    time = np.asarray([row["time"] for row in rows])
    if np.any(np.diff(time) <= 0):
        raise ValueError("time points must be strictly increasing")

    plt.rcParams.update(
        {
            "font.size": 11.5,
            "axes.titlesize": 15,
            "axes.labelsize": 12.5,
            "legend.fontsize": 10,
        }
    )
    fig, axes = plt.subplots(
        3,
        1,
        figsize=(8.0, 8.4),
        sharex=True,
        gridspec_kw={"height_ratios": (2.0, 1.25, 0.9), "hspace": 0.10},
    )
    ax_trajectory, ax_error, ax_acceptance = axes

    trajectory_series = (
        ("ideal_imbalance", "Exact ideal", "#202020", "-", 2.6),
        ("raw_imbalance", "Raw ensemble", "#8A8A8A", ":", 2.1),
        ("gauss_only_imbalance", "Gauss only", "#1768AC", "--", 2.1),
        (
            "gauss_plus_wilson_imbalance",
            "Gauss + Wilson",
            "#2E7D32",
            "-.",
            2.2,
        ),
    )
    for key, label, color, linestyle, linewidth in trajectory_series:
        ax_trajectory.plot(
            time,
            [row[key] for row in rows],
            label=label,
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
        )
    ax_trajectory.set(
        ylabel=r"matter imbalance $O_{\rm LR}(t)$",
        ylim=(-0.02, 1.04),
        title="Wilson-aware verification reduces matter-dynamics bias",
    )
    ax_trajectory.grid(alpha=0.22)
    ax_trajectory.legend(frameon=False, ncols=2, loc="lower left")
    ax_trajectory.text(
        0.98,
        0.94,
        "exact single-fault ensemble; final fault probability 0.20",
        transform=ax_trajectory.transAxes,
        ha="right",
        va="top",
        fontsize=9.5,
        color="0.3",
    )

    error_series = (
        ("raw_abs_error", "Raw", "#D1495B"),
        ("gauss_only_abs_error", "Gauss only", "#1768AC"),
        ("gauss_plus_wilson_abs_error", "Gauss + Wilson", "#2E7D32"),
    )
    for key, label, color in error_series:
        values = np.asarray([row[key] for row in rows])
        ax_error.plot(
            time,
            values,
            color=color,
            linewidth=2.1,
            label=f"{label} (mean {values.mean():.3f})",
        )
    ax_error.set_ylabel(r"absolute error $|\Delta O_{\rm LR}|$")
    ax_error.set_ylim(bottom=0.0)
    ax_error.grid(alpha=0.22)
    ax_error.legend(frameon=False, loc="upper left")

    acceptance_series = (
        ("raw_acceptance", "Raw", "#8A8A8A", ":"),
        ("gauss_only_acceptance", "Gauss only", "#1768AC", "--"),
        (
            "gauss_plus_wilson_acceptance",
            "Gauss + Wilson",
            "#2E7D32",
            "-.",
        ),
    )
    for key, label, color, linestyle in acceptance_series:
        ax_acceptance.plot(
            time,
            [row[key] for row in rows],
            label=label,
            color=color,
            linestyle=linestyle,
            linewidth=2.0,
            drawstyle="steps-post",
        )
    ax_acceptance.set(
        xlabel="dimensionless evolution time",
        ylabel="acceptance",
        xlim=(time[0], time[-1]),
        ylim=(0.79, 1.015),
    )
    ax_acceptance.grid(alpha=0.22)
    ax_acceptance.legend(frameon=False, ncols=3, loc="lower left")

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        output_dir / "fig07_periodic_exact_mitigation.pdf",
        output_dir / "fig07_periodic_exact_mitigation.png",
    ]
    fig.savefig(paths[0], bbox_inches="tight")
    fig.savefig(paths[1], dpi=220, bbox_inches="tight")
    plt.close(fig)
    return paths
