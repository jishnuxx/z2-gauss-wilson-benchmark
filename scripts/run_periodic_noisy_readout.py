#!/usr/bin/env python3
"""Run and persist synthetic noisy periodic joint-readout results."""

import argparse
import csv
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.noise import NoiseConfig
from z2lgt.periodic_noisy_readout import run_periodic_noisy_readout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--time", type=float, default=0.8)
    parser.add_argument("--dt", type=float, default=0.4)
    parser.add_argument("--shots", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=35791)
    parser.add_argument("--single-qubit-error", type=float, default=0.001)
    parser.add_argument("--two-qubit-error", type=float, default=0.01)
    parser.add_argument("--readout-error", type=float, default=0.02)
    parser.add_argument("--outdir", type=Path, default=Path("results"))
    args = parser.parse_args()
    payload = run_periodic_noisy_readout(
        time=args.time,
        dt=args.dt,
        shots=args.shots,
        seed=args.seed,
        noise_config=NoiseConfig(
            args.single_qubit_error,
            args.two_qubit_error,
            args.readout_error,
        ),
    )

    json_path = args.outdir / "noisy/periodic_joint_readout.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    csv_path = args.outdir / "processed/periodic_noisy_joint_readout.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for record in payload["records"]:
        analysis = record["analysis"]
        rows.append(
            {
                "case": record["case"],
                "wilson_sector": record["wilson_sector"],
                "P_Gauss": analysis["P_Gauss"],
                "wilson_expectation": analysis["wilson_expectation"],
                "imbalance": analysis["imbalance"],
                "imbalance_se": analysis["imbalance_se"],
                "gauss_only_imbalance": analysis["gauss_only_imbalance"],
                "gauss_plus_wilson_imbalance": analysis[
                    "gauss_plus_wilson_imbalance"
                ],
                "gauss_only_acceptance": analysis["gauss_only_acceptance"],
                "gauss_plus_wilson_acceptance": analysis[
                    "gauss_plus_wilson_acceptance"
                ],
            }
        )
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("Periodic synthetic noisy joint readout")
    print(f"  noise config: {payload['noise_config']}")
    print(f"  shots per sector: {payload['shots']}")
    for record in payload["records"]:
        analysis = record["analysis"]
        print(
            f"  {record['case']}: P_Gauss={analysis['P_Gauss']:.6f}, "
            f"<W>={analysis['wilson_expectation']:.6f}, "
            f"O_raw={analysis['imbalance']:.6f}, "
            f"O_Gauss={analysis['gauss_only_imbalance']:.6f}, "
            f"O_Gauss+W={analysis['gauss_plus_wilson_imbalance']}, "
            f"joint_acceptance={analysis['gauss_plus_wilson_acceptance']:.6f}"
        )
    plus, minus = payload["records"]
    print(
        "  measured Wilson contrast: "
        f"{plus['analysis']['wilson_expectation'] - minus['analysis']['wilson_expectation']:.6f}"
    )
    print(f"  resources: {payload['records'][0]['resources']}")
    print(f"  JSON: {json_path}")
    print(f"  CSV: {csv_path}")


if __name__ == "__main__":
    main()
