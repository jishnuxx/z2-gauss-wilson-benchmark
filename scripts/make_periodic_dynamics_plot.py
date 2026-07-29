#!/usr/bin/env python3
"""Create the exact periodic-sector trajectory figure."""

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.periodic_plotting import (
    plot_periodic_sector_dynamics,
    read_periodic_dynamics_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=Path("results/processed/periodic_dynamics_ideal.csv"),
    )
    parser.add_argument("--outdir", type=Path, default=Path("figures"))
    args = parser.parse_args()
    rows = read_periodic_dynamics_csv(args.input)
    for path in plot_periodic_sector_dynamics(rows, args.outdir):
        print(path)


if __name__ == "__main__":
    main()
