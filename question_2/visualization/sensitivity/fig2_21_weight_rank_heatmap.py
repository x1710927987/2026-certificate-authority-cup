from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt


COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from q2_visualization_common import (  # noqa: E402
    SCHEME_ORDER,
    SCHEME_LABELS,
    load_visualization_context,
    save_metadata,
)


OUTPUT_DIR = Path(__file__).resolve().parent


def main() -> None:
    context = load_visualization_context()
    overall_rows = context["subjective_overall_rows"]
    scenario_rows = context["subjective_scenario_rows"]
    scenario_names = [row["scenario_name"] for row in scenario_rows]

    weighted_rank_matrix = [
        [
            int(
                next(
                    row["weighted_sum_rank"]
                    for row in overall_rows
                    if row["scenario_name"] == scenario_name and row["scheme_name"] == scheme_name
                )
            )
            for scheme_name in SCHEME_ORDER
        ]
        for scenario_name in scenario_names
    ]
    topsis_rank_matrix = [
        [
            int(
                next(
                    row["topsis_rank"]
                    for row in overall_rows
                    if row["scenario_name"] == scenario_name and row["scheme_name"] == scheme_name
                )
            )
            for scheme_name in SCHEME_ORDER
        ]
        for scenario_name in scenario_names
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.5))
    for ax, matrix, title in zip(
        axes,
        [weighted_rank_matrix, topsis_rank_matrix],
        ["Weighted-sum ranking", "TOPSIS ranking"],
    ):
        image = ax.imshow(matrix, cmap="YlOrRd_r", aspect="auto")
        ax.set_xticks(range(len(SCHEME_ORDER)), [SCHEME_LABELS[name] for name in SCHEME_ORDER], rotation=15)
        ax.set_yticks(range(len(scenario_names)), scenario_names)
        ax.set_title(title)
        for i, scenario_name in enumerate(scenario_names):
            for j, scheme_name in enumerate(SCHEME_ORDER):
                ax.text(j, i, matrix[i][j], ha="center", va="center", color="black")
        fig.colorbar(image, ax=ax, shrink=0.82)

    fig.suptitle("Fig 2-21 Scheme-rank heatmap under subjective-weight scenarios", fontsize=14, y=0.98)
    fig.tight_layout()
    output_path = OUTPUT_DIR / "fig2_21_weight_rank_heatmap.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    save_metadata(
        OUTPUT_DIR / "fig2_21_weight_rank_heatmap.json",
        {
            "figure_id": "fig2_21",
            "scenarios": scenario_names,
            "schemes": SCHEME_ORDER,
            "output_image": str(output_path),
        },
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
