#!/usr/bin/env python3
"""Plot the exact single-fault mitigation comparison."""

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.periodic_mitigation_plotting import (
    plot_periodic_exact_mitigation,
    read_periodic_mitigation_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=Path("results/processed/periodic_exact_mitigation.csv"),
    )
    parser.add_argument("--outdir", type=Path, default=Path("figures"))
    args = parser.parse_args()
    rows = read_periodic_mitigation_csv(args.input)
    for path in plot_periodic_exact_mitigation(rows, args.outdir):
        print(path)


if __name__ == "__main__":
    main()
