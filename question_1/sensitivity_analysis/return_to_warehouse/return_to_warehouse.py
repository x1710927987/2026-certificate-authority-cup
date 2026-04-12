"""
Structural sensitivity analysis: return to warehouse.

The warehouse point is fixed at (0, 0) mm.
For each layer, the model is re-solved with an added return-to-warehouse cost
from the final visited cell to the warehouse.

Outputs:
- return_to_warehouse_summary.csv
- return_to_warehouse_path_steps.csv
- return_to_warehouse_plot.png
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from ortools.sat.python import cp_model
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: ortools\n"
        "Please install it with:\n"
        "    pip install ortools\n"
    ) from exc

try:
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: matplotlib\n"
        "Please install it with:\n"
        "    pip install matplotlib\n"
    ) from exc


SOLVER_TIME_LIMIT_SECONDS = 120.0
SOLVER_NUM_WORKERS = 8
COST_SCALE = 10000
WAREHOUSE_X_MM = 0.0
WAREHOUSE_Y_MM = 0.0

SCRIPT_DIR = Path(__file__).resolve().parent
QUESTION1_DIR = SCRIPT_DIR.parents[1]
CDATA_DIR = SCRIPT_DIR.parents[2]

BASE_RESULTS_JSON = QUESTION1_DIR / "basic_model_result_for_question_1" / "question_1_results.json"
PART_GEOMETRY_FILE = CDATA_DIR / "part_geometry.csv"
LOCAL_RELATIONS_FILE = CDATA_DIR / "local_geometry_relations.csv"
MACHINE_PARAMS_FILE = CDATA_DIR / "machine_params.json"

SUMMARY_CSV = SCRIPT_DIR / "return_to_warehouse_summary.csv"
PATH_STEPS_CSV = SCRIPT_DIR / "return_to_warehouse_path_steps.csv"
PLOT_FILE = SCRIPT_DIR / "return_to_warehouse_plot.png"


@dataclass
class CellInfo:
    part_id: str
    layer_id: int
    cell_id: str
    scan_length_mm: float
    x_mm: float
    y_mm: float


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_machine_params() -> dict:
    return load_json(MACHINE_PARAMS_FILE)


def load_part_geometry() -> Dict[Tuple[str, int], List[CellInfo]]:
    by_layer: Dict[Tuple[str, int], List[CellInfo]] = {}
    with PART_GEOMETRY_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["part_id"], int(row["layer_id"]))
            by_layer.setdefault(key, []).append(
                CellInfo(
                    part_id=row["part_id"],
                    layer_id=int(row["layer_id"]),
                    cell_id=row["cell_id"],
                    scan_length_mm=float(row["scan_length_mm"]),
                    x_mm=float(row["x_mm"]),
                    y_mm=float(row["y_mm"]),
                )
            )
    for key in by_layer:
        by_layer[key].sort(key=lambda c: c.cell_id)
    return by_layer


def load_travel_distances() -> Dict[Tuple[str, int], Dict[Tuple[str, str], float]]:
    by_layer: Dict[Tuple[str, int], Dict[Tuple[str, str], float]] = {}
    with LOCAL_RELATIONS_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["part_id"], int(row["layer_id"]))
            by_layer.setdefault(key, {})[(row["cell_i"], row["cell_j"])] = float(row["travel_distance_mm"])
    return by_layer


def solve_open_path_with_return_to_point(
    cells: List[CellInfo],
    travel_distances: Dict[Tuple[str, str], float],
    return_x_mm: float,
    return_y_mm: float,
) -> tuple[list[str], str]:
    cell_ids = [cell.cell_id for cell in cells]
    n = len(cell_ids)
    id_to_idx = {cell_id: idx + 1 for idx, cell_id in enumerate(cell_ids)}
    idx_to_id = {idx + 1: cell_id for idx, cell_id in enumerate(cell_ids)}
    cell_lookup = {cell.cell_id: cell for cell in cells}

    model = cp_model.CpModel()
    arc_vars: Dict[Tuple[int, int], cp_model.IntVar] = {}
    arcs = []
    objective_terms = []

    for i in range(0, n + 1):
        for j in range(0, n + 1):
            if i == j:
                continue
            var = model.NewBoolVar(f"x_{i}_{j}")
            arc_vars[(i, j)] = var
            arcs.append((i, j, var))

            if i == 0 and j > 0:
                cost = 0
            elif i > 0 and j == 0:
                cell = cell_lookup[idx_to_id[i]]
                return_distance_mm = math.hypot(cell.x_mm - return_x_mm, cell.y_mm - return_y_mm)
                cost = int(round(return_distance_mm * COST_SCALE))
            else:
                cost_mm = travel_distances[(idx_to_id[i], idx_to_id[j])]
                cost = int(round(cost_mm * COST_SCALE))
            objective_terms.append(cost * var)

    model.AddCircuit(arcs)
    model.Minimize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(SOLVER_TIME_LIMIT_SECONDS)
    solver.parameters.num_search_workers = int(SOLVER_NUM_WORKERS)

    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"Exact solve failed. CP-SAT status={status}")

    successor: Dict[int, int] = {}
    for (i, j), var in arc_vars.items():
        if solver.Value(var) == 1:
            successor[i] = j

    path_indices: List[int] = []
    current = successor[0]
    visited = set()
    while current != 0:
        if current in visited:
            raise RuntimeError("Cycle reconstruction failed: repeated node before returning to dummy node.")
        visited.add(current)
        path_indices.append(current)
        current = successor[current]

    if len(path_indices) != n:
        raise RuntimeError("Recovered path length does not match layer cell count.")

    status_name = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
    return [idx_to_id[idx] for idx in path_indices], status_name


def path_edges(path: List[str]) -> set[Tuple[str, str]]:
    return set(zip(path[:-1], path[1:]))


def path_difference_rate(base_path: List[str], candidate_path: List[str]) -> float:
    if len(base_path) <= 1:
        return 0.0
    base_edges = path_edges(base_path)
    candidate_edges = path_edges(candidate_path)
    changed_count = sum(1 for edge in base_edges if edge not in candidate_edges)
    return changed_count / (len(base_path) - 1)


def write_csv(path: Path, header: List[str], rows: List[List[object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def make_layer_label(schedule_index: int, part_id: str, layer_id: int) -> str:
    suffix = part_id.split("_")[-1]
    return f"{schedule_index}:{suffix}{layer_id}"


def main() -> None:
    base_results = load_json(BASE_RESULTS_JSON)
    machine = load_machine_params()
    layers = load_part_geometry()
    travel_by_layer = load_travel_distances()

    scan_speed_mm_per_s = float(machine["scan_speed_mm_per_s"])
    travel_speed_mm_per_s = float(machine["travel_speed_mm_per_s"])
    laser_on_delay_s = float(machine["laser_on_delay_s"])

    base_layer_lookup = {
        (item["part_id"], int(item["layer_id"])): item
        for item in base_results["layer_results"]
    }

    summary_rows: List[List[object]] = []
    path_rows: List[List[object]] = []

    layer_labels = []
    base_time_vals = []
    rule_time_vals = []
    added_return_vals = []
    path_diff_vals = []

    for schedule_item in base_results["schedule"]:
        schedule_index = int(schedule_item["schedule_index"])
        part_id = schedule_item["part_id"]
        layer_id = int(schedule_item["layer_id"])
        key = (part_id, layer_id)

        base_layer = base_layer_lookup[key]
        base_path = list(base_layer["path_cell_ids"])
        base_total_time_s = float(base_layer["layer_total_time_s"])

        cells = layers[key]
        travel_distances = travel_by_layer[key]
        cell_lookup = {cell.cell_id: cell for cell in cells}

        candidate_path, solver_status = solve_open_path_with_return_to_point(
            cells=cells,
            travel_distances=travel_distances,
            return_x_mm=WAREHOUSE_X_MM,
            return_y_mm=WAREHOUSE_Y_MM,
        )

        internal_travel_distance_mm = 0.0
        for prev_id, next_id in zip(candidate_path[:-1], candidate_path[1:]):
            internal_travel_distance_mm += travel_distances[(prev_id, next_id)]

        end_cell = cell_lookup[candidate_path[-1]]
        return_distance_mm = math.hypot(end_cell.x_mm - WAREHOUSE_X_MM, end_cell.y_mm - WAREHOUSE_Y_MM)
        internal_travel_time_s = internal_travel_distance_mm / travel_speed_mm_per_s
        return_time_s = return_distance_mm / travel_speed_mm_per_s
        scan_time_s = sum(cell_lookup[cell_id].scan_length_mm for cell_id in candidate_path) / scan_speed_mm_per_s
        laser_on_time_s = len(candidate_path) * laser_on_delay_s
        layer_total_time_s = scan_time_s + laser_on_time_s + internal_travel_time_s + return_time_s

        delta_time_s = layer_total_time_s - base_total_time_s
        delta_time_percent = (delta_time_s / base_total_time_s * 100.0) if base_total_time_s > 0 else 0.0
        diff_rate = path_difference_rate(base_path, candidate_path)

        layer_label = make_layer_label(schedule_index, part_id, layer_id)
        summary_rows.append(
            [
                schedule_index,
                part_id,
                layer_id,
                layer_label,
                solver_status,
                base_layer["end_cell_id"],
                candidate_path[0],
                candidate_path[-1],
                f"{internal_travel_distance_mm:.6f}",
                f"{return_distance_mm:.6f}",
                f"{scan_time_s:.6f}",
                f"{laser_on_time_s:.6f}",
                f"{internal_travel_time_s:.6f}",
                f"{return_time_s:.6f}",
                f"{layer_total_time_s:.6f}",
                f"{base_total_time_s:.6f}",
                f"{delta_time_s:.6f}",
                f"{delta_time_percent:.6f}",
                f"{diff_rate:.6f}",
            ]
        )

        for step, cell_id in enumerate(candidate_path, start=1):
            path_rows.append([schedule_index, part_id, layer_id, step, cell_id])

        layer_labels.append(layer_label)
        base_time_vals.append(base_total_time_s)
        rule_time_vals.append(layer_total_time_s)
        added_return_vals.append(return_time_s)
        path_diff_vals.append(diff_rate * 100.0)

    write_csv(
        SUMMARY_CSV,
        [
            "schedule_index",
            "part_id",
            "layer_id",
            "layer_label",
            "solver_status",
            "base_end_cell_id",
            "result_start_cell_id",
            "result_end_cell_id",
            "internal_travel_distance_mm",
            "return_distance_mm",
            "scan_time_s",
            "laser_on_time_s",
            "internal_travel_time_s",
            "return_time_s",
            "layer_total_time_s",
            "base_layer_total_time_s",
            "delta_time_s",
            "delta_time_percent",
            "path_difference_rate",
        ],
        summary_rows,
    )

    write_csv(
        PATH_STEPS_CSV,
        ["schedule_index", "part_id", "layer_id", "visit_step", "cell_id"],
        path_rows,
    )

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.2))

    x_pos = list(range(len(layer_labels)))
    width = 0.38
    axes[0].bar([x - width / 2 for x in x_pos], base_time_vals, width=width, label="Base")
    axes[0].bar([x + width / 2 for x in x_pos], rule_time_vals, width=width, label="Return-to-warehouse")
    axes[0].set_xticks(x_pos)
    axes[0].set_xticklabels(layer_labels, rotation=45)
    axes[0].set_ylabel("Layer total time (s)")
    axes[0].set_title("Base vs Return-to-Warehouse")
    axes[0].grid(True, axis="y", alpha=0.3)
    axes[0].legend()

    axes[1].bar(layer_labels, added_return_vals, color="#2ca02c", label="Added return time")
    axes[1].plot(layer_labels, path_diff_vals, marker="o", linewidth=2, color="#d62728", label="Path difference rate (%)")
    axes[1].set_ylabel("Return / path-change response")
    axes[1].set_title("Return Rule Response by Layer")
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].grid(True, axis="y", alpha=0.3)
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(PLOT_FILE, dpi=220, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {SUMMARY_CSV}")
    print(f"Saved: {PATH_STEPS_CSV}")
    print(f"Saved: {PLOT_FILE}")


if __name__ == "__main__":
    main()
