from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt


COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from q2_visualization_common import load_visualization_context, save_metadata, to_float  # noqa: E402


OUTPUT_DIR = Path(__file__).resolve().parent


def empirical_cdf(values):
    sorted_values = sorted(values)
    n = len(sorted_values)
    probs = [(idx + 1) / n for idx in range(n)]
    return sorted_values, probs


def main() -> None:
    context = load_visualization_context()
    threshold_rows = context["threshold_rows"]
    original_values = [to_float(row["original_scan_risk"]) for row in threshold_rows]
    improved_values = [to_float(row["improved_scan_risk"]) for row in threshold_rows]
    h_crit = to_float(threshold_rows[0]["H_crit"])
    h_thres = to_float(threshold_rows[0]["H_thres"])
    quantile_q = to_float(threshold_rows[0]["quantile_q"])

    original_x, original_y = empirical_cdf(original_values)
    improved_x, improved_y = empirical_cdf(improved_values)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    axes[0].hist(original_values, bins=28, alpha=0.65, color="#4C78A8", label="original scan risk")
    axes[0].hist(improved_values, bins=28, alpha=0.65, color="#F58518", label="improved scan risk")
    axes[0].axvline(h_crit, color="#2C5E91", linestyle="--", linewidth=1.8, label="H_crit")
    axes[0].axvline(h_thres, color="#C04B2D", linestyle="--", linewidth=1.8, label="H_thres")
    axes[0].set_title("Distribution comparison under the reference path")
    axes[0].set_xlabel("heat-risk value")
    axes[0].set_ylabel("frequency")
    axes[0].grid(alpha=0.25)
    axes[0].legend(frameon=False)

    axes[1].plot(original_x, original_y, color="#4C78A8", linewidth=2, label="original empirical CDF")
    axes[1].plot(improved_x, improved_y, color="#F58518", linewidth=2, label="improved empirical CDF")
    axes[1].axhline(quantile_q, color="#666666", linestyle=":", linewidth=1.6, label="quantile q")
    axes[1].axvline(h_crit, color="#2C5E91", linestyle="--", linewidth=1.6)
    axes[1].axvline(h_thres, color="#C04B2D", linestyle="--", linewidth=1.6)
    axes[1].annotate(
        f"(H_crit={h_crit:.2f}, q={quantile_q:.3f})",
        xy=(h_crit, quantile_q),
        xytext=(h_crit * 0.72, min(0.96, quantile_q + 0.10)),
        arrowprops=dict(arrowstyle="->", color="#2C5E91"),
        fontsize=10,
        color="#2C5E91",
    )
    axes[1].annotate(
        f"(H_thres={h_thres:.6f}, q={quantile_q:.3f})",
        xy=(h_thres, quantile_q),
        xytext=(h_thres * 2.1, max(0.22, quantile_q - 0.18)),
        arrowprops=dict(arrowstyle="->", color="#C04B2D"),
        fontsize=10,
        color="#C04B2D",
    )
    axes[1].set_title("Quantile alignment from the original model to the improved model")
    axes[1].set_xlabel("heat-risk value")
    axes[1].set_ylabel("empirical CDF")
    axes[1].grid(alpha=0.25)
    axes[1].legend(frameon=False, loc="lower right")

    fig.suptitle("Fig 2-2 Threshold alignment under the fixed reference path row_major", fontsize=14, y=0.98)
    fig.tight_layout()
    output_path = OUTPUT_DIR / "fig2_2_threshold_alignment.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    save_metadata(
        OUTPUT_DIR / "fig2_2_threshold_alignment.json",
        {
            "figure_id": "fig2_2",
            "title": "Threshold alignment",
            "reference_scheme": "row_major",
            "H_crit": h_crit,
            "H_thres": h_thres,
            "quantile_q": quantile_q,
            "output_image": str(output_path),
        },
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
