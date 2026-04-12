from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from q2_visualization_common import (  # noqa: E402
    filter_rows_for_layer,
    geometry_lookup,
    load_visualization_context,
    order_geometry_rows,
    representative_layer_title,
    save_metadata,
    select_layer_with_flag,
    to_float,
)


OUTPUT_DIR = Path(__file__).resolve().parent


def draw_overlay_panel(ax, geometry_rows, cell_rows, title: str, sensitive_flag: str) -> None:
    ordered_rows = order_geometry_rows(geometry_rows)
    values = sorted(to_float(row["peak_heat_state"]) for row in cell_rows)
    threshold = values[max(0, int(0.9 * len(values)) - 1)]
    lookup = {row["cell_id"]: row for row in cell_rows}
    xs = []
    ys = []
    for row in ordered_rows:
        cell_id = row["cell_id"]
        risk_row = lookup[cell_id]
        xmin = to_float(row["xmin_mm"])
        xmax = to_float(row["xmax_mm"])
        ymin = to_float(row["ymin_mm"])
        ymax = to_float(row["ymax_mm"])
        base_face = "#F6F6F6"
        if to_float(risk_row["peak_heat_state"]) >= threshold:
            base_face = "#F4A261"
        rect = Rectangle((xmin, ymin), xmax - xmin, ymax - ymin, facecolor=base_face, edgecolor="#999999", linewidth=0.8)
        ax.add_patch(rect)
        if risk_row[sensitive_flag] == "1":
            outline = Rectangle(
                (xmin, ymin),
                xmax - xmin,
                ymax - ymin,
                fill=False,
                edgecolor="#1D4E89",
                linewidth=2.0,
            )
            ax.add_patch(outline)
        xs.extend([xmin, xmax])
        ys.extend([ymin, ymax])
    ax.set_xlim(min(xs) - 1, max(xs) + 1)
    ax.set_ylim(min(ys) - 1, max(ys) + 1)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("x / mm")
    ax.set_ylabel("y / mm")
    ax.text(
        0.02,
        0.02,
        "orange = top 10% peak heat, blue outline = structural-sensitive cells",
        transform=ax.transAxes,
        fontsize=8,
        ha="left",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.85, edgecolor="none"),
    )


def main() -> None:
    context = load_visualization_context()
    hole_layer = select_layer_with_flag(context["cell_risk_rows"], context["scheme_layer_rows"], "is_hole")
    thin_layer = select_layer_with_flag(context["cell_risk_rows"], context["scheme_layer_rows"], "is_thin")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8), constrained_layout=True)

    hole_geometry = filter_rows_for_layer(context["geometry_rows"], hole_layer["part_id"], hole_layer["layer_id"])
    hole_cell_rows = [
        row
        for row in context["cell_risk_rows"]
        if row["scheme_name"] == "minimum_time"
        and row["part_id"] == hole_layer["part_id"]
        and int(row["layer_id"]) == hole_layer["layer_id"]
    ]
    draw_overlay_panel(
        axes[0],
        hole_geometry,
        hole_cell_rows,
        f"Hole-sensitive layer\n{representative_layer_title(hole_layer)}",
        "is_hole",
    )

    thin_geometry = filter_rows_for_layer(context["geometry_rows"], thin_layer["part_id"], thin_layer["layer_id"])
    thin_cell_rows = [
        row
        for row in context["cell_risk_rows"]
        if row["scheme_name"] == "minimum_time"
        and row["part_id"] == thin_layer["part_id"]
        and int(row["layer_id"]) == thin_layer["layer_id"]
    ]
    draw_overlay_panel(
        axes[1],
        thin_geometry,
        thin_cell_rows,
        f"Thin-wall-sensitive layer\n{representative_layer_title(thin_layer)}",
        "is_thin",
    )

    fig.suptitle("Fig 2-6 Structural-sensitive regions and high-risk zones", fontsize=14, y=1.02)
    output_path = OUTPUT_DIR / "fig2_6_structural_sensitive_overlay.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    save_metadata(
        OUTPUT_DIR / "fig2_6_structural_sensitive_overlay.json",
        {
            "figure_id": "fig2_6",
            "hole_layer": hole_layer,
            "thin_layer": thin_layer,
            "scheme_name": "minimum_time",
            "output_image": str(output_path),
        },
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
