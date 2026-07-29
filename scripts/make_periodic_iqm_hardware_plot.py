#!/usr/bin/env python3
"""Plot the periodic IQM hardware readout separately from simulations."""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.periodic_iqm_hardware_plotting import (  # noqa: E402
    plot_periodic_iqm_hardware_readout,
    read_periodic_iqm_hardware_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("results/processed/periodic_iqm_joint_readout.csv"),
    )
    parser.add_argument("--outdir", type=Path, default=Path("figures"))
    parser.add_argument("--job-id", default=None)
    parser.add_argument(
        "--output-stem",
        default="fig08_periodic_iqm_hardware_readout",
        help="base filename without extension",
    )
    parser.add_argument(
        "--title",
        default="IQM Emerald periodic readout: hardware data only",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_periodic_iqm_hardware_csv(args.input)
    for path in plot_periodic_iqm_hardware_readout(
        rows,
        args.outdir,
        job_id=args.job_id,
        output_stem=args.output_stem,
        title=args.title,
    ):
        print(path)


if __name__ == "__main__":
    main()
