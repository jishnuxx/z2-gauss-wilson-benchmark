#!/usr/bin/env python3
"""One-command, simulator-only reproduction of the benchmark figures."""

import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.blindspot_plotting import make_blindspot_plots
from z2lgt.blindspot_workflow import combine_results, export_minimal_circuits, run_dataset
from z2lgt.noise import NoiseConfig


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--outdir", type=Path, default=Path("results"))
    args = parser.parse_args()
    run_dataset("ideal", shots=args.shots, seed=args.seed, output_dir=args.outdir)
    run_dataset(
        "noisy",
        shots=args.shots,
        seed=args.seed + 10_000,
        output_dir=args.outdir,
        noise_config=NoiseConfig(single_qubit=0.001, two_qubit=0.01, readout=0.02),
    )
    export_minimal_circuits()
    summary = combine_results(
        args.outdir / "ideal/blindspot_minimal.json",
        args.outdir / "noisy/blindspot_minimal.json",
        args.outdir / "processed",
        args.outdir / "iqm/blindspot_minimal.json",
    )
    paths = make_blindspot_plots(summary, Path("figures"))
    print(json.dumps({"summary": str(args.outdir / "processed/blindspot_summary.json"), "figures": [str(path) for path in paths]}, indent=2))


if __name__ == "__main__":
    main()
