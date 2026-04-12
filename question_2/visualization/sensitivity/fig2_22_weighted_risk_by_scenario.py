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
    / "subjective_weights"
    / "subjective_weights_overall_summary.csv"
)


def load_rows():
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    rows = load_rows()
    scenarios = ["base", "hotspot_priority", "cycle_stability_priority", "uniformity_priority", "balanced"]
    x = list(range(len(scenarios)))
    width = 0.18
    fig, ax = plt.subplots(figsize=(11, 5.8))
    for idx, scheme in enumerate(SCHEME_ORDER):
        ys = [
            next(float(row["weighted_sum_total_risk"]) for row in rows if row["scheme_name"] == scheme and row["scenario_name"] == scenario)
            for scenario in scenarios
        ]
        shifted = [item + (idx - 1.5) * width for item in x]
        ax.bar(shifted, ys, width=width, color=SCHEME_COLORS[scheme], alpha=0.9, label=scheme)
    ax.set_xticks(x, scenarios, rotation=15)
    ax.set_title("Fig 2-22 Weighted total risk under subjective-weight scenarios")
    ax.set_ylabel("weighted total thermal risk")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False, ncol=4)
    output_path = OUTPUT_DIR / "fig2_22_weighted_risk_by_scenario.png"
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    save_metadata(OUTPUT_DIR / "fig2_22_weighted_risk_by_scenario.json", {"figure_id": "fig2_22", "input_csv": str(INPUT_CSV), "output_image": str(output_path)})
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
