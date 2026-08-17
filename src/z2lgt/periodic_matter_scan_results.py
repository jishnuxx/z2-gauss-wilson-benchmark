"""Shared result processing for three-point periodic-matter hardware scans."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from qiskit.qpy import load as qpy_load


def load_qpy_circuit(path: Path):
    """Load exactly one frozen QPY circuit."""
    with path.open("rb") as handle:
        circuits = qpy_load(handle)
    if len(circuits) != 1:
        raise PermissionError(
            f"expected exactly one circuit in {path}, found {len(circuits)}"
        )
    return circuits[0]


def write_json(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def point_summaries(
    records: list[dict[str, object]],
    physics_by_point: dict[tuple[float, float], dict[str, object]],
) -> list[dict[str, object]]:
    """Compute sector separation and uncertainty for adjacent result pairs."""
    summaries = []
    for index in range(0, len(records), 2):
        plus, minus = records[index : index + 2]
        point = (float(plus["time"]), float(plus["dt"]))
        if point != (float(minus["time"]), float(minus["dt"])):
            raise RuntimeError("hardware results are not paired by time point")
        separation = float(plus["analysis"]["imbalance"]) - float(
            minus["analysis"]["imbalance"]
        )
        separation_se = math.sqrt(
            float(plus["analysis"]["imbalance_se"]) ** 2
            + float(minus["analysis"]["imbalance_se"]) ** 2
        )
        physics = physics_by_point[point]
        summaries.append(
            {
                "time": point[0],
                "dt": point[1],
                "trotter_steps": 2,
                "exact_sector_separation": physics["exact_sector_separation"],
                "trotter_sector_separation": physics[
                    "trotter_sector_separation"
                ],
                "hardware_sector_separation": separation,
                "hardware_sector_separation_absolute": abs(separation),
                "hardware_sector_separation_se": separation_se,
                "hardware_sector_separation_z": (
                    abs(separation) / separation_se if separation_se else None
                ),
            }
        )
    return summaries


def processed_rows(
    records: list[dict[str, object]],
    summaries: list[dict[str, object]],
    *,
    calibration_set_id: str,
    job_id: str,
) -> list[dict[str, object]]:
    """Flatten circuit and point results for the comparison CSV."""
    summary_by_point = {
        (float(item["time"]), float(item["dt"])): item for item in summaries
    }
    rows = []
    for record in records:
        point = (float(record["time"]), float(record["dt"]))
        summary = summary_by_point[point]
        analysis = record["analysis"]
        rows.append(
            {
                "time": record["time"],
                "dt": record["dt"],
                "trotter_steps": record["trotter_steps"],
                "case": record["case"],
                "wilson_sector": record["wilson_sector"],
                "exact_O_LR": record["exact_O_LR"],
                "trotter_O_LR": record["trotter_O_LR"],
                "hardware_O_LR": analysis["imbalance"],
                "hardware_O_LR_se": analysis["imbalance_se"],
                "exact_sector_separation": summary["exact_sector_separation"],
                "trotter_sector_separation": summary[
                    "trotter_sector_separation"
                ],
                "hardware_sector_separation": summary[
                    "hardware_sector_separation"
                ],
                "hardware_sector_separation_se": summary[
                    "hardware_sector_separation_se"
                ],
                "hardware_sector_separation_z": summary[
                    "hardware_sector_separation_z"
                ],
                "shots": record["shots"],
                "depth": record["depth"],
                "r_count": record["r_count"],
                "cz_count": record["cz_count"],
                "move_count": record["move_count"],
                "calibration_set_id": calibration_set_id,
                "job_id": job_id,
            }
        )
    return rows
