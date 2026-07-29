"""Slide-ready matplotlib figures for the Gauss/string blind-spot result."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


CASE_ORDER = ("no_error", "gauge_violating", "gauge_preserving_string")
CASE_LABELS = {
    "no_error": "No error",
    "gauge_violating": "Gauge-violating\n$Z_0$",
    "gauge_preserving_string": "Gauge-preserving\nstring $X_0$",
}
TABLE_LABELS = {
    "no_error": "No error",
    "gauge_violating": "Gauge-violating Z0",
    "gauge_preserving_string": "Gauge-preserving string X0",
}
MODE_STYLE = {
    "ideal": {"marker": "o", "color": "#1768AC", "label": "Ideal"},
    "noisy": {"marker": "s", "color": "#D1495B", "label": "Noisy"},
    "iqm": {"marker": "D", "color": "#3A7D44", "label": "IQM"},
}


def _records(summary: dict, mode: str) -> dict[str, dict]:
    return {row["error_type"]: row for row in summary["datasets"][mode]["records"]}


def _save(fig, output_dir: Path, stem: str) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = [output_dir / f"{stem}.pdf", output_dir / f"{stem}.png"]
    fig.savefig(paths[0], bbox_inches="tight")
    fig.savefig(paths[1], dpi=220, bbox_inches="tight")
    plt.close(fig)
    return paths


def algebraic_summary(summary: dict, output_dir: Path) -> list[Path]:
    records = _records(summary, "ideal")
    values = np.array(
        [
            [records[case]["analysis"]["P_Gauss"], records[case]["analysis"]["string_sector_correct_probability"]]
            for case in CASE_ORDER
        ]
    )
    fig, ax = plt.subplots(figsize=(10.2, 3.6))
    ax.axis("off")
    table_text = []
    for index, case in enumerate(CASE_ORDER):
        p_g, p_w = values[index]
        table_text.append(
            [
                TABLE_LABELS[case],
                f"{'PASS' if p_g > 0.5 else 'FAIL'}  ({p_g:.3f})",
                f"{'CORRECT' if p_w > 0.5 else 'WRONG'}  ({p_w:.3f})",
                (
                    "target state" if case == "no_error" else
                    "detected locally" if case == "gauge_violating" else
                    "Gauss-only blind spot"
                ),
            ]
        )
    table = ax.table(
        cellText=table_text,
        colLabels=("Injected case", "Local Gauss checks", "Wilson sector", "Diagnosis"),
        cellLoc="center",
        colLoc="center",
        loc="center",
        colWidths=(0.27, 0.22, 0.22, 0.25),
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.8)
    table.scale(1.0, 1.8)
    for column in range(4):
        table[(0, column)].set_facecolor("#263238")
        table[(0, column)].set_text_props(color="white", weight="bold")
    for row in range(1, 4):
        table[(row, 0)].set_facecolor("#EAF2F8")
        for column in (1, 2):
            text = table[(row, column)].get_text().get_text()
            table[(row, column)].set_facecolor("#E8F5E9" if ("PASS" in text or "CORRECT" in text) else "#FDECEC")
    ax.set_title("Gauss-law checks do not certify the Wilson-loop sector", weight="bold", pad=10)
    return _save(fig, output_dir, "fig01_algebraic_blindspot_summary")


def gauss_vs_string(summary: dict, output_dir: Path) -> list[Path]:
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    offsets = {"no_error": (-10, 9), "gauge_violating": (8, 9), "gauge_preserving_string": (-10, 8)}
    for mode, dataset in summary["datasets"].items():
        if mode not in MODE_STYLE or not dataset.get("records"):
            continue
        style = MODE_STYLE[mode]
        for record in dataset["records"]:
            analysis = record["analysis"]
            ax.errorbar(
                analysis["P_Gauss"],
                analysis["wilson_expectation"],
                xerr=analysis["P_Gauss_se"],
                yerr=analysis["wilson_expectation_se"],
                marker=style["marker"],
                color=style["color"],
                markersize=8,
                capsize=3,
                linestyle="none",
                label=style["label"] if record["error_type"] == "no_error" else None,
                zorder=3,
            )
            if mode == "ideal":
                ax.annotate(
                    CASE_LABELS[record["error_type"]].replace("\n", " "),
                    (analysis["P_Gauss"], analysis["wilson_expectation"]),
                    xytext=offsets[record["error_type"]],
                    textcoords="offset points",
                    fontsize=9,
                    ha="right" if offsets[record["error_type"]][0] < 0 else "left",
                )
    ax.axvspan(0.9, 1.02, color="#FDECEC", alpha=0.8, zorder=0)
    ax.text(0.94, -0.55, "Gauss pass,\nwrong string sector", color="#9C2335", ha="center", weight="bold")
    ax.axhline(0, color="0.75", linewidth=1)
    ax.set(
        xlabel=r"joint local-check pass probability $P_{\rm Gauss}$",
        ylabel=r"Wilson-loop expectation $\langle W\rangle$",
        xlim=(-0.05, 1.05),
        ylim=(-1.16, 1.16),
        title="The blind spot of Gauss-only syndrome extraction",
    )
    ax.legend(
        title="Result source",
        frameon=True,
        facecolor="white",
        edgecolor="0.45",
        framealpha=0.95,
        loc="center left",
        fontsize=10.5,
        title_fontsize=10.5,
        borderpad=0.55,
        labelspacing=0.45,
    )
    ax.grid(alpha=0.22)
    return _save(fig, output_dir, "fig02_gauss_vs_string_blindspot")


def postselection_acceptance(summary: dict, output_dir: Path) -> list[Path]:
    noisy = _records(summary, "noisy")
    values = np.array(
        [
            [
                1.0,
                noisy[case]["analysis"]["P_Gauss"],
                noisy[case]["analysis"]["gauss_plus_string_acceptance"],
            ]
            for case in CASE_ORDER
        ]
    )
    x = np.arange(3)
    width = 0.23
    colors = ("#9E9E9E", "#1768AC", "#D1495B")
    labels = ("All shots", "Gauss-only", "Gauss + string")
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    for index in range(3):
        bars = ax.bar(x + (index - 1) * width, values[:, index], width, label=labels[index], color=colors[index])
        ax.bar_label(bars, fmt="%.2f", padding=2, fontsize=8)
    ax.set_xticks(x, [CASE_LABELS[case] for case in CASE_ORDER])
    ax.set(
        ylabel="acceptance fraction",
        ylim=(0, 1.12),
        title="String-aware selection rejects the Gauss-preserving error",
    )
    ax.legend(frameon=False, ncols=3, loc="upper center")
    ax.grid(axis="y", alpha=0.22)
    return _save(fig, output_dir, "fig03_postselection_gauss_vs_stringaware")


def syndrome_response(summary: dict, output_dir: Path) -> list[Path]:
    mode = "iqm" if "iqm" in summary["datasets"] and summary["datasets"]["iqm"].get("response") else "noisy"
    matrix = np.asarray(summary["datasets"][mode]["response"]["matrix_measured_given_true"])
    fig, ax = plt.subplots(figsize=(6.8, 5.8))
    image = ax.imshow(matrix, origin="lower", vmin=0, vmax=1, cmap="magma", aspect="equal")
    ticks = np.arange(0, 16, 2)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set(
        xlabel="true joint syndrome index",
        ylabel="measured joint syndrome index",
        title=f"Syndrome response matrix ({mode})",
    )
    cbar = fig.colorbar(image, ax=ax, pad=0.02)
    cbar.set_label(r"$P(s_{\rm meas}\mid s_{\rm true})$")
    return _save(fig, output_dir, "fig04_syndrome_response_matrix")


def depth_scaling(summary: dict, output_dir: Path) -> list[Path]:
    fig, ax = plt.subplots(figsize=(6.8, 4.7))
    for mode in ("ideal", "noisy"):
        records = summary["datasets"][mode]["depth_scan"]
        style = MODE_STYLE[mode]
        x = [row["idle_layers"] for row in records]
        y = [row["analysis"]["gauss_plus_string_acceptance"] for row in records]
        error = [row["analysis"]["gauss_plus_string_acceptance_se"] for row in records]
        ax.errorbar(x, y, yerr=error, marker=style["marker"], color=style["color"], capsize=3, label=style["label"])
    ax.set(
        xlabel="inserted identity layers",
        ylabel="correct joint syndrome probability",
        ylim=(0, 1.04),
        title="Diagnostic quality versus inserted circuit depth",
    )
    ax.grid(alpha=0.22)
    ax.legend(frameon=False)
    return _save(fig, output_dir, "fig05_check_weight_or_depth_scaling")


def make_blindspot_plots(summary: dict, output_dir: Path = Path("figures")) -> list[Path]:
    paths = []
    for function in (algebraic_summary, gauss_vs_string, postselection_acceptance, syndrome_response, depth_scaling):
        paths.extend(function(summary, output_dir))
    return paths
