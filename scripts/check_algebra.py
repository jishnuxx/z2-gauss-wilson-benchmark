#!/usr/bin/env python3
"""Print and persist the exact Pauli algebra behind the blind-spot claim."""

import json
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.blindspot_model import BlindSpotModel, algebra_report


def main() -> None:
    model = BlindSpotModel()
    report = algebra_report(model)
    print("Local Gauss checks (Qiskit big-endian labels):")
    for check in model.gauss_checks:
        print(f"  {check.name} = {check.qiskit_label}")
    print(f"Wilson loop: W = {model.wilson.qiskit_label}")
    print("\nError algebra:")
    for name, error in report["errors"].items():
        relations = ", ".join(
            f"{check}:{values['relation']}"
            for check, values in error["gauss_relations"].items()
        )
        print(f"  {name} ({error['operator']}): {relations}; W:{error['wilson_relation']}")
        print(f"    post-error expectations: {error['expectations_after_error']}")
    print("\nVerified claims:")
    for claim, passed in report["claims_verified"].items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {claim}")

    print("\nSummary:")
    print("Case                     | Gauss checks | String/Wilson sector | Interpretation")
    print("-------------------------+--------------+-----------------------+------------------------------")
    print("No error                 | PASS         | target (+1)           | target physical state")
    print("Gauge-violating error    | FAIL         | unchanged (+1)        | detected locally")
    print("Gauge-preserving string  | PASS         | changed (-1)          | Gauss-only blind spot")
    output = Path("results/processed/algebra_report.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nMachine-readable report: {output}")
    if not all(report["claims_verified"].values()):
        raise SystemExit("algebra verification failed")


if __name__ == "__main__":
    main()
