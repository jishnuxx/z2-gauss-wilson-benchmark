#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
import numpy as np
from z2lgt.ed import benchmark
from z2lgt.gauss import commutator_norms, localized_imbalance_bits
from z2lgt.model import Z2Model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-sites", type=int, default=3)
    parser.add_argument("--tmax", type=float, default=1.0)
    parser.add_argument("--dt", type=float, default=0.1)
    parser.add_argument("--output", type=Path, default=Path("data/exact/ed_observables.json"))
    args = parser.parse_args()
    model = Z2Model(args.n_sites)
    rows = benchmark(model, localized_imbalance_bits(model), np.arange(0, args.tmax + args.dt / 2, args.dt))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "commutator_norms": commutator_norms(model)}, indent=2))


if __name__ == "__main__":
    main()

