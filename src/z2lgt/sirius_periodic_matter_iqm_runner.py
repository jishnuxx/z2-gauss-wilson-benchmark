"""Safety checks for the six-circuit Sirius periodic-matter scan."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .iqm_candidate import validate_submission_manifest


EXPECTED_BATCH = "periodic-matter-sirius-two-step-scan-t0.6-0.8-1.0"
EXPECTED_POINTS = ((0.6, 0.3), (0.8, 0.4), (1.0, 0.5))
EXPECTED_SECTORS = {"Wplus": 1, "Wminus": -1}
EXPECTED_LAYOUT = (4, 1, 6, 5, 0, 2, 3, 13)
EXPECTED_CIRCUIT_ORDER = tuple(
    (time, dt, case, sector)
    for time, dt in EXPECTED_POINTS
    for case, sector in EXPECTED_SECTORS.items()
)


def validate_sirius_scan_submission_manifest(
    manifest: dict[str, Any],
    *,
    root: Path,
    expected_quantum_computer: str = "sirius",
    expected_shots: int = 5000,
    expected_replicate_label: str | None = None,
) -> list[Path]:
    """Validate structure, approval, and artifacts for the Sirius scan."""
    qpy_paths = validate_submission_manifest(
        manifest,
        root=root,
        expected_quantum_computer=expected_quantum_computer,
        expected_shots=expected_shots,
    )
    expected_batch = (
        EXPECTED_BATCH
        if expected_replicate_label is None
        else f"{EXPECTED_BATCH}-{expected_replicate_label}"
    )
    if manifest.get("batch") != expected_batch:
        raise PermissionError("manifest is not the reviewed Sirius three-point scan")
    if (
        expected_replicate_label is not None
        and manifest.get("replicate_label") != expected_replicate_label
    ):
        raise PermissionError("Sirius scan replicate label is invalid")
    if manifest.get("benchmark_type") != "two_step_fixed_product_formula_scan":
        raise PermissionError("Sirius scan benchmark type is invalid")
    if manifest.get("readout_mode") != "matter_only":
        raise PermissionError("Sirius scan readout mode must be matter_only")
    if manifest.get("wilson_sectors") != EXPECTED_SECTORS:
        raise PermissionError("Sirius scan Wilson-sector labels are invalid")
    if tuple(manifest.get("fixed_initial_layout_indices", ())) != EXPECTED_LAYOUT:
        raise PermissionError("Sirius scan fixed initial layout is invalid")

    points = tuple(
        (item.get("time"), item.get("dt"))
        for item in manifest.get("points", [])
    )
    steps = tuple(item.get("trotter_steps") for item in manifest.get("points", []))
    if points != EXPECTED_POINTS or steps != (2, 2, 2):
        raise PermissionError("Sirius scan points must be the reviewed two-step set")

    checks = manifest.get("hardware_checks")
    if not isinstance(checks, dict) or not checks or not all(
        value is True for value in checks.values()
    ):
        raise PermissionError("Sirius hardware freeze checks are not all satisfied")

    circuits = manifest.get("circuits", [])
    actual_order = tuple(
        (
            record.get("time"),
            record.get("dt"),
            record.get("case"),
            record.get("wilson_sector"),
        )
        for record in circuits
    )
    if actual_order != EXPECTED_CIRCUIT_ORDER:
        raise PermissionError("frozen Sirius circuit order is invalid")
    if any(
        tuple(record.get("logical_to_physical_indices", ())) != EXPECTED_LAYOUT
        for record in circuits
    ):
        raise PermissionError("all Sirius circuits must share the frozen mapping")
    if any(record.get("measurement_count") != 4 for record in circuits):
        raise PermissionError("Sirius scan circuits must measure four matter bits")
    return qpy_paths


def require_explicit_sirius_scan_hardware_consent(
    *,
    submit: bool,
    environment: Mapping[str, str],
    candidate_id: str,
    confirmation: str | None,
) -> None:
    """Require independent environment and candidate-ID consent signals."""
    if not submit:
        return
    if environment.get("Z2LGT_ALLOW_SIRIUS_SCAN_HARDWARE") != "YES":
        raise PermissionError(
            "set Z2LGT_ALLOW_SIRIUS_SCAN_HARDWARE=YES for explicit Sirius "
            "scan consent"
        )
    expected = candidate_id[:12]
    if confirmation != expected:
        raise PermissionError(
            f"pass --confirm-candidate {expected} to confirm the frozen candidate"
        )
