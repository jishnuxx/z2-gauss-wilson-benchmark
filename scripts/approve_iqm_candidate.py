#!/usr/bin/env python3
"""Interactively approve a frozen IQM candidate after human review."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import _bootstrap
from z2lgt.iqm_candidate import load_manifest, resolve_artifact, sha256_file


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest",
        nargs="?",
        type=Path,
        default=Path("results/iqm/emerald_blindspot_candidate/readiness_manifest.json"),
    )
    args = parser.parse_args()
    path = args.manifest.resolve()
    manifest = load_manifest(path)
    for gate in ("all_tests_passed", "request_validated", "circuits_frozen"):
        if manifest.get(gate) is not True:
            raise SystemExit(f"cannot approve: {gate} is not true")
    if manifest.get("hardware_submitted") is True:
        raise SystemExit("cannot approve: candidate is already marked as submitted")
    for record in manifest.get("circuits", []):
        qpy = resolve_artifact(record["qpy"], root=_bootstrap.ROOT)
        if sha256_file(qpy) != record["qpy_sha256"]:
            raise SystemExit(f"cannot approve: QPY hash mismatch for {qpy}")

    print(f"Candidate: {manifest['candidate_id']}")
    print(f"Target: {manifest['quantum_computer']}")
    print(f"Calibration: {manifest['calibration_set_id']}")
    print(f"Shots per circuit: {manifest['shots']}")
    for record in manifest["circuits"]:
        max_cz = max(item["error"] for item in record["cz_pairs"] if item["error"] is not None)
        max_ro = max(item["error"] for item in record["measurements"] if item["error"] is not None)
        print(
            f"  {record['case']}: map={record['logical_to_physical']} "
            f"depth={record['depth']} 2q={record['two_qubit_gate_count']} "
            f"max_CZ_error={max_cz:.6f} max_readout_error={max_ro:.6f}"
        )
    phrase = f"APPROVE {manifest['candidate_id'][:12]}"
    entered = input(f"Type {phrase!r} to approve this exact candidate: ")
    if entered != phrase:
        raise SystemExit("approval phrase did not match; manifest was not changed")
    manifest["human_review_approved"] = True
    manifest["approved_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["approved_by"] = os.environ.get("USER", "unknown")
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Approved: {path}")
    print("No hardware job was submitted.")


if __name__ == "__main__":
    main()
