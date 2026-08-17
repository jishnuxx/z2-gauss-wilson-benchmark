#!/usr/bin/env python3
"""Create the exact, Trotter-error, and Sirius-simulation figure suite."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import _bootstrap  # noqa: F401
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


PLUS_COLOR = "#1565C0"
MINUS_COLOR = "#D97706"
EXACT_COLOR = "#263238"
NOISY_COLOR = "#6A1B9A"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def value(row: dict[str, str], key: str) -> float:
    return float(row[key])


def by_case(rows: list[dict[str, str]], case: str) -> list[dict[str, str]]:
    return sorted(
        (row for row in rows if row["case"] == case),
        key=lambda row: value(row, "time"),
    )


def save(fig: plt.Figure, output_dir: Path, stem: str) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = [output_dir / f"{stem}.pdf", output_dir / f"{stem}.png"]
    fig.savefig(paths[0], bbox_inches="tight")
    fig.savefig(paths[1], dpi=240, bbox_inches="tight")
    plt.close(fig)
    return paths


def plot_exact(
    exact_rows: list[dict[str, str]],
    scan_rows: list[dict[str, str]],
    output_dir: Path,
) -> list[Path]:
    times = np.array([value(row, "time") for row in exact_rows])
    plus = np.array([value(row, "ideal_imbalance") for row in exact_rows])
    minus = np.array([value(row, "wrong_sector_imbalance") for row in exact_rows])
    plus_scan = by_case(scan_rows, "Wplus")
    minus_scan = by_case(scan_rows, "Wminus")

    fig, ax = plt.subplots(figsize=(7.4, 4.7))
    ax.plot(times, plus, color=PLUS_COLOR, linewidth=2.2, label=r"$W=+1$")
    ax.plot(times, minus, color=MINUS_COLOR, linewidth=2.2, label=r"$W=-1$")
    ax.scatter(
        [value(row, "time") for row in plus_scan],
        [value(row, "exact_O_LR") for row in plus_scan],
        color=PLUS_COLOR,
        edgecolor="white",
        linewidth=0.8,
        s=55,
        zorder=4,
    )
    ax.scatter(
        [value(row, "time") for row in minus_scan],
        [value(row, "exact_O_LR") for row in minus_scan],
        color=MINUS_COLOR,
        edgecolor="white",
        linewidth=0.8,
        s=55,
        zorder=4,
    )
    ax.axhline(0.0, color="0.45", linewidth=0.8)
    ax.axvspan(0.6, 1.0, color="0.5", alpha=0.07, label="benchmark window")
    ax.set(
        xlabel=r"evolution time $t$",
        ylabel=r"exact $O_{\rm LR}$",
        title=r"Exact sector-resolved matter dynamics",
        xlim=(times.min(), times.max()),
    )
    ax.grid(alpha=0.2)
    ax.legend(frameon=False, ncol=3, loc="lower left")
    fig.tight_layout()
    return save(fig, output_dir, "fig12_periodic_exact_sector_dynamics")


def plot_trotter_error(
    scan_rows: list[dict[str, str]],
    output_dir: Path,
) -> list[Path]:
    plus = by_case(scan_rows, "Wplus")
    minus = by_case(scan_rows, "Wminus")
    times = np.array([value(row, "time") for row in plus])

    fig, (ax_top, ax_error) = plt.subplots(
        2,
        1,
        figsize=(7.4, 6.3),
        sharex=True,
        gridspec_kw={"height_ratios": [2.15, 1.0], "hspace": 0.08},
    )

    for rows, color, sector in (
        (plus, PLUS_COLOR, r"$W=+1$"),
        (minus, MINUS_COLOR, r"$W=-1$"),
    ):
        exact = np.array([value(row, "exact_O_LR") for row in rows])
        trotter = np.array([value(row, "trotter_O_LR") for row in rows])
        ax_top.plot(
            times,
            exact,
            color=color,
            marker="o",
            linewidth=2.0,
            label=f"{sector} exact",
        )
        ax_top.plot(
            times,
            trotter,
            color=color,
            marker="s",
            linestyle="--",
            linewidth=1.8,
            label=f"{sector} two-step Trotter",
        )
        for time, exact_value, trotter_value in zip(times, exact, trotter, strict=True):
            ax_top.plot(
                [time, time],
                [exact_value, trotter_value],
                color=color,
                alpha=0.38,
                linewidth=1.2,
            )
        ax_error.plot(
            times,
            np.abs(trotter - exact),
            color=color,
            marker="o",
            linewidth=2.0,
            label=sector,
        )

    ax_top.axhline(0.0, color="0.45", linewidth=0.8)
    ax_top.set(
        ylabel=r"$O_{\rm LR}$",
        title=r"Exact versus fixed-depth, two-step Trotter dynamics",
    )
    ax_top.grid(alpha=0.2)
    ax_top.legend(frameon=False, ncol=2, fontsize=9)
    ax_error.set(
        xlabel=r"evolution time $t$",
        ylabel=r"$|O_{\rm LR}^{\rm Trotter}-O_{\rm LR}^{\rm exact}|$",
        xticks=times,
    )
    ax_error.grid(alpha=0.2)
    ax_error.legend(frameon=False, ncol=2)
    fig.text(
        0.5,
        0.005,
        r"Each point uses two Trotter steps, so $\Delta t=t/2$; this is a fixed-depth benchmark, not a uniform-$\Delta t$ trajectory.",
        ha="center",
        va="bottom",
        fontsize=9.5,
        color="0.35",
    )
    fig.subplots_adjust(bottom=0.13)
    return save(fig, output_dir, "fig13_periodic_trotter_error_fixed_depth")


def plot_sirius_simulation(
    scan_rows: list[dict[str, str]],
    output_dir: Path,
) -> list[Path]:
    plus = by_case(scan_rows, "Wplus")
    minus = by_case(scan_rows, "Wminus")
    times = np.array([value(row, "time") for row in plus])

    fig, (ax_obs, ax_sep) = plt.subplots(
        2,
        1,
        figsize=(7.4, 6.4),
        sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1.0], "hspace": 0.08},
    )

    for rows, color, sector in (
        (plus, PLUS_COLOR, r"$W=+1$"),
        (minus, MINUS_COLOR, r"$W=-1$"),
    ):
        trotter = np.array([value(row, "trotter_O_LR") for row in rows])
        noisy = np.array([value(row, "noisy_O_LR") for row in rows])
        error = np.array([value(row, "noisy_O_LR_se") for row in rows])
        ax_obs.plot(
            times,
            trotter,
            color=color,
            marker="s",
            linestyle="--",
            linewidth=1.8,
            label=f"{sector} Trotter target",
        )
        ax_obs.errorbar(
            times,
            noisy,
            yerr=error,
            color=color,
            marker="o",
            linestyle="-",
            linewidth=2.0,
            capsize=3,
            label=f"{sector} noisy simulation",
        )

    plus_trotter = np.array([value(row, "trotter_O_LR") for row in plus])
    minus_trotter = np.array([value(row, "trotter_O_LR") for row in minus])
    plus_noisy = np.array([value(row, "noisy_O_LR") for row in plus])
    minus_noisy = np.array([value(row, "noisy_O_LR") for row in minus])
    separation_error = np.sqrt(
        np.array([value(row, "noisy_O_LR_se") for row in plus]) ** 2
        + np.array([value(row, "noisy_O_LR_se") for row in minus]) ** 2
    )
    ax_sep.plot(
        times,
        plus_trotter - minus_trotter,
        color=EXACT_COLOR,
        marker="s",
        linestyle="--",
        linewidth=1.8,
        label="Trotter separation",
    )
    ax_sep.errorbar(
        times,
        plus_noisy - minus_noisy,
        yerr=separation_error,
        color=NOISY_COLOR,
        marker="o",
        linewidth=2.0,
        capsize=3,
        label="noisy-simulation separation",
    )

    ax_obs.axhline(0.0, color="0.45", linewidth=0.8)
    ax_obs.set(
        ylabel=r"$O_{\rm LR}$",
        title="Sirius calibration-informed simulation — not hardware data",
    )
    ax_obs.grid(alpha=0.2)
    ax_obs.legend(frameon=False, ncol=2, fontsize=9)
    ax_sep.axhline(0.0, color="0.45", linewidth=0.8)
    ax_sep.set(
        xlabel=r"evolution time $t$",
        ylabel=r"$\Delta O_{\rm LR}$",
        xticks=times,
    )
    ax_sep.grid(alpha=0.2)
    ax_sep.legend(frameon=False, fontsize=9)
    fig.text(
        0.5,
        0.01,
        "Independent depolarizing PRX/CZ/MOVE channels and symmetric readout errors; 5000 simulated shots per circuit.",
        ha="center",
        va="bottom",
        fontsize=9.3,
        color="0.35",
    )
    fig.subplots_adjust(bottom=0.13)
    return save(fig, output_dir, "fig14_sirius_calibration_informed_benchmark")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exact-input",
        type=Path,
        default=Path("results/processed/periodic_dynamics_ideal.csv"),
    )
    parser.add_argument(
        "--scan-input",
        type=Path,
        default=Path(
            "results/processed/sirius_periodic_matter_noise_scan_5000.csv"
        ),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("figures"))
    args = parser.parse_args()

    exact_rows = read_rows(args.exact_input)
    scan_rows = read_rows(args.scan_input)
    if not exact_rows or not scan_rows:
        raise SystemExit("figure inputs must be nonempty")

    paths = []
    paths.extend(plot_exact(exact_rows, scan_rows, args.output_dir))
    paths.extend(plot_trotter_error(scan_rows, args.output_dir))
    paths.extend(plot_sirius_simulation(scan_rows, args.output_dir))
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
