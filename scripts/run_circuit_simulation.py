#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.circuits import export_circuit, resource_metrics, trotter_circuit
from z2lgt.gauss import localized_imbalance_bits
from z2lgt.model import Z2Model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-sites", type=int, default=3)
    parser.add_argument("--time", type=float, default=1.0)
    parser.add_argument("--dt", type=float, default=0.1)
    parser.add_argument("--output-stem", type=Path, default=Path("circuits/qasm/z2_circuit"))
    args = parser.parse_args()
    model = Z2Model(args.n_sites)
    circuit = trotter_circuit(model, localized_imbalance_bits(model), args.time, args.dt, measure=True)
    print(json.dumps({**resource_metrics(circuit), **export_circuit(circuit, args.output_stem)}, indent=2))


if __name__ == "__main__":
    main()

