"""Pure analysis helpers for the periodic IQM feasibility audit.

This module deliberately contains no IQM provider calls.  It quantifies the
physics signal and product-formula error before a separate script connects to
an IQM backend for read-only compilation and request validation.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from .circuits import resource_metrics
from .periodic_circuits import periodic_two_sector_circuit_comparison
from .periodic_readout import periodic_joint_readout_circuit


DEFAULT_CANDIDATES: tuple[tuple[float, float], ...] = (
    (0.6, 0.3),
    (0.8, 0.4),
    (1.0, 0.5),
    (1.2, 0.6),
    (0.8, 0.2),
    (1.0, 0.25),
)


def physical_operation_qubits(
    compiled,
    logical_to_physical: list[int],
    operation: str,
) -> list[tuple[int, ...]]:
    """Return physical qubits used by an operation in a transpiled circuit.

    IQM/Qiskit can return either a packed circuit whose output wires are
    numbered ``0..n_logical-1`` or a full-device circuit whose output-wire
    indices already are physical qubit numbers.  The latter occurs when the
    transpiler allocates device ancillas/routing space.  Supporting both forms
    avoids applying the logical layout twice to full-device indices.
    """
    # IQM's transpiler may preserve multiple quantum registers in the output.
    # For such circuits ``find_bit(bit).index`` can expose a register-local
    # index, while the bit's position in ``compiled.qubits`` is the physical
    # output-wire position.  Resolve by object identity first to avoid mixing
    # those two index spaces.
    output_position = {id(qubit): index for index, qubit in enumerate(compiled.qubits)}

    def position(qubit) -> int:
        index = output_position.get(id(qubit))
        if index is None:
            try:
                index = compiled.qubits.index(qubit)
            except ValueError as exc:
                raise RuntimeError(
                    "instruction qubit is absent from compiled circuit"
                ) from exc
        return index

    output_qubits = sorted(
        {
            tuple(position(qubit) for qubit in instruction.qubits)
            for instruction in compiled.data
            if instruction.operation.name == operation
        }
    )
    if compiled.num_qubits > len(logical_to_physical):
        return output_qubits

    physical: list[tuple[int, ...]] = []
    for qubits in output_qubits:
        if qubits and max(qubits) >= len(logical_to_physical):
            raise RuntimeError(
                f"cannot translate packed {operation} qubits {qubits} "
                "through logical-to-physical mapping"
            )
        physical.append(tuple(logical_to_physical[index] for index in qubits))
    return physical


def parse_candidate(value: str) -> tuple[float, float]:
    """Parse a ``TIME:DT`` candidate and enforce an integral step count."""
    try:
        time_text, dt_text = value.split(":", maxsplit=1)
        time = float(time_text)
        dt = float(dt_text)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"candidate must have the form TIME:DT, got {value!r}") from exc
    if not np.isfinite(time) or not np.isfinite(dt) or time <= 0 or dt <= 0:
        raise ValueError("candidate time and dt must be finite and positive")
    steps = int(round(time / dt))
    if steps < 1 or not np.isclose(steps * dt, time, atol=1e-10):
        raise ValueError("candidate time must be an integer multiple of dt")
    return time, dt


def candidate_label(time: float, dt: float) -> str:
    """Return a stable human-readable label for one candidate."""
    return f"t={time:g},dt={dt:g}"


def algorithmic_candidate_metrics(time: float, dt: float) -> dict[str, object]:
    """Compute exact/Trotter signal and source-circuit resources."""
    # periodic_two_sector_circuit_comparison also validates time/dt.
    sectors = periodic_two_sector_circuit_comparison(
        time=time,
        dt=dt,
        include_resources=False,
    )
    plus, minus = sectors
    exact_separation = abs(
        float(plus["exact_imbalance"]) - float(minus["exact_imbalance"])
    )
    trotter_separation = abs(
        float(plus["trotter_imbalance"]) - float(minus["trotter_imbalance"])
    )
    source_resources = {
        "Wplus": resource_metrics(
            periodic_joint_readout_circuit(time, dt, wilson_sector=1)
        ),
        "Wminus": resource_metrics(
            periodic_joint_readout_circuit(time, dt, wilson_sector=-1)
        ),
    }
    return {
        "candidate": candidate_label(time, dt),
        "time": float(time),
        "dt": float(dt),
        "trotter_steps": int(round(time / dt)),
        "exact_Wplus_imbalance": float(plus["exact_imbalance"]),
        "exact_Wminus_imbalance": float(minus["exact_imbalance"]),
        "trotter_Wplus_imbalance": float(plus["trotter_imbalance"]),
        "trotter_Wminus_imbalance": float(minus["trotter_imbalance"]),
        "exact_sector_separation": exact_separation,
        "trotter_sector_separation": trotter_separation,
        "separation_retained": (
            trotter_separation / exact_separation if exact_separation else None
        ),
        "minimum_state_fidelity": min(float(row["state_fidelity"]) for row in sectors),
        "maximum_absolute_trotter_observable_error": max(
            float(row["absolute_imbalance_error"]) for row in sectors
        ),
        "minimum_gauss_expectation": min(
            float(row["trotter_min_gauss"]) for row in sectors
        ),
        "trotter_Wplus_wilson": float(plus["trotter_wilson"]),
        "trotter_Wminus_wilson": float(minus["trotter_wilson"]),
        "source_resources": source_resources,
        "source_max_depth": max(item["depth"] for item in source_resources.values()),
        "source_max_two_qubit_gate_count": max(
            item["two_qubit_gate_count"] for item in source_resources.values()
        ),
        "source_qubit_count": max(
            item["qubit_count"] for item in source_resources.values()
        ),
        "source_measurement_count": max(
            item["measurement_count"] for item in source_resources.values()
        ),
    }


def apply_algorithmic_gate(
    row: dict[str, object],
    *,
    min_fidelity: float,
    min_separation_retained: float,
    min_trotter_separation: float,
) -> None:
    """Annotate one row with an explicit, configurable algorithmic gate."""
    checks = {
        "minimum_state_fidelity": float(row["minimum_state_fidelity"])
        >= min_fidelity,
        "minimum_separation_retained": float(row["separation_retained"])
        >= min_separation_retained,
        "minimum_trotter_sector_separation": float(
            row["trotter_sector_separation"]
        )
        >= min_trotter_separation,
    }
    row["algorithmic_checks"] = checks
    row["algorithmic_gate_passed"] = all(checks.values())


def recommended_candidate(rows: list[dict[str, object]]) -> str | None:
    """Choose the shallowest passing candidate, then the largest signal.

    This is a transparent audit heuristic, not a claim of optimal hardware
    performance.  Native CZ count is preferred when available; otherwise the
    source two-qubit count is used.
    """
    eligible = [row for row in rows if row.get("algorithmic_gate_passed")]
    if not eligible:
        return None

    def key(row: dict[str, object]) -> tuple[float, float, float]:
        gates = row.get("native_max_cz_count")
        if gates is None:
            gates = row["source_max_two_qubit_gate_count"]
        depth = row.get("native_max_depth")
        if depth is None:
            depth = row["source_max_depth"]
        return (
            float(gates),
            float(depth),
            -float(row["trotter_sector_separation"]),
        )

    return str(min(eligible, key=key)["candidate"])


def flattened_candidate(row: dict[str, object]) -> dict[str, object]:
    """Flatten the stable summary fields used in the audit CSV."""
    checks = row.get("algorithmic_checks", {})
    return {
        "candidate": row["candidate"],
        "time": row["time"],
        "dt": row["dt"],
        "trotter_steps": row["trotter_steps"],
        "exact_sector_separation": row["exact_sector_separation"],
        "trotter_sector_separation": row["trotter_sector_separation"],
        "separation_retained": row["separation_retained"],
        "minimum_state_fidelity": row["minimum_state_fidelity"],
        "maximum_absolute_trotter_observable_error": row[
            "maximum_absolute_trotter_observable_error"
        ],
        "source_qubit_count": row["source_qubit_count"],
        "source_max_depth": row["source_max_depth"],
        "source_max_two_qubit_gate_count": row[
            "source_max_two_qubit_gate_count"
        ],
        "native_max_depth": row.get("native_max_depth"),
        "native_max_cz_count": row.get("native_max_cz_count"),
        "maximum_cz_error": row.get("maximum_cz_error"),
        "maximum_readout_error": row.get("maximum_readout_error"),
        "request_validated": row.get("request_validated", False),
        "fidelity_gate_passed": checks.get("minimum_state_fidelity"),
        "retained_separation_gate_passed": checks.get(
            "minimum_separation_retained"
        ),
        "absolute_separation_gate_passed": checks.get(
            "minimum_trotter_sector_separation"
        ),
        "algorithmic_gate_passed": row.get("algorithmic_gate_passed", False),
        "recommended": row.get("recommended", False),
    }


def write_audit(
    report: dict[str, object],
    json_path: Path,
    csv_path: Path,
) -> tuple[Path, Path]:
    """Write the full JSON report and flat candidate comparison CSV."""
    candidates = report.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("audit report must contain at least one candidate")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    flat = [flattened_candidate(row) for row in candidates]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    return json_path, csv_path
