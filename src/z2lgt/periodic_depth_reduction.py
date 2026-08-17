"""Offline depth-reduction audit for periodic hardware candidates."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

from .circuits import resource_metrics
from .periodic_circuits import periodic_two_sector_circuit_comparison
from .periodic_iqm_audit import candidate_label
from .periodic_readout import (
    periodic_joint_readout_circuit,
    periodic_matter_readout_circuit,
    periodic_wilson_matter_readout_circuit,
)


READOUT_MODES = ("joint", "wilson_matter", "matter_only")
DEFAULT_DEPTH_SCAN: tuple[tuple[float, int], ...] = (
    (0.2, 1),
    (0.3, 1),
    (0.4, 1),
    (0.5, 1),
    (0.6, 1),
    (0.7, 1),
    (0.8, 1),
    (0.6, 2),
    (0.8, 2),
    (1.0, 2),
    (1.2, 2),
    (0.8, 4),
    (1.0, 4),
)


def build_readout_circuit(
    mode: str,
    *,
    time: float,
    dt: float,
    wilson_sector: int,
):
    """Return one of the periodic readout circuit variants."""
    if mode == "joint":
        return periodic_joint_readout_circuit(
            time,
            dt,
            wilson_sector=wilson_sector,
        )
    if mode == "wilson_matter":
        return periodic_wilson_matter_readout_circuit(
            time,
            dt,
            wilson_sector=wilson_sector,
        )
    if mode == "matter_only":
        return periodic_matter_readout_circuit(
            time,
            dt,
            wilson_sector=wilson_sector,
        )
    raise ValueError(f"unknown readout mode: {mode}")


def _sector_metrics(time: float, dt: float) -> dict[str, object]:
    rows = periodic_two_sector_circuit_comparison(
        time=time,
        dt=dt,
        include_resources=False,
    )
    plus, minus = rows
    exact_separation = abs(
        float(plus["exact_imbalance"]) - float(minus["exact_imbalance"])
    )
    trotter_separation = abs(
        float(plus["trotter_imbalance"]) - float(minus["trotter_imbalance"])
    )
    return {
        "exact_sector_separation": exact_separation,
        "trotter_sector_separation": trotter_separation,
        "separation_retained": (
            trotter_separation / exact_separation if exact_separation else None
        ),
        "minimum_state_fidelity": min(float(row["state_fidelity"]) for row in rows),
        "maximum_absolute_trotter_observable_error": max(
            float(row["absolute_imbalance_error"]) for row in rows
        ),
        "trotter_Wplus_imbalance": float(plus["trotter_imbalance"]),
        "trotter_Wminus_imbalance": float(minus["trotter_imbalance"]),
        "exact_Wplus_imbalance": float(plus["exact_imbalance"]),
        "exact_Wminus_imbalance": float(minus["exact_imbalance"]),
    }


def audit_row(
    *,
    time: float,
    steps: int,
    mode: str,
    baseline_two_qubit_count: int,
    baseline_depth: int,
    min_trotter_separation: float,
    min_fidelity: float,
) -> dict[str, object]:
    """Return one readout-mode/candidate audit row."""
    if time <= 0 or steps <= 0:
        raise ValueError("time and steps must be positive")
    dt = time / steps
    physics = _sector_metrics(time, dt)
    resources = {
        sector: resource_metrics(
            build_readout_circuit(
                mode,
                time=time,
                dt=dt,
                wilson_sector=sign,
            )
        )
        for sector, sign in (("Wplus", 1), ("Wminus", -1))
    }
    max_depth = max(int(item["depth"]) for item in resources.values())
    max_two_qubit = max(
        int(item["two_qubit_gate_count"]) for item in resources.values()
    )
    signal = float(physics["trotter_sector_separation"])
    fidelity = float(physics["minimum_state_fidelity"])
    signal_pass = signal >= min_trotter_separation
    fidelity_pass = fidelity >= min_fidelity
    return {
        "candidate": candidate_label(time, dt),
        "time": float(time),
        "dt": float(dt),
        "trotter_steps": int(steps),
        "readout_mode": mode,
        **physics,
        "source_max_depth": max_depth,
        "source_max_two_qubit_gate_count": max_two_qubit,
        "source_qubit_count": max(int(item["qubit_count"]) for item in resources.values()),
        "source_measurement_count": max(
            int(item["measurement_count"]) for item in resources.values()
        ),
        "depth_reduction_vs_current_joint": baseline_depth - max_depth,
        "two_qubit_reduction_vs_current_joint": baseline_two_qubit_count - max_two_qubit,
        "two_qubit_reduction_fraction_vs_current_joint": (
            (baseline_two_qubit_count - max_two_qubit) / baseline_two_qubit_count
        ),
        "signal_per_two_qubit_gate": signal / max_two_qubit if max_two_qubit else None,
        "signal_gate_passed": signal_pass,
        "fidelity_gate_passed": fidelity_pass,
        "algorithmic_gate_passed": signal_pass and fidelity_pass,
    }


def depth_reduction_audit(
    candidates: Iterable[tuple[float, int]] = DEFAULT_DEPTH_SCAN,
    *,
    modes: Iterable[str] = READOUT_MODES,
    baseline_time: float = 0.8,
    baseline_steps: int = 2,
    min_trotter_separation: float = 0.10,
    min_fidelity: float = 0.85,
) -> dict[str, object]:
    """Run an offline source-depth scan for reduced periodic readout modes."""
    baseline_dt = baseline_time / baseline_steps
    baseline_resources = {
        sector: resource_metrics(
            periodic_joint_readout_circuit(
                baseline_time,
                baseline_dt,
                wilson_sector=sign,
            )
        )
        for sector, sign in (("Wplus", 1), ("Wminus", -1))
    }
    baseline_depth = max(int(item["depth"]) for item in baseline_resources.values())
    baseline_two_qubit = max(
        int(item["two_qubit_gate_count"]) for item in baseline_resources.values()
    )
    rows = [
        audit_row(
            time=time,
            steps=steps,
            mode=mode,
            baseline_depth=baseline_depth,
            baseline_two_qubit_count=baseline_two_qubit,
            min_trotter_separation=min_trotter_separation,
            min_fidelity=min_fidelity,
        )
        for time, steps in candidates
        for mode in modes
    ]
    recommended = recommended_depth_candidate(rows)
    for row in rows:
        row["recommended"] = row is recommended
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "offline source-circuit depth reduction; no IQM connection or submission",
        "baseline": {
            "candidate": candidate_label(baseline_time, baseline_dt),
            "time": baseline_time,
            "dt": baseline_dt,
            "trotter_steps": baseline_steps,
            "readout_mode": "joint",
            "source_max_depth": baseline_depth,
            "source_max_two_qubit_gate_count": baseline_two_qubit,
        },
        "thresholds": {
            "minimum_trotter_sector_separation": min_trotter_separation,
            "minimum_state_fidelity": min_fidelity,
        },
        "selection_rule": (
            "among threshold-passing rows, require matter_only if available, "
            "then minimize two-qubit count and depth, then maximize Trotter separation"
        ),
        "recommended": None if recommended is None else {
            key: recommended[key]
            for key in (
                "candidate",
                "readout_mode",
                "trotter_sector_separation",
                "source_max_two_qubit_gate_count",
                "source_max_depth",
                "two_qubit_reduction_fraction_vs_current_joint",
            )
        },
        "rows": rows,
    }


def recommended_depth_candidate(rows: list[dict[str, object]]) -> dict[str, object] | None:
    """Choose the shallowest threshold-passing dynamics-readout row."""
    eligible = [row for row in rows if row.get("algorithmic_gate_passed")]
    if not eligible:
        return None

    def key(row: dict[str, object]) -> tuple[int, float, float, float]:
        mode_priority = 0 if row["readout_mode"] == "matter_only" else 1
        return (
            mode_priority,
            float(row["source_max_two_qubit_gate_count"]),
            float(row["source_max_depth"]),
            -float(row["trotter_sector_separation"]),
        )

    return min(eligible, key=key)


def write_depth_reduction_audit(
    report: dict[str, object],
    json_path: Path,
    csv_path: Path,
) -> tuple[Path, Path]:
    """Persist depth-reduction audit JSON and CSV."""
    rows = report.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("audit report must contain rows")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    fieldnames = [
        "candidate",
        "time",
        "dt",
        "trotter_steps",
        "readout_mode",
        "trotter_sector_separation",
        "minimum_state_fidelity",
        "source_qubit_count",
        "source_max_depth",
        "source_max_two_qubit_gate_count",
        "source_measurement_count",
        "depth_reduction_vs_current_joint",
        "two_qubit_reduction_vs_current_joint",
        "two_qubit_reduction_fraction_vs_current_joint",
        "signal_per_two_qubit_gate",
        "signal_gate_passed",
        "fidelity_gate_passed",
        "algorithmic_gate_passed",
        "recommended",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return json_path, csv_path
