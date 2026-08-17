#!/usr/bin/env python3
"""Plot raw versus readout-mitigated IQM hardware diagnostics."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import _bootstrap  # noqa: F401
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


MITIGATED_METHOD = "readout_mitigated_manifest_symmetric"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def select(rows: list[dict[str, str]], dataset: str, method: str) -> list[dict[str, str]]:
    return [row for row in rows if row["dataset"] == dataset and row["method"] == method]


def as_float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    return float("nan") if value == "" else float(value)


def plot(rows: list[dict[str, str]], output_dir: Path, output_stem: str) -> list[Path]:
    static_raw = select(rows, "static_blindspot", "raw")
    static_mitigated = select(rows, "static_blindspot", MITIGATED_METHOD)
    periodic_raw = select(rows, "periodic_readout", "raw")
    periodic_mitigated = select(rows, "periodic_readout", MITIGATED_METHOD)
    if not (static_raw and static_mitigated and periodic_raw and periodic_mitigated):
        raise ValueError("input CSV is missing raw or mitigated rows")

    static_cases = [row["case"] for row in static_raw]
    periodic_cases = [row["case"] for row in periodic_raw]
    x_static = np.arange(len(static_cases), dtype=float)
    x_periodic = np.arange(len(periodic_cases), dtype=float)
    width = 0.34

    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.labelsize": 12,
            "legend.fontsize": 10,
        }
    )
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.0))
    ax_pg, ax_w, ax_pw, ax_imb = axes.ravel()

    raw_pg = np.asarray([as_float(row, "P_Gauss") for row in static_raw])
    mit_pg = np.asarray([as_float(row, "P_Gauss") for row in static_mitigated])
    ideal_pg = np.asarray([as_float(row, "expected_P_Gauss") for row in static_raw])
    ax_pg.bar(x_static - width / 2, raw_pg, width, label="raw", color="#9E9E9E")
    ax_pg.bar(x_static + width / 2, mit_pg, width, label="readout mitigated", color="#2E7D32")
    ax_pg.plot(x_static, ideal_pg, "k_", markersize=16, label="ideal target")
    ax_pg.set(
        xticks=x_static,
        xticklabels=[case.replace("_", "\n") for case in static_cases],
        ylim=(-0.05, 1.08),
        ylabel=r"$P_{\rm Gauss}$",
        title="Static Emerald: local-sector probability",
    )
    ax_pg.grid(axis="y", alpha=0.22)
    ax_pg.legend(frameon=False, loc="lower right")

    raw_w = np.asarray([as_float(row, "wilson_expectation") for row in static_raw])
    mit_w = np.asarray([as_float(row, "wilson_expectation") for row in static_mitigated])
    ideal_w = np.asarray([as_float(row, "expected_wilson_expectation") for row in static_raw])
    ax_w.bar(x_static - width / 2, raw_w, width, color="#9E9E9E")
    ax_w.bar(x_static + width / 2, mit_w, width, color="#2E7D32")
    ax_w.plot(x_static, ideal_w, "k_", markersize=16)
    ax_w.axhline(0.0, color="0.25", linewidth=0.9)
    ax_w.set(
        xticks=x_static,
        xticklabels=[case.replace("_", "\n") for case in static_cases],
        ylim=(-1.08, 1.08),
        ylabel=r"$\langle W\rangle$",
        title="Static Emerald: Wilson sector",
    )
    ax_w.grid(axis="y", alpha=0.22)

    raw_pw = np.asarray([as_float(row, "P_Gauss") for row in periodic_raw])
    mit_pw = np.asarray([as_float(row, "P_Gauss") for row in periodic_mitigated])
    ax_pw.bar(x_periodic - width / 2, raw_pw, width, color="#9E9E9E")
    ax_pw.bar(x_periodic + width / 2, mit_pw, width, color="#1565C0")
    ax_pw.set(
        xticks=x_periodic,
        xticklabels=periodic_cases,
        ylim=(0.0, max(0.42, float(np.max(mit_pw)) + 0.05)),
        ylabel=r"$P_{\rm Gauss}$",
        title="Periodic Emerald: readout correction is modest",
    )
    ax_pw.grid(axis="y", alpha=0.22)

    raw_imb = np.asarray([as_float(row, "imbalance") for row in periodic_raw])
    mit_imb = np.asarray([as_float(row, "imbalance") for row in periodic_mitigated])
    ax_imb.bar(x_periodic - width / 2, raw_imb, width, color="#9E9E9E", label="raw")
    ax_imb.bar(x_periodic + width / 2, mit_imb, width, color="#1565C0", label="readout mitigated")
    ax_imb.axhline(0.0, color="0.25", linewidth=0.9)
    ax_imb.set(
        xticks=x_periodic,
        xticklabels=periodic_cases,
        ylim=(min(-0.04, float(np.nanmin(mit_imb)) - 0.03), max(0.16, float(np.nanmax(mit_imb)) + 0.04)),
        ylabel=r"raw $O_{\rm LR}$",
        title="Periodic Emerald: dynamics still gate-noise limited",
    )
    ax_imb.grid(axis="y", alpha=0.22)
    ax_imb.legend(frameon=False, loc="upper right")

    fig.suptitle(
        "IQM Emerald readout-assignment mitigation from archived calibration metadata",
        fontsize=15,
        y=0.99,
    )
    fig.text(
        0.5,
        0.01,
        "Mitigation uses manifest readout errors only; it is not a gate-error or leakage correction.",
        ha="center",
        va="bottom",
        fontsize=10,
        color="0.35",
    )
    fig.tight_layout(rect=(0, 0.035, 1, 0.965))
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
    parser.add_argument("--input", type=Path, default=Path("results/processed/iqm_readout_mitigation.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("figures"))
    parser.add_argument("--output-stem", default="fig09_iqm_readout_mitigation")
    args = parser.parse_args()

    paths = plot(read_rows(args.input), args.output_dir, args.output_stem)
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
