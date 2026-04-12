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
    overall_rows = context["scheme_overall_rows"]
    row_by_scheme = {row["scheme_name"]: row for row in overall_rows}
    schemes = [scheme for scheme in SCHEME_ORDER if scheme in row_by_scheme]

    fig, ax = plt.subplots(figsize=(8, 6))
    for scheme in schemes:
        row = row_by_scheme[scheme]
        x = to_float(row["total_task_time_s"])
        y = to_float(row["weighted_sum_total_risk"])
        ax.scatter(x, y, s=140, color=SCHEME_COLORS[scheme], edgecolor="white", linewidth=1.0, zorder=3)
        ax.annotate(
            SCHEME_LABELS[scheme],
            xy=(x, y),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=10,
            color=SCHEME_COLORS[scheme],
        )

    ax.set_title("Fig 2-14 Time-risk Pareto view of the four path schemes")
    ax.set_xlabel("total task time / s")
    ax.set_ylabel("weighted total thermal risk")
    ax.grid(alpha=0.3)

    output_path = OUTPUT_DIR / "fig2_14_pareto_time_risk.png"
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    save_metadata(
        OUTPUT_DIR / "fig2_14_pareto_time_risk.json",
        {
            "figure_id": "fig2_14",
            "x_metric": "total_task_time_s",
            "y_metric": "weighted_sum_total_risk",
            "schemes": schemes,
            "output_image": str(output_path),
        },
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
