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
    heat_history_series,
    load_visualization_context,
    representative_layer_title,
    save_metadata,
    select_representative_layer,
)


OUTPUT_DIR = Path(__file__).resolve().parent


def main() -> None:
    context = load_visualization_context()
    representative = select_representative_layer(context["scheme_layer_rows"])
    part_id = representative["part_id"]
    layer_id = representative["layer_id"]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8))
    for scheme_name in SCHEME_ORDER:
        series = heat_history_series(context["heat_history_rows"], scheme_name, part_id, layer_id)
        event_times = [item["event_time_s"] for item in series]
        std_values = [item["heat_std"] for item in series]
        cv_values = [
            0.0 if item["heat_mean"] <= 1e-12 else item["heat_std"] / item["heat_mean"]
            for item in series
        ]
        axes[0].plot(event_times, std_values, linewidth=2, color=SCHEME_COLORS[scheme_name], label=scheme_name)
        axes[1].plot(event_times, cv_values, linewidth=2, color=SCHEME_COLORS[scheme_name], label=scheme_name)

    axes[0].set_title("Heat-state standard deviation over time")
    axes[0].set_xlabel("event time / s")
    axes[0].set_ylabel("std of heat state")
    axes[0].grid(alpha=0.3)
    axes[1].set_title("Coefficient of variation over time")
    axes[1].set_xlabel("event time / s")
    axes[1].set_ylabel("CV of heat state")
    axes[1].grid(alpha=0.3)

    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
        fig.subplots_adjust(bottom=0.18)

    fig.suptitle(
        f"Fig 2-10 Thermal-dispersion evolution on the representative layer\n{representative_layer_title(representative)}",
        fontsize=14,
        y=0.98,
    )
    output_path = OUTPUT_DIR / "fig2_10_dispersion_evolution.png"
    fig.tight_layout(rect=[0, 0.08, 1, 0.95])
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    save_metadata(
        OUTPUT_DIR / "fig2_10_dispersion_evolution.json",
        {
            "figure_id": "fig2_10",
            "representative_layer": representative,
            "schemes": SCHEME_ORDER,
            "output_image": str(output_path),
        },
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
