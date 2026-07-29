#!/usr/bin/env python3
"""Run at least two simulator noise levels through the full analysis path."""

import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.workflow import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--noise-levels", type=float, nargs="+", default=[0.0025, 0.005])
    parser.add_argument("--n-sites", type=int, default=3)
    parser.add_argument("--tmax", type=float, default=1.0)
    parser.add_argument("--dt", type=float, default=0.1)
    parser.add_argument("--shots", type=int, default=5000)
    parser.add_argument("--outdir", type=Path, default=Path("results/noise_scan"))
    args = parser.parse_args()
    if len(args.noise_levels) < 2:
        parser.error("provide at least two --noise-levels")
    summaries = []
    for level in args.noise_levels:
        summaries.append(run_pipeline(
            n_sites=args.n_sites, tmax=args.tmax, dt=args.dt, shots=args.shots,
            noise_level=level, outdir=args.outdir / f"noise_{level:g}"
        ))
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()

