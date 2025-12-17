#!/usr/bin/env python3
"""Golden example verifier for Level D cost-optimal beam task.

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
    material_name = design.get("material", "")
    width = design.get("width_m", 0.0)
    height = design.get("height_m", 0.0)

    # Get material properties
    materials = task_data.get("materials", [])
    material = next((m for m in materials if m["name"] == material_name), None)

    if not material:
        results["overall_pass"] = False
        return results

    # Extract geometry
    L = geometry.get("span_length_m", 4.0)

    # Extract loads
    w_kN_per_m = loads.get("uniform_load_kN_per_m", 15.0)
    w = w_kN_per_m * 1e3  # Convert to N/m

    # Compute geometric properties
    A = width * height
    I = width * height**3 / 12.0

    # Material properties
    E = material["E_Pa"]
    rho = material["rho_kg_per_m3"]
    sigma_y = material["sigma_y_MPa"] * 1e6
    cost_per_kg = material["cost_per_kg"]

    # Deflection
    delta_max = 5.0 * w * L**4 / (384.0 * E * I)

    # Bending stress
    M_max = w * L**2 / 8.0
    c = height / 2.0
    sigma = M_max * c / I
    sigma_MPa = sigma / 1e6

    # Mass and cost
    m = rho * A * L
    cost = m * cost_per_kg

    # Frequency
    k_eq = 48.0 * E * I / L**3
    m_eff = 0.5 * m
    f = (1.0 / (2.0 * math.pi)) * math.sqrt(k_eq / m_eff)

    # Check constraints
    max_deflection_constraint = constraints.get("max_deflection_m", 0.015)
    max_mass_constraint = constraints.get("max_total_cost_USD", 600.0)
    min_frequency_constraint = constraints.get("min_natural_frequency_Hz", 8.0)

    max_stress_constraint = sigma_y / 1.5

    results["constraints_satisfied"] = {
        "deflection": delta_max <= max_deflection_constraint,
        "mass": cost <= max_mass_constraint,
        "frequency": f >= min_frequency_constraint,
        "stress": sigma_MPa <= (max_stress_constraint / 1e6),
    }

    # Compare with response metrics (with tolerance)
    tolerance = 0.15  # 15% tolerance for approximations

    response_deflection = system_metrics.get("max_deflection_m", 0.0)
    response_stress = system_metrics.get("max_bending_stress_MPa", 0.0)
    response_frequency = system_metrics.get("natural_frequency_Hz", 0.0)
    response_mass = system_metrics.get("mass_kg", 0.0)
    response_cost = system_metrics.get("total_cost_USD", 0.0)

    results["metrics_correct"] = {
        "deflection": abs(response_deflection - delta_max) / max(delta_max, 1e-6)
        <= tolerance,
        "stress": abs(response_stress - sigma_MPa) / max(sigma_MPa, 1.0) <= tolerance,
        "frequency": abs(response_frequency - f) / max(f, 1.0) <= tolerance,
        "mass": abs(response_mass - m) / max(m, 1.0) <= tolerance,
        "cost": abs(response_cost - cost) / max(cost, 1.0) <= tolerance,
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
        sum(results["metrics_correct"].values()) >= 4
    )  # At least 4/5 metrics correct

    results["overall_pass"] = (
        all_constraints and most_metrics_correct and results["code_executes"]
    )

    return results


if __name__ == "__main__":
    # Test with golden example
    example_path = "level_d_cost_beam_1.json"
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
