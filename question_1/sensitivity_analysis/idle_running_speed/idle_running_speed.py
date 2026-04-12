"""
Result sensitivity analysis for travel speed.

Reads the base-model output and recomputes all time metrics under different
travel speeds, while keeping the optimized path fixed.

Outputs:
- idle_running_speed_summary.csv
- idle_running_speed_layer_details.csv
- idle_running_speed_plot.png
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: matplotlib\n"
        "Please install it with:\n"
        "    pip install matplotlib\n"
    ) from exc


TRAVEL_SPEED_VALUES_MM_PER_S = [1200.0, 1500.0, 1800.0, 2100.0, 2400.0]

BASE_RESULTS_JSON = Path(__file__).resolve().parents[2] / "basic_model_result_for_question_1" / "question_1_results.json"
OUTPUT_DIR = Path(__file__).resolve().parent
SUMMARY_CSV = OUTPUT_DIR / "idle_running_speed_summary.csv"
LAYER_DETAILS_CSV = OUTPUT_DIR / "idle_running_speed_layer_details.csv"
PLOT_FILE = OUTPUT_DIR / "idle_running_speed_plot.png"


def load_base_results() -> dict:
    with BASE_RESULTS_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def main() -> None:
    data = load_base_results()
    layer_results = data["layer_results"]
    machine = data["machine_params"]
    transition_counts = data["transition_counts"]
    inter_part_result = data["inter_part_transfer_result"]

    layer_change_time_s = float(machine["layer_change_time_s"])
    inter_layer_change_count = int(transition_counts["inter_layer_change_count"])
    total_inter_layer_time_s = inter_layer_change_count * layer_change_time_s
    total_inter_part_distance_mm = float(inter_part_result["total_inter_part_distance_mm"])

    scan_total_fixed = sum(float(item["scan_time_s"]) for item in layer_results)
    laser_total_fixed = sum(float(item["laser_on_time_s"]) for item in layer_results)
    intra_travel_distance_total_mm = sum(float(item["travel_distance_mm"]) for item in layer_results)

    summary_rows: list[list[object]] = []
    layer_rows: list[list[object]] = []

    x_vals = []
    total_task_vals = []
    travel_related_vals = []

    for speed in TRAVEL_SPEED_VALUES_MM_PER_S:
        total_intra_travel_time_s = intra_travel_distance_total_mm / speed
        total_inter_part_time_s = total_inter_part_distance_mm / speed
        total_intra_layer_time_s = scan_total_fixed + laser_total_fixed + total_intra_travel_time_s
        total_task_time_s = total_intra_layer_time_s + total_inter_layer_time_s + total_inter_part_time_s
        travel_related_time_s = total_intra_travel_time_s + total_inter_part_time_s

        summary_rows.append(
            [
                f"{speed:.6f}",
                f"{scan_total_fixed:.6f}",
                f"{laser_total_fixed:.6f}",
                f"{total_intra_travel_time_s:.6f}",
                f"{total_inter_layer_time_s:.6f}",
                f"{total_inter_part_time_s:.6f}",
                f"{total_task_time_s:.6f}",
            ]
        )

        for item in layer_results:
            travel_distance_mm = float(item["travel_distance_mm"])
            travel_time_s = travel_distance_mm / speed
            scan_time_s = float(item["scan_time_s"])
            laser_on_time_s = float(item["laser_on_time_s"])
            layer_total_time_s = scan_time_s + laser_on_time_s + travel_time_s
            layer_rows.append(
                [
                    f"{speed:.6f}",
                    item["schedule_index"],
                    item["part_id"],
                    item["layer_id"],
                    item["start_cell_id"],
                    item["end_cell_id"],
                    f"{travel_distance_mm:.6f}",
                    f"{travel_time_s:.6f}",
                    f"{scan_time_s:.6f}",
                    f"{laser_on_time_s:.6f}",
                    f"{layer_total_time_s:.6f}",
                ]
            )

        x_vals.append(speed)
        total_task_vals.append(total_task_time_s)
        travel_related_vals.append(travel_related_time_s)

    write_csv(
        SUMMARY_CSV,
        [
            "travel_speed_mm_per_s",
            "total_scan_time_s",
            "total_laser_on_time_s",
            "total_intra_layer_travel_time_s",
            "total_inter_layer_time_s",
            "total_inter_part_time_s",
            "total_task_time_s",
        ],
        summary_rows,
    )
    write_csv(
        LAYER_DETAILS_CSV,
        [
            "travel_speed_mm_per_s",
            "schedule_index",
            "part_id",
            "layer_id",
            "start_cell_id",
            "end_cell_id",
            "travel_distance_mm",
            "travel_time_s",
            "scan_time_s",
            "laser_on_time_s",
            "layer_total_time_s",
        ],
        layer_rows,
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

    axes[0].plot(x_vals, total_task_vals, marker="o", linewidth=2, color="#1f77b4")
    axes[0].set_xlabel("Travel speed (mm/s)")
    axes[0].set_ylabel("Total task time (s)")
    axes[0].set_title("Task Time vs Travel Speed")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(x_vals, travel_related_vals, marker="s", linewidth=2, color="#d62728")
    axes[1].set_xlabel("Travel speed (mm/s)")
    axes[1].set_ylabel("Travel-related time (s)")
    axes[1].set_title("Travel-Time Components vs Travel Speed")
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(PLOT_FILE, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {SUMMARY_CSV}")
    print(f"Saved: {LAYER_DETAILS_CSV}")
    print(f"Saved: {PLOT_FILE}")


if __name__ == "__main__":
    main()
