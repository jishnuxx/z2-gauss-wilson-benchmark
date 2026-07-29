#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.plotting import make_openchain_plots


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis", type=Path)
    parser.add_argument("--plot-dir", type=Path, default=Path("plots/open_chain"))
    args = parser.parse_args()
    records = json.loads(args.analysis.read_text(encoding="utf-8"))
    print("\n".join(map(str, make_openchain_plots(records, args.plot_dir))))


if __name__ == "__main__":
    main()
