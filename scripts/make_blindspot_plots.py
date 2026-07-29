#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.blindspot_plotting import make_blindspot_plots


def main() -> None:
    parser = argparse.ArgumentParser(description="Create blind-spot figures from processed JSON")
    parser.add_argument("summary", nargs="?", type=Path, default=Path("results/processed/blindspot_summary.json"))
    parser.add_argument("--outdir", type=Path, default=Path("figures"))
    args = parser.parse_args()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    print("\n".join(str(path) for path in make_blindspot_plots(summary, args.outdir)))


if __name__ == "__main__":
    main()
