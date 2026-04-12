"""
Question 2 base model for the 2026 认证杯 C 题.

This script evaluates four path schemes under the base parameters only:
- row_major
- serpentine
- center_out
- minimum_time (from Question 1)

It computes:
- per-layer and total print-time metrics for each scheme
- threshold calibration via the fixed row_major reference path
- full layer heat histories under the improved thermal model
- cell-level thermal risk indices (mu, xi, theta, phi)
- layer / part / scheme summaries
- first-level risk aggregation using entropy weights
- overall comparison by weighted-sum and TOPSIS

Expected input files (relative to the project root):
- part_geometry.csv
- local_geometry_relations.csv
- machine_params.json
- thermal_params.json
- baseline_paths.csv
- question_1/basic_model_result_for_question_1/question_1_results.json
- question_2/激光粉末床相关五种材料热物性汇总表.md

Outputs are written to the same directory as this script.
CSV / JSON outputs are always produced.
An XLSX workbook is also created if openpyxl is installed.
"""

from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict, deque
from pathlib import Path
from statistics import median
from typing import Dict, Iterable, List, Sequence, Tuple

try:
    from openpyxl import Workbook

    HAS_OPENPYXL = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_OPENPYXL = False


# =============================================================================
# Base-model configuration
# =============================================================================
BASE_MATERIAL_NAME = "PA12"
AMBIENT_TEMPERATURE_C = 25.0

A0_SELF_HEAT = 4.0
A1_NEIGHBOR_HEAT = 1.0
GAMMA_CONTACT = 0.5
CONTACT_LENGTH_SCALE_MM = 4.0

LAMBDA_THIN = 0.35
LAMBDA_HOLE = 0.25

FIRST_LEVEL_WEIGHTS = {
    "R_theta": 0.35,
    "R_mu": 0.20,
    "R_xi": 0.20,
    "R_phi": 0.25,
}

TOP_HEAD_FRACTION = 0.10

INTER_PART_TRANSFER_DISTANCE_MM = 50.0


# =============================================================================
# Input / output names
# =============================================================================
PART_GEOMETRY_FILE = "part_geometry.csv"
LOCAL_RELATIONS_FILE = "local_geometry_relations.csv"
MACHINE_PARAMS_FILE = "machine_params.json"
THERMAL_PARAMS_FILE = "thermal_params.json"
BASELINE_PATHS_FILE = "baseline_paths.csv"
QUESTION_1_RESULTS_FILE = (
    "question_1/basic_model_result_for_question_1/question_1_results.json"
)
MATERIAL_MARKDOWN_FILE = "question_2/激光粉末床相关五种材料热物性汇总表.md"

OUTPUT_RESULTS_JSON = "question_2_base_results.json"
OUTPUT_SCHEME_OVERALL_CSV = "scheme_overall_summary.csv"
OUTPUT_SCHEME_PART_CSV = "scheme_part_summary.csv"
OUTPUT_SCHEME_LAYER_CSV = "scheme_layer_summary.csv"
OUTPUT_CELL_RISK_CSV = "cell_risk_details.csv"
OUTPUT_HEAT_HISTORY_CSV = "heat_history_records.csv"
OUTPUT_PATH_STEPS_CSV = "scheme_path_steps.csv"
OUTPUT_THRESHOLD_CSV = "threshold_alignment_reference.csv"
OUTPUT_WEIGHTS_CSV = "evaluation_weights_summary.csv"
OUTPUT_MATERIALS_CSV = "material_properties_summary.csv"
OUTPUT_WORKBOOK_XLSX = "question_2_base_results.xlsx"


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def project_root() -> Path:
    return script_dir().parents[1]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_range_midpoint(text: str) -> float:
    cleaned = (
        text.replace("–", "-")
        .replace("—", "-")
        .replace("−", "-")
        .replace(" ", "")
        .replace(",", "")
    )
    numbers = [float(match) for match in re.findall(r"\d+(?:\.\d+)?", cleaned)]
    if not numbers:
        raise ValueError(f"Could not parse numeric range from: {text!r}")
    if len(numbers) == 1:
        return numbers[0]
    return (numbers[0] + numbers[1]) / 2.0


def normalize_material_name(cell_text: str) -> str:
    text = cell_text.strip()
    if "PA12" in text:
        return "PA12"
    if "316L" in text:
        return "316L"
    if "Ti-6Al-4V" in text or "Ti64" in text or "Ti-6Al" in text:
        return "Ti-6Al-4V"
    if "AlSi10Mg" in text:
        return "AlSi10Mg"
    if "Inconel 718" in text or "INCONEL" in text or "IN718" in text:
        return "Inconel 718"
    raise ValueError(f"Unknown material row: {cell_text!r}")


def load_material_properties(markdown_path: Path) -> Dict[str, dict]:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    materials: Dict[str, dict] = {}

    for line in lines:
        if not line.startswith("|"):
            continue
        if ":---" in line or "材料（中 / 英）" in line:
            continue

        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) < 5:
            continue

        raw_name = cells[0]
        try:
            material_name = normalize_material_name(raw_name)
        except ValueError:
            continue

        materials[material_name] = {
            "material_name": material_name,
            "raw_name": raw_name,
            "melting_temperature_c": parse_range_midpoint(cells[1]),
            "specific_heat_j_per_kg_k": parse_range_midpoint(cells[2]),
            "density_g_per_cm3": parse_range_midpoint(cells[3]),
            "cte_1e_minus_6_per_k": parse_range_midpoint(cells[4]),
            "melting_temperature_range": cells[1],
            "specific_heat_range": cells[2],
            "density_range": cells[3],
            "cte_range": cells[4],
        }

    expected = {"PA12", "316L", "Ti-6Al-4V", "AlSi10Mg", "Inconel 718"}
    missing = expected.difference(materials)
    if missing:
        raise ValueError(f"Missing materials in markdown table: {sorted(missing)}")
    return materials


def compute_material_reference_values(
    materials: Dict[str, dict],
    ambient_temperature_c: float,
) -> dict:
    alpha_values = [item["cte_1e_minus_6_per_k"] for item in materials.values()]
    delta_t_values = [
        item["melting_temperature_c"] - ambient_temperature_c
        for item in materials.values()
    ]
    return {
        "alpha_L_ref": median(alpha_values),
        "delta_T_ref": median(delta_t_values),
    }


def load_part_geometry(path: Path) -> Dict[Tuple[str, int], Dict[str, dict]]:
    by_layer: Dict[Tuple[str, int], Dict[str, dict]] = defaultdict(dict)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["part_id"], int(row["layer_id"]))
            by_layer[key][row["cell_id"]] = {
                "part_id": row["part_id"],
                "layer_id": int(row["layer_id"]),
                "cell_id": row["cell_id"],
                "grid_x": int(row["grid_x"]),
                "grid_y": int(row["grid_y"]),
                "x_mm": float(row["x_mm"]),
                "y_mm": float(row["y_mm"]),
                "scan_length_mm": float(row["scan_length_mm"]),
                "area_mm2": float(row["area_mm2"]),
                "cell_type": row["type"],
                "xmin_mm": float(row["xmin_mm"]),
                "xmax_mm": float(row["xmax_mm"]),
                "ymin_mm": float(row["ymin_mm"]),
                "ymax_mm": float(row["ymax_mm"]),
                "layer_cell_count": int(row["layer_cell_count"]),
            }
    return by_layer


def load_local_relations(path: Path) -> Dict[Tuple[str, int], Dict[Tuple[str, str], dict]]:
    by_layer: Dict[Tuple[str, int], Dict[Tuple[str, str], dict]] = defaultdict(dict)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["part_id"], int(row["layer_id"]))
            dx_mm = float(row["dx_mm"])
            dy_mm = float(row["dy_mm"])
            by_layer[key][(row["cell_i"], row["cell_j"])] = {
                "travel_distance_mm": float(row["travel_distance_mm"]),
                "adjacent_flag": int(row["adjacent_flag"]),
                "spatial_weight": float(row["spatial_weight"]),
                "shared_boundary_mm": float(row["shared_boundary_mm"]),
                "contact_type": row["contact_type"],
                "local_relation_flag": int(row["local_relation_flag"]),
                "center_distance_mm": math.hypot(dx_mm, dy_mm),
            }
    return by_layer


def load_baseline_paths(path: Path) -> Dict[str, Dict[Tuple[str, int], List[str]]]:
    schemes: Dict[str, Dict[Tuple[str, int], List[Tuple[int, str]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["part_id"], int(row["layer_id"]))
            schemes[row["strategy_name"]][key].append((int(row["step"]), row["cell_id"]))

    ordered: Dict[str, Dict[Tuple[str, int], List[str]]] = {}
    for scheme_name, layer_map in schemes.items():
        ordered[scheme_name] = {}
        for key, pairs in layer_map.items():
            ordered[scheme_name][key] = [
                cell_id for _, cell_id in sorted(pairs, key=lambda pair: pair[0])
            ]
    return ordered


def load_minimum_time_paths(path: Path) -> Dict[Tuple[str, int], List[str]]:
    data = load_json(path)
    result: Dict[Tuple[str, int], List[str]] = {}
    for layer_result in data["layer_results"]:
        key = (layer_result["part_id"], int(layer_result["layer_id"]))
        result[key] = list(layer_result["path_cell_ids"])
    return result


def build_interleaved_schedule(
    geometry: Dict[Tuple[str, int], Dict[str, dict]]
) -> List[Tuple[str, int]]:
    parts = sorted({part_id for part_id, _ in geometry})
    layer_ids = sorted({layer_id for _, layer_id in geometry})
    schedule: List[Tuple[str, int]] = []
    for layer_id in layer_ids:
        for part_id in parts:
            key = (part_id, layer_id)
            if key in geometry:
                schedule.append(key)
    return schedule


def validate_path(
    path_cell_ids: Sequence[str],
    geometry_for_layer: Dict[str, dict],
    key: Tuple[str, int],
    scheme_name: str,
) -> None:
    expected = set(geometry_for_layer)
    actual = list(path_cell_ids)
    if len(actual) != len(expected):
        raise ValueError(
            f"{scheme_name} path length mismatch for {key}: "
            f"expected {len(expected)}, got {len(actual)}"
        )
    if set(actual) != expected:
        raise ValueError(f"{scheme_name} path cell set mismatch for {key}.")
    if len(set(actual)) != len(actual):
        raise ValueError(f"{scheme_name} path contains duplicate cells for {key}.")


def find_hole_edge_cells(geometry_for_layer: Dict[str, dict]) -> set[str]:
    occupied = {
        (cell["grid_x"], cell["grid_y"]): cell_id
        for cell_id, cell in geometry_for_layer.items()
    }
    xs = [coord[0] for coord in occupied]
    ys = [coord[1] for coord in occupied]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    all_coords = {
        (x, y)
        for x in range(min_x, max_x + 1)
        for y in range(min_y, max_y + 1)
    }
    empty_coords = all_coords.difference(occupied)
    if not empty_coords:
        return set()

    def neighbors4(coord: Tuple[int, int]) -> Iterable[Tuple[int, int]]:
        x, y = coord
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yield (x + dx, y + dy)

    boundary_empty = {
        coord
        for coord in empty_coords
        if coord[0] in {min_x, max_x} or coord[1] in {min_y, max_y}
    }
    external = set(boundary_empty)
    queue: deque[Tuple[int, int]] = deque(boundary_empty)
    while queue:
        coord = queue.popleft()
        for nxt in neighbors4(coord):
            if nxt in empty_coords and nxt not in external:
                external.add(nxt)
                queue.append(nxt)

    hole_coords = empty_coords.difference(external)
    if not hole_coords:
        return set()

    hole_edge_cells: set[str] = set()
    for (x, y), cell_id in occupied.items():
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                if (x + dx, y + dy) in hole_coords:
                    hole_edge_cells.add(cell_id)
                    break
            else:
                continue
            break
    return hole_edge_cells


def top_fraction_mean(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    count = max(1, math.ceil(len(values) * fraction))
    selected = sorted(values, reverse=True)[:count]
    return sum(selected) / len(selected)


def empirical_quantile(values: Sequence[float], q: float) -> float:
    if not values:
        raise ValueError("Cannot compute quantile of empty sequence.")
    sorted_values = sorted(values)
    if q <= 0:
        return sorted_values[0]
    if q >= 1:
        return sorted_values[-1]
    pos = q * (len(sorted_values) - 1)
    lower = math.floor(pos)
    upper = math.ceil(pos)
    if lower == upper:
        return sorted_values[lower]
    weight = pos - lower
    return (
        sorted_values[lower] * (1.0 - weight)
        + sorted_values[upper] * weight
    )


def empirical_cdf(values: Sequence[float], threshold: float) -> float:
    if not values:
        raise ValueError("Cannot compute empirical CDF of empty sequence.")
    count = sum(1 for value in values if value <= threshold)
    return count / float(len(values))


def compute_material_context(
    materials: Dict[str, dict],
    base_material_name: str,
    ambient_temperature_c: float,
) -> dict:
    base = materials[base_material_name]
    refs = compute_material_reference_values(materials, ambient_temperature_c)
    delta_t_safe = base["melting_temperature_c"] - ambient_temperature_c
    kappa = math.sqrt(base["cte_1e_minus_6_per_k"] / refs["alpha_L_ref"]) * math.sqrt(
        refs["delta_T_ref"] / delta_t_safe
    )
    return {
        "base_material_name": base_material_name,
        "base_material": base,
        "reference_alpha_L": refs["alpha_L_ref"],
        "reference_delta_T": refs["delta_T_ref"],
        "delta_T_safe": delta_t_safe,
        "kappa_mat": kappa,
    }


def build_contact_neighbors(
    relations_for_layer: Dict[Tuple[str, str], dict],
    geometry_for_layer: Dict[str, dict],
) -> Dict[str, List[str]]:
    neighbors: Dict[str, List[str]] = {cell_id: [] for cell_id in geometry_for_layer}
    for (cell_i, cell_j), rel in relations_for_layer.items():
        if rel["shared_boundary_mm"] > 0:
            neighbors[cell_i].append(cell_j)
    return neighbors


def compute_contact_weight(rel: dict) -> float:
    return rel["spatial_weight"] * (
        1.0 + GAMMA_CONTACT * (rel["shared_boundary_mm"] / CONTACT_LENGTH_SCALE_MM)
    )


def build_layer_timing(
    path_cell_ids: Sequence[str],
    geometry_for_layer: Dict[str, dict],
    relations_for_layer: Dict[Tuple[str, str], dict],
    scan_speed_mm_per_s: float,
    travel_speed_mm_per_s: float,
    laser_on_delay_s: float,
) -> Tuple[List[dict], dict]:
    events: List[dict] = []
    current_time = 0.0
    total_travel_distance_mm = 0.0

    for visit_step, cell_id in enumerate(path_cell_ids, start=1):
        cell = geometry_for_layer[cell_id]
        if visit_step == 1:
            travel_distance_mm = 0.0
        else:
            prev_cell_id = path_cell_ids[visit_step - 2]
            travel_distance_mm = relations_for_layer[(prev_cell_id, cell_id)][
                "travel_distance_mm"
            ]
        travel_time_s = travel_distance_mm / travel_speed_mm_per_s
        laser_on_time_s = laser_on_delay_s
        scan_time_s = cell["scan_length_mm"] / scan_speed_mm_per_s

        current_time += travel_time_s + laser_on_time_s + scan_time_s
        total_travel_distance_mm += travel_distance_mm

        events.append(
            {
                "visit_step": visit_step,
                "cell_id": cell_id,
                "travel_distance_mm": travel_distance_mm,
                "travel_time_s": travel_time_s,
                "laser_on_time_s": laser_on_time_s,
                "scan_time_s": scan_time_s,
                "scan_completion_time_s": current_time,
            }
        )

    totals = {
        "cell_count": len(path_cell_ids),
        "travel_distance_mm": total_travel_distance_mm,
        "travel_time_s": sum(event["travel_time_s"] for event in events),
        "scan_time_s": sum(event["scan_time_s"] for event in events),
        "laser_on_time_s": sum(event["laser_on_time_s"] for event in events),
    }
    totals["layer_total_time_s"] = (
        totals["travel_time_s"] + totals["scan_time_s"] + totals["laser_on_time_s"]
    )
    return events, totals


def compute_improved_heat_histories(
    path_cell_ids: Sequence[str],
    event_times: Sequence[float],
    geometry_for_layer: Dict[str, dict],
    relations_for_layer: Dict[Tuple[str, str], dict],
    alpha: float,
    beta: float,
    c_value: float,
    rho_value: float,
) -> Dict[str, List[float]]:
    cell_ids = list(path_cell_ids)
    histories: Dict[str, List[float]] = {cell_id: [] for cell_id in cell_ids}

    previous_state = {cell_id: 0.0 for cell_id in cell_ids}
    previous_time = 0.0

    for event_index, source_cell_id in enumerate(path_cell_ids):
        current_time = event_times[event_index]
        decay_factor = (
            0.0 if event_index == 0 else math.exp(-alpha * (current_time - previous_time))
        )

        next_state: Dict[str, float] = {}
        for target_cell_id in cell_ids:
            decayed_value = (
                0.0 if event_index == 0 else previous_state[target_cell_id] * decay_factor
            )

            target_cell = geometry_for_layer[target_cell_id]
            mass_factor = target_cell["scan_length_mm"] * rho_value

            if target_cell_id == source_cell_id:
                q_value = A0_SELF_HEAT / (c_value * mass_factor)
            else:
                rel = relations_for_layer[(source_cell_id, target_cell_id)]
                q_value = (
                    A1_NEIGHBOR_HEAT
                    / (c_value * mass_factor)
                    * compute_contact_weight(rel)
                    * math.exp(-beta * rel["center_distance_mm"])
                )

            next_value = decayed_value + q_value
            histories[target_cell_id].append(next_value)
            next_state[target_cell_id] = next_value

        previous_state = next_state
        previous_time = current_time

    return histories


def compute_threshold_alignment(
    row_major_paths: Dict[Tuple[str, int], List[str]],
    geometry: Dict[Tuple[str, int], Dict[str, dict]],
    relations: Dict[Tuple[str, int], Dict[Tuple[str, str], dict]],
    machine_params: dict,
    thermal_params: dict,
    material_context: dict,
) -> Tuple[float, float, List[dict]]:
    original_scan_values: List[float] = []
    improved_scan_values: List[float] = []
    alignment_rows: List[dict] = []

    scan_speed = float(machine_params["scan_speed_mm_per_s"])
    travel_speed = float(machine_params["travel_speed_mm_per_s"])
    laser_on = float(machine_params["laser_on_delay_s"])
    alpha = float(thermal_params["alpha_per_s"])
    beta = float(thermal_params["beta_per_mm"])
    h_crit = float(thermal_params["H_crit"])
    original_a = float(thermal_params["A"])
    c_value = material_context["base_material"]["specific_heat_j_per_kg_k"]
    rho_value = material_context["base_material"]["density_g_per_cm3"]

    for key in sorted(row_major_paths):
        path_cell_ids = row_major_paths[key]
        geometry_for_layer = geometry[key]
        relations_for_layer = relations[key]
        validate_path(path_cell_ids, geometry_for_layer, key, "row_major")

        events, _ = build_layer_timing(
            path_cell_ids=path_cell_ids,
            geometry_for_layer=geometry_for_layer,
            relations_for_layer=relations_for_layer,
            scan_speed_mm_per_s=scan_speed,
            travel_speed_mm_per_s=travel_speed,
            laser_on_delay_s=laser_on,
        )
        event_times = [event["scan_completion_time_s"] for event in events]

        improved_histories = compute_improved_heat_histories(
            path_cell_ids=path_cell_ids,
            event_times=event_times,
            geometry_for_layer=geometry_for_layer,
            relations_for_layer=relations_for_layer,
            alpha=alpha,
            beta=beta,
            c_value=c_value,
            rho_value=rho_value,
        )

        for event_index, event in enumerate(events):
            current_cell_id = event["cell_id"]
            original_value = 0.0
            for previous_index in range(event_index):
                prev_cell_id = path_cell_ids[previous_index]
                prev_time = event_times[previous_index]
                rel = relations_for_layer[(prev_cell_id, current_cell_id)]
                original_value += original_a * math.exp(
                    -alpha * (event_times[event_index] - prev_time)
                ) * math.exp(-beta * rel["center_distance_mm"])

            improved_value = improved_histories[current_cell_id][event_index]
            original_scan_values.append(original_value)
            improved_scan_values.append(improved_value)
            alignment_rows.append(
                {
                    "part_id": key[0],
                    "layer_id": key[1],
                    "cell_id": current_cell_id,
                    "visit_step": event["visit_step"],
                    "original_scan_risk": original_value,
                    "improved_scan_risk": improved_value,
                }
            )

    quantile_q = empirical_cdf(original_scan_values, h_crit)
    h_thres = empirical_quantile(improved_scan_values, quantile_q)

    for row in alignment_rows:
        row["reference_scheme"] = "row_major"
        row["H_crit"] = h_crit
        row["quantile_q"] = quantile_q
        row["H_thres"] = h_thres

    return h_thres, quantile_q, alignment_rows


def compute_structural_sensitivity(
    cell: dict,
    hole_edge_cells: set[str],
    kappa_mat: float,
) -> Tuple[int, int, float]:
    is_thin = 1 if cell["cell_type"] == "thin_wall" else 0
    is_hole = 1 if cell["cell_id"] in hole_edge_cells else 0
    s_type = 1.0 + LAMBDA_THIN * is_thin + LAMBDA_HOLE * is_hole
    s_value = 1.0 + kappa_mat * (s_type - 1.0)
    return is_thin, is_hole, s_value


def first_below_threshold_index(
    values: Sequence[float],
    threshold: float,
    start_index: int,
) -> int | None:
    for index in range(start_index, len(values)):
        if values[index] < threshold:
            return index
    return None


def compute_cell_risk_metrics(
    cell_id: str,
    history: Sequence[float],
    visit_index: int,
    visit_time_s: float,
    event_times: Sequence[float],
    neighbors: Sequence[str],
    neighbor_histories: Dict[str, Sequence[float]],
    relations_for_layer: Dict[Tuple[str, str], dict],
    threshold_h: float,
    alpha: float,
    s_value: float,
) -> dict:
    mu_sum = 0.0
    for idx in range(visit_index, len(history)):
        previous_value = history[idx - 1] if idx > 0 else 0.0
        increase = history[idx] - previous_value
        if increase > 0:
            mu_sum += increase
    mu_value = s_value * mu_sum

    scan_heat = history[visit_index]
    if scan_heat < threshold_h:
        cooldown_time_s = 0.0
        xi_value = 0.0
    else:
        below_index = first_below_threshold_index(history, threshold_h, visit_index)
        if below_index is not None:
            cooldown_time_s = event_times[below_index] - visit_time_s
        else:
            last_time = event_times[-1]
            last_heat = history[-1]
            extra_decay_s = 0.0
            if last_heat > threshold_h:
                extra_decay_s = math.log(last_heat / threshold_h) / alpha
            cooldown_time_s = (last_time - visit_time_s) + extra_decay_s
        xi_value = s_value * cooldown_time_s

    below_index = first_below_threshold_index(history, threshold_h, visit_index)
    theta_count = 0 if below_index is None else sum(
        1 for idx in range(below_index + 1, len(history)) if history[idx] > threshold_h
    )
    theta_value = s_value * float(theta_count)

    phi_samples: List[float] = []
    for event_index in range(len(event_times)):
        numerator = 0.0
        denominator = 0.0
        for neighbor_id in neighbors:
            rel = relations_for_layer[(cell_id, neighbor_id)]
            weight = compute_contact_weight(rel)
            numerator += weight * abs(
                history[event_index] - neighbor_histories[neighbor_id][event_index]
            )
            denominator += weight
        phi_samples.append(0.0 if denominator <= 0 else numerator / denominator)
    phi_value = sum(phi_samples) / len(phi_samples) if phi_samples else 0.0

    return {
        "mu": mu_value,
        "xi": xi_value,
        "theta": theta_value,
        "phi": phi_value,
        "scan_heat_state": scan_heat,
        "peak_heat_state": max(history),
        "final_heat_state": history[-1],
        "cooldown_time_s": cooldown_time_s,
        "above_threshold_event_count": sum(1 for value in history if value > threshold_h),
    }


def aggregate_cell_metrics(metric_rows: Sequence[dict]) -> dict:
    mu_values = [row["mu"] for row in metric_rows]
    xi_values = [row["xi"] for row in metric_rows]
    theta_values = [row["theta"] for row in metric_rows]
    phi_values = [row["phi"] for row in metric_rows]

    return {
        "cell_count": len(metric_rows),
        "mu_mean": sum(mu_values) / len(mu_values) if mu_values else 0.0,
        "mu_top10_mean": top_fraction_mean(mu_values, TOP_HEAD_FRACTION),
        "xi_mean": sum(xi_values) / len(xi_values) if xi_values else 0.0,
        "xi_max": max(xi_values) if xi_values else 0.0,
        "theta_mean": sum(theta_values) / len(theta_values) if theta_values else 0.0,
        "theta_top10_mean": top_fraction_mean(theta_values, TOP_HEAD_FRACTION),
        "phi_mean": sum(phi_values) / len(phi_values) if phi_values else 0.0,
        "phi_top10_mean": top_fraction_mean(phi_values, TOP_HEAD_FRACTION),
        "phi_max": max(phi_values) if phi_values else 0.0,
        "scan_heat_mean": (
            sum(row["scan_heat_state"] for row in metric_rows) / len(metric_rows)
            if metric_rows
            else 0.0
        ),
        "peak_heat_max": (
            max(row["peak_heat_state"] for row in metric_rows) if metric_rows else 0.0
        ),
        "final_heat_mean": (
            sum(row["final_heat_state"] for row in metric_rows) / len(metric_rows)
            if metric_rows
            else 0.0
        ),
    }


def entropy_weights(summary_rows: Sequence[dict], feature_names: Sequence[str]) -> Dict[str, float]:
    if len(feature_names) == 1:
        return {feature_names[0]: 1.0}
    if not summary_rows or len(summary_rows) == 1:
        equal = 1.0 / len(feature_names)
        return {feature_name: equal for feature_name in feature_names}

    divergences: List[float] = []
    m = len(summary_rows)
    for feature_name in feature_names:
        column = [max(float(row[feature_name]), 0.0) for row in summary_rows]
        column_sum = sum(column)
        if column_sum <= 0 or max(column) - min(column) <= 1e-12:
            divergences.append(0.0)
            continue
        probabilities = [value / column_sum for value in column]
        entropy = 0.0
        for value in probabilities:
            if value > 0:
                entropy -= value * math.log(value)
        entropy /= math.log(m)
        divergences.append(1.0 - entropy)

    divergence_sum = sum(divergences)
    if divergence_sum <= 1e-12:
        equal = 1.0 / len(feature_names)
        return {feature_name: equal for feature_name in feature_names}

    return {
        feature_name: divergences[idx] / divergence_sum
        for idx, feature_name in enumerate(feature_names)
    }


def add_first_level_scores(
    summary_row: dict,
    weight_groups: Dict[str, Dict[str, float]],
) -> None:
    summary_row["R_mu"] = sum(
        summary_row[feature] * weight
        for feature, weight in weight_groups["R_mu"].items()
    )
    summary_row["R_xi"] = sum(
        summary_row[feature] * weight
        for feature, weight in weight_groups["R_xi"].items()
    )
    summary_row["R_theta"] = sum(
        summary_row[feature] * weight
        for feature, weight in weight_groups["R_theta"].items()
    )
    summary_row["R_phi"] = sum(
        summary_row[feature] * weight
        for feature, weight in weight_groups["R_phi"].items()
    )
    summary_row["weighted_sum_total_risk"] = (
        FIRST_LEVEL_WEIGHTS["R_theta"] * summary_row["R_theta"]
        + FIRST_LEVEL_WEIGHTS["R_mu"] * summary_row["R_mu"]
        + FIRST_LEVEL_WEIGHTS["R_xi"] * summary_row["R_xi"]
        + FIRST_LEVEL_WEIGHTS["R_phi"] * summary_row["R_phi"]
    )


def compute_topsis_scores(summary_rows: Sequence[dict]) -> Dict[str, float]:
    criteria = ["R_theta", "R_mu", "R_xi", "R_phi"]
    if not summary_rows:
        return {}

    scheme_names = [row["scheme_name"] for row in summary_rows]
    matrix = [
        [float(row[criterion]) for criterion in criteria]
        for row in summary_rows
    ]

    denominators = []
    for criterion_index in range(len(criteria)):
        denom = math.sqrt(sum(row[criterion_index] ** 2 for row in matrix))
        denominators.append(denom if denom > 0 else 1.0)

    weighted = []
    for row in matrix:
        normalized = [row[idx] / denominators[idx] for idx in range(len(criteria))]
        weighted.append(
            [normalized[idx] * FIRST_LEVEL_WEIGHTS[criteria[idx]] for idx in range(len(criteria))]
        )

    ideal_best = [min(row[idx] for row in weighted) for idx in range(len(criteria))]
    ideal_worst = [max(row[idx] for row in weighted) for idx in range(len(criteria))]

    scores: Dict[str, float] = {}
    for scheme_name, row in zip(scheme_names, weighted):
        dist_best = math.sqrt(
            sum((row[idx] - ideal_best[idx]) ** 2 for idx in range(len(criteria)))
        )
        dist_worst = math.sqrt(
            sum((row[idx] - ideal_worst[idx]) ** 2 for idx in range(len(criteria)))
        )
        scores[scheme_name] = 0.5 if dist_best + dist_worst <= 1e-12 else dist_worst / (
            dist_best + dist_worst
        )
    return scores


def rank_by(rows: List[dict], value_key: str, rank_key: str, reverse: bool) -> None:
    ordered = sorted(rows, key=lambda row: row[value_key], reverse=reverse)
    for rank, row in enumerate(ordered, start=1):
        row[rank_key] = rank


def write_csv(path: Path, rows: Sequence[dict], fieldnames: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def maybe_write_workbook(output_dir: Path, sheets: Dict[str, List[dict]]) -> str:
    if not HAS_OPENPYXL:
        return "skipped (openpyxl not installed)"

    workbook = Workbook()
    workbook.remove(workbook.active)
    for sheet_name, rows in sheets.items():
        ws = workbook.create_sheet(title=sheet_name[:31])
        if not rows:
            continue
        headers = list(rows[0].keys())
        ws.append(headers)
        for row in rows:
            ws.append([row.get(header) for header in headers])
    workbook.save(output_dir / OUTPUT_WORKBOOK_XLSX)
    return "written"


def build_scheme_paths(
    geometry: Dict[Tuple[str, int], Dict[str, dict]],
    baseline_paths: Dict[str, Dict[Tuple[str, int], List[str]]],
    minimum_time_paths: Dict[Tuple[str, int], List[str]],
) -> Dict[str, Dict[Tuple[str, int], List[str]]]:
    schemes = {
        "row_major": baseline_paths["row_major"],
        "serpentine": baseline_paths["serpentine"],
        "center_out": baseline_paths["center_out"],
        "minimum_time": minimum_time_paths,
    }
    for scheme_name, layer_map in schemes.items():
        for key, geometry_for_layer in geometry.items():
            if key not in layer_map:
                raise ValueError(f"Missing {scheme_name} path for layer {key}.")
            validate_path(layer_map[key], geometry_for_layer, key, scheme_name)
    return schemes


def build_schedule_metadata(
    schedule: Sequence[Tuple[str, int]],
    travel_speed_mm_per_s: float,
    layer_change_time_s: float,
) -> dict:
    inter_part_switch_count = 0
    inter_layer_change_count = 0
    for current, nxt in zip(schedule[:-1], schedule[1:]):
        if current[1] != nxt[1]:
            inter_layer_change_count += 1
        elif current[0] != nxt[0]:
            inter_part_switch_count += 1

    return {
        "schedule": [
            {
                "schedule_index": index + 1,
                "part_id": part_id,
                "layer_id": layer_id,
            }
            for index, (part_id, layer_id) in enumerate(schedule)
        ],
        "inter_part_switch_count": inter_part_switch_count,
        "inter_layer_change_count": inter_layer_change_count,
        "inter_part_transfer_distance_mm": INTER_PART_TRANSFER_DISTANCE_MM,
        "inter_part_transfer_time_per_switch_s": (
            INTER_PART_TRANSFER_DISTANCE_MM / travel_speed_mm_per_s
        ),
        "layer_change_time_s": layer_change_time_s,
    }


def evaluate_scheme_layers(
    scheme_name: str,
    scheme_paths: Dict[Tuple[str, int], List[str]],
    schedule: Sequence[Tuple[str, int]],
    geometry: Dict[Tuple[str, int], Dict[str, dict]],
    relations: Dict[Tuple[str, int], Dict[Tuple[str, str], dict]],
    machine_params: dict,
    thermal_params: dict,
    material_context: dict,
    threshold_h: float,
) -> Tuple[List[dict], List[dict], List[dict], List[dict], List[dict]]:
    scan_speed = float(machine_params["scan_speed_mm_per_s"])
    travel_speed = float(machine_params["travel_speed_mm_per_s"])
    laser_on = float(machine_params["laser_on_delay_s"])
    alpha = float(thermal_params["alpha_per_s"])
    beta = float(thermal_params["beta_per_mm"])
    c_value = material_context["base_material"]["specific_heat_j_per_kg_k"]
    rho_value = material_context["base_material"]["density_g_per_cm3"]
    kappa_mat = material_context["kappa_mat"]

    layer_summary_rows: List[dict] = []
    cell_risk_rows: List[dict] = []
    heat_history_rows: List[dict] = []
    path_step_rows: List[dict] = []
    part_cells: Dict[str, List[dict]] = defaultdict(list)

    for schedule_index, key in enumerate(schedule, start=1):
        part_id, layer_id = key
        path_cell_ids = scheme_paths[key]
        geometry_for_layer = geometry[key]
        relations_for_layer = relations[key]
        hole_edge_cells = find_hole_edge_cells(geometry_for_layer)
        neighbors = build_contact_neighbors(relations_for_layer, geometry_for_layer)

        events, time_totals = build_layer_timing(
            path_cell_ids=path_cell_ids,
            geometry_for_layer=geometry_for_layer,
            relations_for_layer=relations_for_layer,
            scan_speed_mm_per_s=scan_speed,
            travel_speed_mm_per_s=travel_speed,
            laser_on_delay_s=laser_on,
        )
        event_times = [event["scan_completion_time_s"] for event in events]
        histories = compute_improved_heat_histories(
            path_cell_ids=path_cell_ids,
            event_times=event_times,
            geometry_for_layer=geometry_for_layer,
            relations_for_layer=relations_for_layer,
            alpha=alpha,
            beta=beta,
            c_value=c_value,
            rho_value=rho_value,
        )
        visit_index_map = {cell_id: index for index, cell_id in enumerate(path_cell_ids)}

        for event in events:
            path_step_rows.append(
                {
                    "scheme_name": scheme_name,
                    "schedule_index": schedule_index,
                    "part_id": part_id,
                    "layer_id": layer_id,
                    "visit_step": event["visit_step"],
                    "cell_id": event["cell_id"],
                    "travel_distance_mm": f"{event['travel_distance_mm']:.6f}",
                    "travel_time_s": f"{event['travel_time_s']:.6f}",
                    "scan_time_s": f"{event['scan_time_s']:.6f}",
                    "laser_on_time_s": f"{event['laser_on_time_s']:.6f}",
                    "scan_completion_time_s": f"{event['scan_completion_time_s']:.6f}",
                }
            )

        layer_cell_metrics: List[dict] = []
        for cell_id in path_cell_ids:
            cell = geometry_for_layer[cell_id]
            visit_index = visit_index_map[cell_id]
            is_thin, is_hole, s_value = compute_structural_sensitivity(
                cell=cell,
                hole_edge_cells=hole_edge_cells,
                kappa_mat=kappa_mat,
            )
            metric_values = compute_cell_risk_metrics(
                cell_id=cell_id,
                history=histories[cell_id],
                visit_index=visit_index,
                visit_time_s=event_times[visit_index],
                event_times=event_times,
                neighbors=neighbors[cell_id],
                neighbor_histories=histories,
                relations_for_layer=relations_for_layer,
                threshold_h=threshold_h,
                alpha=alpha,
                s_value=s_value,
            )

            cell_row = {
                "scheme_name": scheme_name,
                "schedule_index": schedule_index,
                "part_id": part_id,
                "layer_id": layer_id,
                "cell_id": cell_id,
                "visit_step": visit_index + 1,
                "cell_type": cell["cell_type"],
                "grid_x": cell["grid_x"],
                "grid_y": cell["grid_y"],
                "x_mm": cell["x_mm"],
                "y_mm": cell["y_mm"],
                "scan_length_mm": cell["scan_length_mm"],
                "is_thin": is_thin,
                "is_hole": is_hole,
                "S_j": s_value,
                **metric_values,
            }
            cell_risk_rows.append(cell_row)
            layer_cell_metrics.append(cell_row)
            part_cells[part_id].append(cell_row)

            for event_index, heat_value in enumerate(histories[cell_id]):
                event = events[event_index]
                heat_history_rows.append(
                    {
                        "scheme_name": scheme_name,
                        "schedule_index": schedule_index,
                        "part_id": part_id,
                        "layer_id": layer_id,
                        "event_step": event["visit_step"],
                        "event_cell_id": event["cell_id"],
                        "event_time_s": event["scan_completion_time_s"],
                        "target_cell_id": cell_id,
                        "heat_state": heat_value,
                        "above_threshold": 1 if heat_value > threshold_h else 0,
                    }
                )

        feature_row = aggregate_cell_metrics(layer_cell_metrics)
        layer_summary_rows.append(
            {
                "scheme_name": scheme_name,
                "schedule_index": schedule_index,
                "part_id": part_id,
                "layer_id": layer_id,
                "cell_count": len(path_cell_ids),
                "start_cell_id": path_cell_ids[0],
                "end_cell_id": path_cell_ids[-1],
                "travel_distance_mm": time_totals["travel_distance_mm"],
                "travel_time_s": time_totals["travel_time_s"],
                "scan_time_s": time_totals["scan_time_s"],
                "laser_on_time_s": time_totals["laser_on_time_s"],
                "layer_total_time_s": time_totals["layer_total_time_s"],
                **feature_row,
            }
        )

    part_summary_rows: List[dict] = []
    for part_id in sorted(part_cells):
        part_features = aggregate_cell_metrics(part_cells[part_id])
        matching_layers = [row for row in layer_summary_rows if row["part_id"] == part_id]
        part_summary_rows.append(
            {
                "scheme_name": scheme_name,
                "part_id": part_id,
                "layer_count": len(matching_layers),
                "travel_distance_mm": sum(row["travel_distance_mm"] for row in matching_layers),
                "travel_time_s": sum(row["travel_time_s"] for row in matching_layers),
                "scan_time_s": sum(row["scan_time_s"] for row in matching_layers),
                "laser_on_time_s": sum(row["laser_on_time_s"] for row in matching_layers),
                "part_intra_layer_time_s": sum(row["layer_total_time_s"] for row in matching_layers),
                **part_features,
            }
        )

    return layer_summary_rows, part_summary_rows, cell_risk_rows, heat_history_rows, path_step_rows


def compute_scheme_overall_rows(
    layer_summary_rows: Sequence[dict],
    schedule_metadata: dict,
) -> List[dict]:
    by_scheme_layers: Dict[str, List[dict]] = defaultdict(list)
    for row in layer_summary_rows:
        by_scheme_layers[row["scheme_name"]].append(row)

    results: List[dict] = []
    for scheme_name in sorted(by_scheme_layers):
        scheme_layers = by_scheme_layers[scheme_name]
        inter_part_total_distance_mm = (
            schedule_metadata["inter_part_switch_count"]
            * schedule_metadata["inter_part_transfer_distance_mm"]
        )
        inter_part_total_time_s = (
            schedule_metadata["inter_part_switch_count"]
            * schedule_metadata["inter_part_transfer_time_per_switch_s"]
        )
        inter_layer_total_time_s = (
            schedule_metadata["inter_layer_change_count"]
            * schedule_metadata["layer_change_time_s"]
        )
        results.append(
            {
                "scheme_name": scheme_name,
                "layer_count": len(scheme_layers),
                "travel_distance_mm": sum(row["travel_distance_mm"] for row in scheme_layers),
                "travel_time_s": sum(row["travel_time_s"] for row in scheme_layers),
                "scan_time_s": sum(row["scan_time_s"] for row in scheme_layers),
                "laser_on_time_s": sum(row["laser_on_time_s"] for row in scheme_layers),
                "intra_layer_total_time_s": sum(row["layer_total_time_s"] for row in scheme_layers),
                "inter_layer_change_time_s": inter_layer_total_time_s,
                "inter_part_transfer_distance_mm": inter_part_total_distance_mm,
                "inter_part_transfer_time_s": inter_part_total_time_s,
                "total_task_time_s": (
                    sum(row["layer_total_time_s"] for row in scheme_layers)
                    + inter_layer_total_time_s
                    + inter_part_total_time_s
                ),
            }
        )
    return results


def attach_overall_feature_rows(overall_rows: List[dict], cell_risk_rows: Sequence[dict]) -> None:
    by_scheme: Dict[str, List[dict]] = defaultdict(list)
    for row in cell_risk_rows:
        by_scheme[row["scheme_name"]].append(row)
    for row in overall_rows:
        row.update(aggregate_cell_metrics(by_scheme[row["scheme_name"]]))


def apply_scores_to_rows(
    overall_rows: List[dict],
    part_rows: List[dict],
    layer_rows: List[dict],
) -> Dict[str, Dict[str, float]]:
    weight_groups = {
        "R_mu": entropy_weights(overall_rows, ["mu_mean", "mu_top10_mean"]),
        "R_xi": entropy_weights(overall_rows, ["xi_mean", "xi_max"]),
        "R_theta": entropy_weights(overall_rows, ["theta_mean", "theta_top10_mean"]),
        "R_phi": entropy_weights(overall_rows, ["phi_mean", "phi_top10_mean", "phi_max"]),
    }

    for row in overall_rows:
        add_first_level_scores(row, weight_groups)
    for row in part_rows:
        add_first_level_scores(row, weight_groups)
    for row in layer_rows:
        add_first_level_scores(row, weight_groups)

    rank_by(overall_rows, "weighted_sum_total_risk", "weighted_sum_rank", reverse=False)
    topsis_scores = compute_topsis_scores(overall_rows)
    for row in overall_rows:
        row["topsis_score"] = topsis_scores[row["scheme_name"]]
    rank_by(overall_rows, "topsis_score", "topsis_rank", reverse=True)
    return weight_groups


def build_weight_rows(weight_groups: Dict[str, Dict[str, float]]) -> List[dict]:
    rows: List[dict] = []
    for group_name, weights in weight_groups.items():
        for feature_name, value in weights.items():
            rows.append(
                {
                    "group_name": group_name,
                    "feature_name": feature_name,
                    "weight_value": value,
                }
            )
    for key, value in FIRST_LEVEL_WEIGHTS.items():
        rows.append(
            {
                "group_name": "first_level",
                "feature_name": key,
                "weight_value": value,
            }
        )
    return rows


def main() -> None:
    output_dir = script_dir()
    root_dir = project_root()

    geometry = load_part_geometry(root_dir / PART_GEOMETRY_FILE)
    relations = load_local_relations(root_dir / LOCAL_RELATIONS_FILE)
    machine_params = load_json(root_dir / MACHINE_PARAMS_FILE)
    thermal_params = load_json(root_dir / THERMAL_PARAMS_FILE)
    baseline_paths = load_baseline_paths(root_dir / BASELINE_PATHS_FILE)
    minimum_time_paths = load_minimum_time_paths(root_dir / QUESTION_1_RESULTS_FILE)
    materials = load_material_properties(root_dir / MATERIAL_MARKDOWN_FILE)
    material_context = compute_material_context(
        materials=materials,
        base_material_name=BASE_MATERIAL_NAME,
        ambient_temperature_c=AMBIENT_TEMPERATURE_C,
    )

    schemes = build_scheme_paths(geometry, baseline_paths, minimum_time_paths)
    schedule = build_interleaved_schedule(geometry)
    schedule_metadata = build_schedule_metadata(
        schedule=schedule,
        travel_speed_mm_per_s=float(machine_params["travel_speed_mm_per_s"]),
        layer_change_time_s=float(machine_params["layer_change_time_s"]),
    )

    threshold_h, quantile_q, threshold_rows = compute_threshold_alignment(
        row_major_paths=schemes["row_major"],
        geometry=geometry,
        relations=relations,
        machine_params=machine_params,
        thermal_params=thermal_params,
        material_context=material_context,
    )

    all_layer_rows: List[dict] = []
    all_part_rows: List[dict] = []
    all_cell_rows: List[dict] = []
    all_heat_history_rows: List[dict] = []
    all_path_step_rows: List[dict] = []

    for scheme_name in ["row_major", "serpentine", "center_out", "minimum_time"]:
        layer_rows, part_rows, cell_rows, heat_rows, path_rows = evaluate_scheme_layers(
            scheme_name=scheme_name,
            scheme_paths=schemes[scheme_name],
            schedule=schedule,
            geometry=geometry,
            relations=relations,
            machine_params=machine_params,
            thermal_params=thermal_params,
            material_context=material_context,
            threshold_h=threshold_h,
        )
        all_layer_rows.extend(layer_rows)
        all_part_rows.extend(part_rows)
        all_cell_rows.extend(cell_rows)
        all_heat_history_rows.extend(heat_rows)
        all_path_step_rows.extend(path_rows)

    overall_rows = compute_scheme_overall_rows(all_layer_rows, schedule_metadata)
    attach_overall_feature_rows(overall_rows, all_cell_rows)
    weight_groups = apply_scores_to_rows(overall_rows, all_part_rows, all_layer_rows)
    weight_rows = build_weight_rows(weight_groups)

    material_rows = []
    for material_name in sorted(materials):
        item = materials[material_name]
        material_rows.append(
            {
                "material_name": material_name,
                "melting_temperature_c": item["melting_temperature_c"],
                "specific_heat_j_per_kg_k": item["specific_heat_j_per_kg_k"],
                "density_g_per_cm3": item["density_g_per_cm3"],
                "cte_1e_minus_6_per_k": item["cte_1e_minus_6_per_k"],
                "delta_T_safe_c": item["melting_temperature_c"] - AMBIENT_TEMPERATURE_C,
                "melting_temperature_range": item["melting_temperature_range"],
                "specific_heat_range": item["specific_heat_range"],
                "density_range": item["density_range"],
                "cte_range": item["cte_range"],
            }
        )

    results_payload = {
        "model_scope": "Question 2 base model only (no sensitivity analysis or visualization in this script)",
        "scheme_names": ["row_major", "serpentine", "center_out", "minimum_time"],
        "base_material_name": BASE_MATERIAL_NAME,
        "material_context": {
            "ambient_temperature_c": AMBIENT_TEMPERATURE_C,
            "base_material": material_context["base_material"],
            "reference_alpha_L": material_context["reference_alpha_L"],
            "reference_delta_T": material_context["reference_delta_T"],
            "delta_T_safe": material_context["delta_T_safe"],
            "kappa_mat": material_context["kappa_mat"],
        },
        "thermal_model_parameters": {
            "A0_self_heat": A0_SELF_HEAT,
            "A1_neighbor_heat": A1_NEIGHBOR_HEAT,
            "alpha_per_s": float(thermal_params["alpha_per_s"]),
            "beta_per_mm": float(thermal_params["beta_per_mm"]),
            "gamma_contact": GAMMA_CONTACT,
            "contact_length_scale_mm": CONTACT_LENGTH_SCALE_MM,
            "H_crit_original": float(thermal_params["H_crit"]),
            "H_thres_aligned": threshold_h,
            "threshold_quantile_q": quantile_q,
        },
        "structural_sensitivity_parameters": {
            "lambda_thin": LAMBDA_THIN,
            "lambda_hole": LAMBDA_HOLE,
            "S_type_formula": "1 + lambda_1 * I_thin + lambda_2 * I_hole",
            "S_formula": "1 + kappa_mat * (S_type - 1)",
        },
        "schedule_metadata": schedule_metadata,
        "scheme_overall_summary": overall_rows,
        "evaluation_weight_summary": weight_rows,
    }

    (output_dir / OUTPUT_RESULTS_JSON).write_text(
        json.dumps(results_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    write_csv(output_dir / OUTPUT_SCHEME_OVERALL_CSV, overall_rows, list(overall_rows[0].keys()))
    write_csv(output_dir / OUTPUT_SCHEME_PART_CSV, all_part_rows, list(all_part_rows[0].keys()))
    write_csv(output_dir / OUTPUT_SCHEME_LAYER_CSV, all_layer_rows, list(all_layer_rows[0].keys()))
    write_csv(output_dir / OUTPUT_CELL_RISK_CSV, all_cell_rows, list(all_cell_rows[0].keys()))
    write_csv(output_dir / OUTPUT_HEAT_HISTORY_CSV, all_heat_history_rows, list(all_heat_history_rows[0].keys()))
    write_csv(output_dir / OUTPUT_PATH_STEPS_CSV, all_path_step_rows, list(all_path_step_rows[0].keys()))
    write_csv(output_dir / OUTPUT_THRESHOLD_CSV, threshold_rows, list(threshold_rows[0].keys()))
    write_csv(output_dir / OUTPUT_WEIGHTS_CSV, weight_rows, list(weight_rows[0].keys()))
    write_csv(output_dir / OUTPUT_MATERIALS_CSV, material_rows, list(material_rows[0].keys()))

    workbook_status = maybe_write_workbook(
        output_dir,
        {
            "scheme_overall": overall_rows,
            "scheme_part": all_part_rows,
            "scheme_layer": all_layer_rows,
            "cell_risk_details": all_cell_rows,
            "heat_history": all_heat_history_rows,
            "path_steps": all_path_step_rows,
            "threshold_alignment": threshold_rows,
            "weights": weight_rows,
            "materials": material_rows,
        },
    )
    print("Question 2 base model finished.")
    print(f"Base material: {BASE_MATERIAL_NAME}")
    print(f"Aligned threshold H_thres: {threshold_h:.10f}")
    print(f"Workbook status: {workbook_status}")


if __name__ == "__main__":
    main()
