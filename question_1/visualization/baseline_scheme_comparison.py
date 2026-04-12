from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

from visualization_common import (
    BASELINE_PATHS_FILE,
    TYPE_COLORS,
    cell_lookup,
    choose_representative_layers,
    compute_path_metrics,
    layer_label_from_key,
    load_base_path_lookup,
    load_base_results,
    load_baseline_paths,
    load_geometry_by_layer,
    load_machine_params,
    load_travel_distances_by_layer,
)


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH_COMPARE_A = SCRIPT_DIR / "baseline_vs_optimal_path_part_A.png"
OUTPUT_PATH_COMPARE_B = SCRIPT_DIR / "baseline_vs_optimal_path_part_B.png"
OUTPUT_METRIC_PLOT = SCRIPT_DIR / "baseline_vs_optimal_metrics.png"
OUTPUT_METRICS_CSV = SCRIPT_DIR / "baseline_vs_optimal_metrics.csv"

STRATEGY_ORDER = ["row_major", "serpentine", "center_out", "optimal"]
STRATEGY_COLORS = {
    "row_major": "#8E44AD",
    "serpentine": "#16A085",
    "center_out": "#E67E22",
    "optimal": "#1B4F72",
}


def style_axis(ax, cells, title: str) -> None:
    xmins = [cell["xmin_mm"] for cell in cells]
    xmaxs = [cell["xmax_mm"] for cell in cells]
    ymins = [cell["ymin_mm"] for cell in cells]
    ymaxs = [cell["ymax_mm"] for cell in cells]
    ax.set_xlim(min(xmins) - 2, max(xmaxs) + 2)
    ax.set_ylim(min(ymins) - 2, max(ymaxs) + 2)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.grid(alpha=0.15, linewidth=0.5)


def draw_cells(ax, cells) -> None:
    for cell in cells:
        rect = Rectangle(
            (cell["xmin_mm"], cell["ymin_mm"]),
            cell["xmax_mm"] - cell["xmin_mm"],
            cell["ymax_mm"] - cell["ymin_mm"],
            facecolor=TYPE_COLORS.get(cell["type"], "#B2BEC3"),
            edgecolor="white",
            linewidth=0.9,
            alpha=0.8,
        )
        ax.add_patch(rect)


def draw_path(ax, path_ids, lookup, color: str) -> None:
    points = [(lookup[cell_id]["x_mm"], lookup[cell_id]["y_mm"]) for cell_id in path_ids]
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    ax.plot(xs, ys, color=color, linewidth=1.8, alpha=0.85, zorder=4)
    for (x1, y1), (x2, y2) in zip(points[:-1], points[1:]):
        arrow = FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="->",
            mutation_scale=7,
            linewidth=0.9,
            color=color,
            alpha=0.65,
            zorder=5,
        )
        ax.add_patch(arrow)
    start = lookup[path_ids[0]]
    end = lookup[path_ids[-1]]
    ax.scatter(start["x_mm"], start["y_mm"], s=55, c="#2ECC71", edgecolors="black", zorder=6)
    ax.scatter(end["x_mm"], end["y_mm"], s=55, c="#E74C3C", edgecolors="black", zorder=6)


def compute_scheme_metrics():
    base_results = load_base_results()
    representative = choose_representative_layers(base_results)
    geometry_by_layer = load_geometry_by_layer()
    travel_by_layer = load_travel_distances_by_layer()
    machine = load_machine_params()
    baseline_lookup = load_baseline_paths()
    base_path_lookup = load_base_path_lookup()

    scan_speed = float(machine["scan_speed_mm_per_s"])
    travel_speed = float(machine["travel_speed_mm_per_s"])
    laser_on = float(machine["laser_on_delay_s"])

    aggregate = {
        strategy: {"travel_distance_mm": 0.0, "layer_total_time_s": 0.0}
        for strategy in STRATEGY_ORDER
    }

    for key, cells in geometry_by_layer.items():
        travel_distances = travel_by_layer[key]
        for strategy in STRATEGY_ORDER:
            if strategy == "optimal":
                path_ids = base_path_lookup[key]
            else:
                path_ids = baseline_lookup[(key[0], key[1], strategy)]
            metrics = compute_path_metrics(path_ids, cells, travel_distances, scan_speed, travel_speed, laser_on)
            aggregate[strategy]["travel_distance_mm"] += metrics["travel_distance_mm"]
            aggregate[strategy]["layer_total_time_s"] += metrics["layer_total_time_s"]

    with OUTPUT_METRICS_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["strategy_name", "total_travel_distance_mm", "total_layer_time_s"])
        for strategy in STRATEGY_ORDER:
            writer.writerow([
                strategy,
                f"{aggregate[strategy]['travel_distance_mm']:.6f}",
                f"{aggregate[strategy]['layer_total_time_s']:.6f}",
            ])

    return representative, geometry_by_layer, baseline_lookup, base_path_lookup, aggregate


def make_path_compare(output_path: Path, key, geometry_by_layer, baseline_lookup, base_path_lookup) -> None:
    cells = geometry_by_layer[key]
    lookup = cell_lookup(cells)
    fig, axes = plt.subplots(2, 2, figsize=(11, 10), constrained_layout=True)
    axes = axes.ravel()
    for ax, strategy in zip(axes, STRATEGY_ORDER):
        draw_cells(ax, cells)
        if strategy == "optimal":
            path_ids = base_path_lookup[key]
        else:
            path_ids = baseline_lookup[(key[0], key[1], strategy)]
        draw_path(ax, path_ids, lookup, STRATEGY_COLORS[strategy])
        style_axis(ax, cells, f"{strategy}: {layer_label_from_key(key)}")
    fig.savefig(output_path, dpi=230)
    plt.close(fig)


def make_metric_plot(aggregate) -> None:
    strategies = STRATEGY_ORDER
    travel_vals = [aggregate[s]["travel_distance_mm"] for s in strategies]
    time_vals = [aggregate[s]["layer_total_time_s"] for s in strategies]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    axes[0].bar(strategies, travel_vals, color=[STRATEGY_COLORS[s] for s in strategies])
    axes[0].set_title("Total travel distance across all layers")
    axes[0].set_ylabel("Distance (mm)")
    axes[0].grid(axis="y", alpha=0.2)

    axes[1].bar(strategies, time_vals, color=[STRATEGY_COLORS[s] for s in strategies])
    axes[1].set_title("Total intra-layer time across all layers")
    axes[1].set_ylabel("Time (s)")
    axes[1].grid(axis="y", alpha=0.2)

    optimal_distance = aggregate["optimal"]["travel_distance_mm"]
    optimal_time = aggregate["optimal"]["layer_total_time_s"]
    for ax, vals, optimal_val in (
        (axes[0], travel_vals, optimal_distance),
        (axes[1], time_vals, optimal_time),
    ):
        for idx, val in enumerate(vals):
            if val == 0:
                continue
            improvement = (val - optimal_val) / val * 100.0
            ax.text(idx, val, f"{improvement:.2f}%", ha="center", va="bottom", fontsize=8)

    fig.savefig(OUTPUT_METRIC_PLOT, dpi=230)
    plt.close(fig)


def main() -> None:
    representative, geometry_by_layer, baseline_lookup, base_path_lookup, aggregate = compute_scheme_metrics()
    make_path_compare(OUTPUT_PATH_COMPARE_A, representative["part_A"], geometry_by_layer, baseline_lookup, base_path_lookup)
    make_path_compare(OUTPUT_PATH_COMPARE_B, representative["part_B"], geometry_by_layer, baseline_lookup, base_path_lookup)
    make_metric_plot(aggregate)
    print(f"Saved baseline-vs-optimal comparison figures using data from {BASELINE_PATHS_FILE.name}.")


if __name__ == "__main__":
    main()
