from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt

COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from q2_visualization_common import SCHEME_ORDER, save_metadata  # noqa: E402


OUTPUT_DIR = Path(__file__).resolve().parent
INPUT_CSV = (
    Path(__file__).resolve().parents[2]
    / "sensitivity_analysis"
    / "materials"
    / "materials_overall_summary.csv"
)


def load_rows():
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    rows = load_rows()
    materials = ["PA12", "316L", "Ti-6Al-4V", "AlSi10Mg", "Inconel 718"]
    matrix = [
        [
            int(next(row["weighted_sum_rank"] for row in rows if row["material_name"] == mat and row["scheme_name"] == scheme))
            for scheme in SCHEME_ORDER
        ]
        for mat in materials
    ]
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    image = ax.imshow(matrix, cmap="YlOrRd_r", aspect="auto")
    ax.set_xticks(range(len(SCHEME_ORDER)), SCHEME_ORDER, rotation=15)
    ax.set_yticks(range(len(materials)), materials)
    ax.set_title("Fig 2-20 Material-path ranking heatmap")
    for i, mat in enumerate(materials):
        for j, scheme in enumerate(SCHEME_ORDER):
            ax.text(j, i, matrix[i][j], ha="center", va="center", color="black")
    fig.colorbar(image, ax=ax, shrink=0.85)
    output_path = OUTPUT_DIR / "fig2_20_material_rank_heatmap.png"
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    save_metadata(OUTPUT_DIR / "fig2_20_material_rank_heatmap.json", {"figure_id": "fig2_20", "input_csv": str(INPUT_CSV), "output_image": str(output_path)})
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
