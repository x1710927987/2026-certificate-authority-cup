from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
QUESTION1_DIR = SCRIPT_DIR.parent
CDATA_DIR = QUESTION1_DIR.parent

BASE_RESULTS_JSON = QUESTION1_DIR / "basic_model_result_for_question_1" / "question_1_results.json"
BASE_LAYER_SUMMARY_CSV = QUESTION1_DIR / "basic_model_result_for_question_1" / "question_1_layer_summary.csv"
BASE_PATH_STEPS_CSV = QUESTION1_DIR / "basic_model_result_for_question_1" / "question_1_path_steps.csv"

PART_GEOMETRY_FILE = CDATA_DIR / "part_geometry.csv"
LOCAL_RELATIONS_FILE = CDATA_DIR / "local_geometry_relations.csv"
BASELINE_PATHS_FILE = CDATA_DIR / "baseline_paths.csv"
MACHINE_PARAMS_FILE = CDATA_DIR / "machine_params.json"

FIXED_START_SUMMARY = QUESTION1_DIR / "sensitivity_analysis" / "fixed_starting_point" / "fixed_starting_point_summary.csv"
FIXED_ENDPOINT_SUMMARY = QUESTION1_DIR / "sensitivity_analysis" / "fixed_endpoint" / "fixed_endpoint_summary.csv"
RETURN_WAREHOUSE_SUMMARY = QUESTION1_DIR / "sensitivity_analysis" / "return_to_warehouse" / "return_to_warehouse_summary.csv"

COST_SCALE = 10000
SOLVER_TIME_LIMIT_SECONDS = 120.0
SOLVER_NUM_WORKERS = 8

TYPE_COLORS = {
    "boundary": "#E58E26",
    "interior": "#2D98DA",
    "thin_wall": "#20BF6B",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_csv_dicts(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_machine_params() -> dict:
    return load_json(MACHINE_PARAMS_FILE)


def load_base_results() -> dict:
    return load_json(BASE_RESULTS_JSON)


def load_geometry_by_layer() -> Dict[Tuple[str, int], List[dict]]:
    by_layer: Dict[Tuple[str, int], List[dict]] = {}
    for row in load_csv_dicts(PART_GEOMETRY_FILE):
        key = (row["part_id"], int(row["layer_id"]))
        row["layer_id"] = int(row["layer_id"])
        row["grid_x"] = int(row["grid_x"])
        row["grid_y"] = int(row["grid_y"])
        for key_name in (
            "x_mm",
            "y_mm",
            "scan_length_mm",
            "area_mm2",
            "xmin_mm",
            "xmax_mm",
            "ymin_mm",
            "ymax_mm",
            "nearest_center_distance_mm",
        ):
            row[key_name] = float(row[key_name])
        row["layer_cell_count"] = int(row["layer_cell_count"])
        by_layer.setdefault(key, []).append(row)
    for key in by_layer:
        by_layer[key].sort(key=lambda item: item["cell_id"])
    return by_layer


def load_travel_distances_by_layer() -> Dict[Tuple[str, int], Dict[Tuple[str, str], float]]:
    by_layer: Dict[Tuple[str, int], Dict[Tuple[str, str], float]] = {}
    for row in load_csv_dicts(LOCAL_RELATIONS_FILE):
        key = (row["part_id"], int(row["layer_id"]))
        by_layer.setdefault(key, {})[(row["cell_i"], row["cell_j"])] = float(row["travel_distance_mm"])
    return by_layer


def load_base_path_lookup() -> Dict[Tuple[str, int], List[str]]:
    lookup: Dict[Tuple[str, int], List[Tuple[int, str]]] = {}
    for row in load_csv_dicts(BASE_PATH_STEPS_CSV):
        key = (row["part_id"], int(row["layer_id"]))
        lookup.setdefault(key, []).append((int(row["visit_step"]), row["cell_id"]))
    return {
        key: [cell_id for _, cell_id in sorted(items)]
        for key, items in lookup.items()
    }


def load_baseline_paths() -> Dict[Tuple[str, int, str], List[str]]:
    lookup: Dict[Tuple[str, int, str], List[Tuple[int, str]]] = {}
    for row in load_csv_dicts(BASELINE_PATHS_FILE):
        key = (row["part_id"], int(row["layer_id"]), row["strategy_name"])
        lookup.setdefault(key, []).append((int(row["step"]), row["cell_id"]))
    return {
        key: [cell_id for _, cell_id in sorted(items)]
        for key, items in lookup.items()
    }


def choose_representative_layers(base_results: dict) -> Dict[str, Tuple[str, int]]:
    per_part: Dict[str, List[dict]] = {}
    for item in base_results["layer_results"]:
        per_part.setdefault(item["part_id"], []).append(item)
    chosen: Dict[str, Tuple[str, int]] = {}
    for part_id, items in per_part.items():
        picked = sorted(
            items,
            key=lambda item: (
                -int(item["cell_count"]),
                -float(item["travel_distance_mm"]),
                int(item["layer_id"]),
            ),
        )[0]
        chosen[part_id] = (part_id, int(picked["layer_id"]))
    return chosen


def layer_label_from_key(key: Tuple[str, int]) -> str:
    part_id, layer_id = key
    suffix = part_id.split("_")[-1]
    return f"{suffix}{layer_id}"


def schedule_label(row: dict) -> str:
    suffix = row["part_id"].split("_")[-1]
    return f"{suffix}{int(row['layer_id'])}"


def cell_lookup(cells: Iterable[dict]) -> Dict[str, dict]:
    return {cell["cell_id"]: cell for cell in cells}


def compute_path_travel_distance(path_cell_ids: List[str], travel_distances: Dict[Tuple[str, str], float]) -> float:
    if len(path_cell_ids) <= 1:
        return 0.0
    return sum(travel_distances[(a, b)] for a, b in zip(path_cell_ids[:-1], path_cell_ids[1:]))


def compute_path_metrics(
    path_cell_ids: List[str],
    cells: List[dict],
    travel_distances: Dict[Tuple[str, str], float],
    scan_speed_mm_per_s: float,
    travel_speed_mm_per_s: float,
    laser_on_delay_s: float,
) -> dict:
    lookup = cell_lookup(cells)
    travel_distance_mm = compute_path_travel_distance(path_cell_ids, travel_distances)
    travel_time_s = travel_distance_mm / travel_speed_mm_per_s
    scan_time_s = sum(lookup[cell_id]["scan_length_mm"] for cell_id in path_cell_ids) / scan_speed_mm_per_s
    laser_on_time_s = len(path_cell_ids) * laser_on_delay_s
    return {
        "travel_distance_mm": travel_distance_mm,
        "travel_time_s": travel_time_s,
        "scan_time_s": scan_time_s,
        "laser_on_time_s": laser_on_time_s,
        "layer_total_time_s": scan_time_s + laser_on_time_s + travel_time_s,
    }


def path_difference_rate(base_path: List[str], candidate_path: List[str]) -> float:
    if len(base_path) <= 1:
        return 0.0
    base_edges = set(zip(base_path[:-1], base_path[1:]))
    candidate_edges = set(zip(candidate_path[:-1], candidate_path[1:]))
    changed = sum(1 for edge in base_edges if edge not in candidate_edges)
    return changed / (len(base_path) - 1)


def solve_open_path(
    cells: List[dict],
    travel_distances: Dict[Tuple[str, str], float],
    fixed_start_cell_id: str | None = None,
    fixed_end_cell_id: str | None = None,
    return_point: Tuple[float, float] | None = None,
) -> Tuple[List[str], str]:
    try:
        from ortools.sat.python import cp_model
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Missing dependency: ortools\n"
            "Please install it with:\n"
            "    pip install ortools\n"
        ) from exc

    ordered_cells = sorted(cells, key=lambda item: item["cell_id"])
    ids = [cell["cell_id"] for cell in ordered_cells]
    n = len(ids)
    id_to_idx = {cell_id: idx + 1 for idx, cell_id in enumerate(ids)}
    idx_to_id = {idx + 1: cell_id for idx, cell_id in enumerate(ids)}
    lookup = cell_lookup(ordered_cells)

    model = cp_model.CpModel()
    arc_vars = {}
    arcs = []
    objective_terms = []

    fixed_start_idx = id_to_idx[fixed_start_cell_id] if fixed_start_cell_id else None
    fixed_end_idx = id_to_idx[fixed_end_cell_id] if fixed_end_cell_id else None

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
                if return_point is None:
                    cost = 0
                else:
                    warehouse_x, warehouse_y = return_point
                    cell = lookup[idx_to_id[i]]
                    distance_mm = math.hypot(cell["x_mm"] - warehouse_x, cell["y_mm"] - warehouse_y)
                    cost = int(round(distance_mm * COST_SCALE))
            else:
                cost_mm = travel_distances[(idx_to_id[i], idx_to_id[j])]
                cost = int(round(cost_mm * COST_SCALE))
            objective_terms.append(cost * var)

    model.AddCircuit(arcs)
    model.Minimize(sum(objective_terms))

    if fixed_start_idx is not None:
        for j in range(1, n + 1):
            model.Add(arc_vars[(0, j)] == (1 if j == fixed_start_idx else 0))

    if fixed_end_idx is not None:
        for i in range(1, n + 1):
            model.Add(arc_vars[(i, 0)] == (1 if i == fixed_end_idx else 0))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(SOLVER_TIME_LIMIT_SECONDS)
    solver.parameters.num_search_workers = int(SOLVER_NUM_WORKERS)

    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"Open-path solve failed. CP-SAT status={status}")

    successor = {}
    for (i, j), var in arc_vars.items():
        if solver.Value(var) == 1:
            successor[i] = j

    path_indices: List[int] = []
    current = successor[0]
    visited = set()
    while current != 0:
        if current in visited:
            raise RuntimeError("Path reconstruction failed due to repeated node.")
        visited.add(current)
        path_indices.append(current)
        current = successor[current]

    if len(path_indices) != n:
        raise RuntimeError("Recovered path length does not match the layer cell count.")

    status_name = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
    return [idx_to_id[idx] for idx in path_indices], status_name
