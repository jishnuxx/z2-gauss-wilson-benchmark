#!/usr/bin/env python3
"""Audit all single-qubit Pauli errors at multiple injection times."""

import argparse
from pathlib import Path

import numpy as np

import _bootstrap  # noqa: F401
from z2lgt.periodic_error_timing import (
    timed_single_qubit_error_sweep,
    write_periodic_error_timing_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tmax", type=float, default=2.0)
    parser.add_argument("--steps", type=int, default=17)
    parser.add_argument("--injection-steps", type=int, default=8)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/processed/periodic_error_timing_sweep.csv"),
    )
    args = parser.parse_args()
    if args.tmax <= 0 or args.steps < 2 or args.injection_steps < 1:
        raise SystemExit("require tmax > 0, steps >= 2, and injection-steps >= 1")

    observation = np.linspace(0.0, args.tmax, args.steps)
    injection = np.linspace(
        0.0,
        args.tmax,
        args.injection_steps,
        endpoint=False,
    )
    rows = timed_single_qubit_error_sweep(observation, injection)
    output = write_periodic_error_timing_csv(rows, args.output)
    invisible = [
        row
        for row in rows
        if row["diagnostic_class"] == "undetected_by_gauss_and_wilson"
    ]
    worst_invisible = max(
        invisible,
        key=lambda row: row["max_abs_imbalance_error_after_injection"],
    )
    t0_invisible = [row for row in invisible if row["injection_time"] == 0.0]
    worst_t0 = max(
        row["max_abs_imbalance_error_after_injection"] for row in t0_invisible
    )
    harmful = [
        row
        for row in rows
        if row["max_abs_imbalance_error_after_injection"] > 1e-10
    ]
    harmful_detected = [
        row
        for row in harmful
        if row["gauss_detected"] or row["wilson_flipped"]
    ]

    print("Periodic mid-evolution error-timing sweep")
    print(f"  injection times: {len(injection)}")
    print(f"  Pauli errors per injection: 24")
    print(f"  error-time cases audited: {len(rows)}")
    print(f"  worst invisible error at t=0: {worst_t0:.6f}")
    print(
        "  worst invisible mid-evolution error: "
        f"{worst_invisible['pauli']}_{worst_invisible['subsystem'][0]}"
        f"{worst_invisible['local_index']} injected at "
        f"t={worst_invisible['injection_time']:.6f} -> "
        f"max |Delta O_LR|="
        f"{worst_invisible['max_abs_imbalance_error_after_injection']:.6f}"
    )
    print(
        "  harmful cases detected by Gauss or Wilson: "
        f"{len(harmful_detected)}/{len(harmful)}"
    )
    print(f"  output: {output}")


if __name__ == "__main__":
    main()
