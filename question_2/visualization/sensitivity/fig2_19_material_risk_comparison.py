from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt

COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from q2_visualization_common import SCHEME_COLORS, SCHEME_ORDER, save_metadata  # noqa: E402


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
    x = list(range(len(materials)))
    width = 0.18
    fig, ax = plt.subplots(figsize=(11, 5.8))
    for idx, scheme in enumerate(SCHEME_ORDER):
        ys = [
            next(float(row["weighted_sum_total_risk"]) for row in rows if row["scheme_name"] == scheme and row["material_name"] == mat)
            for mat in materials
        ]
        shifted = [item + (idx - 1.5) * width for item in x]
        ax.bar(shifted, ys, width=width, color=SCHEME_COLORS[scheme], alpha=0.9, label=scheme)
    ax.set_xticks(x, materials, rotation=15)
    ax.set_title("Fig 2-19 Weighted total thermal risk across materials")
    ax.set_ylabel("weighted total thermal risk")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False, ncol=4)
    output_path = OUTPUT_DIR / "fig2_19_material_risk_comparison.png"
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    save_metadata(OUTPUT_DIR / "fig2_19_material_risk_comparison.json", {"figure_id": "fig2_19", "input_csv": str(INPUT_CSV), "output_image": str(output_path)})
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
