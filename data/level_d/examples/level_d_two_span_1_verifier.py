#!/usr/bin/env python3
"""Golden example verifier for Level D two-span beam task.

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
    span_1 = design.get("span_1", {})
    span_2 = design.get("span_2", {})

    span_1_material_name = span_1.get("material", "")
    span_1_height = span_1.get("height_m", 0.0)
    span_2_material_name = span_2.get("material", "")
    span_2_height = span_2.get("height_m", 0.0)

    # Get material properties
    material_options = task_data.get("material_options", [])
    span_1_material = next(
        (m for m in material_options if m["name"] == span_1_material_name), None
    )
    span_2_material = next(
        (m for m in material_options if m["name"] == span_2_material_name), None
    )

    if not span_1_material or not span_2_material:
        results["overall_pass"] = False
        return results

    # Extract geometry
    L1 = geometry.get("span_1_length_m", 3.0)
    L2 = geometry.get("span_2_length_m", 3.0)
    width = geometry.get("width_m", 0.1)

    # Extract loads
    w1 = loads.get("span_1_uniform_load_N_per_m", 5000.0)
    P2 = loads.get("span_2_point_load_N", 10000.0)
    a2 = loads.get("point_load_location_m", 1.5)
    b2 = L2 - a2

    # Compute geometric properties
    A1 = width * span_1_height
    I1 = width * span_1_height**3 / 12
    A2 = width * span_2_height
    I2 = width * span_2_height**3 / 12

    # Material properties
    E1 = span_1_material["E_Pa"]
    rho1 = span_1_material["rho_kg_per_m3"]
    sigma_y1 = span_1_material["sigma_y_MPa"] * 1e6

    E2 = span_2_material["E_Pa"]
    rho2 = span_2_material["rho_kg_per_m3"]
    sigma_y2 = span_2_material["sigma_y_MPa"] * 1e6

    # Compute total mass
    m1 = rho1 * A1 * L1
    m2 = rho2 * A2 * L2
    total_mass = m1 + m2

    # Approximate deflections (simplified - using superposition)
    # Span 1: uniform load, simply supported approximation
    delta_1_mid = 5 * w1 * L1**4 / (384 * E1 * I1)

    # Span 2: point load, simply supported approximation
    delta_2_mid = P2 * a2 * b2 * (L2**2 - a2**2 - b2**2) / (6 * E2 * I2 * L2)

    # Mid-support deflection (continuity condition approximation)
    # Simplified: assume equal deflections from both spans
    delta_mid_support = max(delta_1_mid, delta_2_mid) * 0.5  # Rough approximation

    max_deflection = max(delta_1_mid, delta_2_mid, delta_mid_support)

    # Compute maximum bending stresses
    M1_max = w1 * L1**2 / 8  # Approximate for uniform load
    sigma_1_max = M1_max * (span_1_height / 2) / I1

    M2_max = P2 * a2 * b2 / L2  # Point load
    sigma_2_max = M2_max * (span_2_height / 2) / I2

    # Approximate natural frequency (simplified)
    # Use equivalent single-degree-of-freedom approximation
    k1_equiv = 3 * E1 * I1 / L1**3
    k2_equiv = 3 * E2 * I2 / L2**3
    k_eq = 1 / (1 / k1_equiv + 1 / k2_equiv)  # Series springs

    m_eff = (m1 + m2) / 2  # Effective mass
    f_natural = (1 / (2 * math.pi)) * math.sqrt(k_eq / m_eff)

    # Check constraints
    max_deflection_constraint = constraints.get("max_deflection_at_nodes_m", 0.005)
    max_mass_constraint = constraints.get("max_total_mass_kg", 150.0)
    min_frequency_constraint = constraints.get("min_natural_frequency_Hz", 30.0)

    max_stress_constraint_1 = sigma_y1 / 1.5
    max_stress_constraint_2 = sigma_y2 / 1.5

    results["constraints_satisfied"] = {
        "deflection": max_deflection <= max_deflection_constraint,
        "mass": total_mass <= max_mass_constraint,
        "frequency": f_natural >= min_frequency_constraint,
        "stress_span_1": sigma_1_max <= max_stress_constraint_1,
        "stress_span_2": sigma_2_max <= max_stress_constraint_2,
    }

    # Compare with response metrics (with tolerance)
    tolerance = 0.1  # 10% tolerance for approximations

    response_max_deflection = system_metrics.get("max_deflection_m", 0.0)
    response_max_stress_1 = system_metrics.get("max_stress_span_1_MPa", 0.0) * 1e6
    response_max_stress_2 = system_metrics.get("max_stress_span_2_MPa", 0.0) * 1e6
    response_frequency = system_metrics.get("min_frequency_Hz", 0.0)
    response_mass = system_metrics.get("total_mass_kg", 0.0)

    results["metrics_correct"] = {
        "deflection": abs(response_max_deflection - max_deflection)
        / max(max_deflection, 1e-6)
        <= tolerance,
        "stress_span_1": abs(response_max_stress_1 - sigma_1_max)
        / max(sigma_1_max, 1e6)
        <= tolerance,
        "stress_span_2": abs(response_max_stress_2 - sigma_2_max)
        / max(sigma_2_max, 1e6)
        <= tolerance,
        "frequency": abs(response_frequency - f_natural) / max(f_natural, 1.0)
        <= tolerance,
        "mass": abs(response_mass - total_mass) / max(total_mass, 1.0) <= tolerance,
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
        sum(results["metrics_correct"].values()) >= 3
    )  # At least 3/5 metrics correct

    results["overall_pass"] = (
        all_constraints and most_metrics_correct and results["code_executes"]
    )

    return results


if __name__ == "__main__":
    # Test with golden example
    example_path = "level_d_two_span_1.json"
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
