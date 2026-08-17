#!/usr/bin/env python3
"""Run the offline periodic depth-reduction audit."""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.periodic_depth_reduction import (
    DEFAULT_DEPTH_SCAN,
    READOUT_MODES,
    depth_reduction_audit,
    write_depth_reduction_audit,
)


def parse_candidate(value: str) -> tuple[float, int]:
    try:
        time_text, steps_text = value.split(":", maxsplit=1)
        time = float(time_text)
        steps = int(steps_text)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(
            f"candidate must have form TIME:STEPS, got {value!r}"
        ) from exc
    if time <= 0 or steps <= 0:
        raise argparse.ArgumentTypeError("TIME and STEPS must be positive")
    return time, steps


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate",
        action="append",
        type=parse_candidate,
        metavar="TIME:STEPS",
        help="candidate to audit; repeat for multiple candidates",
    )
    parser.add_argument(
        "--mode",
        action="append",
        choices=READOUT_MODES,
        help="readout mode to include; repeat for multiple modes",
    )
    parser.add_argument("--min-trotter-separation", type=float, default=0.10)
    parser.add_argument("--min-fidelity", type=float, default=0.85)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("results/processed/periodic_depth_reduction_audit.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("results/processed/periodic_depth_reduction_audit.csv"),
    )
    args = parser.parse_args()

    report = depth_reduction_audit(
        args.candidate or DEFAULT_DEPTH_SCAN,
        modes=args.mode or READOUT_MODES,
        min_trotter_separation=args.min_trotter_separation,
        min_fidelity=args.min_fidelity,
    )
    json_path, csv_path = write_depth_reduction_audit(
        report,
        args.output_json,
        args.output_csv,
    )

    print("Periodic source-depth reduction audit")
    print(f"  rows: {len(report['rows'])}")
    print(f"  baseline: {report['baseline']}")
    print(f"  recommended: {report['recommended']}")
    print(f"  JSON: {json_path}")
    print(f"  CSV: {csv_path}")
    print("  IQM connected: false")
    print("  backend.run called: false")
    print("  hardware submitted: false")


if __name__ == "__main__":
    main()
