"""Synthetic noisy simulation of periodic joint diagnostic circuits."""

from __future__ import annotations

from dataclasses import asdict

from .circuits import resource_metrics
from .noise import NoiseConfig, noisy_counts
from .periodic_readout import (
    analyze_periodic_joint_counts,
    periodic_joint_readout_circuit,
)


def run_periodic_noisy_readout(
    *,
    time: float = 0.8,
    dt: float = 0.4,
    shots: int = 20_000,
    seed: int = 35791,
    noise_config: NoiseConfig | None = None,
) -> dict[str, object]:
    """Run both conserved sectors under a transparent local noise model."""
    if shots <= 0:
        raise ValueError("shots must be positive")
    config = noise_config or NoiseConfig(
        single_qubit=0.001,
        two_qubit=0.01,
        readout=0.02,
    )
    records = []
    for offset, (sector, label) in enumerate(((1, "Wplus"), (-1, "Wminus"))):
        circuit = periodic_joint_readout_circuit(
            time,
            dt,
            wilson_sector=sector,
        )
        counts = noisy_counts(
            circuit,
            shots,
            config,
            seed + offset,
            optimization_level=1,
        )
        records.append(
            {
                "case": label,
                "wilson_sector": sector,
                "raw_counts": counts,
                "analysis": analyze_periodic_joint_counts(counts),
                "resources": resource_metrics(circuit),
            }
        )
    return {
        "schema_version": 1,
        "mode": "synthetic_noisy_aer",
        "time": time,
        "dt": dt,
        "shots": shots,
        "seed": seed,
        "noise_config": asdict(config),
        "records": records,
    }
