from __future__ import annotations

import csv
import importlib.util
import json
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


ROOT_DIR = Path(__file__).resolve().parents[3]
BASE_MODEL_PATH = (
    ROOT_DIR
    / "question_2"
    / "basic_model_for_question_2"
    / "basic_model_for_question_2.py"
)


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


def plot_parameter_panels(
    output_path: Path,
    parameter_name: str,
    parameter_values: Sequence[float],
    overall_rows: Sequence[dict],
    threshold_rows: Sequence[dict],
) -> None:
    scheme_names = sorted({row["scheme_name"] for row in overall_rows})
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()

    metric_specs = [
        ("weighted_sum_total_risk", "Weighted Total Risk"),
        ("R_theta", "R_theta"),
        ("R_phi", "R_phi"),
        ("topsis_score", "TOPSIS Score"),
    ]

    x_values = list(parameter_values)
    for ax, (metric_key, title) in zip(axes, metric_specs):
        for scheme_name in scheme_names:
            ys = [
                row[metric_key]
                for row in overall_rows
                if row["scheme_name"] == scheme_name
            ]
            ax.plot(x_values, ys, marker="o", linewidth=2, label=scheme_name)
        ax.set_title(title)
        ax.set_xlabel(parameter_name)
        ax.grid(alpha=0.3)

    fig2, ax2 = plt.subplots(figsize=(8, 4.8))
    ax2.plot(
        [row["parameter_value"] for row in threshold_rows],
        [row["H_thres"] for row in threshold_rows],
        marker="o",
        linewidth=2,
        color="#C04B2D",
    )
    ax2.set_title(f"Aligned Threshold vs {parameter_name}")
    ax2.set_xlabel(parameter_name)
    ax2.set_ylabel("H_thres")
    ax2.grid(alpha=0.3)

    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
        fig.subplots_adjust(bottom=0.14)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    threshold_output = output_path.with_name(output_path.stem + "_threshold.png")
    fig2.tight_layout()
    fig2.savefig(threshold_output, dpi=200, bbox_inches="tight")
    plt.close(fig)
    plt.close(fig2)


def run_model_parameter_sensitivity(
    parameter_name: str,
    parameter_values: Sequence[float],
    output_dir: Path,
    update_base_globals,
) -> None:
    base = load_base_module()

    geometry = base.load_part_geometry(base.project_root() / base.PART_GEOMETRY_FILE)
    relations = base.load_local_relations(base.project_root() / base.LOCAL_RELATIONS_FILE)
    machine_params = base.load_json(base.project_root() / base.MACHINE_PARAMS_FILE)
    thermal_params_template = base.load_json(base.project_root() / base.THERMAL_PARAMS_FILE)
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

    original_a0 = base.A0_SELF_HEAT
    original_gamma = base.GAMMA_CONTACT

    overall_rows_all: List[dict] = []
    layer_rows_all: List[dict] = []
    threshold_rows_all: List[dict] = []
    weight_rows_all: List[dict] = []
    results_summary: List[dict] = []

    try:
        for parameter_value in parameter_values:
            thermal_params = dict(thermal_params_template)
            update_base_globals(base, thermal_params, parameter_value)

            threshold_h, quantile_q, _ = base.compute_threshold_alignment(
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
                all_layer_rows.extend(layer_rows)
                all_part_rows.extend(part_rows)
                all_cell_rows.extend(cell_rows)

            overall_rows = base.compute_scheme_overall_rows(
                layer_summary_rows=all_layer_rows,
                schedule_metadata=schedule_metadata,
            )
            base.attach_overall_feature_rows(overall_rows, all_cell_rows)
            weight_groups = base.apply_scores_to_rows(overall_rows, all_part_rows, all_layer_rows)
            weight_rows = base.build_weight_rows(weight_groups)

            best_weighted = ""
            best_topsis = ""
            for row in overall_rows:
                row["parameter_name"] = parameter_name
                row["parameter_value"] = parameter_value
                overall_rows_all.append(row)
                if row["weighted_sum_rank"] == 1:
                    best_weighted = row["scheme_name"]
                if row["topsis_rank"] == 1:
                    best_topsis = row["scheme_name"]

            for row in all_layer_rows:
                row["parameter_name"] = parameter_name
                row["parameter_value"] = parameter_value
                layer_rows_all.append(row)

            for row in weight_rows:
                row["parameter_name"] = parameter_name
                row["parameter_value"] = parameter_value
                weight_rows_all.append(row)

            threshold_row = {
                "parameter_name": parameter_name,
                "parameter_value": parameter_value,
                "H_crit": float(thermal_params_template["H_crit"]),
                "quantile_q": quantile_q,
                "H_thres": threshold_h,
                "A0_self_heat": base.A0_SELF_HEAT,
                "alpha_per_s": float(thermal_params["alpha_per_s"]),
                "beta_per_mm": float(thermal_params["beta_per_mm"]),
                "gamma_contact": base.GAMMA_CONTACT,
            }
            threshold_rows_all.append(threshold_row)
            results_summary.append(
                {
                    **threshold_row,
                    "best_scheme_weighted_sum": best_weighted,
                    "best_scheme_topsis": best_topsis,
                }
            )
    finally:
        base.A0_SELF_HEAT = original_a0
        base.GAMMA_CONTACT = original_gamma

    results_payload = {
        "analysis_type": "question_2_model_parameter_sensitivity",
        "parameter_name": parameter_name,
        "parameter_values": list(parameter_values),
        "base_material_name": base.BASE_MATERIAL_NAME,
        "results_summary": results_summary,
    }

    (output_dir / f"{parameter_name.lower()}_results.json").write_text(
        json.dumps(results_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(output_dir / f"{parameter_name.lower()}_overall_summary.csv", overall_rows_all)
    write_csv(output_dir / f"{parameter_name.lower()}_layer_summary.csv", layer_rows_all)
    write_csv(output_dir / f"{parameter_name.lower()}_threshold_summary.csv", threshold_rows_all)
    write_csv(output_dir / f"{parameter_name.lower()}_weight_summary.csv", weight_rows_all)

    plot_parameter_panels(
        output_path=output_dir / f"{parameter_name.lower()}_plot.png",
        parameter_name=parameter_name,
        parameter_values=parameter_values,
        overall_rows=overall_rows_all,
        threshold_rows=threshold_rows_all,
    )
