"""Open-chain plotting helpers using only persisted analysis records."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _prepare(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def observable_timeseries(records: list[dict], path: Path, observable: str) -> None:
    _prepare(path)
    times = np.array([record["time"] for record in records])
    values = [record["analysis"][observable] for record in records]
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    ax.plot(times, [value["exact"] for value in values], "k-", label="exact ED")
    ax.errorbar(
        times,
        [value["raw"] for value in values],
        yerr=[value["raw_bootstrap_se"] for value in values],
        marker="o",
        label="noisy raw",
    )
    ax.errorbar(
        times,
        [value["postselected"] for value in values],
        yerr=[value["postselected_bootstrap_se"] for value in values],
        marker="s",
        label="Gauss post-selected",
    )
    ax.set(xlabel="time", ylabel=observable.replace("_", " "))
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def delta_timeseries(records: list[dict], path: Path, observable: str) -> None:
    _prepare(path)
    times = [record["time"] for record in records]
    values = [record["analysis"][observable] for record in records]
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    ax.plot(times, [value["delta_raw"] for value in values], "o-", label="raw")
    ax.plot(
        times,
        [value["delta_postselected"] for value in values],
        "s-",
        label="Gauss post-selected",
    )
    ax.set(xlabel="time", ylabel=r"$\Delta O(t)=|O_{sampled}-O_{ED}|$")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def acceptance_timeseries(records: list[dict], path: Path) -> None:
    _prepare(path)
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    ax.plot(
        [record["time"] for record in records],
        [record["analysis"]["acceptance"] for record in records],
        "o-",
    )
    ax.set(xlabel="time", ylabel="post-selection acceptance", ylim=(0, 1.02))
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def violation_histogram_plot(records: list[dict], path: Path) -> None:
    _prepare(path)
    histogram: Counter[int] = Counter()
    for record in records:
        for pattern, count in record["analysis"]["violation_histogram"].items():
            histogram[pattern.count("1")] += count
    keys = sorted(histogram)
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    ax.bar(keys, [histogram[key] for key in keys])
    ax.set(xlabel="number of violated Gauss constraints", ylabel="counts (all times)")
    ax.set_xticks(keys)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def make_openchain_plots(records: list[dict], plot_dir: Path) -> list[Path]:
    observable = "right_occupation"
    paths = [
        plot_dir / "main_deltaO_raw_vs_postselected.pdf",
        plot_dir / "observable_timeseries.pdf",
        plot_dir / "gauss_violation_histogram.pdf",
        plot_dir / "postselection_acceptance.pdf",
    ]
    delta_timeseries(records, paths[0], observable)
    observable_timeseries(records, paths[1], observable)
    violation_histogram_plot(records, paths[2])
    acceptance_timeseries(records, paths[3])
    return paths
