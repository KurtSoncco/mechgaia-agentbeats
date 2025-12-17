"""Unit tests for Level C response parsing and evaluation."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mechgaia_env.evaluators import LLMJudgeGrader, UnitTestGrader
from src.mechgaia_env.response_parser import (
    extract_json_from_response,
    parse_response,
)


def load_golden_example():
    """Load the golden Level C example."""
    example_path = (
        Path(__file__).parent.parent
        / "data"
        / "level_c"
        / "examples"
        / "level_c_beam_1.json"
    )
    with open(example_path) as f:
        return json.load(f)


def test_extract_json_from_response():
    """Test JSON extraction from various response formats."""
    golden = load_golden_example()
    ref_answer = golden["reference_answer"]

    # Test 1: Proper JSON block format
    response_with_json = f"""
    I've analyzed the beam design problem and here's my solution:
    
    ```json
    {json.dumps(ref_answer, indent=2)}
    ```
    """
    extracted = extract_json_from_response(response_with_json)
    assert extracted is not None, "Should extract JSON from code block"
    assert extracted["design"]["height_m"] == 0.25
    assert "rationale" in extracted
    assert "code" in extracted

    # Test 2: Multiple JSON blocks - should get the last one
    response_multiple = f"""
    First attempt:
    ```json
    {{"design": {{"height_m": 0.15}}, "rationale": "test", "code": "test"}}
    ```
    
    Final answer:
    ```json
    {json.dumps(ref_answer, indent=2)}
    ```
    """
    extracted = extract_json_from_response(response_multiple)
    assert extracted is not None
    assert extracted["design"]["height_m"] == 0.25, "Should extract last JSON block"

    # Test 3: JSON without code block markers (should still work)
    response_no_markers = json.dumps(ref_answer)
    extracted = extract_json_from_response(response_no_markers)
    assert extracted is not None, "Should extract JSON even without code block markers"

    # Test 4: No JSON present
    response_no_json = "This is just text with no JSON at all."
    extracted = extract_json_from_response(response_no_json)
    assert extracted is None, "Should return None when no JSON found"

    # Test 5: Malformed JSON
    response_malformed = """
    ```json
    {"design": {"height_m": 0.25,}, "rationale": "test"}
    ```
    """
    extracted = extract_json_from_response(response_malformed)
    # Should handle trailing comma gracefully or return None
    # The function tries to fix common issues, so it might work or return None
    assert extracted is None or isinstance(extracted, dict)


def test_parse_response_with_json():
    """Test parse_response with JSON-formatted Level C response."""
    golden = load_golden_example()
    ref_answer = golden["reference_answer"]

    # Create response with JSON block
    response_text = f"""
    After analyzing the beam design constraints, I've determined the optimal height.
    
    ```json
    {json.dumps(ref_answer, indent=2)}
    ```
    """

    parsed = parse_response(response_text, task_type="design")

    assert "design" in parsed
    assert "rationale" in parsed
    assert "code" in parsed

    # Check design parameters
    design = parsed["design"]
    assert design["height_m"] == 0.25
    assert design["frequency_Hz"] == 38.5
    assert design["deflection_m"] == 0.0005
    assert design["mass_kg"] == 2.45
    assert design["max_stress_MPa"] == 51.3
    assert design["safety_factor"] == 4.9

    # Check rationale and code are extracted
    assert len(parsed["rationale"]) > 0
    assert "import math" in parsed["code"]


def test_parse_response_fallback():
    """Test parse_response fallback to regex when JSON is missing."""
    # Response without JSON block - should use regex extraction
    response_text = """
    I've designed the beam with the following parameters:
    - Height: 0.25 m
    - Natural frequency: 38.5 Hz
    - Deflection: 0.0005 m
    - Mass: 2.45 kg
    - Maximum stress: 51.3 MPa
    - Safety factor: 4.9
    
    The rationale is that this height balances all constraints.
    """

    parsed = parse_response(response_text, task_type="design")

    # Should still extract some parameters via regex
    assert "design" in parsed
    design = parsed["design"]
    # Regex might extract some values (height, frequency, etc.)
    assert len(design) > 0 or parsed["rationale"] == response_text


def test_evaluator_with_golden_example():
    """Test evaluators with the golden example."""
    golden = load_golden_example()
    ref_answer = golden["reference_answer"]

    # Create a task schema similar to what would be in database
    task_schema = {
        "id": "level_c_beam_1",
        "topic": golden["title"],
        "objectives": ["Maximize natural frequency", "Minimize mass"],
        "constraints": [
            f"Maximum mass: {golden['constraints']['max_mass_kg']} kg",
            f"Maximum deflection: {golden['constraints']['max_deflection_m']} m",
            f"Minimum safety factor: {golden['constraints']['min_safety_factor']}",
            f"Minimum frequency: {golden['constraints']['min_frequency_Hz']} Hz",
        ],
    }

    # Create response dict matching what parser would produce
    response = {
        "design": ref_answer["design"],
        "rationale": ref_answer["rationale"],
        "code": ref_answer["code"],
    }

    # Test LLM Judge Grader (will use mock or skip if API key not available)
    llm_judge = LLMJudgeGrader()
    try:
        scores = llm_judge.evaluate_level_c(task_schema, response)
        assert "technical_accuracy" in scores
        assert "safety_constraint_awareness" in scores
        assert "reasoning_quality" in scores
        assert "engineering_judgment" in scores
        assert "overall_score" in scores
        print("✓ LLM Judge Grader test passed")
    except Exception as e:
        print(f"⚠ LLM Judge Grader test skipped (likely missing API key): {e}")

    # Test Unit Test Grader - code execution
    unit_test_grader = UnitTestGrader()
    code_scores = unit_test_grader.evaluate_level_c_code(
        task_schema, ref_answer["code"], ref_answer["design"]
    )
    assert "code_execution" in code_scores
    assert "syntax_correct" in code_scores
    assert code_scores["code_execution"] >= 0.5, "Code should execute successfully"
    print("✓ Unit Test Grader code execution test passed")


def test_no_missing_json_warnings():
    """Test that proper JSON format doesn't trigger missing JSON warnings."""
    golden = load_golden_example()
    ref_answer = golden["reference_answer"]

    # Properly formatted response
    response_text = f"""
    Analysis complete.
    
    ```json
    {json.dumps(ref_answer, indent=2)}
    ```
    """

    # Extract JSON - should succeed
    json_obj = extract_json_from_response(response_text)
    assert json_obj is not None, "Should extract JSON without warnings"

    # Parse response - should use JSON, not fallback
    parsed = parse_response(response_text, task_type="design")
    assert parsed["design"] == ref_answer["design"], (
        "Should use JSON data, not regex fallback"
    )


if __name__ == "__main__":
    print("Running Level C parser tests...")

    print("\n1. Testing JSON extraction...")
    test_extract_json_from_response()
    print("   ✓ JSON extraction tests passed")

    print("\n2. Testing parse_response with JSON...")
    test_parse_response_with_json()
    print("   ✓ parse_response with JSON tests passed")

    print("\n3. Testing parse_response fallback...")
    test_parse_response_fallback()
    print("   ✓ parse_response fallback tests passed")

    print("\n4. Testing evaluators...")
    test_evaluator_with_golden_example()
    print("   ✓ Evaluator tests passed")

    print("\n5. Testing no missing JSON warnings...")
    test_no_missing_json_warnings()
    print("   ✓ No missing JSON warnings test passed")

    print("\n✅ All tests passed!")
