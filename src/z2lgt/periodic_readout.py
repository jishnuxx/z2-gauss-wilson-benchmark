"""Joint Gauss, Wilson, and matter readout for the periodic benchmark."""

from __future__ import annotations

import math

import numpy as np
from qiskit import QuantumCircuit

from .periodic_circuits import periodic_trotter_circuit
from .periodic_model import PeriodicZ2Model


N_DATA = 8
GAUSS_ANCILLAS = (8, 9, 10)
WILSON_ANCILLA = 11
N_QUBITS_WITH_ANCILLAS = 12
N_CLASSICAL_BITS = 8
WILSON_MATTER_ANCILLA = 8
N_WILSON_MATTER_QUBITS = 9
N_WILSON_MATTER_CLASSICAL_BITS = 5
N_MATTER_CLASSICAL_BITS = 4


def periodic_matter_readout_circuit(
    time: float = 0.8,
    dt: float = 0.4,
    *,
    wilson_sector: int = 1,
    model: PeriodicZ2Model | None = None,
) -> QuantumCircuit:
    r"""Measure only the matter occupations after periodic evolution.

    This is the shallowest dynamics-readout circuit for the observable
    \(O_{\rm LR}=(n_0+n_1-n_2-n_3)/2\).  It does not provide shot-level Gauss or
    Wilson diagnostics; those must be run as separate certification circuits.
    """
    model = model or PeriodicZ2Model()
    data = periodic_trotter_circuit(
        time,
        dt,
        model,
        wilson_sector=wilson_sector,
    )
    circuit = QuantumCircuit(N_DATA, N_MATTER_CLASSICAL_BITS, name=f"periodic_matter_W{'plus' if wilson_sector == 1 else 'minus'}")
    circuit.compose(data, qubits=range(N_DATA), inplace=True)
    circuit.barrier()
    for site in range(model.n_sites):
        circuit.measure(model.matter_qubit(site), site)
    return circuit


def periodic_wilson_matter_readout_circuit(
    time: float = 0.8,
    dt: float = 0.4,
    *,
    wilson_sector: int = 1,
    model: PeriodicZ2Model | None = None,
) -> QuantumCircuit:
    """Measure matter occupations and the Wilson loop, but not Gauss checks."""
    model = model or PeriodicZ2Model()
    data = periodic_trotter_circuit(
        time,
        dt,
        model,
        wilson_sector=wilson_sector,
    )
    circuit = QuantumCircuit(
        N_WILSON_MATTER_QUBITS,
        N_WILSON_MATTER_CLASSICAL_BITS,
        name=f"periodic_wilson_matter_W{'plus' if wilson_sector == 1 else 'minus'}",
    )
    circuit.compose(data, qubits=range(N_DATA), inplace=True)
    circuit.barrier()
    circuit.h(WILSON_MATTER_ANCILLA)
    for link in range(model.n_links):
        circuit.cx(WILSON_MATTER_ANCILLA, model.link_qubit(link))
    circuit.h(WILSON_MATTER_ANCILLA)
    circuit.barrier()
    for site in range(model.n_sites):
        circuit.measure(model.matter_qubit(site), site)
    circuit.measure(WILSON_MATTER_ANCILLA, 4)
    return circuit


def periodic_joint_readout_circuit(
    time: float = 0.8,
    dt: float = 0.4,
    *,
    wilson_sector: int = 1,
    model: PeriodicZ2Model | None = None,
) -> QuantumCircuit:
    """Measure matter Z, G0..G2, and W in one static circuit.

    Classical bits ``c0..c3`` store matter occupations, ``c4..c6`` store
    Gauss violation bits, and ``c7`` stores the Wilson violation bit.  ``G3``
    is inferred in analysis using ``prod_s G_s = prod_i Z_mi``.
    """
    model = model or PeriodicZ2Model()
    data = periodic_trotter_circuit(
        time,
        dt,
        model,
        wilson_sector=wilson_sector,
    )
    circuit = QuantumCircuit(
        N_QUBITS_WITH_ANCILLAS,
        N_CLASSICAL_BITS,
        name=f"periodic_joint_W{'plus' if wilson_sector == 1 else 'minus'}",
    )
    circuit.compose(data, qubits=range(N_DATA), inplace=True)
    circuit.barrier()

    for check_index, ancilla in enumerate(GAUSS_ANCILLAS):
        for qubit, symbol in enumerate(model.gauss_checks[check_index].word):
            if symbol == "Z":
                circuit.cx(qubit, ancilla)

    circuit.h(WILSON_ANCILLA)
    for link in range(model.n_links):
        circuit.cx(WILSON_ANCILLA, model.link_qubit(link))
    circuit.h(WILSON_ANCILLA)
    circuit.barrier()

    for site in range(model.n_sites):
        circuit.measure(model.matter_qubit(site), site)
    for check_index, ancilla in enumerate(GAUSS_ANCILLAS):
        circuit.measure(ancilla, 4 + check_index)
    circuit.measure(WILSON_ANCILLA, 7)
    return circuit


def canonical_periodic_readout_bits(key: str) -> tuple[int, ...]:
    """Convert Qiskit's c7..c0 count key to canonical c0..c7 bits."""
    compact = key.replace(" ", "")
    if len(compact) != N_CLASSICAL_BITS or set(compact) - {"0", "1"}:
        raise ValueError(f"expected an eight-bit count key, got {key!r}")
    return tuple(int(bit) for bit in reversed(compact))


def canonical_matter_readout_bits(key: str) -> tuple[int, int, int, int]:
    """Convert Qiskit's c3..c0 count key to canonical matter bits c0..c3."""
    compact = key.replace(" ", "")
    if len(compact) != N_MATTER_CLASSICAL_BITS or set(compact) - {"0", "1"}:
        raise ValueError(f"expected a four-bit matter count key, got {key!r}")
    return tuple(int(bit) for bit in reversed(compact))


def canonical_wilson_matter_readout_bits(key: str) -> tuple[int, int, int, int, int]:
    """Convert Qiskit's c4..c0 count key to canonical matter bits plus Wilson bit."""
    compact = key.replace(" ", "")
    if len(compact) != N_WILSON_MATTER_CLASSICAL_BITS or set(compact) - {"0", "1"}:
        raise ValueError(f"expected a five-bit Wilson/matter count key, got {key!r}")
    return tuple(int(bit) for bit in reversed(compact))


def _reported_shots(total: float) -> int | float:
    rounded = round(total)
    return int(rounded) if math.isclose(total, rounded, rel_tol=0.0, abs_tol=1e-9) else total


def _imbalance_from_matter_bits(m0: int, m1: int, m2: int, m3: int) -> float:
    return (m0 + m1 - m2 - m3) / 2.0


def analyze_matter_counts(counts: dict[str, int | float]) -> dict[str, object]:
    r"""Extract \(O_{\rm LR}\) from matter-only shot counts."""
    shot_weight = float(sum(counts.values()))
    if shot_weight <= 0:
        raise ValueError("counts must contain at least one shot")
    imbalance_sum = 0.0
    imbalance_square_sum = 0.0
    for key, count in counts.items():
        imbalance = _imbalance_from_matter_bits(*canonical_matter_readout_bits(key))
        imbalance_sum += float(count) * imbalance
        imbalance_square_sum += float(count) * imbalance**2
    imbalance_mean = imbalance_sum / shot_weight
    sample_variance = max(0.0, imbalance_square_sum / shot_weight - imbalance_mean**2)
    return {
        "shots": _reported_shots(shot_weight),
        "imbalance": imbalance_mean,
        "imbalance_se": math.sqrt(sample_variance / shot_weight),
    }


def analyze_wilson_matter_counts(counts: dict[str, int | float]) -> dict[str, object]:
    r"""Extract \(O_{\rm LR}\) and \(\langle W\rangle\) from Wilson/matter counts."""
    shot_weight = float(sum(counts.values()))
    if shot_weight <= 0:
        raise ValueError("counts must contain at least one shot")
    imbalance_sum = 0.0
    imbalance_square_sum = 0.0
    wilson_sum = 0.0
    wilson_target = 0.0
    for key, count in counts.items():
        m0, m1, m2, m3, w = canonical_wilson_matter_readout_bits(key)
        imbalance = _imbalance_from_matter_bits(m0, m1, m2, m3)
        imbalance_sum += float(count) * imbalance
        imbalance_square_sum += float(count) * imbalance**2
        wilson_sum += float(count) * (1 - 2 * w)
        wilson_target += float(count) * (w == 0)
    imbalance_mean = imbalance_sum / shot_weight
    sample_variance = max(0.0, imbalance_square_sum / shot_weight - imbalance_mean**2)
    return {
        "shots": _reported_shots(shot_weight),
        "imbalance": imbalance_mean,
        "imbalance_se": math.sqrt(sample_variance / shot_weight),
        "wilson_expectation": wilson_sum / shot_weight,
        "wilson_target_probability": wilson_target / shot_weight,
    }


def analyze_periodic_joint_counts(counts: dict[str, int]) -> dict[str, object]:
    """Extract joint diagnostics and matter imbalance from shot counts."""
    shot_weight = float(sum(counts.values()))
    if shot_weight <= 0:
        raise ValueError("counts must contain at least one shot")
    gauss_pass = 0
    joint_pass = 0
    w_sum = 0.0
    imbalance_sum = 0.0
    imbalance_square_sum = 0.0
    gauss_selected_sum = 0.0
    joint_selected_sum = 0.0
    gauss_sums = np.zeros(4, dtype=float)

    for key, count in counts.items():
        m0, m1, m2, m3, g0, g1, g2, w = canonical_periodic_readout_bits(key)
        matter_parity = m0 ^ m1 ^ m2 ^ m3
        g3 = matter_parity ^ g0 ^ g1 ^ g2
        gauss_bits = (g0, g1, g2, g3)
        is_gauss = not any(gauss_bits)
        is_target_w = w == 0
        imbalance = _imbalance_from_matter_bits(m0, m1, m2, m3)

        gauss_pass += count * is_gauss
        joint_pass += count * (is_gauss and is_target_w)
        w_sum += count * (1 - 2 * w)
        gauss_sums += count * np.asarray([1 - 2 * bit for bit in gauss_bits])
        imbalance_sum += count * imbalance
        imbalance_square_sum += count * imbalance**2
        if is_gauss:
            gauss_selected_sum += count * imbalance
        if is_gauss and is_target_w:
            joint_selected_sum += count * imbalance

    p_gauss = gauss_pass / shot_weight
    p_joint = joint_pass / shot_weight
    imbalance_mean = imbalance_sum / shot_weight
    sample_variance = max(0.0, imbalance_square_sum / shot_weight - imbalance_mean**2)
    return {
        "shots": _reported_shots(shot_weight),
        "P_Gauss": p_gauss,
        "P_Gauss_se": math.sqrt(p_gauss * (1 - p_gauss) / shot_weight),
        "gauss_expectations": {
            f"G{index}": float(value / shot_weight)
            for index, value in enumerate(gauss_sums)
        },
        "wilson_expectation": w_sum / shot_weight,
        "wilson_target_probability": sum(
            count
            for key, count in counts.items()
            if canonical_periodic_readout_bits(key)[7] == 0
        )
        / shot_weight,
        "imbalance": imbalance_mean,
        "imbalance_se": math.sqrt(sample_variance / shot_weight),
        "gauss_only_acceptance": p_gauss,
        "gauss_plus_wilson_acceptance": p_joint,
        "gauss_only_imbalance": (
            gauss_selected_sum / gauss_pass if gauss_pass else None
        ),
        "gauss_plus_wilson_imbalance": (
            joint_selected_sum / joint_pass if joint_pass else None
        ),
    }
