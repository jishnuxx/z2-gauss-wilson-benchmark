#!/usr/bin/env python3
"""One-command simulator-only reproduction of the open-chain result package."""

import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.workflow import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-sites", type=int, default=3)
    parser.add_argument("--tmax", type=float, default=1.0)
    parser.add_argument("--dt", type=float, default=0.1)
    parser.add_argument("--shots", type=int, default=5000)
    parser.add_argument("--noise-level", type=float, default=0.005)
    parser.add_argument("--bootstrap", type=int, default=300)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--outdir", type=Path, default=Path("results/open_chain_minimal"))
    args = parser.parse_args()
    summary = run_pipeline(**vars(args))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
