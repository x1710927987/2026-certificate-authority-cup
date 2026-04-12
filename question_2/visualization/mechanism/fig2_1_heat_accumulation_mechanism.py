from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle


COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from q2_visualization_common import save_metadata  # noqa: E402


OUTPUT_DIR = Path(__file__).resolve().parent


def draw_event_grid(ax) -> None:
    cells = {
        "target": (2, 2),
        "n1": (1, 3),
        "n2": (3, 3),
        "n3": (1, 1),
        "n4": (3, 1),
    }
    for name, (x, y) in cells.items():
        face = "#FFD166" if name == "target" else "#DCEAF7"
        rect = Rectangle((x, y), 1, 1, facecolor=face, edgecolor="#5A5A5A", linewidth=1.2)
        ax.add_patch(rect)
        label = "target\ncell j" if name == "target" else name
        ax.text(x + 0.5, y + 0.55, label, ha="center", va="center", fontsize=10)

    arrow_specs = [
        ((1.5, 3.5), (2.0, 3.0), "historical heat"),
        ((3.5, 3.5), (3.0, 3.0), "historical heat"),
        ((1.5, 1.5), (2.0, 2.0), "historical heat"),
        ((3.5, 1.5), (3.0, 2.0), "historical heat"),
    ]
    for start, end, label in arrow_specs:
        arrow = FancyArrowPatch(start, end, arrowstyle="->", mutation_scale=14, linewidth=1.4, color="#2C5E91")
        ax.add_patch(arrow)
    ax.text(2.5, 0.75, "neighbor contributions decay with distance", ha="center", fontsize=10, color="#2C5E91")
    ax.text(2.5, 4.35, "direct self-heating pulse when the target cell is scanned", ha="center", fontsize=10, color="#C04B2D")
    self_arrow = FancyArrowPatch((2.5, 4.0), (2.5, 3.05), arrowstyle="->", mutation_scale=14, linewidth=1.6, color="#C04B2D")
    ax.add_patch(self_arrow)
    ax.set_xlim(0.6, 4.4)
    ax.set_ylim(0.4, 4.8)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Event-driven heat input around a target cell", fontsize=12)


def draw_formula_panel(ax) -> None:
    ax.axis("off")
    lines = [
        r"$H_j^{sum}(t)=\sum_{i:\,t_i\leq t} H_{ij}(t)$",
        "",
        r"$H_{ij}(t)=q(\pi_j,\pi_i)\exp[-\alpha(t-t_i)]$",
        "",
        r"$q(\pi_j,\pi_i)=",
        r"\begin{cases}",
        r"\dfrac{A_0}{c\,m_j}, & \pi_j=\pi_i \\[6pt]",
        r"\dfrac{A_1}{c\,m_j}\,w_{ij}^{contact}\exp(-\beta d_{ij}), & \pi_j\neq\pi_i",
        r"\end{cases}$",
        "",
        r"$w_{ij}^{contact}=spatial\_weight_{ij}\left(1+\gamma\dfrac{L_{ij}^{contact}}{L_0}\right)$",
        "",
        "Key idea:",
        "self-heating + historical neighbor heating",
        "with time decay and spatial decay.",
    ]
    y = 0.95
    for line in lines:
        if line.startswith("$") or line.startswith(r"\begin") or line.startswith(r"\end"):
            ax.text(0.02, y, line, fontsize=13, va="top")
            y -= 0.085
        else:
            ax.text(0.02, y, line, fontsize=11, va="top")
            y -= 0.07 if line else 0.04
    ax.set_title("Heat accumulation model used in Question 2", fontsize=12, loc="left")


def main() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8), gridspec_kw={"width_ratios": [1.0, 1.15]})
    draw_event_grid(axes[0])
    draw_formula_panel(axes[1])
    fig.suptitle("Fig 2-1 Heat accumulation mechanism", fontsize=14, y=0.98)
    fig.tight_layout()
    output_path = OUTPUT_DIR / "fig2_1_heat_accumulation_mechanism.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    save_metadata(
        OUTPUT_DIR / "fig2_1_heat_accumulation_mechanism.json",
        {
            "figure_id": "fig2_1",
            "title": "Heat accumulation mechanism",
            "description": "Schematic figure for the event-driven heat accumulation model in Question 2.",
            "output_image": str(output_path),
        },
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
