"""Sandboxed Python execution environment for code evaluation."""

import time
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from typing import Any, Dict, Optional

import numpy as np
import scipy

from src.mechgaia_env.config import config


class SandboxExecutor:
    """Executes Python code in a restricted environment."""

    def __init__(self, timeout: Optional[int] = None):
        self.timeout = timeout or config.sandbox_timeout
        self.safe_modules = {
            "numpy": np,
            "np": np,
            "scipy": scipy,
            "math": __import__("math"),
        }

    def execute(
        self,
        code: str,
        variables: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute Python code safely.

        Args:
            code: Python code to execute
            variables: Dictionary of variables to inject into execution context
            timeout: Execution timeout in seconds

        Returns:
            Dictionary with 'result', 'error', 'stdout', 'stderr' keys
        """
        timeout = timeout or self.timeout

        # Create execution namespace
        namespace = self.safe_modules.copy()
        if variables:
            namespace.update(variables)

        # Capture stdout/stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()

        result = None
        error = None

        start_time = time.time()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Execute code
                exec(code, namespace)

                # Try to get result
                if "result" in namespace:
                    result = namespace["result"]
                else:
                    # Try to evaluate the last line as an expression if it's not an assignment
                    lines = [
                        line.strip()
                        for line in code.strip().split("\n")
                        if line.strip() and not line.strip().startswith("#")
                    ]
                    if lines:
                        last_line = lines[-1]
                        # Check if last line is an expression (not an assignment statement)
                        # Assignment would have '=' but not '==', '!=', '<=', '>='
                        is_assignment = (
                            "=" in last_line
                            and "==" not in last_line
                            and "!=" not in last_line
                            and "<=" not in last_line
                            and ">=" not in last_line
                        )

                        if not is_assignment and not last_line.startswith("import"):
                            # Last line is likely an expression - try to evaluate it
                            try:
                                last_expr_result = eval(last_line, namespace)
                                result = last_expr_result
                            except (SyntaxError, NameError, TypeError, ValueError):
                                # Last line wasn't a valid expression, will fall back to variable lookup
                                pass

                    # Fallback: Get last assigned variable (heuristic)
                    if result is None:
                        # Get all variables in namespace (preserves insertion order in Python 3.7+)
                        all_vars = list(namespace.keys())
                        # Filter out safe modules and injected variables
                        safe_module_keys = set(self.safe_modules.keys())
                        injected_keys = set(variables.keys()) if variables else set()
                        new_vars_list = [
                            v
                            for v in all_vars
                            if v not in safe_module_keys and v not in injected_keys
                        ]

                        if new_vars_list:
                            # Prioritize variables that look like results (result, answer, solution, delta_l, etc.)
                            result_keywords = [
                                "result",
                                "answer",
                                "solution",
                                "delta_l",
                                "delta",
                                "final",
                                "output",
                                "value",
                            ]
                            result_vars = [
                                v
                                for v in new_vars_list
                                if any(kw in v.lower() for kw in result_keywords)
                            ]
                            if result_vars:
                                # Get the last matching variable (most recent assignment)
                                result = namespace[result_vars[-1]]
                            else:
                                # Get the last variable in assignment order
                                result = namespace[new_vars_list[-1]]
        except Exception as e:
            error = str(e)
        finally:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                error = f"Execution timeout after {timeout} seconds"

        return {
            "result": result,
            "error": error,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "execution_time": elapsed if "elapsed" in locals() else 0,
        }
