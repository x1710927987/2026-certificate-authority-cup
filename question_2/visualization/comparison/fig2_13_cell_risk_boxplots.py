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
    load_visualization_context,
    save_metadata,
    to_float,
)


OUTPUT_DIR = Path(__file__).resolve().parent


def main() -> None:
    context = load_visualization_context()
    cell_rows = context["cell_risk_rows"]
    metric_specs = [
        ("mu", "mu"),
        ("xi", "xi"),
        ("theta", "theta"),
        ("phi", "phi"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()
    for ax, (metric_key, title) in zip(axes, metric_specs):
        grouped_values = [
            [to_float(row[metric_key]) for row in cell_rows if row["scheme_name"] == scheme]
            for scheme in SCHEME_ORDER
        ]
        box = ax.boxplot(
            grouped_values,
            patch_artist=True,
            tick_labels=[SCHEME_LABELS[name] for name in SCHEME_ORDER],
        )
        for patch, scheme in zip(box["boxes"], SCHEME_ORDER):
            patch.set_facecolor(SCHEME_COLORS[scheme])
            patch.set_alpha(0.6)
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=15)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Fig 2-13 Cell-level thermal-risk distribution comparison", fontsize=14, y=0.98)
    fig.tight_layout()
    output_path = OUTPUT_DIR / "fig2_13_cell_risk_boxplots.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    save_metadata(
        OUTPUT_DIR / "fig2_13_cell_risk_boxplots.json",
        {
            "figure_id": "fig2_13",
            "metrics": [item[0] for item in metric_specs],
            "schemes": SCHEME_ORDER,
            "output_image": str(output_path),
        },
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
