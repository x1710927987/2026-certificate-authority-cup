from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from visualization_common import BASE_LAYER_SUMMARY_CSV, load_base_results, load_csv_dicts, schedule_label


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_LAYER_BREAKDOWN = SCRIPT_DIR / "layer_time_breakdown_stacked.png"
OUTPUT_TOTAL_BREAKDOWN = SCRIPT_DIR / "total_task_time_decomposition.png"


def make_layer_breakdown() -> None:
    layer_rows = load_csv_dicts(BASE_LAYER_SUMMARY_CSV)
    labels = [schedule_label(row) for row in layer_rows]
    scan_vals = [float(row["scan_time_s"]) for row in layer_rows]
    laser_vals = [float(row["laser_on_time_s"]) for row in layer_rows]
    travel_vals = [float(row["travel_time_s"]) for row in layer_rows]

    fig, ax = plt.subplots(figsize=(12, 5.5), constrained_layout=True)
    ax.bar(labels, scan_vals, label="Scan", color="#2D98DA")
    ax.bar(labels, laser_vals, bottom=scan_vals, label="Laser on", color="#E58E26")
    ax.bar(
        labels,
        travel_vals,
        bottom=[a + b for a, b in zip(scan_vals, laser_vals)],
        label="Travel",
        color="#1B4F72",
    )
    ax.set_title("Layer-level time breakdown under the base model")
    ax.set_xlabel("Printing order")
    ax.set_ylabel("Time (s)")
    ax.grid(axis="y", alpha=0.2)
    ax.legend()
    fig.savefig(OUTPUT_LAYER_BREAKDOWN, dpi=230)
    plt.close(fig)


def make_total_breakdown(base_results: dict) -> None:
    agg = base_results["aggregate_times_s"]
    labels = ["Total task"]
    intra = [float(agg["total_intra_layer_time_s"])]
    inter_layer = [float(agg["total_inter_layer_time_s"])]
    inter_part = [float(agg["total_inter_part_time_s"])]

    fig, ax = plt.subplots(figsize=(6, 5.5), constrained_layout=True)
    ax.bar(labels, intra, label="Intra-layer", color="#1B4F72")
    ax.bar(labels, inter_layer, bottom=intra, label="Inter-layer", color="#20BF6B")
    ax.bar(
        labels,
        inter_part,
        bottom=[a + b for a, b in zip(intra, inter_layer)],
        label="Inter-part",
        color="#E58E26",
    )
    total = intra[0] + inter_layer[0] + inter_part[0]
    ax.text(0, total, f"{total:.3f}s", ha="center", va="bottom", fontsize=10)
    ax.set_title("Total task time decomposition")
    ax.set_ylabel("Time (s)")
    ax.grid(axis="y", alpha=0.2)
    ax.legend()
    fig.savefig(OUTPUT_TOTAL_BREAKDOWN, dpi=230)
    plt.close(fig)


def main() -> None:
    base_results = load_base_results()
    make_layer_breakdown()
    make_total_breakdown(base_results)
    print("Saved layer-level and total-task time breakdown figures.")


if __name__ == "__main__":
    main()
