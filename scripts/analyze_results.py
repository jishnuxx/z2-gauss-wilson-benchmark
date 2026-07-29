#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.blindspot_workflow import combine_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Combine persisted ideal/noisy/IQM results")
    parser.add_argument("--ideal", type=Path, default=Path("results/ideal/blindspot_minimal.json"))
    parser.add_argument("--noisy", type=Path, default=Path("results/noisy/blindspot_minimal.json"))
    parser.add_argument("--iqm", type=Path, default=Path("results/iqm/blindspot_minimal.json"))
    parser.add_argument("--outdir", type=Path, default=Path("results/processed"))
    args = parser.parse_args()
    summary = combine_results(args.ideal, args.noisy, args.outdir, args.iqm)
    print(json.dumps({"output": str(args.outdir / "blindspot_summary.json"), "rows": summary["diagnostic_table"]}, indent=2))


if __name__ == "__main__":
    main()
