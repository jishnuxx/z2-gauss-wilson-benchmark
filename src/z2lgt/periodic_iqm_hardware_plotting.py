"""Hardware-only plots for the periodic IQM readout run."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


REQUIRED_COLUMNS = {
    "case",
    "shots",
    "P_Gauss",
    "P_Gauss_se",
    "wilson_expectation",
    "imbalance",
    "imbalance_se",
}


def read_periodic_iqm_hardware_csv(path: Path) -> list[dict[str, float | str]]:
    """Read processed periodic IQM hardware rows."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(
            reader.fieldnames
        ):
            raise ValueError(f"missing required columns in {path}")
        rows: list[dict[str, float | str]] = []
        for row in reader:
            parsed: dict[str, float | str] = {"case": row["case"]}
            for key, value in row.items():
                if key == "case":
                    continue
                parsed[key] = float(value)
            rows.append(parsed)
    cases = [row["case"] for row in rows]
    if cases != ["Wplus", "Wminus"]:
        raise ValueError("expected Wplus then Wminus hardware rows")
    return rows


def plot_periodic_iqm_hardware_readout(
    rows: list[dict[str, float | str]],
    output_dir: Path = Path("figures"),
    *,
    job_id: str | None = None,
    output_stem: str = "fig08_periodic_iqm_hardware_readout",
    title: str = "IQM Emerald periodic readout: hardware data only",
) -> list[Path]:
    """Plot the actual Emerald periodic readout, separate from simulations."""
    if [row.get("case") for row in rows] != ["Wplus", "Wminus"]:
        raise ValueError("expected Wplus then Wminus hardware rows")

    cases = [str(row["case"]) for row in rows]
    x = np.arange(len(cases), dtype=float)
    wilson = np.asarray([float(row["wilson_expectation"]) for row in rows])
    p_gauss = np.asarray([float(row["P_Gauss"]) for row in rows])
    p_gauss_se = np.asarray([float(row["P_Gauss_se"]) for row in rows])
    imbalance = np.asarray([float(row["imbalance"]) for row in rows])
    imbalance_se = np.asarray([float(row["imbalance_se"]) for row in rows])
    raw_separation = float(imbalance[0] - imbalance[1])
    wilson_contrast = float(wilson[0] - wilson[1])
    shot_counts = {int(float(row["shots"])) for row in rows}
    shots_label = (
        f"{next(iter(shot_counts))} shots per sector"
        if len(shot_counts) == 1
        else "mixed shot counts"
    )

    plt.rcParams.update(
        {
            "font.size": 12,
            "axes.titlesize": 15,
            "axes.labelsize": 13,
            "legend.fontsize": 10,
        }
    )
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(10.6, 4.4),
        gridspec_kw={"width_ratios": (1.05, 1.0), "wspace": 0.28},
    )
    ax_w, ax_o = axes

    colors = ["#2E7D32", "#7B1FA2"]
    ax_w.bar(x, wilson, color=colors, width=0.58, alpha=0.92, label=r"$\langle W\rangle$")
    ax_w.errorbar(
        x,
        p_gauss,
        yerr=p_gauss_se,
        color="#111111",
        marker="o",
        linestyle="none",
        capsize=4,
        markersize=6,
        label=r"$P_{\rm Gauss}$",
    )
    ax_w.axhline(0.0, color="0.25", linewidth=1.0)
    ax_w.set(
        xticks=x,
        xticklabels=(r"$W_{\rm target}=+1$", r"$W=-1$ prepared"),
        ylim=(-0.64, 0.55),
        ylabel="measured diagnostic value",
        title="Emerald resolves the Wilson sign",
    )
    ax_w.grid(axis="y", alpha=0.22)
    ax_w.legend(frameon=False, loc="upper center", ncols=2)
    for xpos, value in zip(x, wilson, strict=True):
        va = "bottom" if value >= 0 else "top"
        offset = 0.035 if value >= 0 else -0.035
        ax_w.text(
            xpos,
            value + offset,
            f"{value:+.3f}",
            ha="center",
            va=va,
            fontsize=11,
            color="0.15",
        )
    ax_w.text(
        0.5,
        -0.60,
        rf"Wilson contrast = {wilson_contrast:.3f}",
        ha="center",
        va="bottom",
        fontsize=10.5,
        color="0.25",
    )

    ax_o.bar(x, imbalance, yerr=imbalance_se, capsize=4, color=colors, width=0.58)
    ax_o.axhline(0.0, color="0.25", linewidth=1.0)
    ax_o.set(
        xticks=x,
        xticklabels=("Wplus", "Wminus"),
        ylim=(0.0, max(0.24, float(np.max(imbalance + imbalance_se)) + 0.04)),
        ylabel=r"raw matter imbalance $O_{\rm LR}$",
        title=r"Hardware $O_{\rm LR}$ separation is modest",
    )
    ax_o.grid(axis="y", alpha=0.22)
    for xpos, value, err in zip(x, imbalance, imbalance_se, strict=True):
        ax_o.text(
            xpos,
            value + err + 0.012,
            f"{value:+.4f}",
            ha="center",
            va="bottom",
            fontsize=11,
            color="0.15",
        )
    ax_o.text(
        0.5,
        0.92,
        rf"raw $\Delta O_{{\rm LR}}$ = {raw_separation:.4f}",
        transform=ax_o.transAxes,
        ha="center",
        va="top",
        fontsize=10.5,
        color="0.25",
    )

    fig.suptitle(
        title,
        fontsize=16,
        y=1.02,
    )
    footer = (
        f"Job {job_id}; {shots_label}."
        if job_id
        else f"IQM Emerald hardware; {shots_label}."
    )
    fig.text(
        0.5,
        -0.02,
        footer,
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
