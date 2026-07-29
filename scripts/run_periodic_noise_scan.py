#!/usr/bin/env python3
"""Run and persist a scaled synthetic-noise scan."""

import argparse
import csv
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.periodic_noise_scan import run_periodic_noise_scale_scan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=46100)
    parser.add_argument("--outdir", type=Path, default=Path("results"))
    args = parser.parse_args()
    payload = run_periodic_noise_scale_scan(shots=args.shots, seed=args.seed)

    json_path = args.outdir / "noisy/periodic_noise_scan.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    csv_path = args.outdir / "processed/periodic_noise_scan.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rows = payload["summary_rows"]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("Periodic synthetic noise-strength scan")
    print(f"  baseline config: {payload['baseline_noise_config']}")
    print(f"  shots per sector per scale: {payload['shots_per_sector_per_scale']}")
    plus_rows = [row for row in rows if row["case"] == "Wplus"]
    print(
        "  scale | target joint accept | wrong false accept | "
        "Wilson contrast | target raw O error"
    )
    for row in plus_rows:
        print(
            f"  {row['noise_scale']:5.2f} | "
            f"{row['target_joint_acceptance']:19.6f} | "
            f"{row['wrong_sector_false_acceptance']:18.6f} | "
            f"{row['wilson_contrast']:15.6f} | "
            f"{row['imbalance_abs_error_vs_trotter']:.6f}"
        )
    print(f"  JSON: {json_path}")
    print(f"  CSV: {csv_path}")


if __name__ == "__main__":
    main()
