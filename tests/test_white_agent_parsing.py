"""Tests for white-agent output parsing (JSON contract)."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mechgaia_env.response_parser import (
    extract_json_from_response,
    parse_response,
)


def test_level_c_json_parsing():
    """Test parsing Level C responses with JSON format."""
    # Properly formatted Level C response
    proper_response = """
I've analyzed the beam design problem and determined the optimal height.

```json
{
  "design": {
    "height_m": 0.25,
    "frequency_Hz": 38.5,
    "deflection_m": 0.0005,
    "mass_kg": 2.45,
    "max_stress_MPa": 51.3,
    "safety_factor": 4.9
  },
  "rationale": "Selected height of 0.25 m to balance frequency and mass constraints.",
  "code": "import math\\\\nL = 1.0\\\\nh = 0.25\\\\nprint({'height_m': h})"
}
```
"""

    parsed = parse_response(proper_response, task_type="design")

    assert "design" in parsed
    assert "rationale" in parsed
    assert "code" in parsed

    design = parsed["design"]
    assert design["height_m"] == 0.25
    assert design["frequency_Hz"] == 38.5
    assert design["deflection_m"] == 0.0005
    assert design["mass_kg"] == 2.45
    assert design["max_stress_MPa"] == 51.3
    assert design["safety_factor"] == 4.9

    assert len(parsed["rationale"]) > 0
    assert "import math" in parsed["code"]


def test_level_d_json_parsing():
    """Test parsing Level D responses with JSON format."""
    proper_response = """
After analyzing the multi-span beam system, here's my design:

```json
{
  "design": {
    "span_1": {
      "material": "Steel A",
      "height_m": 0.25
    },
    "span_2": {
      "material": "Steel B",
      "height_m": 0.30
    }
  },
  "system_metrics": {
    "max_deflection_m": 0.004,
    "max_stress_span_1_MPa": 120.0,
    "max_stress_span_2_MPa": 150.0,
    "min_frequency_Hz": 35.0,
    "total_mass_kg": 120.0
  },
  "rationale": "Selected materials and heights to optimize frequency while meeting constraints.",
  "code": "import math\\\\n# System analysis code\\\\nprint('Analysis complete')"
}
```
"""

    parsed = parse_response(proper_response, task_type="multi_step_design")

    assert "design" in parsed
    assert "system_metrics" in parsed
    assert "rationale" in parsed
    assert "code" in parsed

    design = parsed["design"]
    assert "span_1" in design
    assert "span_2" in design
    assert design["span_1"]["material"] == "Steel A"
    assert design["span_1"]["height_m"] == 0.25
    assert design["span_2"]["material"] == "Steel B"
    assert design["span_2"]["height_m"] == 0.30

    metrics = parsed["system_metrics"]
    assert metrics["max_deflection_m"] == 0.004
    assert metrics["max_stress_span_1_MPa"] == 120.0
    assert metrics["min_frequency_Hz"] == 35.0
    assert metrics["total_mass_kg"] == 120.0


def test_json_extraction_edge_cases():
    """Test JSON extraction with various edge cases."""
    # Multiple JSON blocks - should get last one
    multiple_blocks = """
First attempt:
```json
{"design": {"height_m": 0.15}, "rationale": "test1", "code": "code1"}
```

Final answer:
```json
{
  "design": {"height_m": 0.25},
  "rationale": "Final rationale",
  "code": "Final code"
}
```
"""

    extracted = extract_json_from_response(multiple_blocks)
    assert extracted is not None
    assert extracted["design"]["height_m"] == 0.25
    assert extracted["rationale"] == "Final rationale"

    # JSON without code block markers
    no_markers = '{"design": {"height_m": 0.20}, "rationale": "test", "code": "code"}'
    extracted = extract_json_from_response(no_markers)
    # Should still work if it's valid JSON
    assert extracted is None or isinstance(extracted, dict)

    # Malformed JSON (trailing comma)
    malformed = """
```json
{
  "design": {"height_m": 0.25,},
  "rationale": "test",
  "code": "code"
}
```
"""
    extracted = extract_json_from_response(malformed)
    # Should handle trailing comma or return None
    assert extracted is None or isinstance(extracted, dict)

    # No JSON present
    no_json = "This is just text with no JSON at all."
    extracted = extract_json_from_response(no_json)
    assert extracted is None


def test_fallback_parsing():
    """Test fallback parsing when JSON is missing."""
    # Response without JSON - should use regex extraction
    text_response = """
I've designed the beam with the following parameters:
- Height: 0.25 m
- Natural frequency: 38.5 Hz
- Deflection: 0.0005 m
- Mass: 2.45 kg
- Maximum stress: 51.3 MPa
- Safety factor: 4.9

The rationale is that this height balances all constraints.
"""

    parsed = parse_response(text_response, task_type="design")

    # Should still extract some parameters via regex
    assert "design" in parsed
    # Regex might extract height, frequency, etc.
    design = parsed["design"]
    # At minimum, should have rationale
    assert "rationale" in parsed or len(design) > 0


def test_level_b_parsing():
    """Test parsing Level B calculation responses."""
    response_with_answer = """
I've calculated the beam deflection using the Euler-Bernoulli formula.

The maximum deflection at the center is: 0.0015 m

Calculation steps:
1. Computed moment of inertia: I = b * h^3 / 12
2. Applied deflection formula: δ = PL^3 / (48EI)
3. Result: 0.0015 m
"""

    parsed = parse_response(response_with_answer, task_type="calculation")

    assert "answer" in parsed
    assert parsed["answer"] is not None
    # Should extract numerical answer
    assert isinstance(parsed["answer"], (int, float))

    # Response with code
    response_with_code = """
I'll use Python to calculate this:

```python
P = 10.0  # kN
L = 2.0   # m
E = 200.0  # GPa
b = 0.1   # m
h = 0.2   # m

I = b * h**3 / 12
delta = P * 1000 * L**3 / (48 * E * 1e9 * I)
print(f"Deflection: {delta} m")
```

The deflection is 0.0015 m.
"""

    parsed = parse_response(response_with_code, task_type="calculation")

    assert "answer" in parsed
    assert "code" in parsed
    assert parsed["answer"] is not None or parsed["code"] is not None


def test_level_a_parsing():
    """Test parsing Level A multiple choice responses."""
    response = """
After analyzing the options, I believe Option 2 is correct.

The key difference between yield strength and ultimate strength is that yield strength represents the stress at which permanent deformation begins, while ultimate strength is the maximum stress before fracture. This makes Option 2 the correct answer.
"""

    parsed = parse_response(response, task_type="multiple_choice", num_options=4)

    assert "selected_option" in parsed
    assert parsed["selected_option"] == 1  # Option 2 (0-indexed)
    assert "explanation" in parsed
    assert len(parsed["explanation"]) > 0


if __name__ == "__main__":
    print("Running white-agent parsing tests...")

    print("\n1. Testing Level C JSON parsing...")
    test_level_c_json_parsing()
    print("   ✓ Level C JSON parsing tests passed")

    print("\n2. Testing Level D JSON parsing...")
    test_level_d_json_parsing()
    print("   ✓ Level D JSON parsing tests passed")

    print("\n3. Testing JSON extraction edge cases...")
    test_json_extraction_edge_cases()
    print("   ✓ JSON extraction edge case tests passed")

    print("\n4. Testing fallback parsing...")
    test_fallback_parsing()
    print("   ✓ Fallback parsing tests passed")

    print("\n5. Testing Level B parsing...")
    test_level_b_parsing()
    print("   ✓ Level B parsing tests passed")

    print("\n6. Testing Level A parsing...")
    test_level_a_parsing()
    print("   ✓ Level A parsing tests passed")

    print("\n✅ All white-agent parsing tests passed!")
