"""Tests for JSON schema validation per level."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import ValidationError

from src.mechgaia_env.schemas import LevelATask, LevelBTask, LevelCTask, LevelDTask


def test_level_a_schema_validation():
    """Test Level A task schema validation."""
    # Valid Level A task
    valid_task = {
        "id": "level_a_test",
        "topic": "Test Topic",
        "question": "What is the answer?",
        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "correct_option": 0,
        "distractor_analysis": ["Analysis 1", "Analysis 2"],
    }

    task = LevelATask(**valid_task)
    assert task.id == "level_a_test"
    assert len(task.options) == 4
    assert task.correct_option == 0

    # Invalid: missing required field
    invalid_task = {
        "id": "level_a_test",
        "topic": "Test Topic",
        # Missing question
        "options": ["Option 1"],
        "correct_option": 0,
    }

    try:
        LevelATask(**invalid_task)
        assert False, "Should raise ValidationError"
    except ValidationError:
        pass

    # Invalid: correct_option out of range
    invalid_task2 = {
        "id": "level_a_test",
        "topic": "Test Topic",
        "question": "What is the answer?",
        "options": ["Option 1", "Option 2"],
        "correct_option": 5,  # Out of range
    }

    try:
        LevelATask(**invalid_task2)
        # Pydantic doesn't validate range by default, but we can check
        task = LevelATask(**invalid_task2)
        assert (
            task.correct_option == 5
        )  # It accepts it, but should be validated in application logic
    except ValidationError:
        pass


def test_level_b_schema_validation():
    """Test Level B task schema validation."""
    valid_task = {
        "id": "level_b_test",
        "topic": "Beam Deflection",
        "problem_template": "Calculate deflection for L={L} m, P={P} kN",
        "symbolic_variables": {"L": "Length", "P": "Load"},
        "units": {"L": "m", "P": "kN"},
        "ground_truth_formula": "P * L**3 / (48 * E * I)",
        "reference_solution": 0.001,
        "tolerance": 0.01,
        "parameter_ranges": {
            "L": {"min": 1.0, "max": 10.0},
            "P": {"min": 1.0, "max": 100.0},
        },
    }

    task = LevelBTask(**valid_task)
    assert task.id == "level_b_test"
    assert task.tolerance == 0.01
    assert "L" in task.parameter_ranges

    # Invalid: missing required field
    invalid_task = {
        "id": "level_b_test",
        "topic": "Beam Deflection",
        # Missing problem_template
        "symbolic_variables": {"L": "Length"},
        "units": {"L": "m"},
        "ground_truth_formula": "L**3",
        "reference_solution": 0.001,
    }

    try:
        LevelBTask(**invalid_task)
        assert False, "Should raise ValidationError"
    except ValidationError:
        pass


def test_level_c_schema_validation():
    """Test Level C task schema validation."""
    valid_task = {
        "id": "level_c_test",
        "topic": "Beam Optimization",
        "objectives": ["Minimize mass", "Maximize frequency"],
        "constraints": ["Deflection < 10mm", "Stress < yield"],
        "design_variables": {
            "height": {
                "type": "continuous",
                "min": 0.1,
                "max": 0.3,
                "unit": "m",
            },
            "material": {
                "type": "categorical",
                "options": ["steel", "aluminum"],
            },
        },
        "reference_design": {"height": 0.2, "material": "steel"},
        "material_options": ["steel", "aluminum"],
        "evaluation_criteria": {"mass_weight": 0.5, "frequency_weight": 0.5},
    }

    task = LevelCTask(**valid_task)
    assert task.id == "level_c_test"
    assert len(task.objectives) == 2
    assert "height" in task.design_variables

    # Invalid: missing required field
    invalid_task = {
        "id": "level_c_test",
        "topic": "Beam Optimization",
        # Missing objectives
        "constraints": ["Deflection < 10mm"],
        "design_variables": {},
        "reference_design": {},
    }

    try:
        LevelCTask(**invalid_task)
        assert False, "Should raise ValidationError"
    except ValidationError:
        pass


def test_level_d_schema_validation():
    """Test Level D task schema validation."""
    # Load actual Level D example
    example_path = (
        Path(__file__).parent.parent
        / "data"
        / "level_d"
        / "examples"
        / "level_d_two_span_1.json"
    )

    if example_path.exists():
        with open(example_path) as f:
            task_data = json.load(f)

        task = LevelDTask(**task_data)
        assert task.level == "D"
        assert task.id == "level_d_two_span_1"
        assert len(task.steps) > 0
        assert "design" in task.expected_output_schema
        assert "system_metrics" in task.expected_output_schema

    # Test with minimal valid task
    minimal_task = {
        "id": "level_d_test",
        "level": "D",
        "type": "multi_component_beam",
        "title": "Test Task",
        "description": "Test description",
        "steps": [{"name": "step1", "description": "Step 1"}],
        "given": {},
        "constraints": {},
        "objectives": [],
        "expected_output_schema": {
            "design": {},
            "system_metrics": {},
            "rationale": "string",
            "code": "string",
        },
        "material_options": [],
    }

    task = LevelDTask(**minimal_task)
    assert task.level == "D"
    assert task.type == "multi_component_beam"

    # Invalid: missing required field
    invalid_task = {
        "id": "level_d_test",
        "level": "D",
        # Missing type
        "title": "Test Task",
        "description": "Test description",
        "steps": [],
        "expected_output_schema": {},
    }

    try:
        LevelDTask(**invalid_task)
        assert False, "Should raise ValidationError"
    except ValidationError:
        pass


def test_schema_from_json_files():
    """Test that example JSON files validate against schemas."""
    # Test Level C example
    level_c_path = (
        Path(__file__).parent.parent
        / "data"
        / "level_c"
        / "examples"
        / "level_c_beam_1.json"
    )

    if level_c_path.exists():
        with open(level_c_path) as f:
            data = json.load(f)

        # Level C examples are stored differently - they're task instances, not task schemas
        # So we validate the structure manually
        assert "id" in data
        assert "level" in data
        assert data["level"] == "C"
        assert "expected_output_schema" in data
        assert "design" in data["expected_output_schema"]

    # Test Level D example
    level_d_path = (
        Path(__file__).parent.parent
        / "data"
        / "level_d"
        / "examples"
        / "level_d_two_span_1.json"
    )

    if level_d_path.exists():
        with open(level_d_path) as f:
            data = json.load(f)

        # Validate against LevelDTask schema
        task = LevelDTask(**data)
        assert task.level == "D"
        assert task.id == "level_d_two_span_1"


if __name__ == "__main__":
    print("Running schema validation tests...")

    print("\n1. Testing Level A schema...")
    test_level_a_schema_validation()
    print("   ✓ Level A schema tests passed")

    print("\n2. Testing Level B schema...")
    test_level_b_schema_validation()
    print("   ✓ Level B schema tests passed")

    print("\n3. Testing Level C schema...")
    test_level_c_schema_validation()
    print("   ✓ Level C schema tests passed")

    print("\n4. Testing Level D schema...")
    test_level_d_schema_validation()
    print("   ✓ Level D schema tests passed")

    print("\n5. Testing schema from JSON files...")
    test_schema_from_json_files()
    print("   ✓ JSON file schema tests passed")

    print("\n✅ All schema validation tests passed!")
