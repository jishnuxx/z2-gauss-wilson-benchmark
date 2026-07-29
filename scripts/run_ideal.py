#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.blindspot_workflow import export_minimal_circuits, run_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ideal four-link blind-spot benchmark")
    parser.add_argument("--shots", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--outdir", type=Path, default=Path("results"))
    args = parser.parse_args()
    payload = run_dataset("ideal", shots=args.shots, seed=args.seed, output_dir=args.outdir)
    circuits = export_minimal_circuits()
    print(json.dumps({
        "output": str(args.outdir / "ideal/blindspot_minimal.json"),
        "processed_csv": str(args.outdir / "processed/blindspot_ideal.csv"),
        "records": len(payload["records"]),
        "circuits": circuits,
    }, indent=2))


if __name__ == "__main__":
    main()
