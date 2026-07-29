"""Safety validation for the frozen periodic IQM hardware run."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .iqm_candidate import validate_hardware_manifest


EXPECTED_SECTORS = {"Wplus": 1, "Wminus": -1}


def validate_periodic_hardware_manifest(
    manifest: dict[str, Any],
    *,
    root: Path,
    expected_quantum_computer: str,
    expected_shots: int,
) -> list[Path]:
    """Validate generic gates plus periodic-candidate invariants."""
    qpy_paths = validate_hardware_manifest(
        manifest,
        root=root,
        expected_quantum_computer=expected_quantum_computer,
        expected_shots=expected_shots,
    )
    batch = manifest.get("batch")
    if not isinstance(batch, str) or not batch.startswith("periodic-two-sector-"):
        raise PermissionError("manifest is not a periodic two-sector candidate")
    if manifest.get("wilson_sectors") != EXPECTED_SECTORS:
        raise PermissionError("periodic Wilson-sector labels are invalid")
    if manifest.get("time") != 0.8 or manifest.get("dt") != 0.4:
        raise PermissionError("periodic candidate must be the reviewed t=0.8, dt=0.4 point")
    if manifest.get("trotter_steps") != 2:
        raise PermissionError("periodic candidate must contain two Trotter steps")
    checks = manifest.get("hardware_checks")
    if not isinstance(checks, dict) or not checks or not all(
        value is True for value in checks.values()
    ):
        raise PermissionError("periodic hardware freeze checks are not all satisfied")
    circuits = manifest.get("circuits", [])
    cases = [record.get("case") for record in circuits]
    signs = [record.get("wilson_sector") for record in circuits]
    if cases != ["Wplus", "Wminus"] or signs != [1, -1]:
        raise PermissionError("frozen circuit order must be Wplus then Wminus")
    mappings = {
        tuple(record.get("logical_to_physical", [])) for record in circuits
    }
    if len(mappings) != 1 or len(next(iter(mappings), ())) != 12:
        raise PermissionError("both periodic sectors must share one 12-qubit mapping")
    return qpy_paths


def require_explicit_periodic_hardware_consent(
    *,
    submit: bool,
    environment: Mapping[str, str],
    candidate_id: str,
    confirmation: str | None,
) -> None:
    """Require three independent signals before periodic hardware execution."""
    if not submit:
        return
    if environment.get("Z2LGT_ALLOW_PERIODIC_IQM_HARDWARE") != "YES":
        raise PermissionError(
            "set Z2LGT_ALLOW_PERIODIC_IQM_HARDWARE=YES for explicit periodic "
            "hardware consent"
        )
    expected = candidate_id[:12]
    if confirmation != expected:
        raise PermissionError(
            f"pass --confirm-candidate {expected} to confirm the frozen candidate"
        )
