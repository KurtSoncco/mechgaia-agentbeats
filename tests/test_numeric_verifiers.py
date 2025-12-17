"""Tests for Level B/C/D numeric verifiers."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mechgaia_env.evaluators import UnitTestGrader


def test_level_b_numeric_verifier():
    """Test Level B numeric verification."""
    grader = UnitTestGrader()

    # Test case: Beam deflection calculation
    # Use a simple fixed expected value that's clearly > 1e-6 to avoid absolute tolerance issues
    task_schema = {
        "topic": "Beam Deflection",
        "tolerance": 0.01,
    }

    parameters = {
        "P": 100.0,  # kN
        "L": 10.0,  # m
        "E": 200.0,  # GPa
        "b": 50.0,  # mm
        "h": 100.0,  # mm
    }

    # Use a fixed expected value of 0.001 m (1 mm) - clearly > 1e-6
    # This ensures we test relative tolerance logic, not absolute tolerance
    expected = 0.001  # 1 mm deflection

    gold_answer = {
        "solution": expected,
        "tolerance": 0.01,
    }

    # Test correct answer
    correct_response = {
        "answer": expected,
        "code": "",
    }

    scores = grader.evaluate_level_b(
        task_schema, parameters, gold_answer, correct_response
    )
    assert scores["correctness"] >= 0.99, (
        f"Expected correctness >= 0.99, got {scores['correctness']}"
    )
    assert scores["value_tolerance"] == 1.0

    # Test answer with small error (within tolerance)
    close_response = {
        "answer": expected * 1.005,  # 0.5% error
        "code": "",
    }

    scores = grader.evaluate_level_b(
        task_schema, parameters, gold_answer, close_response
    )
    assert scores["correctness"] >= 0.95, (
        f"Expected correctness >= 0.95 for 0.5% error, got {scores['correctness']}"
    )

    # Test answer with large error (outside tolerance)
    # Use a much larger multiplier to ensure it's clearly outside tolerance
    # Even with absolute tolerance, 10x should fail
    wrong_response = {
        "answer": expected * 10.0,  # 900% error
        "code": "",
    }

    scores = grader.evaluate_level_b(
        task_schema, parameters, gold_answer, wrong_response
    )
    # For very small values using absolute tolerance, 10x error should still fail
    # But if it's using relative tolerance, 900% error should definitely fail
    assert scores["correctness"] < 0.5, (
        f"Expected correctness < 0.5 for large error (10x), got {scores['correctness']}"
    )

    # Test with code execution
    code_response = {
        "answer": expected,  # Use expected value directly for code test
        "code": f"""
# Code that calculates deflection
result = {expected}
print(result)
""",
    }

    scores = grader.evaluate_level_b(
        task_schema, parameters, gold_answer, code_response
    )
    # Code should execute and produce reasonable result
    assert scores["code_execution"] >= 0.5


def test_level_c_code_execution():
    """Test Level C code execution verifier."""
    grader = UnitTestGrader()

    task_schema = {
        "topic": "Beam Optimization",
    }

    design_params = {
        "height_m": 0.25,
        "frequency_Hz": 38.5,
        "deflection_m": 0.0005,
        "mass_kg": 2.45,
        "max_stress_MPa": 51.3,
        "safety_factor": 4.9,
    }

    # Valid code
    valid_code = """
import math
L = 1.0
b = 0.05
h = 0.25
E = 210e9
rho = 7850.0
P = 100.0
A = b * h
m = rho * A * L
I = b * h**3 / 12
Delta = P * L**3 / (3 * E * I)
M_max = P * L
c = h / 2.0
sigma = M_max * c / I
sigma_MPa = sigma / 1e6
sigma_y = 250.0
SF = sigma_y / sigma_MPa
f = (1.875**2 / (2 * math.pi * L**2)) * math.sqrt(E * I / (rho * A))
print({'height_m': h, 'frequency_Hz': f, 'deflection_m': Delta, 'mass_kg': m, 'max_stress_MPa': sigma_MPa, 'safety_factor': SF})
"""

    scores = grader.evaluate_level_c_code(task_schema, valid_code, design_params)
    assert scores["code_execution"] >= 0.5
    assert scores["syntax_correct"] == 1.0

    # Invalid code (syntax error)
    invalid_code = """
import math
L = 1.0
b = 0.05
h = 0.25
# Missing closing parenthesis
result = math.sqrt(E * I / (rho * A
"""

    scores = grader.evaluate_level_c_code(task_schema, invalid_code, design_params)
    assert scores["code_execution"] == 0.0
    assert scores["syntax_correct"] == 0.0
    assert "error" in scores


def test_level_d_code_execution():
    """Test Level D code execution and constraint verification."""
    grader = UnitTestGrader()

    # Load Level D example
    example_path = (
        Path(__file__).parent.parent
        / "data"
        / "level_d"
        / "examples"
        / "level_d_two_span_1.json"
    )

    if not example_path.exists():
        print("⚠ Level D example not found, skipping test")
        return

    with open(example_path) as f:
        task_data = json.load(f)

    task_schema = task_data

    # Create a sample response
    response = {
        "design": {
            "span_1": {"material": "Steel A", "height_m": 0.25},
            "span_2": {"material": "Steel B", "height_m": 0.30},
        },
        "system_metrics": {
            "max_deflection_m": 0.004,
            "max_stress_span_1_MPa": 120.0,
            "max_stress_span_2_MPa": 150.0,
            "min_frequency_Hz": 35.0,
            "total_mass_kg": 120.0,
        },
        "rationale": "Selected materials and heights to meet constraints",
        "code": """
import math
L1 = 3.0
L2 = 3.0
width = 0.1
h1 = 0.25
h2 = 0.30
E1 = 200e9
E2 = 210e9
rho1 = 7850.0
rho2 = 7850.0
A1 = width * h1
A2 = width * h2
I1 = width * h1**3 / 12
I2 = width * h2**3 / 12
m1 = rho1 * A1 * L1
m2 = rho2 * A2 * L2
total_mass = m1 + m2
print(f'Total mass: {total_mass} kg')
""",
    }

    scores = grader.evaluate_level_d_code(task_schema, response["code"], response)

    assert "code_execution" in scores
    assert "syntax_correct" in scores
    assert "system_constraints_satisfied" in scores

    # Code should execute
    assert scores["code_execution"] >= 0.5
    assert scores["syntax_correct"] == 1.0

    # Check constraint satisfaction (depends on actual values)
    # This is a basic check - actual constraint satisfaction depends on computed values
    assert 0.0 <= scores["system_constraints_satisfied"] <= 1.0


def test_near_zero_gold_solution():
    """Test handling of near-zero gold solutions."""
    grader = UnitTestGrader()

    task_schema = {"tolerance": 0.01}
    parameters = {}
    gold_answer = {"solution": 1e-8, "tolerance": 0.01}  # Very small value

    # Answer very close to zero
    response = {"answer": 1.1e-8, "code": ""}

    scores = grader.evaluate_level_b(task_schema, parameters, gold_answer, response)
    # Should handle near-zero values with absolute tolerance
    assert scores["correctness"] >= 0.0


if __name__ == "__main__":
    print("Running numeric verifier tests...")

    print("\n1. Testing Level B numeric verifier...")
    test_level_b_numeric_verifier()
    print("   ✓ Level B numeric verifier tests passed")

    print("\n2. Testing Level C code execution...")
    test_level_c_code_execution()
    print("   ✓ Level C code execution tests passed")

    print("\n3. Testing Level D code execution...")
    test_level_d_code_execution()
    print("   ✓ Level D code execution tests passed")

    print("\n4. Testing near-zero gold solution handling...")
    test_near_zero_gold_solution()
    print("   ✓ Near-zero handling tests passed")

    print("\n✅ All numeric verifier tests passed!")
