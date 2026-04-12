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
    / "model_parameters"
    / "alpha"
    / "alpha_overall_summary.csv"
)


def load_rows():
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    rows = load_rows()
    x_values = sorted({float(row["parameter_value"]) for row in rows})
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for scheme in SCHEME_ORDER:
        ys = [
            next(float(row["weighted_sum_total_risk"]) for row in rows if row["scheme_name"] == scheme and float(row["parameter_value"]) == x)
            for x in x_values
        ]
        ax.plot(x_values, ys, marker="o", linewidth=2, color=SCHEME_COLORS[scheme], label=scheme)
    ax.set_title("Fig 2-16 Sensitivity to temporal decay coefficient alpha")
    ax.set_xlabel("alpha")
    ax.set_ylabel("weighted total thermal risk")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False)
    output_path = OUTPUT_DIR / "fig2_16_alpha_sensitivity.png"
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    save_metadata(OUTPUT_DIR / "fig2_16_alpha_sensitivity.json", {"figure_id": "fig2_16", "input_csv": str(INPUT_CSV), "output_image": str(output_path)})
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
