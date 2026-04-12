"""
Question 1 solver for the 2026 认证杯 C 题.

This script implements the base model only:
- exact single-layer open-path optimization
- interleaved printing schedule: A1, B1, A2, B2, ...
- total task time accounting:
  * per-layer intra-layer time
  * inter-layer change time
  * fixed inter-part transfer distance in the base model
  * inter-part transfer time converted from distance using travel speed

Expected input files:
- part_geometry.csv
- local_geometry_relations.csv
- machine_params.json

All CSV/JSON files should be placed in the same directory as this script.

Outputs:
- question_1_results.json
- question_1_layer_summary.csv
- question_1_path_steps.csv
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from ortools.sat.python import cp_model
except ImportError as exc:  # pragma: no cover - runtime guidance
    raise SystemExit(
        "Missing dependency: ortools\n"
        "Please install it with:\n"
        "    pip install ortools\n"
    ) from exc


# =============================================================================
# Developer configuration: confirm these parameters before running the script.
# -----------------------------------------------------------------------------
# Base model assumption for inter-part transfer:
# The scanner transfer distance between the two parts is fixed at 50 mm.
# The corresponding transfer time is computed by:
#     inter_part_transfer_time = 50 / travel_speed_mm_per_s
#
# NOTE:
# The range 20 mm to 100 mm with step 5 mm is no longer part of the base model.
# That range should be used later in sensitivity analysis, not in this script.
# =============================================================================
INTER_PART_TRANSFER_DISTANCE_MM = 50.0

# Exact single-layer solver settings.
SOLVER_TIME_LIMIT_SECONDS = 120.0
SOLVER_NUM_WORKERS = 8

# Objective scaling for CP-SAT integer optimization.
COST_SCALE = 10000

# Input / output file names.
PART_GEOMETRY_FILE = "part_geometry.csv"
LOCAL_RELATIONS_FILE = "local_geometry_relations.csv"
MACHINE_PARAMS_FILE = "machine_params.json"

OUTPUT_RESULTS_JSON = "question_1_results.json"
OUTPUT_LAYER_SUMMARY_CSV = "question_1_layer_summary.csv"
OUTPUT_PATH_STEPS_CSV = "question_1_path_steps.csv"


@dataclass
class CellInfo:
    part_id: str
    layer_id: int
    cell_id: str
    scan_length_mm: float
    cell_type: str


@dataclass
class LayerResult:
    schedule_index: int
    part_id: str
    layer_id: int
    solver_status: str
    cell_count: int
    start_cell_id: str
    end_cell_id: str
    path_cell_ids: List[str]
    travel_distance_mm: float
    travel_time_s: float
    scan_time_s: float
    laser_on_time_s: float
    layer_total_time_s: float


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def validate_base_config() -> float:
    distance_mm = float(INTER_PART_TRANSFER_DISTANCE_MM)
    if distance_mm <= 0:
        raise ValueError("INTER_PART_TRANSFER_DISTANCE_MM must be positive.")
    return distance_mm


def load_machine_params(base_dir: Path) -> dict:
    with (base_dir / MACHINE_PARAMS_FILE).open("r", encoding="utf-8") as f:
        return json.load(f)


def load_part_geometry(base_dir: Path) -> Dict[Tuple[str, int], List[CellInfo]]:
    by_layer: Dict[Tuple[str, int], List[CellInfo]] = {}
    with (base_dir / PART_GEOMETRY_FILE).open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["part_id"], int(row["layer_id"]))
            by_layer.setdefault(key, []).append(
                CellInfo(
                    part_id=row["part_id"],
                    layer_id=int(row["layer_id"]),
                    cell_id=row["cell_id"],
                    scan_length_mm=float(row["scan_length_mm"]),
                    cell_type=row["type"],
                )
            )
    for key in by_layer:
        by_layer[key].sort(key=lambda c: c.cell_id)
    return by_layer


def load_travel_distances(base_dir: Path) -> Dict[Tuple[str, int], Dict[Tuple[str, str], float]]:
    by_layer: Dict[Tuple[str, int], Dict[Tuple[str, str], float]] = {}
    with (base_dir / LOCAL_RELATIONS_FILE).open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["part_id"], int(row["layer_id"]))
            by_layer.setdefault(key, {})[(row["cell_i"], row["cell_j"])] = float(row["travel_distance_mm"])
    return by_layer


def build_interleaved_schedule(layers: Dict[Tuple[str, int], List[CellInfo]]) -> List[Tuple[str, int]]:
    parts = sorted({part_id for part_id, _ in layers})
    all_layer_ids = sorted({layer_id for _, layer_id in layers})
    schedule: List[Tuple[str, int]] = []
    for layer_id in all_layer_ids:
        for part_id in parts:
            key = (part_id, layer_id)
            if key in layers:
                schedule.append(key)
    return schedule


def solve_layer_exact_open_path(
    cells: List[CellInfo],
    travel_distances: Dict[Tuple[str, str], float],
    time_limit_seconds: float,
) -> Tuple[List[str], str]:
    """
    Exact single-layer optimization via:
    - dummy node 0
    - complete directed graph
    - Hamiltonian cycle through all nodes using AddCircuit
    - removing dummy node to recover the open path
    """
    cell_ids = [cell.cell_id for cell in cells]
    n = len(cell_ids)
    id_to_idx = {cell_id: idx + 1 for idx, cell_id in enumerate(cell_ids)}
    idx_to_id = {idx + 1: cell_id for idx, cell_id in enumerate(cell_ids)}

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

            if i == 0 or j == 0:
                cost = 0
            else:
                cost_mm = travel_distances[(idx_to_id[i], idx_to_id[j])]
                cost = int(round(cost_mm * COST_SCALE))
            objective_terms.append(cost * var)

    model.AddCircuit(arcs)
    model.Minimize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_seconds)
    solver.parameters.num_search_workers = int(SOLVER_NUM_WORKERS)

    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"Layer exact solve failed. CP-SAT status={status}")

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

    if status == cp_model.OPTIMAL:
        status_name = "OPTIMAL"
    else:
        status_name = "FEASIBLE"
    return [idx_to_id[idx] for idx in path_indices], status_name


def compute_layer_result(
    schedule_index: int,
    part_id: str,
    layer_id: int,
    path_cell_ids: List[str],
    solver_status: str,
    cells: List[CellInfo],
    travel_distances: Dict[Tuple[str, str], float],
    scan_speed_mm_per_s: float,
    travel_speed_mm_per_s: float,
    laser_on_delay_s: float,
) -> LayerResult:
    cell_lookup = {cell.cell_id: cell for cell in cells}

    scan_time_s = sum(cell_lookup[cell_id].scan_length_mm for cell_id in path_cell_ids) / scan_speed_mm_per_s
    laser_on_time_s = len(path_cell_ids) * laser_on_delay_s

    travel_distance_mm = 0.0
    for prev_id, next_id in zip(path_cell_ids[:-1], path_cell_ids[1:]):
        travel_distance_mm += travel_distances[(prev_id, next_id)]
    travel_time_s = travel_distance_mm / travel_speed_mm_per_s

    layer_total_time_s = scan_time_s + laser_on_time_s + travel_time_s

    return LayerResult(
        schedule_index=schedule_index,
        part_id=part_id,
        layer_id=layer_id,
        solver_status=solver_status,
        cell_count=len(path_cell_ids),
        start_cell_id=path_cell_ids[0],
        end_cell_id=path_cell_ids[-1],
        path_cell_ids=path_cell_ids,
        travel_distance_mm=travel_distance_mm,
        travel_time_s=travel_time_s,
        scan_time_s=scan_time_s,
        laser_on_time_s=laser_on_time_s,
        layer_total_time_s=layer_total_time_s,
    )


def compute_inter_part_transfer(
    switch_count: int,
    transfer_distance_mm: float,
    travel_speed_mm_per_s: float,
) -> dict:
    total_distance_mm = switch_count * transfer_distance_mm
    total_time_s = total_distance_mm / travel_speed_mm_per_s if travel_speed_mm_per_s > 0 else 0.0
    return {
        "switch_count": switch_count,
        "distance_per_switch_mm": transfer_distance_mm,
        "travel_speed_mm_per_s": travel_speed_mm_per_s,
        "total_inter_part_distance_mm": total_distance_mm,
        "total_inter_part_time_s": total_time_s,
    }


def count_schedule_transitions(schedule: List[Tuple[str, int]]) -> Tuple[int, int]:
    """
    With interleaved printing:
    - inter-part switch: same layer id, different part id
    - inter-layer change: next task has a larger layer id
    """
    inter_part_switch_count = 0
    inter_layer_change_count = 0

    for current, nxt in zip(schedule[:-1], schedule[1:]):
        current_part, current_layer = current
        next_part, next_layer = nxt
        if next_layer == current_layer and next_part != current_part:
            inter_part_switch_count += 1
        if next_layer != current_layer:
            inter_layer_change_count += 1

    return inter_part_switch_count, inter_layer_change_count


def write_layer_summary_csv(base_dir: Path, layer_results: List[LayerResult]) -> None:
    with (base_dir / OUTPUT_LAYER_SUMMARY_CSV).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "schedule_index",
                "part_id",
                "layer_id",
                "solver_status",
                "cell_count",
                "start_cell_id",
                "end_cell_id",
                "travel_distance_mm",
                "travel_time_s",
                "scan_time_s",
                "laser_on_time_s",
                "layer_total_time_s",
            ]
        )
        for item in layer_results:
            writer.writerow(
                [
                    item.schedule_index,
                    item.part_id,
                    item.layer_id,
                    item.solver_status,
                    item.cell_count,
                    item.start_cell_id,
                    item.end_cell_id,
                    f"{item.travel_distance_mm:.6f}",
                    f"{item.travel_time_s:.6f}",
                    f"{item.scan_time_s:.6f}",
                    f"{item.laser_on_time_s:.6f}",
                    f"{item.layer_total_time_s:.6f}",
                ]
            )


def write_path_steps_csv(base_dir: Path, layer_results: List[LayerResult]) -> None:
    with (base_dir / OUTPUT_PATH_STEPS_CSV).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "schedule_index",
                "part_id",
                "layer_id",
                "visit_step",
                "cell_id",
            ]
        )
        for item in layer_results:
            for step, cell_id in enumerate(item.path_cell_ids, start=1):
                writer.writerow([item.schedule_index, item.part_id, item.layer_id, step, cell_id])


def write_results_json(base_dir: Path, payload: dict) -> None:
    with (base_dir / OUTPUT_RESULTS_JSON).open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main() -> None:
    base_dir = script_dir()

    inter_part_transfer_distance_mm = validate_base_config()
    machine_params = load_machine_params(base_dir)
    layers = load_part_geometry(base_dir)
    travel_by_layer = load_travel_distances(base_dir)

    scan_speed_mm_per_s = float(machine_params["scan_speed_mm_per_s"])
    travel_speed_mm_per_s = float(machine_params["travel_speed_mm_per_s"])
    laser_on_delay_s = float(machine_params["laser_on_delay_s"])
    layer_change_time_s = float(machine_params["layer_change_time_s"])

    schedule = build_interleaved_schedule(layers)
    inter_part_switch_count, inter_layer_change_count = count_schedule_transitions(schedule)

    layer_results: List[LayerResult] = []
    for schedule_index, (part_id, layer_id) in enumerate(schedule, start=1):
        key = (part_id, layer_id)
        cells = layers[key]
        travel_distances = travel_by_layer[key]

        path_cell_ids, solver_status = solve_layer_exact_open_path(
            cells=cells,
            travel_distances=travel_distances,
            time_limit_seconds=SOLVER_TIME_LIMIT_SECONDS,
        )
        layer_result = compute_layer_result(
            schedule_index=schedule_index,
            part_id=part_id,
            layer_id=layer_id,
            path_cell_ids=path_cell_ids,
            solver_status=solver_status,
            cells=cells,
            travel_distances=travel_distances,
            scan_speed_mm_per_s=scan_speed_mm_per_s,
            travel_speed_mm_per_s=travel_speed_mm_per_s,
            laser_on_delay_s=laser_on_delay_s,
        )
        layer_results.append(layer_result)

    inter_part_result = compute_inter_part_transfer(
        switch_count=inter_part_switch_count,
        transfer_distance_mm=inter_part_transfer_distance_mm,
        travel_speed_mm_per_s=travel_speed_mm_per_s,
    )

    total_scan_time_s = sum(item.scan_time_s for item in layer_results)
    total_laser_on_time_s = sum(item.laser_on_time_s for item in layer_results)
    total_travel_time_s = sum(item.travel_time_s for item in layer_results)
    total_intra_layer_time_s = sum(item.layer_total_time_s for item in layer_results)
    total_inter_layer_time_s = inter_layer_change_count * layer_change_time_s
    total_inter_part_time_s = inter_part_result["total_inter_part_time_s"]
    total_task_time_s = total_intra_layer_time_s + total_inter_layer_time_s + total_inter_part_time_s

    results_payload = {
        "model_scope": "Question 1 base model only (no sensitivity analysis performed in this script)",
        "printing_schedule_rule": "interleaved by layer: part_A layer 1, part_B layer 1, part_A layer 2, part_B layer 2, ...",
        "machine_params": {
            "scan_speed_mm_per_s": scan_speed_mm_per_s,
            "travel_speed_mm_per_s": travel_speed_mm_per_s,
            "laser_on_delay_s": laser_on_delay_s,
            "layer_change_time_s": layer_change_time_s,
        },
        "base_model_inter_part_config": {
            "inter_part_transfer_distance_mm": inter_part_transfer_distance_mm,
            "inter_part_transfer_time_per_switch_s": inter_part_transfer_distance_mm / travel_speed_mm_per_s,
        },
        "schedule": [
            {"schedule_index": idx + 1, "part_id": part_id, "layer_id": layer_id}
            for idx, (part_id, layer_id) in enumerate(schedule)
        ],
        "transition_counts": {
            "inter_part_switch_count": inter_part_switch_count,
            "inter_layer_change_count": inter_layer_change_count,
        },
        "layer_results": [asdict(item) for item in layer_results],
        "aggregate_times_s": {
            "total_scan_time_s": total_scan_time_s,
            "total_laser_on_time_s": total_laser_on_time_s,
            "total_travel_time_s": total_travel_time_s,
            "total_intra_layer_time_s": total_intra_layer_time_s,
            "total_inter_layer_time_s": total_inter_layer_time_s,
            "total_inter_part_time_s": total_inter_part_time_s,
            "total_task_time_s": total_task_time_s,
        },
        "aggregate_distances_mm": {
            "total_intra_layer_travel_distance_mm": sum(item.travel_distance_mm for item in layer_results),
            "total_inter_part_distance_mm": inter_part_result["total_inter_part_distance_mm"],
        },
        "inter_part_transfer_result": inter_part_result,
    }

    write_layer_summary_csv(base_dir, layer_results)
    write_path_steps_csv(base_dir, layer_results)
    write_results_json(base_dir, results_payload)

    print("Question 1 base-model solve completed.")
    print(f"Layers solved: {len(layer_results)}")
    print(f"Total scan time (s): {total_scan_time_s:.6f}")
    print(f"Total laser-on time (s): {total_laser_on_time_s:.6f}")
    print(f"Total travel time (s): {total_travel_time_s:.6f}")
    print(f"Total intra-layer time (s): {total_intra_layer_time_s:.6f}")
    print(f"Total inter-layer time (s): {total_inter_layer_time_s:.6f}")
    print(f"Total inter-part distance (mm): {inter_part_result['total_inter_part_distance_mm']:.6f}")
    print(f"Total inter-part time (s): {total_inter_part_time_s:.6f}")
    print(f"Total task time (s): {total_task_time_s:.6f}")
    print(f"Saved: {OUTPUT_RESULTS_JSON}")
    print(f"Saved: {OUTPUT_LAYER_SUMMARY_CSV}")
    print(f"Saved: {OUTPUT_PATH_STEPS_CSV}")


if __name__ == "__main__":
    main()
