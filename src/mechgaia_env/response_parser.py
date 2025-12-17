"""Response parsing utilities for extracting answers from agent responses."""

import json
import re
from typing import Any, Dict, Optional


def extract_selected_option(response_text: str, num_options: int = 4) -> Optional[int]:
    """Extract selected option number from response text.

    Args:
        response_text: The response text from the agent
        num_options: Number of options available (default 4)

    Returns:
        Selected option index (0-indexed) or None if not found
    """
    response_lower = response_text.lower()

    # Pattern 1: "option 1", "option 2", etc.
    option_pattern = r"option\s*(\d+)"
    matches = re.findall(option_pattern, response_lower)
    if matches:
        option_num = int(matches[-1])  # Take last mention
        if 1 <= option_num <= num_options:
            return option_num - 1  # Convert to 0-indexed

    # Pattern 2: "1.", "2.", etc. at start of line or after "option"
    numbered_pattern = r"(?:^|\s|option\s*)(\d+)[\.\)]"
    matches = re.findall(numbered_pattern, response_text)
    if matches:
        # Check if any match is a valid option number
        for match in matches:
            option_num = int(match)
            if 1 <= option_num <= num_options:
                # Verify it's actually referring to an option
                # Look for context like "correct option", "answer is", etc.
                idx = response_text.lower().find(match)
                context = response_text[
                    max(0, idx - 20) : min(len(response_text), idx + 20)
                ].lower()
                if any(
                    word in context
                    for word in ["option", "answer", "correct", "choice", "select"]
                ):
                    return option_num - 1

    # Pattern 3: "The correct answer is 1" or "Answer: 2"
    answer_pattern = r"(?:correct\s+)?(?:answer|option|choice)\s+is\s*:?\s*(\d+)"
    matches = re.findall(answer_pattern, response_lower)
    if matches:
        option_num = int(matches[-1])
        if 1 <= option_num <= num_options:
            return option_num - 1

    # Pattern 4: Look for explicit statement like "1 is correct" or "option 1 is the right answer"
    explicit_pattern = r"(\d+)\s+is\s+(?:the\s+)?(?:correct|right|answer)"
    matches = re.findall(explicit_pattern, response_lower)
    if matches:
        option_num = int(matches[-1])
        if 1 <= option_num <= num_options:
            return option_num - 1

    return None


def extract_numerical_answer(response_text: str) -> Optional[float]:
    """Extract numerical answer from response text.

    Args:
        response_text: The response text from the agent

    Returns:
        Numerical value or None if not found
    """
    # Enhanced patterns to catch more answer formats
    patterns = [
        # Explicit answer statements: "answer is 123.45", "the answer is 123.45"
        r"(?:the\s+)?(?:answer|result|solution|value|final\s+answer|final\s+result)\s*(?:is|:|=)\s*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)",
        # Standalone equals: "= 123.45"
        r"=\s*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)",
        # With units: "123.45 Pa", "123.45 MPa"
        r"([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)\s*(?:pa|mpa|n|kn|m|mm|kg|g|nm|knm)",
        # In parentheses: "(123.45)" or "answer (123.45)"
        r"(?:answer|result|solution)\s*\(([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)\)",
        # After colon: "Answer: 123.45" or "Result: 123.45"
        r"(?:answer|result|solution|value)\s*:\s*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)",
        # Standalone number at end of sentence: "The stress is 123.45."
        r"is\s+([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)\s*[\.\s]",
        # In code execution results: look for print statements or return values
        r"(?:print|result|return|output)\s*[=:]\s*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)",
        # Scientific notation: "1.23e-4" or "1.23E-4"
        r"([-+]?\d+\.?\d*[eE][-+]?\d+)",
    ]

    # Try patterns in order of specificity
    for pattern in patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        if matches:
            try:
                # Take the last match (most likely to be the final answer)
                value = float(matches[-1])
                return value
            except ValueError:
                continue

    # Fallback: Look for any floating point number that might be an answer
    # This is less reliable but can catch cases where format is unusual
    # Look for numbers that appear after keywords like "answer", "result", etc.
    fallback_pattern = r"(?:answer|result|solution|value|final)[\s\S]{0,100}?([-+]?\d+\.\d+(?:[eE][-+]?\d+)?)"
    fallback_matches = re.findall(fallback_pattern, response_text, re.IGNORECASE)
    if fallback_matches:
        try:
            # Filter out very small numbers that might be errors or intermediate values
            value = float(fallback_matches[-1])
            if abs(value) > 1e-10:  # Ignore very small numbers that might be errors
                return value
        except ValueError:
            pass

    return None


def extract_code_snippet(response_text: str) -> Optional[str]:
    """Extract Python code snippet from response.

    Args:
        response_text: The response text from the agent

    Returns:
        Code snippet or None if not found
    """
    # Look for code blocks
    code_block_pattern = r"```(?:python)?\s*\n(.*?)```"
    matches = re.findall(code_block_pattern, response_text, re.DOTALL)
    if matches:
        return matches[-1].strip()

    # Look for inline code
    inline_code_pattern = r"`([^`]+)`"
    matches = re.findall(inline_code_pattern, response_text)
    if matches:
        # Check if it looks like Python code
        for match in matches:
            if any(
                keyword in match
                for keyword in ["import", "def", "=", "print", "return"]
            ):
                return match.strip()

    return None


def extract_json_from_response(response_text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON object from response text, looking for the last ```json code block.

    Args:
        response_text: The response text from the agent

    Returns:
        Parsed JSON dictionary or None if not found
    """
    # Look for JSON code blocks - find the LAST one (most likely to be the final output)
    json_block_pattern = r"```json\s*\n(.*?)```"
    matches = re.findall(json_block_pattern, response_text, re.DOTALL)

    if matches:
        # Use the last match (most likely to be the final output)
        json_str = matches[-1].strip()
        try:
            json_obj = json.loads(json_str)
            return json_obj
        except json.JSONDecodeError:
            # Try to handle common issues like trailing commas or comments
            # Remove trailing commas before closing braces/brackets
            json_str = re.sub(r",\s*}", "}", json_str)
            json_str = re.sub(r",\s*]", "]", json_str)
            try:
                json_obj = json.loads(json_str)
                return json_obj
            except json.JSONDecodeError:
                return None

    # Also try to find JSON objects not in code blocks (less common but possible)
    # Look for JSON-like structures: { ... } that might contain "design", "rationale", "code"
    json_like_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
    potential_json_matches = re.findall(json_like_pattern, response_text, re.DOTALL)

    for match in reversed(potential_json_matches):  # Try last first
        try:
            json_obj = json.loads(match)
            # Check if it looks like a Level C response (has design, rationale, or code keys)
            if isinstance(json_obj, dict) and any(
                key in json_obj for key in ["design", "rationale", "code"]
            ):
                return json_obj
        except json.JSONDecodeError:
            continue

    return None


def extract_design_parameters(response_text: str) -> Dict[str, Any]:
    """Extract design parameters from response text.

    Looks for patterns like "width = 0.1 m", "height = 0.3 m", etc.

    Args:
        response_text: The response text from the agent

    Returns:
        Dictionary with design parameters
    """
    design = {}

    # Pattern 1: "parameter = value unit" or "parameter = value"
    # Examples: "width = 0.1 m", "height = 0.3 m", "length = 1.5 m"
    param_pattern = (
        r"(\w+)\s*=\s*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)\s*(?:m|mm|cm|kg|g|pa|mpa|hz)?"
    )
    matches = re.findall(param_pattern, response_text, re.IGNORECASE)

    for param_name, param_value in matches:
        try:
            value = float(param_value)
            design[param_name.lower()] = value
        except ValueError:
            pass

    # Pattern 2: "parameter of value unit" or "parameter is value unit"
    # Examples: "height of 0.25 m", "length of 1.5 m", "width is 0.1 m"
    param_of_pattern = r"(\w+)\s+(?:of|is)\s+([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)\s*(?:m|mm|cm|kg|g|pa|mpa|hz)?"
    matches = re.findall(param_of_pattern, response_text, re.IGNORECASE)

    for param_name, param_value in matches:
        try:
            value = float(param_value)
            param_key = param_name.lower()
            # Only add if not already found
            if param_key not in design:
                design[param_key] = value
        except ValueError:
            pass

    # Pattern 3: "parameter: value" format
    param_colon_pattern = r"(\w+)\s*:\s*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)"
    matches = re.findall(param_colon_pattern, response_text, re.IGNORECASE)

    for param_name, param_value in matches:
        try:
            value = float(param_value)
            param_key = param_name.lower()
            # Only add if not already found
            if param_key not in design:
                design[param_key] = value
        except ValueError:
            pass

    # Pattern 4: Look for common design parameters in natural language
    # "natural frequency of X Hz" -> frequency: X
    freq_pattern = r"(?:natural\s+)?frequency\s+(?:of|is|:)?\s*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)\s*hz"
    freq_matches = re.findall(freq_pattern, response_text, re.IGNORECASE)
    if freq_matches:
        try:
            design["frequency"] = float(freq_matches[-1])
            design["natural_frequency"] = float(freq_matches[-1])
        except ValueError:
            pass

    return design


def extract_answer_from_code_result(
    code_text: str, response_text: str
) -> Optional[float]:
    """Extract numerical answer from code execution results.

    Looks for patterns like print statements, return values, or variable assignments
    that might contain the final answer.

    Args:
        code_text: The code snippet
        response_text: The full response text (may contain execution results)

    Returns:
        Numerical value or None if not found
    """
    # Look for print statements in code
    print_pattern = r"print\s*\([^)]*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)"
    matches = re.findall(print_pattern, code_text)
    if matches:
        try:
            return float(matches[-1])
        except ValueError:
            pass

    # Look for return statements
    return_pattern = r"return\s+([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)"
    matches = re.findall(return_pattern, code_text)
    if matches:
        try:
            return float(matches[-1])
        except ValueError:
            pass

    # Look for variable assignments that might be the answer
    # e.g., "result = 123.45" or "answer = 123.45"
    var_pattern = r"(?:result|answer|solution|value|final)\s*=\s*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)"
    matches = re.findall(var_pattern, code_text, re.IGNORECASE)
    if matches:
        try:
            return float(matches[-1])
        except ValueError:
            pass

    # Look in response text for execution results
    # Pattern: "Python execution result: 123.45" or "result: 123.45"
    exec_result_pattern = r"(?:execution\s+)?(?:result|output|value)\s*:?\s*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)"
    matches = re.findall(exec_result_pattern, response_text, re.IGNORECASE)
    if matches:
        try:
            return float(matches[-1])
        except ValueError:
            pass

    return None


def parse_response(
    response_text: str, task_type: str, num_options: int = 4
) -> Dict[str, Any]:
    """Parse agent response based on task type.

    Args:
        response_text: The response text from the agent
        task_type: Type of task ("multiple_choice", "calculation", "design")
        num_options: Number of options for multiple choice tasks

    Returns:
        Dictionary with parsed response data
    """
    parsed = {
        "raw_response": response_text,
        "explanation": response_text,  # Default to full response
    }

    if task_type == "multiple_choice":
        selected_option = extract_selected_option(response_text, num_options)
        parsed["selected_option"] = selected_option
        parsed["explanation"] = response_text

    elif task_type == "calculation":
        # First try to extract answer from the response text directly
        answer = extract_numerical_answer(response_text)

        # Also try to extract code and see if answer is in code execution results
        code = extract_code_snippet(response_text)
        if code:
            parsed["code"] = code
            # Try to extract answer from code execution results
            code_answer = extract_answer_from_code_result(code, response_text)
            # Use code answer if we found one and didn't find a direct answer,
            # or if code answer seems more reliable (e.g., from print/return)
            if code_answer is not None and (answer is None or abs(code_answer) > 1e-10):
                answer = code_answer

        parsed["answer"] = answer
        parsed["explanation"] = response_text

    elif task_type == "design":
        # First try to extract JSON from response (preferred method)
        json_obj = extract_json_from_response(response_text)

        if json_obj:
            # JSON found - use structured data
            parsed["design"] = json_obj.get("design", {})
            parsed["rationale"] = json_obj.get("rationale", "")
            parsed["code"] = json_obj.get("code", "")
        else:
            # Fallback to regex-based extraction
            code = extract_code_snippet(response_text)
            if code:
                parsed["code"] = code
            # Extract design parameters from text using regex patterns
            design_params = extract_design_parameters(response_text)
            parsed["design"] = design_params
            parsed["rationale"] = response_text

    elif task_type == "multi_step_design":
        # Level D: multi-step design task
        # First try to extract JSON from response (preferred method)
        json_obj = extract_json_from_response(response_text)

        if json_obj:
            # JSON found - use structured data
            parsed["design"] = json_obj.get("design", {})
            parsed["system_metrics"] = json_obj.get("system_metrics", {})
            parsed["rationale"] = json_obj.get("rationale", "")
            parsed["code"] = json_obj.get("code", "")
        else:
            # Fallback to regex-based extraction
            code = extract_code_snippet(response_text)
            if code:
                parsed["code"] = code
            # Extract design parameters from text using regex patterns
            design_params = extract_design_parameters(response_text)
            parsed["design"] = design_params
            parsed["system_metrics"] = {}  # Can't easily extract from text
            parsed["rationale"] = response_text

    return parsed
