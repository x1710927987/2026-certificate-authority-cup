"""
Result sensitivity analysis for inter-part transfer distance.

Reads the base-model output and recomputes total task time under different
fixed inter-part transfer distances. The optimized path remains unchanged.

Outputs:
- intra_part_distance_summary.csv
- intra_part_distance_plot.png
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


INTER_PART_DISTANCE_VALUES_MM = list(range(20, 101, 5))

BASE_RESULTS_JSON = Path(__file__).resolve().parents[2] / "basic_model_result_for_question_1" / "question_1_results.json"
OUTPUT_DIR = Path(__file__).resolve().parent
SUMMARY_CSV = OUTPUT_DIR / "intra_part_distance_summary.csv"
PLOT_FILE = OUTPUT_DIR / "intra_part_distance_plot.png"


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
    aggregate_times = data["aggregate_times_s"]
    transition_counts = data["transition_counts"]
    travel_speed_mm_per_s = float(data["machine_params"]["travel_speed_mm_per_s"])

    total_intra_layer_time_s = float(aggregate_times["total_intra_layer_time_s"])
    total_inter_layer_time_s = float(aggregate_times["total_inter_layer_time_s"])
    inter_part_switch_count = int(transition_counts["inter_part_switch_count"])

    summary_rows: list[list[object]] = []
    x_vals = []
    total_task_vals = []
    total_inter_part_time_vals = []

    for distance_mm in INTER_PART_DISTANCE_VALUES_MM:
        total_inter_part_distance_mm = inter_part_switch_count * distance_mm
        total_inter_part_time_s = total_inter_part_distance_mm / travel_speed_mm_per_s
        total_task_time_s = total_intra_layer_time_s + total_inter_layer_time_s + total_inter_part_time_s

        summary_rows.append(
            [
                f"{distance_mm:.6f}",
                inter_part_switch_count,
                f"{total_inter_part_distance_mm:.6f}",
                f"{total_inter_part_time_s:.6f}",
                f"{total_task_time_s:.6f}",
            ]
        )

        x_vals.append(distance_mm)
        total_task_vals.append(total_task_time_s)
        total_inter_part_time_vals.append(total_inter_part_time_s)

    write_csv(
        SUMMARY_CSV,
        [
            "inter_part_distance_per_switch_mm",
            "inter_part_switch_count",
            "total_inter_part_distance_mm",
            "total_inter_part_time_s",
            "total_task_time_s",
        ],
        summary_rows,
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

    axes[0].plot(x_vals, total_task_vals, marker="o", linewidth=2, color="#1f77b4")
    axes[0].set_xlabel("Inter-part transfer distance per switch (mm)")
    axes[0].set_ylabel("Total task time (s)")
    axes[0].set_title("Task Time vs Inter-Part Distance")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(x_vals, total_inter_part_time_vals, marker="s", linewidth=2, color="#2ca02c")
    axes[1].set_xlabel("Inter-part transfer distance per switch (mm)")
    axes[1].set_ylabel("Total inter-part time (s)")
    axes[1].set_title("Inter-Part Time vs Inter-Part Distance")
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(PLOT_FILE, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {SUMMARY_CSV}")
    print(f"Saved: {PLOT_FILE}")


if __name__ == "__main__":
    main()
