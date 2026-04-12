from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[4]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from question_2.sensitivity_analysis.model_parameters.common import (
    run_model_parameter_sensitivity,
)


PARAMETER_NAME = "gamma"
PARAMETER_VALUES = [0.0, 0.25, 0.5, 0.75, 1.0]


def update_base_globals(base, thermal_params: dict, parameter_value: float) -> None:
    base.GAMMA_CONTACT = float(parameter_value)


if __name__ == "__main__":
    run_model_parameter_sensitivity(
        parameter_name=PARAMETER_NAME,
        parameter_values=PARAMETER_VALUES,
        output_dir=Path(__file__).resolve().parent,
        update_base_globals=update_base_globals,
    )
