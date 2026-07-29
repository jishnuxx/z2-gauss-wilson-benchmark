#!/usr/bin/env python3
"""Verify the algebra of the periodic observable-aware benchmark."""

import json
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.periodic_model import PeriodicZ2Model, periodic_algebra_report


def main() -> None:
    model = PeriodicZ2Model()
    report = periodic_algebra_report(model)

    print("Periodic four-site Z2 matter ring")
    print("Qubit order: matter q0..q3, links q4..q7")
    print("Electric-link term: omitted (coefficient fixed to zero)")
    print("\nLocal Gauss checks:")
    for check in model.gauss_checks:
        print(f"  {check.name} = {check.qiskit_label}")
    print(f"Conserved Wilson loop: W = {model.wilson.qiskit_label}")

    print("\nHamiltonian conservation checks:")
    for name, norm in report["hamiltonian_gauss_commutator_norms"].items():
        print(f"  ||[H,{name}]|| = {norm:.3e}")
    print(
        "  ||[H,W]|| = "
        f"{report['hamiltonian_wilson_commutator_norm']:.3e}"
    )

    print("\nError algebra:")
    for name, error in report["errors"].items():
        relations = ", ".join(
            f"{check}:{relation}"
            for check, relation in error["gauss_relations"].items()
        )
        suffix = (
            f"; W:{error['wilson_relation']}"
            if "wilson_relation" in error
            else ""
        )
        print(f"  {name} ({error['operator']}): {relations}{suffix}")

    print("\nVerified claims:")
    for claim, passed in report["claims_verified"].items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {claim}")

    output = Path("results/processed/periodic_algebra_report.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"\nMachine-readable report: {output}")
    if not all(report["claims_verified"].values()):
        raise SystemExit("periodic algebra verification failed")


if __name__ == "__main__":
    main()
