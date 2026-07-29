#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.analysis import analyze_counts
from z2lgt.bitstrings import canonical_counts, load_counts
from z2lgt.model import Z2Model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("counts", type=Path)
    parser.add_argument("exact", type=Path, help="JSON object containing exact observable values")
    parser.add_argument("--n-sites", type=int, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/processed/analysis.json"))
    args = parser.parse_args()
    raw, metadata = load_counts(args.counts)
    model = Z2Model(args.n_sites)
    exact = json.loads(args.exact.read_text(encoding="utf-8"))
    result = analyze_counts(canonical_counts(raw, model.n_qubits), model, exact)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"metadata": metadata, "analysis": result}, indent=2), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()

