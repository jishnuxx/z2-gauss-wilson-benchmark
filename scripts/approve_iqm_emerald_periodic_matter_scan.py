#!/usr/bin/env python3
"""Interactively approve the frozen six-circuit Emerald scan."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import _bootstrap

from z2lgt.emerald_periodic_matter_iqm_runner import (
    validate_emerald_scan_submission_manifest,
)
from z2lgt.iqm_candidate import load_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest",
        nargs="?",
        type=Path,
        default=Path(
            "results/iqm/emerald_periodic_matter_scan_candidate_5000/"
            "readiness_manifest.json"
        ),
    )
    parser.add_argument("--replicate-label")
    args = parser.parse_args()
    path = args.manifest.resolve()
    manifest = load_manifest(path)
    if manifest.get("hardware_submitted") is True:
        raise SystemExit("cannot approve: candidate is already marked as submitted")

    review_copy = dict(manifest)
    review_copy["human_review_approved"] = True
    validate_emerald_scan_submission_manifest(
        review_copy,
        root=_bootstrap.ROOT,
        expected_quantum_computer="emerald",
        expected_shots=int(manifest["shots"]),
        expected_replicate_label=args.replicate_label,
    )

    print(f"Candidate: {manifest['candidate_id']}")
    print(f"Target: {manifest['quantum_computer']}")
    print(f"Calibration: {manifest['calibration_set_id']}")
    print(f"Shots per circuit: {manifest['shots']}")
    print(f"Replicate: {manifest.get('replicate_label', 'primary')}")
    print("Fixed mapping:", manifest["fixed_initial_layout_components"])
    for physics in manifest["physics_metrics_by_point"]:
        print(
            f"  physics t={physics['time']:g} dt={physics['dt']:g}: "
            f"Trotter separation={physics['trotter_sector_separation']:.6f} "
            f"fidelity={physics['minimum_state_fidelity']:.6f}"
        )
    for record in manifest["circuits"]:
        print(
            f"  t={record['time']:g} dt={record['dt']:g} {record['case']}: "
            f"depth={record['depth']} R={record['r_count']} "
            f"CZ={record['cz_count']} MOVE={record['move_count']}"
        )
    print(
        "Maximum calibrated errors: "
        f"R={manifest['maximum_r_error']:.6f} "
        f"CZ={manifest['maximum_cz_error']:.6f} "
        f"readout={manifest['maximum_readout_error']:.6f}"
    )

    phrase = f"APPROVE {manifest['candidate_id'][:12]}"
    entered = input(f"Type {phrase!r} to approve this exact candidate: ")
    if entered != phrase:
        raise SystemExit("approval phrase did not match; manifest was not changed")
    manifest["human_review_approved"] = True
    manifest["approved_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["approved_by"] = os.environ.get("USER", "unknown")
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Approved: {path}")
    print("No hardware job was submitted.")


if __name__ == "__main__":
    main()
