#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.blindspot_workflow import run_dataset
from z2lgt.noise import NoiseConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the noisy four-link blind-spot benchmark")
    parser.add_argument("--shots", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=22345)
    parser.add_argument("--single-qubit-error", type=float, default=0.001)
    parser.add_argument("--two-qubit-error", type=float, default=0.01)
    parser.add_argument("--readout-error", type=float, default=0.02)
    parser.add_argument("--outdir", type=Path, default=Path("results"))
    args = parser.parse_args()
    config = NoiseConfig(args.single_qubit_error, args.two_qubit_error, args.readout_error)
    payload = run_dataset("noisy", shots=args.shots, seed=args.seed, output_dir=args.outdir, noise_config=config)
    print(json.dumps({"output": str(args.outdir / "noisy/blindspot_minimal.json"), "records": len(payload["records"]), "noise_config": payload["noise_config"]}, indent=2))


if __name__ == "__main__":
    main()
