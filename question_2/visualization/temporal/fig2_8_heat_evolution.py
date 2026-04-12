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

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for scheme_name in SCHEME_ORDER:
        series = heat_history_series(context["heat_history_rows"], scheme_name, part_id, layer_id)
        event_times = [item["event_time_s"] for item in series]
        heat_mean = [item["heat_mean"] for item in series]
        heat_peak = [item["heat_peak"] for item in series]
        axes[0].plot(event_times, heat_mean, linewidth=2, color=SCHEME_COLORS[scheme_name], label=scheme_name)
        axes[1].plot(event_times, heat_peak, linewidth=2, color=SCHEME_COLORS[scheme_name], label=scheme_name)

    axes[0].set_title("Average heat-state evolution")
    axes[0].set_xlabel("event time / s")
    axes[0].set_ylabel("average heat state")
    axes[0].grid(alpha=0.3)
    axes[1].set_title("Peak heat-state evolution")
    axes[1].set_xlabel("event time / s")
    axes[1].set_ylabel("peak heat state")
    axes[1].grid(alpha=0.3)

    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
        fig.subplots_adjust(bottom=0.18)

    fig.suptitle(
        f"Fig 2-8 Average and peak heat-state evolution on the representative layer\n{representative_layer_title(representative)}",
        fontsize=14,
        y=0.98,
    )
    fig.tight_layout()
    output_path = OUTPUT_DIR / "fig2_8_heat_evolution.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    save_metadata(
        OUTPUT_DIR / "fig2_8_heat_evolution.json",
        {
            "figure_id": "fig2_8",
            "representative_layer": representative,
            "schemes": SCHEME_ORDER,
            "output_image": str(output_path),
        },
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
