from __future__ import annotations

import csv
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Sequence

try:
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover - runtime guidance
    raise SystemExit(
        "Missing dependency: matplotlib\n"
        "Please install it with:\n"
        "    pip install matplotlib\n"
    ) from exc

try:
    from openpyxl import Workbook

    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

BASE_MODEL_PATH = (
    ROOT_DIR
    / "question_2"
    / "basic_model_for_question_2"
    / "basic_model_for_question_2.py"
)

OUTPUT_DIR = Path(__file__).resolve().parent

SCENARIOS = [
    {
        "scenario_name": "base",
        "description": "Base first-level weights from the main model",
        "weights": {"R_theta": 0.35, "R_mu": 0.20, "R_xi": 0.20, "R_phi": 0.25},
    },
    {
        "scenario_name": "hotspot_priority",
        "description": "Prioritize local overheating",
        "weights": {"R_theta": 0.45, "R_mu": 0.20, "R_xi": 0.15, "R_phi": 0.20},
    },
    {
        "scenario_name": "cycle_stability_priority",
        "description": "Prioritize thermal cycling and stability",
        "weights": {"R_theta": 0.25, "R_mu": 0.30, "R_xi": 0.30, "R_phi": 0.15},
    },
    {
        "scenario_name": "uniformity_priority",
        "description": "Prioritize thermal uniformity",
        "weights": {"R_theta": 0.25, "R_mu": 0.20, "R_xi": 0.20, "R_phi": 0.35},
    },
    {
        "scenario_name": "balanced",
        "description": "Balanced first-level weights",
        "weights": {"R_theta": 0.25, "R_mu": 0.25, "R_xi": 0.25, "R_phi": 0.25},
    },
]


def load_base_module():
    spec = importlib.util.spec_from_file_location("q2_base_model", BASE_MODEL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load base model module from {BASE_MODEL_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: Sequence[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
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
    workbook.save(output_dir / "subjective_weights_results.xlsx")
    return "written"


def plot_weight_scenarios(
    output_dir: Path,
    overall_rows: Sequence[dict],
    scenario_rows: Sequence[dict],
) -> None:
    scheme_names = ["row_major", "serpentine", "center_out", "minimum_time"]
    scenario_names = [item["scenario_name"] for item in SCENARIOS]
    x_positions = list(range(len(scenario_names)))

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    metric_specs = [
        ("weighted_sum_total_risk", "Weighted Total Risk"),
        ("topsis_score", "TOPSIS Score"),
    ]
    for ax, (metric_key, title) in zip(axes, metric_specs):
        for scheme_name in scheme_names:
            ys = [
                next(
                    row[metric_key]
                    for row in overall_rows
                    if row["scenario_name"] == scenario_name and row["scheme_name"] == scheme_name
                )
                for scenario_name in scenario_names
            ]
            ax.plot(x_positions, ys, marker="o", linewidth=2, label=scheme_name)
        ax.set_xticks(x_positions, scenario_names, rotation=15)
        ax.set_title(title)
        ax.grid(alpha=0.3)

    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
        fig.subplots_adjust(bottom=0.18)
    fig.tight_layout()
    fig.savefig(output_dir / "subjective_weights_plot.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    fig2, axes2 = plt.subplots(1, 2, figsize=(13, 5.5))
    weighted_rank_matrix = [
        [
            next(
                row["weighted_sum_rank"]
                for row in overall_rows
                if row["scenario_name"] == scenario_name and row["scheme_name"] == scheme_name
            )
            for scheme_name in scheme_names
        ]
        for scenario_name in scenario_names
    ]
    topsis_rank_matrix = [
        [
            next(
                row["topsis_rank"]
                for row in overall_rows
                if row["scenario_name"] == scenario_name and row["scheme_name"] == scheme_name
            )
            for scheme_name in scheme_names
        ]
        for scenario_name in scenario_names
    ]
    for ax, matrix, title in zip(
        axes2,
        [weighted_rank_matrix, topsis_rank_matrix],
        ["Weighted-Sum Rank Heatmap", "TOPSIS Rank Heatmap"],
    ):
        image = ax.imshow(matrix, cmap="YlOrRd_r", aspect="auto")
        ax.set_xticks(range(len(scheme_names)), scheme_names, rotation=15)
        ax.set_yticks(range(len(scenario_names)), scenario_names)
        ax.set_title(title)
        for i, scenario_name in enumerate(scenario_names):
            for j, scheme_name in enumerate(scheme_names):
                ax.text(j, i, matrix[i][j], ha="center", va="center", color="black")
        fig2.colorbar(image, ax=ax, shrink=0.82)
    fig2.tight_layout()
    fig2.savefig(output_dir / "subjective_weights_rank_heatmap.png", dpi=200, bbox_inches="tight")
    plt.close(fig2)

    fig3, ax3 = plt.subplots(figsize=(10, 5))
    best_weighted = [row["best_scheme_weighted_sum"] for row in scenario_rows]
    best_topsis = [row["best_scheme_topsis"] for row in scenario_rows]
    weighted_codes = [scheme_names.index(name) + 1 for name in best_weighted]
    topsis_codes = [scheme_names.index(name) + 1 for name in best_topsis]
    ax3.plot(x_positions, weighted_codes, marker="o", linewidth=2, label="best_weighted_sum")
    ax3.plot(x_positions, topsis_codes, marker="s", linewidth=2, label="best_topsis")
    ax3.set_xticks(x_positions, scenario_names, rotation=15)
    ax3.set_yticks(range(1, len(scheme_names) + 1), scheme_names)
    ax3.set_title("Best Scheme Changes Across Weight Scenarios")
    ax3.grid(alpha=0.3)
    ax3.legend(frameon=False)
    fig3.tight_layout()
    fig3.savefig(output_dir / "subjective_weights_best_scheme.png", dpi=200, bbox_inches="tight")
    plt.close(fig3)


def apply_first_level_weights(base, weight_mapping: Dict[str, float]) -> None:
    for key, value in weight_mapping.items():
        base.FIRST_LEVEL_WEIGHTS[key] = float(value)


def main() -> None:
    base = load_base_module()

    geometry = base.load_part_geometry(base.project_root() / base.PART_GEOMETRY_FILE)
    relations = base.load_local_relations(base.project_root() / base.LOCAL_RELATIONS_FILE)
    machine_params = base.load_json(base.project_root() / base.MACHINE_PARAMS_FILE)
    thermal_params = base.load_json(base.project_root() / base.THERMAL_PARAMS_FILE)
    baseline_paths = base.load_baseline_paths(base.project_root() / base.BASELINE_PATHS_FILE)
    minimum_time_paths = base.load_minimum_time_paths(
        base.project_root() / base.QUESTION_1_RESULTS_FILE
    )
    materials = base.load_material_properties(base.project_root() / base.MATERIAL_MARKDOWN_FILE)
    material_context = base.compute_material_context(
        materials=materials,
        base_material_name=base.BASE_MATERIAL_NAME,
        ambient_temperature_c=base.AMBIENT_TEMPERATURE_C,
    )
    schemes = base.build_scheme_paths(geometry, baseline_paths, minimum_time_paths)
    schedule = base.build_interleaved_schedule(geometry)
    schedule_metadata = base.build_schedule_metadata(
        schedule=schedule,
        travel_speed_mm_per_s=float(machine_params["travel_speed_mm_per_s"]),
        layer_change_time_s=float(machine_params["layer_change_time_s"]),
    )

    threshold_h, quantile_q, _ = base.compute_threshold_alignment(
        row_major_paths=schemes["row_major"],
        geometry=geometry,
        relations=relations,
        machine_params=machine_params,
        thermal_params=thermal_params,
        material_context=material_context,
    )

    raw_layer_rows: List[dict] = []
    raw_part_rows: List[dict] = []
    raw_cell_rows: List[dict] = []
    for scheme_name in ["row_major", "serpentine", "center_out", "minimum_time"]:
        layer_rows, part_rows, cell_rows, _, _ = base.evaluate_scheme_layers(
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
        raw_layer_rows.extend(layer_rows)
        raw_part_rows.extend(part_rows)
        raw_cell_rows.extend(cell_rows)

    original_first_level = dict(base.FIRST_LEVEL_WEIGHTS)

    overall_rows_all: List[dict] = []
    layer_rows_all: List[dict] = []
    part_rows_all: List[dict] = []
    weight_rows_all: List[dict] = []
    scenario_rows: List[dict] = []

    try:
        for scenario in SCENARIOS:
            scenario_name = scenario["scenario_name"]
            weight_mapping = scenario["weights"]
            apply_first_level_weights(base, weight_mapping)

            layer_rows = deepcopy(raw_layer_rows)
            part_rows = deepcopy(raw_part_rows)
            cell_rows = deepcopy(raw_cell_rows)

            overall_rows = base.compute_scheme_overall_rows(
                layer_summary_rows=layer_rows,
                schedule_metadata=schedule_metadata,
            )
            base.attach_overall_feature_rows(overall_rows, cell_rows)
            weight_groups = base.apply_scores_to_rows(overall_rows, part_rows, layer_rows)
            weight_rows = base.build_weight_rows(weight_groups)

            best_weighted = ""
            best_topsis = ""
            for row in overall_rows:
                row["scenario_name"] = scenario_name
                row["scenario_description"] = scenario["description"]
                overall_rows_all.append(row)
                if row["weighted_sum_rank"] == 1:
                    best_weighted = row["scheme_name"]
                if row["topsis_rank"] == 1:
                    best_topsis = row["scheme_name"]

            for row in layer_rows:
                row["scenario_name"] = scenario_name
                row["scenario_description"] = scenario["description"]
                layer_rows_all.append(row)

            for row in part_rows:
                row["scenario_name"] = scenario_name
                row["scenario_description"] = scenario["description"]
                part_rows_all.append(row)

            for row in weight_rows:
                row["scenario_name"] = scenario_name
                row["scenario_description"] = scenario["description"]
                weight_rows_all.append(row)

            scenario_rows.append(
                {
                    "scenario_name": scenario_name,
                    "scenario_description": scenario["description"],
                    "R_theta_weight": weight_mapping["R_theta"],
                    "R_mu_weight": weight_mapping["R_mu"],
                    "R_xi_weight": weight_mapping["R_xi"],
                    "R_phi_weight": weight_mapping["R_phi"],
                    "H_crit": float(thermal_params["H_crit"]),
                    "quantile_q": quantile_q,
                    "H_thres": threshold_h,
                    "base_material_name": base.BASE_MATERIAL_NAME,
                    "best_scheme_weighted_sum": best_weighted,
                    "best_scheme_topsis": best_topsis,
                }
            )
    finally:
        apply_first_level_weights(base, original_first_level)

    results_payload = {
        "analysis_type": "question_2_subjective_weight_sensitivity",
        "base_material_name": base.BASE_MATERIAL_NAME,
        "threshold_quantile_q": quantile_q,
        "H_thres": threshold_h,
        "scenarios": scenario_rows,
    }
    (OUTPUT_DIR / "subjective_weights_results.json").write_text(
        json.dumps(results_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    write_csv(OUTPUT_DIR / "subjective_weights_overall_summary.csv", overall_rows_all)
    write_csv(OUTPUT_DIR / "subjective_weights_layer_summary.csv", layer_rows_all)
    write_csv(OUTPUT_DIR / "subjective_weights_part_summary.csv", part_rows_all)
    write_csv(OUTPUT_DIR / "subjective_weights_weight_summary.csv", weight_rows_all)
    write_csv(OUTPUT_DIR / "subjective_weights_scenario_summary.csv", scenario_rows)

    workbook_status = maybe_write_workbook(
        OUTPUT_DIR,
        {
            "overall": overall_rows_all,
            "layer": layer_rows_all,
            "part": part_rows_all,
            "weights": weight_rows_all,
            "scenarios": scenario_rows,
        },
    )
    plot_weight_scenarios(OUTPUT_DIR, overall_rows_all, scenario_rows)

    print("Question 2 subjective-weight sensitivity finished.")
    print(f"Workbook status: {workbook_status}")


if __name__ == "__main__":
    main()
