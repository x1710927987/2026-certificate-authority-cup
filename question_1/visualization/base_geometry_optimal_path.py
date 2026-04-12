from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

from visualization_common import (
    TYPE_COLORS,
    cell_lookup,
    choose_representative_layers,
    layer_label_from_key,
    load_base_path_lookup,
    load_base_results,
    load_geometry_by_layer,
)


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_GEOMETRY = SCRIPT_DIR / "representative_layer_geometry.png"
OUTPUT_PATH = SCRIPT_DIR / "representative_layer_optimal_path.png"
OUTPUT_ORDER = SCRIPT_DIR / "representative_layer_visit_order.png"


def style_axis(ax, cells, title: str) -> None:
    xmins = [cell["xmin_mm"] for cell in cells]
    xmaxs = [cell["xmax_mm"] for cell in cells]
    ymins = [cell["ymin_mm"] for cell in cells]
    ymaxs = [cell["ymax_mm"] for cell in cells]
    ax.set_xlim(min(xmins) - 2, max(xmaxs) + 2)
    ax.set_ylim(min(ymins) - 2, max(ymaxs) + 2)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(title, fontsize=12)
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.grid(alpha=0.15, linewidth=0.5)


def draw_cells(ax, cells, show_centers: bool = True) -> None:
    for cell in cells:
        facecolor = TYPE_COLORS.get(cell["type"], "#B2BEC3")
        rect = Rectangle(
            (cell["xmin_mm"], cell["ymin_mm"]),
            cell["xmax_mm"] - cell["xmin_mm"],
            cell["ymax_mm"] - cell["ymin_mm"],
            facecolor=facecolor,
            edgecolor="white",
            linewidth=1.0,
            alpha=0.85,
        )
        ax.add_patch(rect)
        if show_centers:
            ax.scatter(cell["x_mm"], cell["y_mm"], s=10, c="#2F3640", zorder=3)


def draw_path(ax, path_ids, lookup, color="#1B4F72") -> None:
    points = [(lookup[cell_id]["x_mm"], lookup[cell_id]["y_mm"]) for cell_id in path_ids]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    ax.plot(xs, ys, color=color, linewidth=2.0, alpha=0.85, zorder=4)
    for (x1, y1), (x2, y2) in zip(points[:-1], points[1:]):
        arrow = FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="->",
            mutation_scale=8,
            linewidth=1.0,
            color=color,
            alpha=0.7,
            zorder=5,
        )
        ax.add_patch(arrow)
    start = lookup[path_ids[0]]
    end = lookup[path_ids[-1]]
    ax.scatter(start["x_mm"], start["y_mm"], s=75, c="#2ECC71", edgecolors="black", zorder=6, label="Start")
    ax.scatter(end["x_mm"], end["y_mm"], s=75, c="#E74C3C", edgecolors="black", zorder=6, label="End")


def draw_order_labels(ax, path_ids, lookup) -> None:
    for idx, cell_id in enumerate(path_ids, start=1):
        cell = lookup[cell_id]
        ax.text(
            cell["x_mm"],
            cell["y_mm"],
            str(idx),
            ha="center",
            va="center",
            fontsize=6.5,
            color="black",
            zorder=6,
        )


def make_geometry_figure(representative, geometry_by_layer) -> None:
    fig, axes = plt.subplots(1, len(representative), figsize=(6 * len(representative), 5), constrained_layout=True)
    if len(representative) == 1:
        axes = [axes]
    for ax, key in zip(axes, representative.values()):
        cells = geometry_by_layer[key]
        draw_cells(ax, cells, show_centers=True)
        style_axis(ax, cells, f"Geometry map: {layer_label_from_key(key)}")
    fig.savefig(OUTPUT_GEOMETRY, dpi=220)
    plt.close(fig)


def make_path_figure(representative, geometry_by_layer, base_path_lookup) -> None:
    fig, axes = plt.subplots(1, len(representative), figsize=(6 * len(representative), 5), constrained_layout=True)
    if len(representative) == 1:
        axes = [axes]
    for ax, key in zip(axes, representative.values()):
        cells = geometry_by_layer[key]
        lookup = cell_lookup(cells)
        path_ids = base_path_lookup[key]
        draw_cells(ax, cells, show_centers=False)
        draw_path(ax, path_ids, lookup)
        style_axis(ax, cells, f"Optimal path: {layer_label_from_key(key)}")
        ax.legend(loc="upper right", fontsize=8)
    fig.savefig(OUTPUT_PATH, dpi=220)
    plt.close(fig)


def make_order_figure(representative, geometry_by_layer, base_path_lookup) -> None:
    fig, axes = plt.subplots(1, len(representative), figsize=(6 * len(representative), 5), constrained_layout=True)
    if len(representative) == 1:
        axes = [axes]
    for ax, key in zip(axes, representative.values()):
        cells = geometry_by_layer[key]
        lookup = cell_lookup(cells)
        path_ids = base_path_lookup[key]
        draw_cells(ax, cells, show_centers=False)
        draw_order_labels(ax, path_ids, lookup)
        style_axis(ax, cells, f"Visit order: {layer_label_from_key(key)}")
    fig.savefig(OUTPUT_ORDER, dpi=240)
    plt.close(fig)


def main() -> None:
    base_results = load_base_results()
    representative = choose_representative_layers(base_results)
    geometry_by_layer = load_geometry_by_layer()
    base_path_lookup = load_base_path_lookup()

    make_geometry_figure(representative, geometry_by_layer)
    make_path_figure(representative, geometry_by_layer, base_path_lookup)
    make_order_figure(representative, geometry_by_layer, base_path_lookup)

    chosen_text = ", ".join(
        f"{part_id}->{layer_label_from_key(key)}" for part_id, key in representative.items()
    )
    print(f"Saved base-model geometry and path figures. Representative layers: {chosen_text}")


if __name__ == "__main__":
    main()
