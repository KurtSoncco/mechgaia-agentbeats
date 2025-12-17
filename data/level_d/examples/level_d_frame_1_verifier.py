#!/usr/bin/env python3
"""Golden example verifier for Level D portal frame task.

This verifier checks that a Level D response meets system-level constraints
and computes metrics correctly.
"""

import json
import math
from typing import Any, Dict


def verify_level_d_response(
    response: Dict[str, Any], task_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Verify a Level D response against the task requirements.

    Args:
        response: Parsed response with design, system_metrics, rationale, code
        task_data: Full task JSON data

    Returns:
        Dictionary with verification results
    """
    results = {
        "constraints_satisfied": {},
        "metrics_correct": {},
        "code_executes": False,
        "overall_pass": False,
    }

    design = response.get("design", {})
    system_metrics = response.get("system_metrics", {})
    code = response.get("code", "")

    # Get task constraints
    constraints = task_data.get("constraints", {})
    given = task_data.get("given", {})
    geometry = given.get("geometry", {})
    loads = given.get("loads", {})

    # Extract design parameters
    columns = design.get("columns", {})
    beam = design.get("beam", {})

    col_material_name = columns.get("material", "")
    col_width = columns.get("width_m", 0.0)
    col_height = columns.get("height_m", 0.0)
    beam_material_name = beam.get("material", "")
    beam_width = beam.get("width_m", 0.0)
    beam_height = beam.get("height_m", 0.0)

    # Get material properties
    material_options = task_data.get("material_options", [])
    col_material = next(
        (m for m in material_options if m["name"] == col_material_name), None
    )
    beam_material = next(
        (m for m in material_options if m["name"] == beam_material_name), None
    )

    if not col_material or not beam_material:
        results["overall_pass"] = False
        return results

    # Extract geometry
    H = geometry.get("story_height_m", 3.0)
    L = geometry.get("span_length_m", 5.0)

    # Extract loads
    F1 = loads.get("lateral_floor_1_kN", 40.0) * 1e3  # Convert to N
    F2 = loads.get("lateral_floor_2_kN", 60.0) * 1e3  # Convert to N
    w_beam = loads.get("beam_gravity_load_kN_per_m", 20.0) * 1e3  # Convert to N/m

    # Compute geometric properties
    A_col = col_width * col_height
    I_col = col_width * col_height**3 / 12.0
    A_beam = beam_width * beam_height
    I_beam = beam_width * beam_height**3 / 12.0

    # Material properties
    E_col = col_material["E_Pa"]
    rho_col = col_material["rho_kg_per_m3"]
    sigma_y_col = col_material["sigma_y_MPa"] * 1e6

    E_beam = beam_material["E_Pa"]
    rho_beam = beam_material["rho_kg_per_m3"]
    sigma_y_beam = beam_material["sigma_y_MPa"] * 1e6

    # Approximate column stiffness per story (two columns)
    k_story = 2.0 * 12.0 * E_col * I_col / H**3

    # Story drifts
    drift_1 = F1 / k_story
    drift_2 = (F1 + F2) / k_story
    max_story_drift = max(drift_1, drift_2)
    max_story_drift_ratio = max_story_drift / H

    # Beam deflection
    beam_deflection = 5.0 * w_beam * L**4 / (384.0 * E_beam * I_beam)

    # Bending stresses
    M_beam_max = w_beam * L**2 / 12.0  # Fixed-fixed approximation
    sigma_beam = M_beam_max * (beam_height / 2.0) / I_beam
    sigma_beam_MPa = sigma_beam / 1e6

    M_col_max = (F1 + F2) * H  # Cantilever approximation
    sigma_col = M_col_max * (col_height / 2.0) / I_col
    sigma_col_MPa = sigma_col / 1e6

    # Mass estimate
    col_length_total = 4.0 * H  # two columns, two stories
    beam_length_total = 2.0 * L  # two beams (one per story)
    m_cols = rho_col * A_col * col_length_total
    m_beams = rho_beam * A_beam * beam_length_total
    m_total = m_cols + m_beams

    # Lateral stiffness and first mode frequency
    k_lat = 2.0 * k_story
    m_eff = 0.8 * m_total
    f1 = (1.0 / (2.0 * math.pi)) * math.sqrt(k_lat / m_eff)

    # Check constraints
    max_story_drift_ratio_constraint = constraints.get("max_story_drift_ratio", 0.01)
    max_beam_deflection_constraint = constraints.get("max_beam_deflection_m", 0.02)
    max_mass_constraint = constraints.get("max_total_mass_kg", 3000.0)
    min_frequency_constraint = constraints.get("min_first_mode_frequency_Hz", 2.0)

    max_stress_constraint_col = sigma_y_col / 1.5
    max_stress_constraint_beam = sigma_y_beam / 1.5

    results["constraints_satisfied"] = {
        "story_drift_ratio": max_story_drift_ratio <= max_story_drift_ratio_constraint,
        "beam_deflection": beam_deflection <= max_beam_deflection_constraint,
        "mass": m_total <= max_mass_constraint,
        "frequency": f1 >= min_frequency_constraint,
        "stress_column": sigma_col_MPa <= (max_stress_constraint_col / 1e6),
        "stress_beam": sigma_beam_MPa <= (max_stress_constraint_beam / 1e6),
    }

    # Compare with response metrics (with tolerance)
    tolerance = 0.15  # 15% tolerance for approximations

    response_drift_1 = system_metrics.get("story_1_drift_m", 0.0)
    response_drift_2 = system_metrics.get("story_2_drift_m", 0.0)
    response_max_drift_ratio = system_metrics.get("max_story_drift_ratio", 0.0)
    response_beam_deflection = system_metrics.get("beam_deflection_m", 0.0)
    response_stress_col = system_metrics.get("max_stress_column_MPa", 0.0)
    response_stress_beam = system_metrics.get("max_stress_beam_MPa", 0.0)
    response_frequency = system_metrics.get("first_mode_frequency_Hz", 0.0)
    response_mass = system_metrics.get("total_mass_kg", 0.0)

    results["metrics_correct"] = {
        "drift_1": abs(response_drift_1 - drift_1) / max(drift_1, 1e-6) <= tolerance,
        "drift_2": abs(response_drift_2 - drift_2) / max(drift_2, 1e-6) <= tolerance,
        "drift_ratio": abs(response_max_drift_ratio - max_story_drift_ratio)
        / max(max_story_drift_ratio, 1e-6)
        <= tolerance,
        "beam_deflection": abs(response_beam_deflection - beam_deflection)
        / max(beam_deflection, 1e-6)
        <= tolerance,
        "stress_column": abs(response_stress_col - sigma_col_MPa)
        / max(sigma_col_MPa, 1.0)
        <= tolerance,
        "stress_beam": abs(response_stress_beam - sigma_beam_MPa)
        / max(sigma_beam_MPa, 1.0)
        <= tolerance,
        "frequency": abs(response_frequency - f1) / max(f1, 1.0) <= tolerance,
        "mass": abs(response_mass - m_total) / max(m_total, 1.0) <= tolerance,
    }

    # Try to execute code (basic check)
    try:
        # Create a safe execution context
        exec_globals = {
            "__builtins__": {
                "__import__": __import__,
                "print": print,
                "math": math,
                "max": max,
                "min": min,
            },
            "math": math,
            "max": max,
            "min": min,
        }
        exec(code, exec_globals)
        results["code_executes"] = True
    except Exception as e:
        results["code_executes"] = False
        results["code_error"] = str(e)

    # Overall pass if all constraints satisfied and metrics reasonably correct
    all_constraints = all(results["constraints_satisfied"].values())
    most_metrics_correct = (
        sum(results["metrics_correct"].values()) >= 6
    )  # At least 6/8 metrics correct

    results["overall_pass"] = (
        all_constraints and most_metrics_correct and results["code_executes"]
    )

    return results


if __name__ == "__main__":
    # Test with golden example
    example_path = "level_d_frame_1.json"
    with open(example_path) as f:
        task_data = json.load(f)

    # Use reference answer as test response
    reference = task_data.get("reference_answer", {})
    if reference:
        results = verify_level_d_response(reference, task_data)
        print("Verification Results:")
        print(json.dumps(results, indent=2))
    else:
        print("No reference answer found in task data")
