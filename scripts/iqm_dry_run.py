#!/usr/bin/env python3
"""Inspect an exported-ready circuit without connecting to IQM."""

import argparse
import json

import _bootstrap  # noqa: F401
from z2lgt.circuits import trotter_circuit
from z2lgt.gauss import localized_imbalance_bits
from z2lgt.iqm_interface import dry_run
from z2lgt.model import Z2Model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-sites", type=int, default=3)
    parser.add_argument("--time", type=float, default=0.2)
    parser.add_argument("--dt", type=float, default=0.1)
    args = parser.parse_args()
    model = Z2Model(args.n_sites)
    circuit = trotter_circuit(model, localized_imbalance_bits(model), args.time, args.dt, measure=True)
    print(json.dumps(dry_run(circuit), indent=2))


if __name__ == "__main__":
    main()

