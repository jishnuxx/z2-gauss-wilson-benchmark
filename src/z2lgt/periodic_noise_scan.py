"""Noise-strength scan for the periodic joint-readout benchmark."""

from __future__ import annotations

from collections.abc import Iterable

from .noise import NoiseConfig
from .periodic_circuits import periodic_two_sector_circuit_comparison
from .periodic_noisy_readout import run_periodic_noisy_readout


def run_periodic_noise_scale_scan(
    scales: Iterable[float] = (0.0, 0.25, 0.5, 1.0),
    *,
    time: float = 0.8,
    dt: float = 0.4,
    shots: int = 5000,
    seed: int = 46100,
    baseline: NoiseConfig | None = None,
) -> dict[str, object]:
    """Scale a transparent baseline noise model and summarize both sectors."""
    if shots <= 0:
        raise ValueError("shots must be positive")
    scale_values = tuple(float(scale) for scale in scales)
    if not scale_values or any(scale < 0 for scale in scale_values):
        raise ValueError("scales must be a nonempty sequence of nonnegative values")
    base = baseline or NoiseConfig(0.001, 0.01, 0.02)
    references = {
        int(row["sector"]): float(row["trotter_imbalance"])
        for row in periodic_two_sector_circuit_comparison(
            time,
            dt,
            include_resources=False,
        )
    }

    datasets = []
    summary_rows = []
    for index, scale in enumerate(scale_values):
        config = NoiseConfig(
            base.single_qubit * scale,
            base.two_qubit * scale,
            base.readout * scale,
        )
        payload = run_periodic_noisy_readout(
            time=time,
            dt=dt,
            shots=shots,
            seed=seed + 100 * index,
            noise_config=config,
        )
        payload["noise_scale"] = scale
        datasets.append(payload)
        plus, minus = payload["records"]
        for record in payload["records"]:
            analysis = record["analysis"]
            sector = int(record["wilson_sector"])
            summary_rows.append(
                {
                    "noise_scale": scale,
                    "case": record["case"],
                    "wilson_sector": sector,
                    "P_Gauss": analysis["P_Gauss"],
                    "wilson_expectation": analysis["wilson_expectation"],
                    "imbalance": analysis["imbalance"],
                    "imbalance_abs_error_vs_trotter": abs(
                        analysis["imbalance"] - references[sector]
                    ),
                    "gauss_only_imbalance": analysis["gauss_only_imbalance"],
                    "gauss_plus_wilson_imbalance": analysis[
                        "gauss_plus_wilson_imbalance"
                    ],
                    "gauss_only_acceptance": analysis["gauss_only_acceptance"],
                    "gauss_plus_wilson_acceptance": analysis[
                        "gauss_plus_wilson_acceptance"
                    ],
                    "wilson_contrast": (
                        plus["analysis"]["wilson_expectation"]
                        - minus["analysis"]["wilson_expectation"]
                    ),
                    "target_joint_acceptance": plus["analysis"][
                        "gauss_plus_wilson_acceptance"
                    ],
                    "wrong_sector_false_acceptance": minus["analysis"][
                        "gauss_plus_wilson_acceptance"
                    ],
                }
            )
    return {
        "schema_version": 1,
        "description": "scaled synthetic Aer noise; not IQM calibration",
        "time": time,
        "dt": dt,
        "shots_per_sector_per_scale": shots,
        "baseline_noise_config": {
            "single_qubit": base.single_qubit,
            "two_qubit": base.two_qubit,
            "readout": base.readout,
        },
        "scales": list(scale_values),
        "trotter_references": references,
        "datasets": datasets,
        "summary_rows": summary_rows,
    }
