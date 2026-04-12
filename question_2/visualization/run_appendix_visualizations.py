from __future__ import annotations

import subprocess
import sys
from pathlib import Path


VIS_ROOT = Path(__file__).resolve().parent

SCRIPTS = [
    VIS_ROOT / "spatial" / "fig2_4_threshold_exceedance_map.py",
    VIS_ROOT / "spatial" / "fig2_6_structural_sensitive_overlay.py",
    VIS_ROOT / "temporal" / "fig2_7_representative_cell_histories.py",
    VIS_ROOT / "temporal" / "fig2_9_exceedance_count_evolution.py",
    VIS_ROOT / "temporal" / "fig2_10_dispersion_evolution.py",
    VIS_ROOT / "comparison" / "fig2_11_representative_layer_metrics.py",
    VIS_ROOT / "comparison" / "fig2_13_cell_risk_boxplots.py",
    VIS_ROOT / "sensitivity" / "fig2_15_A0_sensitivity.py",
    VIS_ROOT / "sensitivity" / "fig2_16_alpha_sensitivity.py",
    VIS_ROOT / "sensitivity" / "fig2_17_beta_sensitivity.py",
    VIS_ROOT / "sensitivity" / "fig2_18_gamma_sensitivity.py",
    VIS_ROOT / "sensitivity" / "fig2_19_material_risk_comparison.py",
    VIS_ROOT / "sensitivity" / "fig2_20_material_rank_heatmap.py",
    VIS_ROOT / "sensitivity" / "fig2_22_weighted_risk_by_scenario.py",
]


def main() -> None:
    for script_path in SCRIPTS:
        print(f"Running {script_path.name} ...")
        subprocess.run([sys.executable, str(script_path)], check=True)
    print("All appendix-style Question 2 visualizations have been generated.")


if __name__ == "__main__":
    main()
