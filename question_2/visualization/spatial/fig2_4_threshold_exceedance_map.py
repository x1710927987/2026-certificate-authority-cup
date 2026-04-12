from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, Normalize


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
    h_thres = context["base_results"]["thermal_model_parameters"]["H_thres_aligned"]

    geometry_rows = filter_rows_for_layer(context["geometry_rows"], part_id, layer_id)
    cell_rows = filter_rows_for_layer(context["cell_risk_rows"], part_id, layer_id)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10), constrained_layout=True)
    axes = axes.flatten()
    cmap = ListedColormap(["#E7EEF5", "#D1495B"])
    mappable = None
    for ax, scheme_name in zip(axes, SCHEME_ORDER):
        scheme_rows = [row for row in cell_rows if row["scheme_name"] == scheme_name]
        values_by_cell = {
            row["cell_id"]: 1.0 if to_float(row["final_heat_state"]) > h_thres else 0.0
            for row in scheme_rows
        }
        mappable = draw_layer_values(
            ax=ax,
            layer_geometry_rows=geometry_rows,
            values_by_cell=values_by_cell,
            title=scheme_name,
            cmap_name="coolwarm",
            vmin=0.0,
            vmax=1.0,
        )
        mappable.set_cmap(cmap)
        mappable.set_norm(Normalize(vmin=0.0, vmax=1.0))
        ax.text(
            0.02,
            0.02,
            f"red = final_heat_state > H_thres ({h_thres:.6f})",
            transform=ax.transAxes,
            fontsize=8,
            ha="left",
            va="bottom",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor="none"),
        )

    fig.suptitle(
        f"Fig 2-4 Threshold exceedance map on the representative layer\n{representative_layer_title(representative)}",
        fontsize=14,
        y=0.98,
    )
    cbar = fig.colorbar(mappable, ax=axes, shrink=0.82, location="right", ticks=[0, 1])
    cbar.ax.set_yticklabels(["below", "above"])
    cbar.set_label("threshold status")
    output_path = OUTPUT_DIR / "fig2_4_threshold_exceedance_map.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    save_metadata(
        OUTPUT_DIR / "fig2_4_threshold_exceedance_map.json",
        {
            "figure_id": "fig2_4",
            "representative_layer": representative,
            "H_thres": h_thres,
            "schemes": SCHEME_ORDER,
            "output_image": str(output_path),
        },
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
