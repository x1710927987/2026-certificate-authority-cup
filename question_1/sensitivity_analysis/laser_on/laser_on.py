"""
Result sensitivity analysis for laser-on delay.

Reads the base-model output and recomputes all time metrics under different
laser-on delays, while keeping the optimized path fixed.

Outputs:
- laser_on_summary.csv
- laser_on_layer_details.csv
- laser_on_plot.png
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


LASER_ON_DELAY_VALUES_S = [0.005, 0.01, 0.015, 0.02, 0.03]

BASE_RESULTS_JSON = Path(__file__).resolve().parents[2] / "basic_model_result_for_question_1" / "question_1_results.json"
OUTPUT_DIR = Path(__file__).resolve().parent
SUMMARY_CSV = OUTPUT_DIR / "laser_on_summary.csv"
LAYER_DETAILS_CSV = OUTPUT_DIR / "laser_on_layer_details.csv"
PLOT_FILE = OUTPUT_DIR / "laser_on_plot.png"


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
    aggregate_times = data["aggregate_times_s"]

    total_scan_time_s = float(aggregate_times["total_scan_time_s"])
    total_travel_time_s = float(aggregate_times["total_travel_time_s"])
    total_inter_layer_time_s = float(aggregate_times["total_inter_layer_time_s"])
    total_inter_part_time_s = float(aggregate_times["total_inter_part_time_s"])

    summary_rows: list[list[object]] = []
    layer_rows: list[list[object]] = []

    x_vals = []
    total_task_vals = []
    total_laser_vals = []

    for laser_on_delay_s in LASER_ON_DELAY_VALUES_S:
        total_laser_on_time_s = 0.0
        for item in layer_results:
            total_laser_on_time_s += int(item["cell_count"]) * laser_on_delay_s

        total_intra_layer_time_s = total_scan_time_s + total_travel_time_s + total_laser_on_time_s
        total_task_time_s = total_intra_layer_time_s + total_inter_layer_time_s + total_inter_part_time_s

        summary_rows.append(
            [
                f"{laser_on_delay_s:.6f}",
                f"{total_scan_time_s:.6f}",
                f"{total_travel_time_s:.6f}",
                f"{total_laser_on_time_s:.6f}",
                f"{total_inter_layer_time_s:.6f}",
                f"{total_inter_part_time_s:.6f}",
                f"{total_task_time_s:.6f}",
            ]
        )

        for item in layer_results:
            cell_count = int(item["cell_count"])
            scan_time_s = float(item["scan_time_s"])
            travel_time_s = float(item["travel_time_s"])
            laser_on_time_s = cell_count * laser_on_delay_s
            layer_total_time_s = scan_time_s + travel_time_s + laser_on_time_s
            layer_rows.append(
                [
                    f"{laser_on_delay_s:.6f}",
                    item["schedule_index"],
                    item["part_id"],
                    item["layer_id"],
                    item["start_cell_id"],
                    item["end_cell_id"],
                    cell_count,
                    f"{travel_time_s:.6f}",
                    f"{scan_time_s:.6f}",
                    f"{laser_on_time_s:.6f}",
                    f"{layer_total_time_s:.6f}",
                ]
            )

        x_vals.append(laser_on_delay_s)
        total_task_vals.append(total_task_time_s)
        total_laser_vals.append(total_laser_on_time_s)

    write_csv(
        SUMMARY_CSV,
        [
            "laser_on_delay_s",
            "total_scan_time_s",
            "total_travel_time_s",
            "total_laser_on_time_s",
            "total_inter_layer_time_s",
            "total_inter_part_time_s",
            "total_task_time_s",
        ],
        summary_rows,
    )
    write_csv(
        LAYER_DETAILS_CSV,
        [
            "laser_on_delay_s",
            "schedule_index",
            "part_id",
            "layer_id",
            "start_cell_id",
            "end_cell_id",
            "cell_count",
            "travel_time_s",
            "scan_time_s",
            "laser_on_time_s",
            "layer_total_time_s",
        ],
        layer_rows,
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

    axes[0].plot(x_vals, total_task_vals, marker="o", linewidth=2, color="#1f77b4")
    axes[0].set_xlabel("Laser-on delay (s)")
    axes[0].set_ylabel("Total task time (s)")
    axes[0].set_title("Task Time vs Laser-On Delay")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(x_vals, total_laser_vals, marker="s", linewidth=2, color="#ff7f0e")
    axes[1].set_xlabel("Laser-on delay (s)")
    axes[1].set_ylabel("Total laser-on time (s)")
    axes[1].set_title("Laser-On Component vs Laser-On Delay")
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(PLOT_FILE, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {SUMMARY_CSV}")
    print(f"Saved: {LAYER_DETAILS_CSV}")
    print(f"Saved: {PLOT_FILE}")


if __name__ == "__main__":
    main()
