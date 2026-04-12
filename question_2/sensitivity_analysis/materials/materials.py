from __future__ import annotations

import csv
import importlib.util
import json
import math
import sys
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
MATERIAL_ORDER = ["PA12", "316L", "Ti-6Al-4V", "AlSi10Mg", "Inconel 718"]


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
    workbook.save(output_dir / "materials_results.xlsx")
    return "written"


def plot_material_panels(output_dir: Path, overall_rows: Sequence[dict], threshold_rows: Sequence[dict]) -> None:
    scheme_names = ["row_major", "serpentine", "center_out", "minimum_time"]
    x_positions = list(range(len(MATERIAL_ORDER)))

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()
    metric_specs = [
        ("weighted_sum_total_risk", "Weighted Total Risk"),
        ("R_theta", "R_theta"),
        ("R_phi", "R_phi"),
        ("topsis_score", "TOPSIS Score"),
    ]

    for ax, (metric_key, title) in zip(axes, metric_specs):
        for scheme_name in scheme_names:
            ys = [
                next(
                    row[metric_key]
                    for row in overall_rows
                    if row["material_name"] == material_name and row["scheme_name"] == scheme_name
                )
                for material_name in MATERIAL_ORDER
            ]
            ax.plot(x_positions, ys, marker="o", linewidth=2, label=scheme_name)
        ax.set_xticks(x_positions, MATERIAL_ORDER, rotation=15)
        ax.set_title(title)
        ax.grid(alpha=0.3)

    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
        fig.subplots_adjust(bottom=0.14)
    fig.tight_layout()
    fig.savefig(output_dir / "materials_plot.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    fig2, ax1 = plt.subplots(figsize=(10, 5))
    threshold_values = [
        next(row["H_thres"] for row in threshold_rows if row["material_name"] == material_name)
        for material_name in MATERIAL_ORDER
    ]
    kappa_values = [
        next(row["kappa_mat"] for row in threshold_rows if row["material_name"] == material_name)
        for material_name in MATERIAL_ORDER
    ]
    ax1.bar(x_positions, threshold_values, color="#D9A65A", alpha=0.85, label="H_thres")
    ax1.set_xticks(x_positions, MATERIAL_ORDER, rotation=15)
    ax1.set_ylabel("H_thres")
    ax1.set_title("Threshold and Material Sensitivity Factor by Material")
    ax1.grid(axis="y", alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(x_positions, kappa_values, color="#2C5E91", marker="o", linewidth=2, label="kappa_mat")
    ax2.set_ylabel("kappa_mat")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=False)
    fig2.tight_layout()
    fig2.savefig(output_dir / "materials_threshold.png", dpi=200, bbox_inches="tight")
    plt.close(fig2)

    fig3, ax3 = plt.subplots(figsize=(8, 5))
    weighted_rank_matrix = [
        [
            next(
                row["weighted_sum_rank"]
                for row in overall_rows
                if row["material_name"] == material_name and row["scheme_name"] == scheme_name
            )
            for scheme_name in scheme_names
        ]
        for material_name in MATERIAL_ORDER
    ]
    image = ax3.imshow(weighted_rank_matrix, cmap="YlOrRd_r", aspect="auto")
    ax3.set_xticks(range(len(scheme_names)), scheme_names, rotation=15)
    ax3.set_yticks(range(len(MATERIAL_ORDER)), MATERIAL_ORDER)
    ax3.set_title("Weighted-Sum Rank Heatmap")
    for i, material_name in enumerate(MATERIAL_ORDER):
        for j, scheme_name in enumerate(scheme_names):
            ax3.text(j, i, weighted_rank_matrix[i][j], ha="center", va="center", color="black")
    fig3.colorbar(image, ax=ax3, shrink=0.85)
    fig3.tight_layout()
    fig3.savefig(output_dir / "materials_rank_heatmap.png", dpi=200, bbox_inches="tight")
    plt.close(fig3)


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
    schemes = base.build_scheme_paths(geometry, baseline_paths, minimum_time_paths)
    schedule = base.build_interleaved_schedule(geometry)
    schedule_metadata = base.build_schedule_metadata(
        schedule=schedule,
        travel_speed_mm_per_s=float(machine_params["travel_speed_mm_per_s"]),
        layer_change_time_s=float(machine_params["layer_change_time_s"]),
    )

    overall_rows_all: List[dict] = []
    layer_rows_all: List[dict] = []
    threshold_rows_all: List[dict] = []
    weight_rows_all: List[dict] = []
    results_summary: List[dict] = []
    material_summary_rows: List[dict] = []

    for material_name in MATERIAL_ORDER:
        material_context = base.compute_material_context(
            materials=materials,
            base_material_name=material_name,
            ambient_temperature_c=base.AMBIENT_TEMPERATURE_C,
        )
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
            row["material_name"] = material_name
            overall_rows_all.append(row)
            if row["weighted_sum_rank"] == 1:
                best_weighted = row["scheme_name"]
            if row["topsis_rank"] == 1:
                best_topsis = row["scheme_name"]

        for row in all_layer_rows:
            row["material_name"] = material_name
            layer_rows_all.append(row)

        for row in weight_rows:
            row["material_name"] = material_name
            weight_rows_all.append(row)

        material_item = material_context["base_material"]
        threshold_row = {
            "material_name": material_name,
            "H_crit": float(thermal_params["H_crit"]),
            "quantile_q": quantile_q,
            "H_thres": threshold_h,
            "kappa_mat": material_context["kappa_mat"],
            "specific_heat_j_per_kg_k": material_item["specific_heat_j_per_kg_k"],
            "density_g_per_cm3": material_item["density_g_per_cm3"],
            "cte_1e_minus_6_per_k": material_item["cte_1e_minus_6_per_k"],
            "melting_temperature_c": material_item["melting_temperature_c"],
            "delta_T_safe_c": material_context["delta_T_safe"],
            "reference_alpha_L": material_context["reference_alpha_L"],
            "reference_delta_T": material_context["reference_delta_T"],
        }
        threshold_rows_all.append(threshold_row)
        results_summary.append(
            {
                **threshold_row,
                "best_scheme_weighted_sum": best_weighted,
                "best_scheme_topsis": best_topsis,
            }
        )
        material_summary_rows.append(
            {
                "material_name": material_name,
                "specific_heat_j_per_kg_k": material_item["specific_heat_j_per_kg_k"],
                "density_g_per_cm3": material_item["density_g_per_cm3"],
                "cte_1e_minus_6_per_k": material_item["cte_1e_minus_6_per_k"],
                "melting_temperature_c": material_item["melting_temperature_c"],
                "delta_T_safe_c": material_context["delta_T_safe"],
                "kappa_mat": material_context["kappa_mat"],
                "reference_alpha_L": material_context["reference_alpha_L"],
                "reference_delta_T": material_context["reference_delta_T"],
                "melting_temperature_range": material_item["melting_temperature_range"],
                "specific_heat_range": material_item["specific_heat_range"],
                "density_range": material_item["density_range"],
                "cte_range": material_item["cte_range"],
            }
        )

    results_payload = {
        "analysis_type": "question_2_material_sensitivity",
        "materials": MATERIAL_ORDER,
        "results_summary": results_summary,
    }
    (OUTPUT_DIR / "materials_results.json").write_text(
        json.dumps(results_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    write_csv(OUTPUT_DIR / "materials_overall_summary.csv", overall_rows_all)
    write_csv(OUTPUT_DIR / "materials_layer_summary.csv", layer_rows_all)
    write_csv(OUTPUT_DIR / "materials_threshold_summary.csv", threshold_rows_all)
    write_csv(OUTPUT_DIR / "materials_weight_summary.csv", weight_rows_all)
    write_csv(OUTPUT_DIR / "materials_material_property_summary.csv", material_summary_rows)

    workbook_status = maybe_write_workbook(
        OUTPUT_DIR,
        {
            "overall": overall_rows_all,
            "layer": layer_rows_all,
            "threshold": threshold_rows_all,
            "weights": weight_rows_all,
            "materials": material_summary_rows,
        },
    )
    plot_material_panels(OUTPUT_DIR, overall_rows_all, threshold_rows_all)

    print("Question 2 material sensitivity finished.")
    print(f"Workbook status: {workbook_status}")


if __name__ == "__main__":
    main()
