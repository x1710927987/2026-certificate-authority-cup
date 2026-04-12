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

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for scheme_name in SCHEME_ORDER:
        series = heat_history_series(context["heat_history_rows"], scheme_name, part_id, layer_id)
        event_times = [item["event_time_s"] for item in series]
        counts = [item["above_threshold_count"] for item in series]
        ax.plot(event_times, counts, linewidth=2, color=SCHEME_COLORS[scheme_name], label=scheme_name)

    ax.set_title(
        f"Fig 2-9 Number of above-threshold cells over time\n{representative_layer_title(representative)}"
    )
    ax.set_xlabel("event time / s")
    ax.set_ylabel("above-threshold cell count")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False)

    output_path = OUTPUT_DIR / "fig2_9_exceedance_count_evolution.png"
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    save_metadata(
        OUTPUT_DIR / "fig2_9_exceedance_count_evolution.json",
        {
            "figure_id": "fig2_9",
            "representative_layer": representative,
            "schemes": SCHEME_ORDER,
            "output_image": str(output_path),
        },
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
