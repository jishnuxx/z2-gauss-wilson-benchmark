"""IQM response-mitigation helpers for the static blind-spot benchmark."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .blindspot_circuits import CASES, joint_diagnostic_circuit, syndrome_response_circuit
from .iqm_candidate import validate_submission_manifest


RESPONSE_BATCH = "blindspot-response-mitigated"
RESPONSE_SYNDROMES = tuple(range(16))


def response_mitigation_circuit_specs():
    """Return labelled circuits for the static response-mitigation hardware batch."""
    specs = []
    for case in CASES:
        specs.append(
            {
                "kind": "data",
                "case": case,
                "label": case,
                "circuit": joint_diagnostic_circuit(case),
            }
        )
    for syndrome in RESPONSE_SYNDROMES:
        specs.append(
            {
                "kind": "response",
                "case": f"response_{syndrome:04b}",
                "true_syndrome": syndrome,
                "label": f"response_{syndrome:04b}",
                "circuit": syndrome_response_circuit(syndrome),
            }
        )
    return specs


def validate_blindspot_response_manifest(
    manifest: dict[str, Any],
    *,
    root: Path,
    expected_quantum_computer: str,
    expected_shots: int,
) -> list[Path]:
    """Validate generic gates plus response-mitigation batch invariants."""
    qpy_paths = validate_submission_manifest(
        manifest,
        root=root,
        expected_quantum_computer=expected_quantum_computer,
        expected_shots=expected_shots,
    )
    if manifest.get("batch") != RESPONSE_BATCH:
        raise PermissionError("manifest is not a static response-mitigation candidate")
    circuits = manifest.get("circuits")
    if not isinstance(circuits, list) or len(circuits) != len(CASES) + len(RESPONSE_SYNDROMES):
        raise PermissionError("response-mitigation candidate must contain 19 circuits")
    data_cases = [record.get("case") for record in circuits[: len(CASES)]]
    if data_cases != list(CASES):
        raise PermissionError("first three response-mitigation circuits must be data cases")
    response_records = circuits[len(CASES) :]
    if [record.get("true_syndrome") for record in response_records] != list(RESPONSE_SYNDROMES):
        raise PermissionError("response calibration circuits must cover syndromes 0..15 in order")
    if not manifest.get("hardware_checks", {}).get("same_mapping_for_all_circuits"):
        raise PermissionError("all response-mitigation circuits must share one hardware mapping")
    return qpy_paths


def require_explicit_response_hardware_consent(
    *,
    submit: bool,
    environment: Mapping[str, str],
    candidate_id: str,
    confirmation: str | None,
) -> None:
    """Require independent consent signals before response-mitigation submission."""
    if not submit:
        return
    if environment.get("Z2LGT_ALLOW_IQM_HARDWARE") != "YES":
        raise PermissionError("set Z2LGT_ALLOW_IQM_HARDWARE=YES for explicit hardware consent")
    expected = candidate_id[:12]
    if confirmation != expected:
        raise PermissionError(f"pass --confirm-candidate {expected} to confirm the frozen candidate")
