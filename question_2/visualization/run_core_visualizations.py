from __future__ import annotations

import subprocess
import sys
from pathlib import Path


VIS_ROOT = Path(__file__).resolve().parent

SCRIPTS = [
    VIS_ROOT / "mechanism" / "fig2_1_heat_accumulation_mechanism.py",
    VIS_ROOT / "mechanism" / "fig2_2_threshold_alignment.py",
    VIS_ROOT / "spatial" / "fig2_3_final_heat_map.py",
    VIS_ROOT / "spatial" / "fig2_5_phi_map.py",
    VIS_ROOT / "temporal" / "fig2_8_heat_evolution.py",
    VIS_ROOT / "comparison" / "fig2_12_global_risk_comparison.py",
    VIS_ROOT / "comparison" / "fig2_14_pareto_time_risk.py",
    VIS_ROOT / "sensitivity" / "fig2_21_weight_rank_heatmap.py",
]


def main() -> None:
    for script_path in SCRIPTS:
        print(f"Running {script_path.name} ...")
        subprocess.run([sys.executable, str(script_path)], check=True)
    print("All core Question 2 visualizations have been generated.")


if __name__ == "__main__":
    main()
