"""Configurable local depolarizing and symmetric readout noise."""

from __future__ import annotations

from dataclasses import dataclass

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error


@dataclass(frozen=True)
class NoiseConfig:
    single_qubit: float = 0.001
    two_qubit: float = 0.005
    readout: float = 0.01

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if not 0 <= value < 1:
                raise ValueError(f"{name} must lie in [0,1)")


def make_noise_model(config: NoiseConfig) -> NoiseModel:
    model = NoiseModel()
    if config.single_qubit:
        error = depolarizing_error(config.single_qubit, 1)
        model.add_all_qubit_quantum_error(error, ["x", "sx", "rz", "id"])
    if config.two_qubit:
        model.add_all_qubit_quantum_error(
            depolarizing_error(config.two_qubit, 2), ["cx"]
        )
    if config.readout:
        p = config.readout
        model.add_all_qubit_readout_error(ReadoutError([[1 - p, p], [p, 1 - p]]))
    return model


def noisy_counts(
    circuit: QuantumCircuit,
    shots: int,
    config: NoiseConfig,
    seed: int = 12345,
    optimization_level: int = 1,
) -> dict[str, int]:
    backend = AerSimulator(noise_model=make_noise_model(config))
    compiled = transpile(
        circuit,
        backend,
        optimization_level=optimization_level,
        seed_transpiler=seed,
    )
    result = backend.run(compiled, shots=shots, seed_simulator=seed).result()
    return dict(result.get_counts())
