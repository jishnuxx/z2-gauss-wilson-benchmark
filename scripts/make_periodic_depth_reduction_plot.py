#!/usr/bin/env python3
"""Plot the periodic depth-reduction audit."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import _bootstrap  # noqa: F401
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


MODE_LABELS = {
    "joint": "joint: matter+Gauss+Wilson",
    "wilson_matter": "matter+Wilson",
    "matter_only": "matter only",
}
MODE_COLORS = {
    "joint": "#757575",
    "wilson_matter": "#7B1FA2",
    "matter_only": "#1565C0",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def plot(rows: list[dict[str, str]], output_dir: Path, output_stem: str) -> list[Path]:
    two_step = [row for row in rows if int(float(row["trotter_steps"])) == 2]
    baseline = next(
        row
        for row in rows
        if row["candidate"] == "t=0.8,dt=0.4" and row["readout_mode"] == "joint"
    )
    recommended = [row for row in rows if row["recommended"] == "True"]

    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.labelsize": 12,
            "legend.fontsize": 9,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4), gridspec_kw={"wspace": 0.28})
    ax_trade, ax_bar = axes

    for mode, label in MODE_LABELS.items():
        selected = [row for row in rows if row["readout_mode"] == mode]
        x = [f(row, "source_max_two_qubit_gate_count") for row in selected]
        y = [f(row, "trotter_sector_separation") for row in selected]
        sizes = [35 + 20 * f(row, "trotter_steps") for row in selected]
        ax_trade.scatter(
            x,
            y,
            s=sizes,
            alpha=0.78,
            color=MODE_COLORS[mode],
            label=label,
        )
    ax_trade.axhline(0.10, color="0.3", linestyle="--", linewidth=1.0, label="signal gate")
    ax_trade.scatter(
        [f(baseline, "source_max_two_qubit_gate_count")],
        [f(baseline, "trotter_sector_separation")],
        marker="*",
        s=220,
        color="#D32F2F",
        edgecolor="black",
        linewidth=0.5,
        label="current joint baseline",
        zorder=5,
    )
    if recommended:
        row = recommended[0]
        ax_trade.scatter(
            [f(row, "source_max_two_qubit_gate_count")],
            [f(row, "trotter_sector_separation")],
            marker="P",
            s=160,
            color="#00A676",
            edgecolor="black",
            linewidth=0.5,
            label="recommended reduced run",
            zorder=6,
        )
    ax_trade.set(
        xlabel="source two-qubit gates",
        ylabel=r"Trotter $|\Delta O_{\rm LR}|$",
        title="Signal versus source two-qubit count",
    )
    ax_trade.grid(alpha=0.22)
    ax_trade.legend(frameon=False, loc="upper left")

    current_rows = [
        row
        for row in two_step
        if row["candidate"] == "t=0.8,dt=0.4"
        and row["readout_mode"] in ("joint", "wilson_matter", "matter_only")
    ]
    current_rows.sort(
        key=lambda row: ["joint", "wilson_matter", "matter_only"].index(row["readout_mode"])
    )
    x = np.arange(len(current_rows), dtype=float)
    ax_bar.bar(
        x - 0.18,
        [f(row, "source_max_two_qubit_gate_count") for row in current_rows],
        0.36,
        color=[MODE_COLORS[row["readout_mode"]] for row in current_rows],
        alpha=0.88,
        label="two-qubit gates",
    )
    ax_depth = ax_bar.twinx()
    ax_depth.plot(
        x + 0.18,
        [f(row, "source_max_depth") for row in current_rows],
        "ko",
        label="depth",
    )
    ax_bar.set(
        xticks=x,
        xticklabels=[row["readout_mode"].replace("_", "\n") for row in current_rows],
        ylabel="source two-qubit gates",
        title=r"Same physics point: $t=0.8,\ dt=0.4$",
    )
    ax_bar.set_ylim(0, 92)
    ax_depth.set_ylim(120, 140)
    ax_depth.set_ylabel("source depth")
    ax_bar.grid(axis="y", alpha=0.22)
    for xpos, row in zip(x, current_rows, strict=True):
        reduction = 100 * f(row, "two_qubit_reduction_fraction_vs_current_joint")
        ax_bar.text(
            xpos,
            f(row, "source_max_two_qubit_gate_count") - 4,
            f"{reduction:.0f}% less",
            ha="center",
            va="top",
            fontsize=9.5,
            color="white",
        )

    fig.suptitle(
        "Periodic hardware depth-reduction audit: split dynamics readout from diagnostics",
        fontsize=14.5,
        y=1.02,
    )
    fig.text(
        0.5,
        -0.015,
        r"One-step Trotter candidates have zero target $O_{\rm LR}$ separation; two steps remain the minimum for this observable.",
        ha="center",
        va="top",
        fontsize=10,
        color="0.35",
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        output_dir / f"{output_stem}.pdf",
        output_dir / f"{output_stem}.png",
    ]
    fig.savefig(paths[0], bbox_inches="tight")
    fig.savefig(paths[1], dpi=220, bbox_inches="tight")
    plt.close(fig)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("results/processed/periodic_depth_reduction_audit.csv"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("figures"))
    parser.add_argument("--output-stem", default="fig10_periodic_depth_reduction_audit")
    args = parser.parse_args()
    for path in plot(read_rows(args.input), args.output_dir, args.output_stem):
        print(path)


if __name__ == "__main__":
    main()
