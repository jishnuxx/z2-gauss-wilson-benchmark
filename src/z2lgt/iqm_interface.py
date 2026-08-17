"""Opt-in IQM readiness checks with a mandatory no-submit default."""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any

from qiskit import QuantumCircuit

from .circuits import resource_metrics


class IQMUnavailable(RuntimeError):
    """Raised when an explicitly requested IQM operation cannot be prepared."""


def iqm_status() -> dict[str, Any]:
    try:
        from iqm import qiskit_iqm  # noqa: F401
        package_available = True
    except ImportError:
        package_available = False
    credential_available = bool(os.environ.get("IQM_TOKEN"))
    return {
        "qiskit_on_iqm_available": package_available,
        "credential_available": credential_available,
        "submission_enabled": False,
    }


def dry_run(circuit: QuantumCircuit) -> dict[str, Any]:
    """Report generic compiled resources; never connects or submits."""
    return {**resource_metrics(circuit), **iqm_status(), "mode": "dry-run"}


_REQUIRED_READINESS_GATES = (
    "all_tests_passed",
    "ideal_ed_agreement_passed",
    "noisy_plots_present",
    "postselection_improvement_passed",
    "circuits_and_measurements_frozen",
    "human_review_approved",
)


def _validate_readiness_manifest(path: Path | None) -> None:
    if path is None:
        raise PermissionError("a hardware readiness manifest is required")
    try:
        manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PermissionError(f"invalid hardware readiness manifest: {exc}") from exc
    failed = [gate for gate in _REQUIRED_READINESS_GATES if manifest.get(gate) is not True]
    if failed:
        raise PermissionError("hardware readiness gates are not satisfied: " + ", ".join(failed))


def get_iqm_backend(
    *, allow_hardware: bool = False, readiness_manifest: Path | None = None, **kwargs
):
    """Construct an IQM backend only behind two explicit safety gates.

    This function never submits jobs.  Callers must both pass
    ``allow_hardware=True`` and set ``Z2LGT_ALLOW_IQM_HARDWARE=YES``.
    """
    if not allow_hardware or os.environ.get("Z2LGT_ALLOW_IQM_HARDWARE") != "YES":
        raise PermissionError(
            "IQM hardware is disabled. Complete simulator validation, freeze circuits, "
            "then explicitly pass allow_hardware=True and set Z2LGT_ALLOW_IQM_HARDWARE=YES."
        )
    _validate_readiness_manifest(readiness_manifest)
    try:
        from iqm.qiskit_iqm import IQMProvider
    except ImportError as exc:
        raise IQMUnavailable("iqm-client[qiskit] is not installed; dry-run remains available") from exc
    if not os.environ.get("IQM_TOKEN"):
        raise IQMUnavailable("IQM_TOKEN is missing; no backend was constructed")
    kwargs.setdefault("url", os.environ.get("IQM_SERVER_URL"))
    kwargs.setdefault("quantum_computer", os.environ.get("IQM_QUANTUM_COMPUTER"))
    if not kwargs["url"]:
        raise IQMUnavailable("IQM_SERVER_URL is missing; no backend was constructed")
    return IQMProvider(**kwargs).get_backend()
