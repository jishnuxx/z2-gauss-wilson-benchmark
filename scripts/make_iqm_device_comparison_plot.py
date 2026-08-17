#!/usr/bin/env python3
"""Plot exact, Trotter, Emerald, and Sirius sector separations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
EMERALD = "#00897B"
SIRIUS = "#7E57C2"
TROTTER = "#263238"
EXACT = "#90A4AE"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "results/processed/iqm_emerald_sirius_comparison.json",
    )
    parser.add_argument(
        "--output-stem",
        type=Path,
        default=ROOT / "figures/fig15_iqm_emerald_sirius_sector_separation",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    devices = payload["devices"]
    emerald = devices["emerald"]["points"]
    sirius = devices["sirius"]["points"]
    times = np.array([point["time"] for point in emerald])

    fig, ax = plt.subplots(figsize=(7.6, 4.9))
    ax.plot(
        times,
        [point["exact_sector_separation"] for point in emerald],
        color=EXACT,
        marker="o",
        linewidth=1.7,
        label="exact simulation",
    )
    ax.plot(
        times,
        [point["trotter_sector_separation"] for point in emerald],
        color=TROTTER,
        marker="s",
        linestyle="--",
        linewidth=2.0,
        label="two-step Trotter target",
    )
    for points, color, marker, label, offset in (
        (emerald, EMERALD, "o", "IQM Emerald (2 jobs)", -0.008),
        (sirius, SIRIUS, "D", "IQM Sirius (2 jobs)", +0.008),
    ):
        ax.errorbar(
            times + offset,
            [point["hardware_sector_separation"] for point in points],
            yerr=[point["hardware_sector_separation_se"] for point in points],
            color=color,
            marker=marker,
            markersize=6.5,
            linewidth=2.0,
            capsize=4,
            label=label,
            zorder=4,
        )

    for point in emerald[1:]:
        ax.annotate(
            f"{point['hardware_sector_separation_z']:.1f}σ",
            (point["time"] - 0.008, point["hardware_sector_separation"]),
            xytext=(0, 12),
            textcoords="offset points",
            ha="center",
            color=EMERALD,
            fontsize=9,
            fontweight="bold",
        )

    ax.axhline(0.0, color="0.45", linewidth=0.9)
    ax.set(
        xlabel=r"evolution time $t$",
        ylabel=r"sector separation $\Delta O_{\rm LR}=O_{+}-O_{-}$",
        title="Matched fixed-depth benchmark: Emerald resolves the sector response",
        xticks=times,
        xlim=(times.min() - 0.06, times.max() + 0.06),
    )
    ax.grid(alpha=0.2)
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    fig.text(
        0.5,
        0.012,
        "Error bars: shot standard errors after inverse-variance combining two independent 5000-shot jobs. Same calibration and mapping within each device.",
        ha="center",
        va="bottom",
        fontsize=8.7,
        color="0.32",
    )
    fig.subplots_adjust(bottom=0.17)

    args.output_stem.parent.mkdir(parents=True, exist_ok=True)
    pdf = args.output_stem.with_suffix(".pdf")
    png = args.output_stem.with_suffix(".png")
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, dpi=240, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {pdf}")
    print(f"Wrote {png}")


if __name__ == "__main__":
    main()
