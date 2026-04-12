from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt


COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from q2_visualization_common import (  # noqa: E402
    SCHEME_COLORS,
    SCHEME_ORDER,
    SCHEME_LABELS,
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
    layer_rows = filter_rows_for_layer(context["scheme_layer_rows"], part_id, layer_id)
    row_by_scheme = {row["scheme_name"]: row for row in layer_rows}
    schemes = [scheme for scheme in SCHEME_ORDER if scheme in row_by_scheme]
    x_positions = list(range(len(schemes)))

    metric_specs = [
        ("R_theta", "R_theta"),
        ("R_mu", "R_mu"),
        ("R_xi", "R_xi"),
        ("R_phi", "R_phi"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()
    for ax, (metric_key, title) in zip(axes, metric_specs):
        values = [to_float(row_by_scheme[scheme][metric_key]) for scheme in schemes]
        colors = [SCHEME_COLORS[scheme] for scheme in schemes]
        ax.bar(x_positions, values, color=colors, alpha=0.9)
        ax.set_xticks(x_positions, [SCHEME_LABELS[scheme] for scheme in schemes], rotation=15)
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle(
        f"Fig 2-11 Thermal-risk indicator comparison on the representative layer\n{representative_layer_title(representative)}",
        fontsize=14,
        y=0.98,
    )
    fig.tight_layout()
    output_path = OUTPUT_DIR / "fig2_11_representative_layer_metrics.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    save_metadata(
        OUTPUT_DIR / "fig2_11_representative_layer_metrics.json",
        {
            "figure_id": "fig2_11",
            "representative_layer": representative,
            "metrics": [item[0] for item in metric_specs],
            "schemes": schemes,
            "output_image": str(output_path),
        },
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
