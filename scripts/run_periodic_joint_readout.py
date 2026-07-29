#!/usr/bin/env python3
"""Validate the 12-qubit joint periodic readout with ideal shots."""

import argparse
import csv
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.circuits import compiled_circuit, export_circuit, ideal_counts, resource_metrics
from z2lgt.periodic_readout import (
    analyze_periodic_joint_counts,
    periodic_joint_readout_circuit,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--time", type=float, default=0.8)
    parser.add_argument("--dt", type=float, default=0.4)
    parser.add_argument("--shots", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=24680)
    parser.add_argument("--outdir", type=Path, default=Path("results"))
    args = parser.parse_args()
    if args.shots <= 0:
        raise SystemExit("shots must be positive")

    records = []
    exports = {}
    for offset, (sector, label) in enumerate(((1, "Wplus"), (-1, "Wminus"))):
        circuit = periodic_joint_readout_circuit(
            args.time,
            args.dt,
            wilson_sector=sector,
        )
        counts = ideal_counts(circuit, args.shots, args.seed + offset)
        analysis = analyze_periodic_joint_counts(counts)
        resources = resource_metrics(circuit)
        records.append(
            {
                "case": label,
                "wilson_sector": sector,
                "time": args.time,
                "dt": args.dt,
                "backend": "AerSimulator-ideal",
                "raw_counts": counts,
                "analysis": analysis,
                "resources": resources,
            }
        )
        compiled = compiled_circuit(circuit)
        stem = f"periodic_joint_{label}_t{args.time:g}_dt{args.dt:g}".replace(
            ".", "p"
        )
        exports[label] = export_circuit(
            compiled,
            Path("circuits/periodic/qasm") / stem,
            qpy_stem=Path("circuits/periodic/qiskit") / stem,
        )

    payload = {
        "schema_version": 1,
        "description": "ideal joint matter/Gauss/Wilson readout",
        "shots": args.shots,
        "records": records,
        "exports": exports,
    }
    json_path = args.outdir / "ideal/periodic_joint_readout.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    csv_path = args.outdir / "processed/periodic_joint_readout.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "case": record["case"],
            "wilson_sector": record["wilson_sector"],
            "P_Gauss": record["analysis"]["P_Gauss"],
            "wilson_expectation": record["analysis"]["wilson_expectation"],
            "imbalance": record["analysis"]["imbalance"],
            "imbalance_se": record["analysis"]["imbalance_se"],
            "gauss_only_acceptance": record["analysis"]["gauss_only_acceptance"],
            "gauss_plus_wilson_acceptance": record["analysis"][
                "gauss_plus_wilson_acceptance"
            ],
        }
        for record in records
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("Periodic ideal joint readout")
    print(f"  shots per sector: {args.shots}")
    for record in records:
        analysis = record["analysis"]
        print(
            f"  {record['case']}: P_Gauss={analysis['P_Gauss']:.6f}, "
            f"<W>={analysis['wilson_expectation']:.6f}, "
            f"O_LR={analysis['imbalance']:.6f} +/- "
            f"{analysis['imbalance_se']:.6f}, "
            f"joint_acceptance={analysis['gauss_plus_wilson_acceptance']:.6f}"
        )
    print(f"  resources: {records[0]['resources']}")
    print(f"  JSON: {json_path}")
    print(f"  CSV: {csv_path}")
    print(f"  circuits: {exports}")


if __name__ == "__main__":
    main()
