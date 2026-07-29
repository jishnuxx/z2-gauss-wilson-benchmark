"""Reusable simulator-only open-chain workflow."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from .analysis import analyze_counts, count_expectation
from .bitstrings import canonical_counts, save_counts
from .circuits import (
    export_circuit,
    ideal_counts,
    ideal_statevector,
    resource_metrics,
    trotter_circuit,
)
from .ed import benchmark, evolve
from .gauss import commutator_norms, localized_imbalance_bits
from .model import Z2Model
from .noise import NoiseConfig, noisy_counts
from .observables import OBSERVABLES, all_state_expectations
from .plotting import make_openchain_plots


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def run_pipeline(
    *,
    n_sites: int,
    tmax: float,
    dt: float,
    shots: int,
    noise_level: float,
    outdir: Path,
    bootstrap: int = 300,
    seed: int = 12345,
) -> dict:
    """Run ED, ideal statevector/shots, noisy shots, analysis, and plots."""
    outdir = Path(outdir)
    for relative in (
        "data/exact", "data/ideal", "data/noisy", "data/bitstrings", "data/processed", "circuits"
    ):
        (outdir / relative).mkdir(parents=True, exist_ok=True)
    model = Z2Model(n_sites=n_sites)
    initial_bits = localized_imbalance_bits(model)
    times = np.arange(0.0, tmax + 0.5 * dt, dt)
    exact_rows = benchmark(model, initial_bits, times)
    exact_states = evolve(model, initial_bits, times)
    _write_json(outdir / "data/exact/ed_observables.json", exact_rows)

    noise = NoiseConfig(
        single_qubit=noise_level / 5,
        two_qubit=noise_level,
        readout=min(2 * noise_level, 0.25),
    )
    _write_json(outdir / "data/noisy/noise_config.json", vars(noise))
    records: list[dict] = []
    resource_rows: list[dict] = []
    ideal_validation: list[dict] = []
    for index, (time, exact_row, exact_state) in enumerate(
        zip(times, exact_rows, exact_states, strict=True)
    ):
        state_circuit = trotter_circuit(model, initial_bits, float(time), dt, measure=False)
        measured_circuit = trotter_circuit(model, initial_bits, float(time), dt, measure=True)
        circuit_state = ideal_statevector(state_circuit)
        trotter_observables = all_state_expectations(circuit_state, model)
        fidelity = float(abs(np.vdot(exact_state, circuit_state)) ** 2)
        ideal_raw = ideal_counts(measured_circuit, shots, seed + index)
        noisy_raw = noisy_counts(measured_circuit, shots, noise, seed + 1000 + index)
        save_counts(
            outdir / f"data/ideal/t_{index:03d}.json",
            ideal_raw,
            {"time": float(time), "shots": shots, "backend": "AerSimulator_ideal"},
        )
        save_counts(
            outdir / f"data/bitstrings/t_{index:03d}.json",
            noisy_raw,
            {
                "time": float(time),
                "shots": shots,
                "backend": "AerSimulator_noise_model",
                "noise": vars(noise),
            },
        )
        ideal_canonical = canonical_counts(ideal_raw, model.n_qubits)
        noisy_canonical = canonical_counts(noisy_raw, model.n_qubits)
        analysis = analyze_counts(
            noisy_canonical,
            model,
            exact_row,
            n_bootstrap=bootstrap,
            seed=seed + 2000 + index,
        )
        ideal_errors = {
            name: abs(count_expectation(ideal_canonical, model, obs) - exact_row[name])
            for name, obs in OBSERVABLES.items()
        }
        ideal_validation.append(
            {
                "time": float(time),
                "statevector_fidelity": fidelity,
                "trotter_observable_error": {
                    name: abs(trotter_observables[name] - exact_row[name]) for name in OBSERVABLES
                },
                "ideal_shot_observable_error": ideal_errors,
            }
        )
        metrics = resource_metrics(measured_circuit)
        resource_rows.append({"time": float(time), **metrics})
        records.append({"time": float(time), "analysis": analysis})

    final_circuit = trotter_circuit(model, initial_bits, float(times[-1]), dt, measure=True)
    exported = export_circuit(
        final_circuit,
        outdir / f"circuits/qasm/z2_{model.n_qubits}q_tmax",
        qpy_stem=outdir / f"circuits/qiskit/z2_{model.n_qubits}q_tmax",
    )
    _write_json(outdir / "data/processed/analysis.json", records)
    _write_json(outdir / "data/processed/ideal_validation.json", ideal_validation)
    with (outdir / "data/processed/circuit_resource_table.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(resource_rows[0]))
        writer.writeheader()
        writer.writerows(resource_rows)
    plots = make_openchain_plots(records, outdir / "plots/open_chain")

    mean_errors = {
        name: {
            "raw": float(np.mean([record["analysis"][name]["delta_raw"] for record in records])),
            "postselected": float(
                np.mean([record["analysis"][name]["delta_postselected"] for record in records])
            ),
        }
        for name in OBSERVABLES
        if name != "gauss_violation_rate"
    }
    improvement = {
        name: errors["postselected"] < errors["raw"] for name, errors in mean_errors.items()
    }
    summary = {
        "n_sites": n_sites,
        "n_qubits": model.n_qubits,
        "initial_bits_q0_first": initial_bits,
        "hermiticity_error": float(
            np.linalg.norm(model.hamiltonian_matrix() - model.hamiltonian_matrix().conj().T)
        ),
        "commutator_norms": commutator_norms(model),
        "max_norm_error": max(abs(row["norm"] - 1.0) for row in exact_rows),
        "minimum_statevector_fidelity": min(row["statevector_fidelity"] for row in ideal_validation),
        "mean_observable_errors": mean_errors,
        "postselection_improves_mean_error": improvement,
        "noisy_postselection_gate_passed": any(improvement.values()),
        "hardware_readiness_certified": False,
        "hardware_readiness_note": (
            "Simulator evidence exists, but tests and frozen measurement/circuit hashes must be "
            "recorded in a readiness manifest before the IQM wrapper can be enabled."
        ),
        "hardware_submitted": False,
        "exported_circuits": exported,
        "plots": [str(path) for path in plots],
    }
    _write_json(outdir / "run_summary.json", summary)
    return summary
