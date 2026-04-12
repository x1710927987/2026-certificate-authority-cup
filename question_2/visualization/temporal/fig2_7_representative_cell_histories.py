from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from q2_visualization_common import (  # noqa: E402
    load_visualization_context,
    representative_layer_title,
    save_metadata,
    select_layer_with_flag,
    select_representative_cells,
    select_representative_layer,
    to_float,
)


OUTPUT_DIR = Path(__file__).resolve().parent


def collect_history(rows, scheme_name, part_id, layer_id, target_cell_id):
    matched = [
        row
        for row in rows
        if row["scheme_name"] == scheme_name
        and row["part_id"] == part_id
        and int(row["layer_id"]) == layer_id
        and row["target_cell_id"] == target_cell_id
    ]
    matched.sort(key=lambda row: int(row["event_step"]))
    return [to_float(row["event_time_s"]) for row in matched], [to_float(row["heat_state"]) for row in matched]


def main() -> None:
    context = load_visualization_context()
    hole_layer = select_representative_layer(context["scheme_layer_rows"])
    thin_layer = select_layer_with_flag(context["cell_risk_rows"], context["scheme_layer_rows"], "is_thin")
    hole_cells = select_representative_cells(
        context["cell_risk_rows"], hole_layer["part_id"], hole_layer["layer_id"], scheme_name="row_major"
    )
    thin_cells = select_representative_cells(
        context["cell_risk_rows"], thin_layer["part_id"], thin_layer["layer_id"], scheme_name="row_major"
    )

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)

    left_labels = {
        "hotspot": hole_cells["hotspot"],
        "hole": hole_cells["hole"],
        "normal": hole_cells["normal"],
    }
    for label, cell_id in left_labels.items():
        times, values = collect_history(
            context["heat_history_rows"], "row_major", hole_layer["part_id"], hole_layer["layer_id"], cell_id
        )
        axes[0].plot(times, values, linewidth=2, label=f"{label}: {cell_id}")
    axes[0].set_title(f"Representative cells on {representative_layer_title(hole_layer)}")
    axes[0].set_xlabel("event time / s")
    axes[0].set_ylabel("heat state")
    axes[0].grid(alpha=0.3)
    axes[0].legend(frameon=False, fontsize=8)

    right_labels = {
        "hotspot": thin_cells["hotspot"],
        "thin": thin_cells["thin"],
        "normal": thin_cells["normal"],
    }
    for label, cell_id in right_labels.items():
        times, values = collect_history(
            context["heat_history_rows"], "row_major", thin_layer["part_id"], thin_layer["layer_id"], cell_id
        )
        axes[1].plot(times, values, linewidth=2, label=f"{label}: {cell_id}")
    axes[1].set_title(f"Representative cells on {representative_layer_title(thin_layer)}")
    axes[1].set_xlabel("event time / s")
    axes[1].set_ylabel("heat state")
    axes[1].grid(alpha=0.3)
    axes[1].legend(frameon=False, fontsize=8)

    fig.suptitle("Fig 2-7 Heat-history curves of representative cells under row_major", fontsize=14, y=1.02)
    output_path = OUTPUT_DIR / "fig2_7_representative_cell_histories.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    save_metadata(
        OUTPUT_DIR / "fig2_7_representative_cell_histories.json",
        {
            "figure_id": "fig2_7",
            "scheme_name": "row_major",
            "hole_layer": hole_layer,
            "thin_layer": thin_layer,
            "hole_layer_cells": left_labels,
            "thin_layer_cells": right_labels,
            "output_image": str(output_path),
        },
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
