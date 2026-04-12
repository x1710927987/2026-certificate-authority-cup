from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

from visualization_common import (
    FIXED_ENDPOINT_SUMMARY,
    FIXED_START_SUMMARY,
    RETURN_WAREHOUSE_SUMMARY,
    TYPE_COLORS,
    cell_lookup,
    layer_label_from_key,
    load_base_path_lookup,
    load_csv_dicts,
    load_geometry_by_layer,
    load_travel_distances_by_layer,
    solve_open_path,
)


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_FIXED_START = SCRIPT_DIR / "fixed_starting_point_path_comparison.png"
OUTPUT_FIXED_END = SCRIPT_DIR / "fixed_endpoint_path_comparison.png"
OUTPUT_RETURN = SCRIPT_DIR / "return_to_warehouse_path_comparison.png"

WAREHOUSE_X_MM = 0.0
WAREHOUSE_Y_MM = 0.0


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


def draw_path(ax, path_ids, lookup, color, label) -> None:
    points = [(lookup[cell_id]["x_mm"], lookup[cell_id]["y_mm"]) for cell_id in path_ids]
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    ax.plot(xs, ys, color=color, linewidth=2.0, alpha=0.82, label=label, zorder=4)
    for (x1, y1), (x2, y2) in zip(points[:-1], points[1:]):
        arrow = FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="->",
            mutation_scale=8,
            linewidth=0.9,
            color=color,
            alpha=0.6,
            zorder=5,
        )
        ax.add_patch(arrow)
    start = lookup[path_ids[0]]
    end = lookup[path_ids[-1]]
    ax.scatter(start["x_mm"], start["y_mm"], s=60, c="#2ECC71", edgecolors="black", zorder=6)
    ax.scatter(end["x_mm"], end["y_mm"], s=60, c="#E74C3C", edgecolors="black", zorder=6)


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


def choose_max_row(path: Path, delta_field: str) -> dict:
    rows = load_csv_dicts(path)
    return sorted(rows, key=lambda row: (-float(row[delta_field]), int(row["schedule_index"])))[0]


def make_two_panel_plot(output_path: Path, cells, base_path, candidate_path, title_left: str, title_right: str, extra_marker=None) -> None:
    lookup = cell_lookup(cells)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), constrained_layout=True)
    for ax, title, path_ids, color in (
        (axes[0], title_left, base_path, "#1B4F72"),
        (axes[1], title_right, candidate_path, "#8E44AD"),
    ):
        draw_cells(ax, cells)
        draw_path(ax, path_ids, lookup, color=color, label=title)
        style_axis(ax, cells, title)
        if extra_marker is not None and ax is axes[1]:
            ax.scatter(extra_marker[0], extra_marker[1], marker="s", s=80, c="#F1C40F", edgecolors="black", zorder=7)
        ax.legend(loc="upper right", fontsize=8)
    fig.savefig(output_path, dpi=230)
    plt.close(fig)


def main() -> None:
    base_path_lookup = load_base_path_lookup()
    geometry_by_layer = load_geometry_by_layer()
    travel_by_layer = load_travel_distances_by_layer()

    start_row = choose_max_row(FIXED_START_SUMMARY, "worst_delta_time_percent")
    start_key = (start_row["part_id"], int(start_row["layer_id"]))
    start_candidate, _ = solve_open_path(
        geometry_by_layer[start_key],
        travel_by_layer[start_key],
        fixed_start_cell_id=start_row["worst_fixed_start_cell_id"],
    )
    make_two_panel_plot(
        OUTPUT_FIXED_START,
        geometry_by_layer[start_key],
        base_path_lookup[start_key],
        start_candidate,
        f"Base path: {layer_label_from_key(start_key)}",
        f"Fixed start ({start_row['worst_fixed_start_cell_id']})",
    )

    end_row = choose_max_row(FIXED_ENDPOINT_SUMMARY, "worst_delta_time_percent")
    end_key = (end_row["part_id"], int(end_row["layer_id"]))
    end_candidate, _ = solve_open_path(
        geometry_by_layer[end_key],
        travel_by_layer[end_key],
        fixed_end_cell_id=end_row["worst_fixed_end_cell_id"],
    )
    make_two_panel_plot(
        OUTPUT_FIXED_END,
        geometry_by_layer[end_key],
        base_path_lookup[end_key],
        end_candidate,
        f"Base path: {layer_label_from_key(end_key)}",
        f"Fixed end ({end_row['worst_fixed_end_cell_id']})",
    )

    return_row = choose_max_row(RETURN_WAREHOUSE_SUMMARY, "delta_time_percent")
    return_key = (return_row["part_id"], int(return_row["layer_id"]))
    return_candidate, _ = solve_open_path(
        geometry_by_layer[return_key],
        travel_by_layer[return_key],
        return_point=(WAREHOUSE_X_MM, WAREHOUSE_Y_MM),
    )
    make_two_panel_plot(
        OUTPUT_RETURN,
        geometry_by_layer[return_key],
        base_path_lookup[return_key],
        return_candidate,
        f"Base path: {layer_label_from_key(return_key)}",
        "Return to warehouse",
        extra_marker=(WAREHOUSE_X_MM, WAREHOUSE_Y_MM),
    )

    print(
        "Saved structural-sensitivity path comparison figures for "
        f"{layer_label_from_key(start_key)}, {layer_label_from_key(end_key)}, and {layer_label_from_key(return_key)}."
    )


if __name__ == "__main__":
    main()
