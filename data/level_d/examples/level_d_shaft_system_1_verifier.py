#!/usr/bin/env python3
"""Golden example verifier for Level D shaft system task.

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
    segment_1 = design.get("segment_1", {})
    segment_2 = design.get("segment_2", {})

    seg1_material_name = segment_1.get("material", "")
    seg1_diameter = segment_1.get("diameter_m", 0.0)
    seg2_material_name = segment_2.get("material", "")
    seg2_diameter = segment_2.get("diameter_m", 0.0)

    # Get material properties
    materials = task_data.get("materials", [])
    seg1_material = next(
        (m for m in materials if m["name"] == seg1_material_name), None
    )
    seg2_material = next(
        (m for m in materials if m["name"] == seg2_material_name), None
    )

    if not seg1_material or not seg2_material:
        results["overall_pass"] = False
        return results

    # Extract geometry
    L1 = geometry.get("segment_1_length_m", 1.2)
    L2 = geometry.get("segment_2_length_m", 0.8)
    gear_loc = geometry.get("gear_location_from_motor_m", 0.8)
    pulley_loc = geometry.get("pulley_location_from_motor_m", 1.6)

    # Extract loads
    T = loads.get("torque_Nm", 2500.0)
    F_gear = loads.get("radial_load_gear_N", 6000.0)
    F_pulley = loads.get("radial_load_pulley_N", 4000.0)

    # Section properties
    J1 = math.pi * seg1_diameter**4 / 32.0
    J2 = math.pi * seg2_diameter**4 / 32.0
    I1 = math.pi * seg1_diameter**4 / 64.0
    I2 = math.pi * seg2_diameter**4 / 64.0
    r1 = seg1_diameter / 2.0
    r2 = seg2_diameter / 2.0

    # Material properties
    G1 = seg1_material["G_Pa"]
    rho1 = seg1_material["rho_kg_per_m3"]
    tau_allow_1 = seg1_material["tau_allow_MPa"] * 1e6
    sigma_allow_1 = seg1_material["sigma_allow_MPa"] * 1e6

    G2 = seg2_material["G_Pa"]
    rho2 = seg2_material["rho_kg_per_m3"]
    tau_allow_2 = seg2_material["tau_allow_MPa"] * 1e6
    sigma_allow_2 = seg2_material["sigma_allow_MPa"] * 1e6

    # Torsional shear
    tau1 = T * r1 / J1
    tau2 = T * r2 / J2
    max_torsional_shear = max(tau1, tau2)
    max_torsional_shear_MPa = max_torsional_shear / 1e6

    # Bending moments
    M_gear = F_gear * gear_loc
    M_pulley = F_pulley * (pulley_loc - gear_loc)

    sigma_gear = M_gear * r1 / I1
    sigma_pulley = M_pulley * r2 / I2
    max_bending_stress = max(sigma_gear, sigma_pulley)
    max_bending_stress_MPa = max_bending_stress / 1e6

    # Twist
    theta1 = T * L1 / (G1 * J1)
    theta2 = T * L2 / (G2 * J2)
    theta_total = theta1 + theta2

    # Mass
    V1 = math.pi * seg1_diameter**2 / 4.0 * L1
    V2 = math.pi * seg2_diameter**2 / 4.0 * L2
    m1 = rho1 * V1
    m2 = rho2 * V2
    m_total = m1 + m2

    # Check constraints
    max_twist_constraint = constraints.get("max_total_twist_rad", 0.01)
    max_mass_constraint = constraints.get("max_total_mass_kg", 120.0)

    # Use the more restrictive allowable stress
    tau_allow_min = min(tau_allow_1, tau_allow_2)
    sigma_allow_min = min(sigma_allow_1, sigma_allow_2)

    results["constraints_satisfied"] = {
        "torsional_shear": max_torsional_shear <= tau_allow_min,
        "bending_stress": max_bending_stress <= sigma_allow_min,
        "twist": theta_total <= max_twist_constraint,
        "mass": m_total <= max_mass_constraint,
    }

    # Compare with response metrics (with tolerance)
    tolerance = 0.15  # 15% tolerance for approximations

    response_torsional_shear = system_metrics.get("max_torsional_shear_MPa", 0.0) * 1e6
    response_bending_stress = system_metrics.get("max_bending_stress_MPa", 0.0) * 1e6
    response_twist = system_metrics.get("total_twist_rad", 0.0)
    response_mass = system_metrics.get("total_mass_kg", 0.0)

    results["metrics_correct"] = {
        "torsional_shear": abs(response_torsional_shear - max_torsional_shear)
        / max(max_torsional_shear, 1e6)
        <= tolerance,
        "bending_stress": abs(response_bending_stress - max_bending_stress)
        / max(max_bending_stress, 1e6)
        <= tolerance,
        "twist": abs(response_twist - theta_total) / max(theta_total, 1e-6)
        <= tolerance,
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
        sum(results["metrics_correct"].values()) >= 3
    )  # At least 3/4 metrics correct

    results["overall_pass"] = (
        all_constraints and most_metrics_correct and results["code_executes"]
    )

    return results


if __name__ == "__main__":
    # Test with golden example
    example_path = "level_d_shaft_system_1.json"
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
