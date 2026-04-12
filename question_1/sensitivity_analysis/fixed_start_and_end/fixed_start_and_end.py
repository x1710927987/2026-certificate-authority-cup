"""
Structural sensitivity analysis: fixed starting point + fixed endpoint.

For each layer, every ordered pair of distinct cells is treated in turn as the
forced start cell and forced end cell. The script re-solves the exact open-path
model and compares the result with the base model.

Outputs:
- fixed_start_and_end_details.csv
- fixed_start_and_end_summary.csv
- fixed_start_and_end_plot.png

All outputs are written to the same directory as this script.
"""

from __future__ import annotations

import csv
import json
import statistics
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

SCRIPT_DIR = Path(__file__).resolve().parent
QUESTION1_DIR = SCRIPT_DIR.parents[1]
CDATA_DIR = SCRIPT_DIR.parents[2]

BASE_RESULTS_JSON = QUESTION1_DIR / "basic_model_result_for_question_1" / "question_1_results.json"
PART_GEOMETRY_FILE = CDATA_DIR / "part_geometry.csv"
LOCAL_RELATIONS_FILE = CDATA_DIR / "local_geometry_relations.csv"
MACHINE_PARAMS_FILE = CDATA_DIR / "machine_params.json"

DETAIL_CSV = SCRIPT_DIR / "fixed_start_and_end_details.csv"
SUMMARY_CSV = SCRIPT_DIR / "fixed_start_and_end_summary.csv"
PLOT_FILE = SCRIPT_DIR / "fixed_start_and_end_plot.png"


@dataclass
class CellInfo:
    part_id: str
    layer_id: int
    cell_id: str
    scan_length_mm: float


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


def solve_open_path_with_constraints(
    cells: List[CellInfo],
    travel_distances: Dict[Tuple[str, str], float],
    fixed_start_cell_id: str,
    fixed_end_cell_id: str,
) -> tuple[list[str], str]:
    cell_ids = [cell.cell_id for cell in cells]
    n = len(cell_ids)
    id_to_idx = {cell_id: idx + 1 for idx, cell_id in enumerate(cell_ids)}
    idx_to_id = {idx + 1: cell_id for idx, cell_id in enumerate(cell_ids)}

    model = cp_model.CpModel()
    arc_vars: Dict[Tuple[int, int], cp_model.IntVar] = {}
    arcs = []
    objective_terms = []

    fixed_start_idx = id_to_idx[fixed_start_cell_id]
    fixed_end_idx = id_to_idx[fixed_end_cell_id]

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

    for j in range(1, n + 1):
        model.Add(arc_vars[(0, j)] == (1 if j == fixed_start_idx else 0))

    for i in range(1, n + 1):
        model.Add(arc_vars[(i, 0)] == (1 if i == fixed_end_idx else 0))

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

    detail_rows: List[List[object]] = []
    summary_rows: List[List[object]] = []

    layer_labels: List[str] = []
    mean_delta_vals: List[float] = []
    max_delta_vals: List[float] = []

    for schedule_item in base_results["schedule"]:
        schedule_index = int(schedule_item["schedule_index"])
        part_id = schedule_item["part_id"]
        layer_id = int(schedule_item["layer_id"])
        key = (part_id, layer_id)

        base_layer = base_layer_lookup[key]
        base_path = list(base_layer["path_cell_ids"])
        base_total_time_s = float(base_layer["layer_total_time_s"])
        base_start_cell_id = base_layer["start_cell_id"]
        base_end_cell_id = base_layer["end_cell_id"]

        cells = layers[key]
        travel_distances = travel_by_layer[key]
        cell_lookup = {cell.cell_id: cell for cell in cells}

        candidate_deltas: List[float] = []
        candidate_rates: List[float] = []
        best_candidate = None
        worst_candidate = None

        total_candidates = len(cells) * (len(cells) - 1)
        print(f"Processing {make_layer_label(schedule_index, part_id, layer_id)}: {total_candidates} start-end pairs")

        for start_cell in cells:
            for end_cell in cells:
                if start_cell.cell_id == end_cell.cell_id:
                    continue

                candidate_path, solver_status = solve_open_path_with_constraints(
                    cells=cells,
                    travel_distances=travel_distances,
                    fixed_start_cell_id=start_cell.cell_id,
                    fixed_end_cell_id=end_cell.cell_id,
                )

                travel_distance_mm = 0.0
                for prev_id, next_id in zip(candidate_path[:-1], candidate_path[1:]):
                    travel_distance_mm += travel_distances[(prev_id, next_id)]

                travel_time_s = travel_distance_mm / travel_speed_mm_per_s
                scan_time_s = sum(cell_lookup[cell_id].scan_length_mm for cell_id in candidate_path) / scan_speed_mm_per_s
                laser_on_time_s = len(candidate_path) * laser_on_delay_s
                layer_total_time_s = scan_time_s + laser_on_time_s + travel_time_s

                delta_time_s = layer_total_time_s - base_total_time_s
                delta_time_percent = 0.0 if base_total_time_s == 0 else 100.0 * delta_time_s / base_total_time_s
                diff_rate = path_difference_rate(base_path, candidate_path)

                candidate_deltas.append(delta_time_percent)
                candidate_rates.append(diff_rate)

                record = {
                    "solver_status": solver_status,
                    "start_cell_id": start_cell.cell_id,
                    "end_cell_id": end_cell.cell_id,
                    "result_start_cell_id": candidate_path[0],
                    "result_end_cell_id": candidate_path[-1],
                    "travel_distance_mm": travel_distance_mm,
                    "travel_time_s": travel_time_s,
                    "scan_time_s": scan_time_s,
                    "laser_on_time_s": laser_on_time_s,
                    "layer_total_time_s": layer_total_time_s,
                    "delta_time_s": delta_time_s,
                    "delta_time_percent": delta_time_percent,
                    "path_difference_rate": diff_rate,
                }

                if best_candidate is None or layer_total_time_s < best_candidate["layer_total_time_s"]:
                    best_candidate = record
                if worst_candidate is None or layer_total_time_s > worst_candidate["layer_total_time_s"]:
                    worst_candidate = record

                detail_rows.append(
                    [
                        schedule_index,
                        part_id,
                        layer_id,
                        make_layer_label(schedule_index, part_id, layer_id),
                        solver_status,
                        base_start_cell_id,
                        base_end_cell_id,
                        start_cell.cell_id,
                        end_cell.cell_id,
                        candidate_path[0],
                        candidate_path[-1],
                        f"{travel_distance_mm:.6f}",
                        f"{travel_time_s:.6f}",
                        f"{scan_time_s:.6f}",
                        f"{laser_on_time_s:.6f}",
                        f"{layer_total_time_s:.6f}",
                        f"{base_total_time_s:.6f}",
                        f"{delta_time_s:.6f}",
                        f"{delta_time_percent:.6f}",
                        f"{diff_rate:.6f}",
                    ]
                )

        mean_delta = statistics.mean(candidate_deltas)
        std_delta = statistics.pstdev(candidate_deltas)
        mean_rate = statistics.mean(candidate_rates)

        layer_label = make_layer_label(schedule_index, part_id, layer_id)
        layer_labels.append(layer_label)
        mean_delta_vals.append(mean_delta)
        max_delta_vals.append(float(worst_candidate["delta_time_percent"]))

        summary_rows.append(
            [
                schedule_index,
                part_id,
                layer_id,
                layer_label,
                base_start_cell_id,
                base_end_cell_id,
                total_candidates,
                best_candidate["start_cell_id"],
                best_candidate["end_cell_id"],
                f"{best_candidate['layer_total_time_s']:.6f}",
                f"{best_candidate['delta_time_percent']:.6f}",
                worst_candidate["start_cell_id"],
                worst_candidate["end_cell_id"],
                f"{worst_candidate['layer_total_time_s']:.6f}",
                f"{worst_candidate['delta_time_percent']:.6f}",
                f"{mean_delta:.6f}",
                f"{std_delta:.6f}",
                f"{mean_rate:.6f}",
            ]
        )

    write_csv(
        DETAIL_CSV,
        [
            "schedule_index",
            "part_id",
            "layer_id",
            "layer_label",
            "solver_status",
            "base_start_cell_id",
            "base_end_cell_id",
            "fixed_start_cell_id",
            "fixed_end_cell_id",
            "result_start_cell_id",
            "result_end_cell_id",
            "travel_distance_mm",
            "travel_time_s",
            "scan_time_s",
            "laser_on_time_s",
            "layer_total_time_s",
            "base_layer_total_time_s",
            "delta_time_s",
            "delta_time_percent",
            "path_difference_rate",
        ],
        detail_rows,
    )

    write_csv(
        SUMMARY_CSV,
        [
            "schedule_index",
            "part_id",
            "layer_id",
            "layer_label",
            "base_start_cell_id",
            "base_end_cell_id",
            "candidate_count",
            "best_fixed_start_cell_id",
            "best_fixed_end_cell_id",
            "best_layer_total_time_s",
            "best_delta_time_percent",
            "worst_fixed_start_cell_id",
            "worst_fixed_end_cell_id",
            "worst_layer_total_time_s",
            "worst_delta_time_percent",
            "mean_delta_time_percent",
            "std_delta_time_percent",
            "mean_path_difference_rate",
        ],
        summary_rows,
    )

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), constrained_layout=True)

    axes[0].plot(layer_labels, mean_delta_vals, marker="o", linewidth=2, color="#1B4F72", label="Mean delta")
    axes[0].plot(layer_labels, max_delta_vals, marker="s", linewidth=2, color="#E67E22", label="Worst-case delta")
    axes[0].set_title("Sensitivity to jointly fixed starting and ending cells")
    axes[0].set_ylabel("Delta time (%)")
    axes[0].grid(alpha=0.25)
    axes[0].legend()

    bars = axes[1].bar(layer_labels, max_delta_vals, color="#8E44AD", alpha=0.85)
    axes[1].set_title("Worst-case relative time increase by layer")
    axes[1].set_ylabel("Worst delta time (%)")
    axes[1].set_xlabel("Layer in printing schedule")
    axes[1].grid(axis="y", alpha=0.25)
    for bar, value in zip(bars, max_delta_vals):
        axes[1].text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.2f}%",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    fig.savefig(PLOT_FILE, dpi=220)
    plt.close(fig)

    print(f"Saved detail results to: {DETAIL_CSV}")
    print(f"Saved summary results to: {SUMMARY_CSV}")
    print(f"Saved plot to: {PLOT_FILE}")


if __name__ == "__main__":
    main()
