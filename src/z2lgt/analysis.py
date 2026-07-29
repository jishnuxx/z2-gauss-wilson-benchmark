"""Count-based observables, bootstrap errors, and success metrics."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from .bitstrings import postselect_counts, violation_histogram
from .model import Z2Model
from .observables import OBSERVABLES


def count_expectation(
    counts: dict[tuple[int, ...], int], model: Z2Model, observable: Callable
) -> float:
    total = sum(counts.values())
    if total == 0:
        return float("nan")
    return float(sum(count * observable(bits, model) for bits, count in counts.items()) / total)


def bootstrap_expectation(
    counts: dict[tuple[int, ...], int],
    model: Z2Model,
    observable: Callable,
    *,
    n_bootstrap: int = 300,
    seed: int = 12345,
) -> tuple[float, float]:
    """Return plug-in mean and multinomial bootstrap standard error."""
    total = sum(counts.values())
    mean = count_expectation(counts, model, observable)
    if total == 0 or n_bootstrap < 2:
        return mean, float("nan")
    keys = list(counts)
    probabilities = np.array([counts[key] for key in keys], dtype=float) / total
    values = np.array([observable(key, model) for key in keys], dtype=float)
    rng = np.random.default_rng(seed)
    samples = rng.multinomial(total, probabilities, size=n_bootstrap)
    estimates = samples @ values / total
    return mean, float(np.std(estimates, ddof=1))


def analyze_counts(
    counts: dict[tuple[int, ...], int],
    model: Z2Model,
    exact: dict[str, float],
    *,
    n_bootstrap: int = 300,
    seed: int = 12345,
) -> dict:
    accepted = postselect_counts(counts, model)
    total = sum(counts.values())
    accepted_total = sum(accepted.values())
    row: dict[str, object] = {
        "shots": total,
        "accepted_shots": accepted_total,
        "acceptance": accepted_total / total if total else float("nan"),
        "violation_histogram": violation_histogram(counts, model),
    }
    for offset, (name, observable) in enumerate(OBSERVABLES.items()):
        raw, raw_error = bootstrap_expectation(
            counts, model, observable, n_bootstrap=n_bootstrap, seed=seed + offset
        )
        post, post_error = bootstrap_expectation(
            accepted, model, observable, n_bootstrap=n_bootstrap, seed=seed + 100 + offset
        )
        reference = float(exact[name])
        row[name] = {
            "exact": reference,
            "raw": raw,
            "raw_bootstrap_se": raw_error,
            "postselected": post,
            "postselected_bootstrap_se": post_error,
            "delta_raw": abs(raw - reference),
            "delta_postselected": abs(post - reference),
        }
    return row

