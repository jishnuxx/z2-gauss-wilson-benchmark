"""Count-level analysis for joint Gauss and Wilson-loop diagnostics."""

from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np


def canonical_syndrome_bits(key: str) -> tuple[int, int, int, int]:
    """Convert Qiskit's c3..c0 display order to canonical q0..q3 bits."""
    compact = key.replace(" ", "")
    if len(compact) != 4 or set(compact) - {"0", "1"}:
        raise ValueError(f"expected a four-bit count key, got {key!r}")
    return tuple(int(bit) for bit in reversed(compact))


def syndrome_index(key: str) -> int:
    bits = canonical_syndrome_bits(key)
    return sum(bit << qubit for qubit, bit in enumerate(bits))


def binomial_se(probability: float, shots: int) -> float:
    if shots <= 0:
        return float("nan")
    return math.sqrt(max(0.0, probability * (1.0 - probability) / shots))


def _reported_shots(total: float) -> int | float:
    rounded = round(total)
    return int(rounded) if math.isclose(total, rounded, rel_tol=0.0, abs_tol=1e-9) else total


def filter_counts(counts: dict[str, int], *, require_gauss: bool, require_string: bool) -> dict[str, int]:
    selected: dict[str, int] = {}
    for key, count in counts.items():
        w, g0, g1, g2 = canonical_syndrome_bits(key)
        if require_gauss and (g0 or g1 or g2):
            continue
        if require_string and w:
            continue
        selected[key] = count
    return selected


def analyze_joint_counts(counts: dict[str, int]) -> dict[str, object]:
    shot_weight = float(sum(counts.values()))
    if shot_weight <= 0:
        raise ValueError("counts must contain at least one shot")
    gauss_pass = 0
    string_correct = 0
    joint_pass = 0
    sums = np.zeros(4, dtype=float)
    w_sum = 0.0
    for key, count in counts.items():
        w, g0, g1, g2 = canonical_syndrome_bits(key)
        g3 = g0 ^ g1 ^ g2
        generators = (g0, g1, g2, g3)
        is_gauss = not (g0 or g1 or g2)
        is_string = not w
        gauss_pass += count * is_gauss
        string_correct += count * is_string
        joint_pass += count * (is_gauss and is_string)
        sums += count * np.array([1 - 2 * bit for bit in generators])
        w_sum += count * (1 - 2 * w)
    p_gauss = gauss_pass / shot_weight
    p_string = string_correct / shot_weight
    p_joint = joint_pass / shot_weight
    w_mean = w_sum / shot_weight
    g_means = sums / shot_weight
    return {
        "shots": _reported_shots(shot_weight),
        "P_Gauss": p_gauss,
        "P_Gauss_se": binomial_se(p_gauss, shot_weight),
        "gauss_expectations": {f"G{i}": float(value) for i, value in enumerate(g_means)},
        "wilson_expectation": float(w_mean),
        "wilson_expectation_se": 2 * binomial_se((1 + w_mean) / 2, shot_weight),
        "string_sector_correct_probability": p_string,
        "string_sector_correct_probability_se": binomial_se(p_string, shot_weight),
        "gauss_plus_string_acceptance": p_joint,
        "gauss_plus_string_acceptance_se": binomial_se(p_joint, shot_weight),
        "all_shots_acceptance": 1.0,
        "gauss_only_accepted_shots": gauss_pass,
        "gauss_plus_string_accepted_shots": joint_pass,
    }


def response_matrix(records: Iterable[dict[str, object]]) -> np.ndarray:
    """Return M[measured,true] from records with true_syndrome and counts."""
    matrix = np.zeros((16, 16), dtype=float)
    seen: set[int] = set()
    for record in records:
        true = int(record["true_syndrome"])
        counts = record["counts"]
        total = sum(counts.values())
        if total <= 0:
            raise ValueError(f"empty counts for true syndrome {true}")
        seen.add(true)
        for key, count in counts.items():
            matrix[syndrome_index(key), true] += count / total
    if seen != set(range(16)):
        raise ValueError("response records must cover all 16 true syndromes")
    return matrix


def diagnostic_rows(records: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    interpretations = {
        "no_error": "target state",
        "gauge_violating": "detected by Gauss syndrome",
        "gauge_preserving_string": "blind spot of Gauss-only syndrome",
    }
    rows = []
    for record in records:
        analysis = record["analysis"]
        rows.append(
            {
                "mode": record["mode"],
                "case": record["error_type"],
                "P_Gauss": analysis["P_Gauss"],
                "local_Gauss_checks": "pass" if analysis["P_Gauss"] >= 0.5 else "fail",
                "wilson_expectation": analysis["wilson_expectation"],
                "string_sector": (
                    "correct" if analysis["string_sector_correct_probability"] >= 0.5 else "wrong"
                ),
                "interpretation": interpretations[record["error_type"]],
            }
        )
    return rows
