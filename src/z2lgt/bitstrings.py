"""Canonical bitstring conversion, persistence, and Gauss post-selection."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .gauss import is_physical, violation_pattern
from .model import Z2Model


def qiskit_key_to_bits(key: str, n_qubits: int) -> tuple[int, ...]:
    """Convert Qiskit's qN-1..q0 key to canonical q0..qN-1 bits."""
    compact = key.replace(" ", "")
    if len(compact) != n_qubits or set(compact) - {"0", "1"}:
        raise ValueError(f"invalid {n_qubits}-qubit count key: {key!r}")
    return tuple(int(char) for char in reversed(compact))


def bits_to_qiskit_key(bits: tuple[int, ...] | list[int]) -> str:
    return "".join(str(bit) for bit in reversed(bits))


def canonical_counts(counts: dict[str, int], n_qubits: int) -> dict[tuple[int, ...], int]:
    return {qiskit_key_to_bits(key, n_qubits): int(value) for key, value in counts.items()}


def postselect_counts(
    counts: dict[tuple[int, ...], int], model: Z2Model
) -> dict[tuple[int, ...], int]:
    return {bits: count for bits, count in counts.items() if is_physical(bits, model)}


def violation_histogram(
    counts: dict[tuple[int, ...], int], model: Z2Model
) -> dict[str, int]:
    histogram: Counter[str] = Counter()
    for bits, count in counts.items():
        histogram[violation_pattern(bits, model)] += count
    return dict(sorted(histogram.items()))


def save_counts(path: Path, counts: dict[str, int], metadata: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"metadata": metadata or {}, "counts_qiskit_order": counts}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def load_counts(path: Path) -> tuple[dict[str, int], dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["counts_qiskit_order"], payload.get("metadata", {})

