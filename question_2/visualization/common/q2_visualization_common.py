from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle


ROOT_DIR = Path(__file__).resolve().parents[3]
QUESTION2_DIR = ROOT_DIR / "question_2"
BASE_MODEL_DIR = QUESTION2_DIR / "basic_model_for_question_2"
SENSITIVITY_DIR = QUESTION2_DIR / "sensitivity_analysis"

PART_GEOMETRY_FILE = ROOT_DIR / "part_geometry.csv"
BASE_RESULTS_JSON = BASE_MODEL_DIR / "question_2_base_results.json"
SCHEME_OVERALL_SUMMARY = BASE_MODEL_DIR / "scheme_overall_summary.csv"
SCHEME_LAYER_SUMMARY = BASE_MODEL_DIR / "scheme_layer_summary.csv"
CELL_RISK_DETAILS = BASE_MODEL_DIR / "cell_risk_details.csv"
HEAT_HISTORY_RECORDS = BASE_MODEL_DIR / "heat_history_records.csv"
SCHEME_PATH_STEPS = BASE_MODEL_DIR / "scheme_path_steps.csv"
THRESHOLD_ALIGNMENT_REFERENCE = BASE_MODEL_DIR / "threshold_alignment_reference.csv"
SUBJECTIVE_WEIGHTS_OVERALL = (
    SENSITIVITY_DIR
    / "subjective_weights"
    / "subjective_weights_overall_summary.csv"
)
SUBJECTIVE_WEIGHTS_SCENARIOS = (
    SENSITIVITY_DIR
    / "subjective_weights"
    / "subjective_weights_scenario_summary.csv"
)

SCHEME_ORDER = ["row_major", "serpentine", "center_out", "minimum_time"]
SCHEME_LABELS = {
    "row_major": "row_major",
    "serpentine": "serpentine",
    "center_out": "center_out",
    "minimum_time": "minimum_time",
}
SCHEME_COLORS = {
    "row_major": "#4C78A8",
    "serpentine": "#F58518",
    "center_out": "#54A24B",
    "minimum_time": "#E45756",
}


def add_common_path() -> None:
    common_dir = Path(__file__).resolve().parent
    if str(common_dir) not in sys.path:
        sys.path.insert(0, str(common_dir))


def load_csv_rows(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def to_int(value) -> int:
    return int(float(value))


def to_float(value) -> float:
    return float(value)


def load_visualization_context() -> dict:
    return {
        "base_results": load_json(BASE_RESULTS_JSON),
        "geometry_rows": load_csv_rows(PART_GEOMETRY_FILE),
        "scheme_overall_rows": load_csv_rows(SCHEME_OVERALL_SUMMARY),
        "scheme_layer_rows": load_csv_rows(SCHEME_LAYER_SUMMARY),
        "cell_risk_rows": load_csv_rows(CELL_RISK_DETAILS),
        "heat_history_rows": load_csv_rows(HEAT_HISTORY_RECORDS),
        "path_step_rows": load_csv_rows(SCHEME_PATH_STEPS),
        "threshold_rows": load_csv_rows(THRESHOLD_ALIGNMENT_REFERENCE),
        "subjective_overall_rows": load_csv_rows(SUBJECTIVE_WEIGHTS_OVERALL),
        "subjective_scenario_rows": load_csv_rows(SUBJECTIVE_WEIGHTS_SCENARIOS),
    }


def layer_key(row: dict) -> Tuple[str, int]:
    return row["part_id"], to_int(row["layer_id"])


def group_rows(rows: Sequence[dict], *keys: str) -> Dict[Tuple[str, ...], List[dict]]:
    grouped: Dict[Tuple[str, ...], List[dict]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row[key]) for key in keys)].append(row)
    return grouped


def select_representative_layer(layer_rows: Sequence[dict]) -> dict:
    scores: Dict[Tuple[str, int], List[float]] = defaultdict(list)
    layer_meta: Dict[Tuple[str, int], dict] = {}
    for row in layer_rows:
        key = layer_key(row)
        scores[key].append(to_float(row["weighted_sum_total_risk"]))
        layer_meta[key] = {
            "part_id": row["part_id"],
            "layer_id": to_int(row["layer_id"]),
            "cell_count": to_int(row["cell_count"]),
        }

    ranked = []
    for key, values in scores.items():
        meta = dict(layer_meta[key])
        meta["mean_weighted_risk"] = sum(values) / len(values)
        ranked.append(meta)
    ranked.sort(
        key=lambda item: (
            item["mean_weighted_risk"],
            item["cell_count"],
            -item["layer_id"],
            item["part_id"],
        ),
        reverse=True,
    )
    return ranked[0]


def filter_rows_for_layer(rows: Sequence[dict], part_id: str, layer_id: int) -> List[dict]:
    return [row for row in rows if row["part_id"] == part_id and to_int(row["layer_id"]) == layer_id]


def geometry_lookup(geometry_rows: Sequence[dict]) -> Dict[str, dict]:
    return {row["cell_id"]: row for row in geometry_rows}


def order_geometry_rows(layer_geometry_rows: Sequence[dict]) -> List[dict]:
    return sorted(
        layer_geometry_rows,
        key=lambda row: (to_float(row["ymin_mm"]), to_float(row["xmin_mm"]), row["cell_id"]),
    )


def draw_layer_values(
    ax,
    layer_geometry_rows: Sequence[dict],
    values_by_cell: Dict[str, float],
    title: str,
    cmap_name: str = "YlOrRd",
    vmin: float | None = None,
    vmax: float | None = None,
    show_cell_labels: bool = False,
):
    cmap = plt.get_cmap(cmap_name)
    ordered_rows = order_geometry_rows(layer_geometry_rows)
    if vmin is None:
        vmin = min(values_by_cell.values()) if values_by_cell else 0.0
    if vmax is None:
        vmax = max(values_by_cell.values()) if values_by_cell else 1.0
    if math.isclose(vmin, vmax):
        vmax = vmin + 1e-9
    norm = Normalize(vmin=vmin, vmax=vmax)

    xs = []
    ys = []
    for row in ordered_rows:
        cell_id = row["cell_id"]
        value = values_by_cell.get(cell_id, float("nan"))
        color = "#f2f2f2" if math.isnan(value) else cmap(norm(value))
        xmin = to_float(row["xmin_mm"])
        xmax = to_float(row["xmax_mm"])
        ymin = to_float(row["ymin_mm"])
        ymax = to_float(row["ymax_mm"])
        rect = Rectangle(
            (xmin, ymin),
            xmax - xmin,
            ymax - ymin,
            facecolor=color,
            edgecolor="#666666",
            linewidth=0.8,
        )
        ax.add_patch(rect)
        xs.extend([xmin, xmax])
        ys.extend([ymin, ymax])
        if show_cell_labels:
            ax.text(
                to_float(row["x_mm"]),
                to_float(row["y_mm"]),
                cell_id.split("_")[-1],
                ha="center",
                va="center",
                fontsize=6,
                color="black",
            )

    ax.set_aspect("equal")
    ax.set_xlim(min(xs) - 1, max(xs) + 1)
    ax.set_ylim(min(ys) - 1, max(ys) + 1)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("x / mm")
    ax.set_ylabel("y / mm")
    ax.grid(False)
    return cm.ScalarMappable(norm=norm, cmap=cmap)


def draw_path_overlay(
    ax,
    layer_geometry_rows: Sequence[dict],
    ordered_cell_ids: Sequence[str],
    title: str,
    line_color: str = "#1f4e79",
) -> None:
    lookup = geometry_lookup(layer_geometry_rows)
    ordered_rows = order_geometry_rows(layer_geometry_rows)
    xs = []
    ys = []
    for row in ordered_rows:
        xmin = to_float(row["xmin_mm"])
        xmax = to_float(row["xmax_mm"])
        ymin = to_float(row["ymin_mm"])
        ymax = to_float(row["ymax_mm"])
        rect = Rectangle(
            (xmin, ymin),
            xmax - xmin,
            ymax - ymin,
            facecolor="#f5f5f5",
            edgecolor="#b0b0b0",
            linewidth=0.7,
        )
        ax.add_patch(rect)
        xs.extend([xmin, xmax])
        ys.extend([ymin, ymax])

    x_points = [to_float(lookup[cell_id]["x_mm"]) for cell_id in ordered_cell_ids if cell_id in lookup]
    y_points = [to_float(lookup[cell_id]["y_mm"]) for cell_id in ordered_cell_ids if cell_id in lookup]
    ax.plot(x_points, y_points, color=line_color, linewidth=1.8, alpha=0.85)
    ax.scatter(x_points, y_points, s=16, color=line_color, zorder=3)
    if x_points and y_points:
        ax.scatter(x_points[0], y_points[0], s=80, color="#2A9D4B", marker="o", zorder=4, label="start")
        ax.scatter(x_points[-1], y_points[-1], s=90, color="#D1495B", marker="X", zorder=4, label="end")
    ax.set_aspect("equal")
    ax.set_xlim(min(xs) - 1, max(xs) + 1)
    ax.set_ylim(min(ys) - 1, max(ys) + 1)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("x / mm")
    ax.set_ylabel("y / mm")
    ax.grid(False)


def path_for_layer(path_step_rows: Sequence[dict], scheme_name: str, part_id: str, layer_id: int) -> List[str]:
    layer_rows = [
        row
        for row in path_step_rows
        if row["scheme_name"] == scheme_name
        and row["part_id"] == part_id
        and to_int(row["layer_id"]) == layer_id
    ]
    layer_rows.sort(key=lambda row: to_int(row["visit_step"]))
    return [row["cell_id"] for row in layer_rows]


def layer_metric_bounds(
    cell_risk_rows: Sequence[dict],
    part_id: str,
    layer_id: int,
    schemes: Sequence[str],
    metric_key: str,
) -> Tuple[float, float]:
    values = [
        to_float(row[metric_key])
        for row in cell_risk_rows
        if row["scheme_name"] in schemes
        and row["part_id"] == part_id
        and to_int(row["layer_id"]) == layer_id
    ]
    return min(values), max(values)


def heat_history_series(
    heat_history_rows: Sequence[dict],
    scheme_name: str,
    part_id: str,
    layer_id: int,
) -> List[dict]:
    layer_rows = [
        row
        for row in heat_history_rows
        if row["scheme_name"] == scheme_name
        and row["part_id"] == part_id
        and to_int(row["layer_id"]) == layer_id
    ]
    event_groups: Dict[int, List[dict]] = defaultdict(list)
    for row in layer_rows:
        event_groups[to_int(row["event_step"])].append(row)

    series = []
    for event_step in sorted(event_groups):
        group = event_groups[event_step]
        heat_values = [to_float(row["heat_state"]) for row in group]
        above_count = sum(to_int(row["above_threshold"]) for row in group)
        series.append(
            {
                "event_step": event_step,
                "event_time_s": to_float(group[0]["event_time_s"]),
                "heat_mean": sum(heat_values) / len(heat_values),
                "heat_peak": max(heat_values),
                "above_threshold_count": above_count,
                "heat_std": _std(heat_values),
            }
        )
    return series


def _std(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    mean_value = sum(values) / len(values)
    return math.sqrt(sum((item - mean_value) ** 2 for item in values) / len(values))


def save_metadata(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def representative_layer_title(meta: dict) -> str:
    return f"{meta['part_id']} layer {meta['layer_id']} (cells={meta['cell_count']})"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def select_layer_with_flag(
    cell_risk_rows: Sequence[dict],
    scheme_layer_rows: Sequence[dict],
    flag_key: str,
    flag_value: str = "1",
) -> dict:
    valid_keys = {
        (row["part_id"], to_int(row["layer_id"]))
        for row in cell_risk_rows
        if row.get(flag_key) == flag_value
    }
    scores: Dict[Tuple[str, int], List[float]] = defaultdict(list)
    layer_meta: Dict[Tuple[str, int], dict] = {}
    for row in scheme_layer_rows:
        key = layer_key(row)
        if key not in valid_keys:
            continue
        scores[key].append(to_float(row["weighted_sum_total_risk"]))
        layer_meta[key] = {
            "part_id": row["part_id"],
            "layer_id": to_int(row["layer_id"]),
            "cell_count": to_int(row["cell_count"]),
        }
    ranked = []
    for key, values in scores.items():
        meta = dict(layer_meta[key])
        meta["mean_weighted_risk"] = sum(values) / len(values)
        ranked.append(meta)
    ranked.sort(key=lambda item: item["mean_weighted_risk"], reverse=True)
    return ranked[0]


def select_representative_cells(
    cell_risk_rows: Sequence[dict],
    part_id: str,
    layer_id: int,
    scheme_name: str = "row_major",
) -> Dict[str, str]:
    layer_rows = [
        row
        for row in cell_risk_rows
        if row["scheme_name"] == scheme_name
        and row["part_id"] == part_id
        and to_int(row["layer_id"]) == layer_id
    ]
    sorted_by_peak = sorted(layer_rows, key=lambda row: to_float(row["peak_heat_state"]), reverse=True)
    hotspot = sorted_by_peak[0]["cell_id"]

    hole_candidates = [row for row in sorted_by_peak if row.get("is_hole") == "1"]
    hole_cell = hole_candidates[0]["cell_id"] if hole_candidates else hotspot

    thin_candidates = [row for row in sorted_by_peak if row.get("is_thin") == "1"]
    thin_cell = thin_candidates[0]["cell_id"] if thin_candidates else hotspot

    normal_candidates = [
        row
        for row in sorted(layer_rows, key=lambda row: to_float(row["peak_heat_state"]))
        if row.get("is_hole") == "0" and row.get("is_thin") == "0"
    ]
    normal_cell = normal_candidates[0]["cell_id"] if normal_candidates else sorted_by_peak[-1]["cell_id"]

    return {
        "hotspot": hotspot,
        "hole": hole_cell,
        "thin": thin_cell,
        "normal": normal_cell,
    }
