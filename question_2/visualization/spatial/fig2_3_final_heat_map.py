from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt


COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from q2_visualization_common import (  # noqa: E402
    SCHEME_ORDER,
    draw_layer_values,
    filter_rows_for_layer,
    load_visualization_context,
    representative_layer_title,
    save_metadata,
    select_representative_layer,
    to_float,
)


OUTPUT_DIR = Path(__file__).resolve().parent


def main() -> None:
    context = load_visualization_context()
    representative = select_representative_layer(context["scheme_layer_rows"])
    part_id = representative["part_id"]
    layer_id = representative["layer_id"]

    geometry_rows = filter_rows_for_layer(context["geometry_rows"], part_id, layer_id)
    cell_rows = filter_rows_for_layer(context["cell_risk_rows"], part_id, layer_id)
    bounds = [
        to_float(row["final_heat_state"])
        for row in cell_rows
        if row["scheme_name"] in SCHEME_ORDER
    ]
    vmin, vmax = min(bounds), max(bounds)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10), constrained_layout=True)
    axes = axes.flatten()
    colorbars = []

    for ax, scheme_name in zip(axes, SCHEME_ORDER):
        scheme_rows = [row for row in cell_rows if row["scheme_name"] == scheme_name]
        values_by_cell = {row["cell_id"]: to_float(row["final_heat_state"]) for row in scheme_rows}
        mappable = draw_layer_values(
            ax=ax,
            layer_geometry_rows=geometry_rows,
            values_by_cell=values_by_cell,
            title=scheme_name,
            cmap_name="YlOrRd",
            vmin=vmin,
            vmax=vmax,
        )
        colorbars.append(mappable)

    fig.suptitle(
        f"Fig 2-3 Final heat accumulation map on the representative layer\n{representative_layer_title(representative)}",
        fontsize=14,
        y=0.98,
    )
    cbar = fig.colorbar(colorbars[-1], ax=axes, shrink=0.85, location="right")
    cbar.set_label("final_heat_state")
    output_path = OUTPUT_DIR / "fig2_3_final_heat_map.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    save_metadata(
        OUTPUT_DIR / "fig2_3_final_heat_map.json",
        {
            "figure_id": "fig2_3",
            "representative_layer": representative,
            "metric": "final_heat_state",
            "schemes": SCHEME_ORDER,
            "output_image": str(output_path),
        },
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
