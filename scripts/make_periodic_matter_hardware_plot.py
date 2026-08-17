#!/usr/bin/env python3
"""Plot the reduced periodic matter-only IQM hardware result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


RAW_METHOD = "raw"
MITIGATED_METHOD = "readout_mitigated_manifest_symmetric"

METHOD_LABELS = {
    RAW_METHOD: "raw hardware",
    MITIGATED_METHOD: "readout mitigated",
}
METHOD_COLORS = {
    RAW_METHOD: "#546E7A",
    MITIGATED_METHOD: "#1565C0",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rows_by_method_and_case(summary: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for row in summary["table"]:
        grouped.setdefault(row["method"], {})[row["case"]] = row
    return grouped


def _resource_text(summary: dict[str, Any], joint_manifest: dict[str, Any] | None) -> str:
    resources = summary.get("resources", {})
    native_cz = resources.get("native_cz_count", "?")
    native_depth = resources.get("native_depth", "?")
    if not joint_manifest:
        return f"Reduced matter circuit: {native_cz} native CZ, depth {native_depth}"
    old_cz = joint_manifest.get("maximum_native_cz_count", "?")
    old_depth = joint_manifest.get("maximum_native_depth", "?")
    try:
        reduction = 100.0 * (float(old_cz) - float(native_cz)) / float(old_cz)
        reduction_text = f"{reduction:.1f}% fewer CZ"
    except (TypeError, ValueError, ZeroDivisionError):
        reduction_text = "fewer CZ"
    return (
        f"Reduced matter circuit: {native_cz} CZ, depth {native_depth}; "
        f"previous joint readout: {old_cz} CZ, depth {old_depth} ({reduction_text})"
    )


def plot(
    summary: dict[str, Any],
    output_dir: Path,
    output_stem: str,
    *,
    joint_manifest: dict[str, Any] | None = None,
) -> list[Path]:
    grouped = rows_by_method_and_case(summary)
    cases = ["Wplus", "Wminus"]
    methods = [RAW_METHOD, MITIGATED_METHOD]
    x = np.arange(len(cases), dtype=float)
    width = 0.32

    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.labelsize": 12,
            "legend.fontsize": 10,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.35), gridspec_kw={"wspace": 0.34})
    ax_obs, ax_sep = axes

    for offset, method in [(-width / 2, RAW_METHOD), (width / 2, MITIGATED_METHOD)]:
        values = [float(grouped[method][case]["imbalance"]) for case in cases]
        errors = [float(grouped[method][case]["imbalance_se"]) for case in cases]
        ax_obs.bar(
            x + offset,
            values,
            width,
            yerr=errors,
            capsize=3.5,
            color=METHOD_COLORS[method],
            alpha=0.86,
            label=METHOD_LABELS[method],
        )

    ideal = summary["ideal_reference"]
    trotter_values = [
        float(ideal["trotter_Wplus_imbalance"]),
        float(ideal["trotter_Wminus_imbalance"]),
    ]
    ax_obs.scatter(
        x,
        trotter_values,
        marker="D",
        s=58,
        color="#D32F2F",
        edgecolor="black",
        linewidth=0.4,
        label="ideal Trotter",
        zorder=5,
    )
    ax_obs.set(
        xticks=x,
        xticklabels=[r"$W=+1$", r"$W=-1$"],
        ylabel=r"$O_{\rm LR}$",
        title="Matter response by Wilson sector",
    )
    ax_obs.axhline(0.0, color="0.25", linewidth=0.8)
    ax_obs.grid(axis="y", alpha=0.22)
    ax_obs.legend(frameon=False)

    sep_x = np.arange(len(methods), dtype=float)
    sep_values = [
        float(summary["separations"][method]["Wplus_minus_Wminus"]) for method in methods
    ]
    sep_errors = [
        float(summary["separations"][method]["combined_standard_error"]) for method in methods
    ]
    ax_sep.bar(
        sep_x,
        sep_values,
        yerr=sep_errors,
        capsize=4,
        color=[METHOD_COLORS[method] for method in methods],
        alpha=0.9,
    )
    trotter_sep = float(ideal["trotter_sector_separation"])
    ax_sep.axhline(
        trotter_sep,
        color="#D32F2F",
        linestyle="--",
        linewidth=1.4,
        label=rf"ideal Trotter $\Delta={trotter_sep:.3f}$",
    )
    for xpos, method, value in zip(sep_x, methods, sep_values, strict=True):
        z_score = float(summary["separations"][method]["z_score"])
        fraction = 100.0 * float(summary["separations"][method]["fraction_of_trotter_separation"])
        ax_sep.text(
            xpos,
            value + sep_errors[int(xpos)] + 0.008,
            f"{z_score:.1f}σ\n{fraction:.0f}% ideal",
            ha="center",
            va="bottom",
            fontsize=9.5,
        )
    ax_sep.set(
        xticks=sep_x,
        xticklabels=[METHOD_LABELS[method].replace(" ", "\n") for method in methods],
        ylabel=rf"$\Delta O_{{\rm LR}}=O_{{+}}-O_{{-}}$",
        title="Resolved hardware sector separation",
    )
    ax_sep.set_ylim(0.0, max(trotter_sep * 1.25, max(sep_values) + 0.06))
    ax_sep.grid(axis="y", alpha=0.22)
    ax_sep.legend(frameon=False, loc="upper right")

    fig.suptitle(
        "IQM Emerald reduced periodic matter readout: hardware data only",
        fontsize=14.5,
        y=1.03,
    )
    fig.text(
        0.5,
        -0.01,
        _resource_text(summary, joint_manifest),
        ha="center",
        va="top",
        fontsize=10,
        color="0.35",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        output_dir / f"{output_stem}.pdf",
        output_dir / f"{output_stem}.png",
    ]
    fig.savefig(paths[0], bbox_inches="tight")
    fig.savefig(paths[1], dpi=220, bbox_inches="tight")
    plt.close(fig)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("results/processed/periodic_iqm_matter_readout_mitigation_5000.json"),
    )
    parser.add_argument(
        "--joint-manifest",
        type=Path,
        default=Path("results/iqm/emerald_periodic_candidate_5000_seed1/readiness_manifest.json"),
        help="optional previous joint-readout manifest for resource comparison",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("figures"))
    parser.add_argument("--output-stem", default="fig11_periodic_iqm_matter_readout_5000")
    args = parser.parse_args()

    joint_manifest = load_json(args.joint_manifest) if args.joint_manifest.exists() else None
    for path in plot(
        load_json(args.input),
        args.output_dir,
        args.output_stem,
        joint_manifest=joint_manifest,
    ):
        print(path)


if __name__ == "__main__":
    main()
