"""Frozen IQM hardware-run manifests and execution safety checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REQUIRED_TRUE_GATES = (
    "all_tests_passed",
    "request_validated",
    "circuits_frozen",
    "human_review_approved",
)


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate_id(identity: dict[str, Any]) -> str:
    """Hash the immutable identity fields of a hardware candidate."""
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PermissionError(f"invalid readiness manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise PermissionError("invalid readiness manifest: expected a JSON object")
    return manifest


def resolve_artifact(path_text: str, *, root: Path) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else root / path


def validate_hardware_manifest(
    manifest: dict[str, Any],
    *,
    root: Path,
    expected_quantum_computer: str | None = None,
    expected_shots: int | None = None,
) -> list[Path]:
    """Validate approval gates and frozen QPY hashes before hardware execution."""
    if manifest.get("schema_version") != 1:
        raise PermissionError("unsupported or missing readiness manifest schema_version")
    failed = [gate for gate in REQUIRED_TRUE_GATES if manifest.get(gate) is not True]
    if failed:
        raise PermissionError("hardware readiness gates are not satisfied: " + ", ".join(failed))
    if manifest.get("hardware_submitted") is True:
        raise PermissionError("this candidate manifest is already marked as submitted")
    if manifest.get("hardware_execution_started") is True:
        raise PermissionError(
            "this manifest has a prior hardware execution attempt; inspect its status before retrying"
        )
    if expected_quantum_computer and manifest.get("quantum_computer") != expected_quantum_computer:
        raise PermissionError(
            "manifest quantum computer does not match the configured target: "
            f"{manifest.get('quantum_computer')} != {expected_quantum_computer}"
        )
    if expected_shots is not None and manifest.get("shots") != expected_shots:
        raise PermissionError(
            f"manifest shots do not match the requested shots: {manifest.get('shots')} != {expected_shots}"
        )

    circuits = manifest.get("circuits")
    if not isinstance(circuits, list) or not circuits:
        raise PermissionError("manifest contains no frozen circuits")
    qpy_paths: list[Path] = []
    for record in circuits:
        try:
            path = resolve_artifact(record["qpy"], root=root)
            expected_hash = record["qpy_sha256"]
        except (KeyError, TypeError) as exc:
            raise PermissionError("manifest circuit record is incomplete") from exc
        if not path.is_file():
            raise PermissionError(f"frozen QPY circuit is missing: {path}")
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            raise PermissionError(f"frozen QPY hash mismatch: {path}")
        qpy_paths.append(path)
    identity = {
        "batch": manifest.get("batch"),
        "server_url": manifest.get("server_url"),
        "quantum_computer": manifest.get("quantum_computer"),
        "calibration_set_id": manifest.get("calibration_set_id"),
        "shots": manifest.get("shots"),
        "optimization_level": manifest.get("optimization_level"),
        "seed_transpiler": manifest.get("seed_transpiler"),
        "qpy_sha256": [record.get("qpy_sha256") for record in circuits],
    }
    if manifest.get("candidate_id") != candidate_id(identity):
        raise PermissionError("candidate identity hash does not match the manifest contents")
    return qpy_paths
