"""Readout-assignment mitigation utilities for archived IQM count data.

The functions in this module deliberately separate two cases:

* independent per-classical-bit assignment mitigation, using readout error
  probabilities archived in a hardware manifest;
* full response-matrix mitigation in a diagnostic syndrome space, using
  calibration circuits with known true syndromes.

Both methods act only on measured classical distributions.  They do not undo
coherent gate errors, decoherence during the algorithm, leakage, or crosstalk.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import numpy as np
from qiskit.qpy import load as qpy_load


def qiskit_key_to_index(key: str, n_bits: int) -> int:
    """Convert a Qiskit count key ``c[n-1]...c[0]`` into a little-endian index."""
    compact = key.replace(" ", "")
    if len(compact) != n_bits or set(compact) - {"0", "1"}:
        raise ValueError(f"expected a {n_bits}-bit count key, got {key!r}")
    return sum(int(bit) << index for index, bit in enumerate(reversed(compact)))


def index_to_qiskit_key(index: int, n_bits: int) -> str:
    """Convert a little-endian integer index into Qiskit's display order."""
    if not 0 <= index < 2**n_bits:
        raise ValueError(f"index {index} is outside the {n_bits}-bit range")
    return "".join(str((index >> bit) & 1) for bit in range(n_bits - 1, -1, -1))


def counts_to_probability_vector(
    counts: dict[str, int | float],
    n_bits: int | None = None,
) -> tuple[np.ndarray, float]:
    """Return ``p[measured_index]`` and the total shot weight."""
    if n_bits is None:
        if not counts:
            raise ValueError("counts must not be empty")
        lengths = {len(key.replace(" ", "")) for key in counts}
        if len(lengths) != 1:
            raise ValueError("all count keys must have the same bit length")
        n_bits = lengths.pop()
    vector = np.zeros(2**n_bits, dtype=float)
    shots = float(sum(counts.values()))
    if shots <= 0:
        raise ValueError("counts must contain positive total weight")
    for key, count in counts.items():
        vector[qiskit_key_to_index(key, n_bits)] += float(count) / shots
    return vector, shots


def probability_vector_to_counts(
    probabilities: Sequence[float],
    shots: int | float,
    *,
    atol: float = 1e-10,
) -> dict[str, float]:
    """Convert a probability vector back to Qiskit-style weighted counts."""
    vector = np.asarray(probabilities, dtype=float)
    if vector.ndim != 1:
        raise ValueError("probabilities must be a one-dimensional vector")
    n_states = vector.size
    n_bits = int(np.log2(n_states))
    if 2**n_bits != n_states:
        raise ValueError("probability vector length must be a power of two")
    if shots <= 0:
        raise ValueError("shots must be positive")
    if not np.isfinite(vector).all():
        raise ValueError("probabilities contain non-finite entries")

    counts: dict[str, float] = {}
    running = 0.0
    last_key = index_to_qiskit_key(n_states - 1, n_bits)
    for index, probability in enumerate(vector[:-1]):
        value = float(probability) * float(shots)
        if abs(value) > atol:
            counts[index_to_qiskit_key(index, n_bits)] = value
        running += value
    last_value = float(shots) - running
    if abs(last_value) > atol:
        counts[last_key] = last_value
    return counts


def independent_assignment_matrix(
    error_probabilities: Sequence[float | dict[str, float]],
) -> np.ndarray:
    """Build ``M[measured,true]`` for independent one-bit readout channels.

    A scalar entry ``p`` is interpreted as a symmetric assignment error,
    ``P(1|0)=P(0|1)=p``.  A dictionary entry can specify asymmetric errors with
    keys ``p01``/``p_meas1_given0`` and ``p10``/``p_meas0_given1``.
    """
    n_bits = len(error_probabilities)
    if n_bits <= 0:
        raise ValueError("at least one readout error probability is required")
    n_states = 2**n_bits
    matrix = np.zeros((n_states, n_states), dtype=float)
    p01: list[float] = []
    p10: list[float] = []
    for entry in error_probabilities:
        if isinstance(entry, dict):
            zero_to_one = float(entry.get("p01", entry.get("p_meas1_given0", np.nan)))
            one_to_zero = float(entry.get("p10", entry.get("p_meas0_given1", np.nan)))
        else:
            zero_to_one = one_to_zero = float(entry)
        if not (0.0 <= zero_to_one < 0.5 and 0.0 <= one_to_zero < 0.5):
            raise ValueError(
                "assignment probabilities must be in [0, 0.5) for stable inversion"
            )
        p01.append(zero_to_one)
        p10.append(one_to_zero)

    for true in range(n_states):
        for measured in range(n_states):
            probability = 1.0
            for bit in range(n_bits):
                true_bit = (true >> bit) & 1
                measured_bit = (measured >> bit) & 1
                if true_bit == 0:
                    probability *= (1.0 - p01[bit]) if measured_bit == 0 else p01[bit]
                else:
                    probability *= p10[bit] if measured_bit == 0 else (1.0 - p10[bit])
            matrix[measured, true] = probability
    return matrix


def project_to_probability_simplex(vector: Sequence[float]) -> tuple[np.ndarray, float]:
    """Clip negative quasi-probabilities and renormalize.

    Returns the projected distribution and the total clipped negative mass.
    """
    raw = np.asarray(vector, dtype=float)
    negative_mass = float(np.sum(np.abs(raw[raw < 0.0])))
    clipped = np.maximum(raw, 0.0)
    total = float(np.sum(clipped))
    if total <= 0:
        raise ValueError("mitigated distribution has no nonnegative probability mass")
    return clipped / total, negative_mass


def invert_response_distribution(
    observed_probabilities: Sequence[float],
    response_matrix: Sequence[Sequence[float]],
    *,
    clip: bool = True,
) -> dict[str, object]:
    """Invert ``observed = M @ true`` and optionally project to probabilities."""
    observed = np.asarray(observed_probabilities, dtype=float)
    matrix = np.asarray(response_matrix, dtype=float)
    if matrix.shape != (observed.size, observed.size):
        raise ValueError(
            "response matrix must be square with the same length as the probability vector"
        )
    if not np.isfinite(matrix).all() or not np.isfinite(observed).all():
        raise ValueError("response inversion received non-finite values")

    try:
        quasi = np.linalg.solve(matrix, observed)
        solver = "solve"
    except np.linalg.LinAlgError:
        quasi = np.linalg.pinv(matrix) @ observed
        solver = "pinv"

    if clip:
        mitigated, negative_mass = project_to_probability_simplex(quasi)
    else:
        mitigated = quasi
        negative_mass = float(np.sum(np.abs(quasi[quasi < 0.0])))
    return {
        "mitigated_probabilities": mitigated,
        "quasi_probabilities": quasi,
        "negative_probability_mass": negative_mass,
        "condition_number": float(np.linalg.cond(matrix)),
        "solver": solver,
    }


def mitigate_counts_with_response_matrix(
    counts: dict[str, int | float],
    response_matrix: Sequence[Sequence[float]],
    *,
    clip: bool = True,
) -> dict[str, object]:
    """Mitigate counts with a supplied full response matrix."""
    matrix = np.asarray(response_matrix, dtype=float)
    n_bits = int(np.log2(matrix.shape[0]))
    observed, shots = counts_to_probability_vector(counts, n_bits)
    inverted = invert_response_distribution(observed, matrix, clip=clip)
    mitigated_counts = probability_vector_to_counts(
        inverted["mitigated_probabilities"],
        shots,
    )
    quasi_counts = probability_vector_to_counts(inverted["quasi_probabilities"], shots)
    return {
        **inverted,
        "shots": shots,
        "mitigated_counts": mitigated_counts,
        "quasi_counts": quasi_counts,
    }


def mitigate_counts_independent(
    counts: dict[str, int | float],
    error_probabilities: Sequence[float | dict[str, float]],
    *,
    clip: bool = True,
) -> dict[str, object]:
    """Apply independent per-bit assignment-error mitigation to counts."""
    matrix = independent_assignment_matrix(error_probabilities)
    return {
        **mitigate_counts_with_response_matrix(counts, matrix, clip=clip),
        "response_model": "independent_bit_assignment",
        "readout_error_probabilities": [
            dict(entry) if isinstance(entry, dict) else float(entry)
            for entry in error_probabilities
        ],
    }


def measured_physical_qubits_by_clbit(qpy_path: Path) -> list[int]:
    """Return the physical qubit measured into each classical bit of a QPY circuit."""
    with qpy_path.open("rb") as handle:
        circuits = qpy_load(handle)
    if len(circuits) != 1:
        raise ValueError(f"expected one circuit in {qpy_path}, found {len(circuits)}")
    circuit = circuits[0]
    mapping: dict[int, int] = {}
    for instruction in circuit.data:
        if instruction.operation.name != "measure":
            continue
        qubit = int(circuit.find_bit(instruction.qubits[0]).index)
        clbit = int(circuit.find_bit(instruction.clbits[0]).index)
        if clbit in mapping:
            raise ValueError(f"classical bit c{clbit} is measured more than once")
        mapping[clbit] = qubit
    expected = set(range(circuit.num_clbits))
    if set(mapping) != expected:
        missing = sorted(expected - set(mapping))
        raise ValueError(f"circuit does not measure every classical bit: missing {missing}")
    return [mapping[index] for index in range(circuit.num_clbits)]


def _manifest_circuit_record(
    manifest: dict[str, Any],
    *,
    case: str,
) -> dict[str, Any]:
    records = manifest.get("circuits")
    if not isinstance(records, list):
        raise ValueError("manifest does not contain a circuits list")
    for record in records:
        if record.get("case") == case:
            return record
    raise ValueError(f"manifest does not contain circuit case {case!r}")


def readout_probabilities_from_manifest(
    manifest_path: Path,
    *,
    case: str,
    root: Path = Path("."),
) -> dict[str, object]:
    """Extract per-classical-bit symmetric readout errors from a manifest.

    The returned probabilities are ordered by classical bit ``c0, c1, ...``.
    """
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    record = _manifest_circuit_record(manifest, case=case)
    qpy_record = str(record["qpy"])
    qpy_path = Path(qpy_record)
    if not qpy_path.is_absolute():
        qpy_path = root / qpy_path
    measured_physical = measured_physical_qubits_by_clbit(qpy_path)
    by_physical = {
        int(item["physical_qubit"]): float(item["error"])
        for item in record.get("measurements", [])
    }
    missing = [qubit for qubit in measured_physical if qubit not in by_physical]
    if missing:
        raise ValueError(
            "manifest is missing readout errors for measured physical qubits "
            + ", ".join(str(qubit) for qubit in missing)
        )
    probabilities = [by_physical[qubit] for qubit in measured_physical]
    return {
        "case": case,
        "qpy": qpy_record,
        "physical_qubits_by_classical_bit": measured_physical,
        "readout_error_probabilities": probabilities,
        "max_readout_error": max(probabilities),
        "mean_readout_error": float(np.mean(probabilities)),
        "calibration_set_id": manifest.get("calibration_set_id"),
        "quantum_computer": manifest.get("quantum_computer"),
        "source": str(manifest_path),
        "assumption": "manifest scalar readout error used as symmetric P(0<->1)",
    }


def response_matrix_from_calibration_records(
    records: Iterable[dict[str, Any]],
    *,
    n_bits: int,
) -> np.ndarray:
    """Build ``M[measured,true]`` from known-syndrome calibration count records."""
    matrix = np.zeros((2**n_bits, 2**n_bits), dtype=float)
    seen: set[int] = set()
    for record in records:
        true = int(record["true_syndrome"])
        if not 0 <= true < 2**n_bits:
            raise ValueError(f"true syndrome {true} is outside the {n_bits}-bit range")
        counts = record["raw_counts"] if "raw_counts" in record else record["counts"]
        probabilities, _ = counts_to_probability_vector(counts, n_bits)
        matrix[:, true] = probabilities
        seen.add(true)
    expected = set(range(2**n_bits))
    if seen != expected:
        missing = sorted(expected - seen)
        raise ValueError(f"calibration records do not cover all true syndromes: {missing}")
    return matrix
