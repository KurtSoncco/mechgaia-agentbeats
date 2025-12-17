"""MechGAIA environment implementation."""

# Type hints are handled inline

import json
from typing import Optional

from pydantic import BaseModel

from src.mechgaia_env.database import BenchmarkDatabase
from src.mechgaia_env.sandbox import SandboxExecutor
from src.mechgaia_env.toolbox import EngineeringToolbox


class EnvInfo(BaseModel):
    """Environment info returned by reset/step."""

    response_text: str = ""

    def model_dump(self, **kwargs):
        result = super().model_dump(**kwargs)
        # Add response text if available
        return result


class ResetResult:
    """Result of environment reset."""

    def __init__(self, observation: str, info: EnvInfo):
        self.observation = observation
        self.info = info


class StepResult:
    """Result of environment step."""

    def __init__(self, observation: str, reward: float, done: bool, info: EnvInfo):
        self.observation = observation
        self.reward = reward
        self.done = done
        self.info = info


class MechgaiaEnv:
    """MechGAIA environment for mechanical engineering problems."""

    def __init__(
        self,
        task_index: int = 1,
        task_instance_id: Optional[str] = None,
        level: Optional[str] = None,
        db_path: Optional[str] = None,
    ):
        self.task_index = task_index
        self.task_instance_id = task_instance_id
        self.level = level
        self.current_step = 0
        self.max_steps = 30
        self.db = BenchmarkDatabase(db_path)
        self.toolbox = EngineeringToolbox()
        self.sandbox = SandboxExecutor()

        # Wiki/documentation for the environment
        self.wiki = """
You are working with MechGAIA, a mechanical engineering problem-solving environment.
You have access to scientific computing tools including:
- Calculator for basic arithmetic
- Python scipy for scientific computing
- Python numpy for numerical operations
- Material database for engineering properties
- Plotting tools for stress-strain and other diagrams
- Other scientific computing libraries as needed

Solve the mechanical engineering problems step by step using the available tools.
"""

        # Available tools
        self.tools_info = [
            {
                "name": "calculator",
                "description": "Perform basic arithmetic calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)')",
                        }
                    },
                    "required": ["expression"],
                },
            },
            {
                "name": "python_exec",
                "description": "Execute Python code for scientific computing (scipy, numpy, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute",
                        }
                    },
                    "required": ["code"],
                },
            },
            {
                "name": "get_material_properties",
                "description": "Get material properties from database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "material_name": {
                            "type": "string",
                            "description": "Name of material (e.g., 'steel', 'aluminum', 'titanium')",
                        }
                    },
                    "required": ["material_name"],
                },
            },
            {
                "name": "respond",
                "description": "Respond directly to the user without using tools",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Your response message",
                        }
                    },
                    "required": ["content"],
                },
            },
        ]

        # Fallback problems for backward compatibility
        self.problems = {
            1: {
                "question": "Calculate the stress in a steel beam with a cross-sectional area of 0.01 m² under a load of 5000 N. Use the formula: stress = force / area.",
                "solution": 500000.0,
                "steps_to_solve": 2,
            }
        }

        self.current_problem = None
        self.current_task_instance = None
        self.solved = False

    def reset(
        self,
        task_index: int | None = None,
        task_instance_id: str | None = None,
        level: str | None = None,
    ) -> ResetResult:
        """Reset the environment for a new task."""
        if task_index is not None:
            self.task_index = task_index
        if task_instance_id is not None:
            self.task_instance_id = task_instance_id
        if level is not None:
            self.level = level

        self.current_step = 0
        self.solved = False
        # Reset Python namespace for new task (clear sandbox persistent state)
        self.sandbox.persistent_namespace = {}

        # Try to load from database first
        if self.task_instance_id:
            instances = self.db.get_task_instances()
            instance = next(
                (i for i in instances if i["id"] == self.task_instance_id), None
            )
            if instance:
                self.current_task_instance = instance
                # Get task schema
                tasks = self.db.get_tasks_by_level(instance["level"])
                task = next((t for t in tasks if t["id"] == instance["task_id"]), None)
                if task:
                    schema_data = (
                        json.loads(task["schema_data"])
                        if isinstance(task["schema_data"], str)
                        else task["schema_data"]
                    )
                    self.current_problem = self._format_task_from_schema(
                        schema_data, instance, instance["level"]
                    )
        elif self.level:
            # Load a random task instance from the level
            tasks = self.db.get_tasks_by_level(self.level)
            if tasks:
                task = tasks[0]  # Use first task
                instances = self.db.get_task_instances(task_id=task["id"])
                if instances:
                    instance = instances[0]
                    self.current_task_instance = instance
                    schema_data = (
                        json.loads(task["schema_data"])
                        if isinstance(task["schema_data"], str)
                        else task["schema_data"]
                    )
                    self.current_problem = self._format_task_from_schema(
                        schema_data, instance, self.level
                    )

        # Fallback to legacy problems
        if not self.current_problem:
            if self.task_index not in self.problems:
                raise ValueError(
                    f"Task {self.task_index} not found. Available tasks: {list(self.problems.keys())}"
                )
            self.current_problem = self.problems[self.task_index]

        observation = f"""
Mechanical Engineering Problem:

{self.current_problem.get("question", self.current_problem.get("problem_text", ""))}

Use the available tools to solve this problem step by step.
"""

        info = EnvInfo()
        return ResetResult(observation=observation, info=info)

    def _format_task_from_schema(
        self, schema_data: dict, instance: dict, level: str
    ) -> dict:
        """Format task from schema data and instance."""
        if level == "A":
            # Level A: multiple choice
            question = schema_data.get("question", "")
            options = schema_data.get("options", [])
            options_text = "\n".join(
                [f"{i + 1}. {opt}" for i, opt in enumerate(options)]
            )
            return {
                "question": f"{question}\n\nOptions:\n{options_text}",
                "level": "A",
                "correct_option": schema_data.get("correct_option"),
                "type": "multiple_choice",
            }
        elif level == "B":
            # Level B: parametric calculation
            template = schema_data.get("problem_template", "")
            parameters = instance.get("parameters", {})
            problem_text = template.format(**parameters)
            return {
                "problem_text": problem_text,
                "level": "B",
                "parameters": parameters,
                "gold_answer": instance.get("gold_answer", {}),
                "type": "calculation",
            }
        elif level == "C":
            # Level C: design task
            objectives = schema_data.get("objectives", [])
            constraints = schema_data.get("constraints", [])
            problem_text = f"""
Design Task: {schema_data.get("topic", "")}

Objectives:
{chr(10).join(f"- {obj}" for obj in objectives)}

Constraints:
{chr(10).join(f"- {con}" for con in constraints)}
"""
            return {
                "problem_text": problem_text,
                "level": "C",
                "objectives": objectives,
                "constraints": constraints,
                "design_variables": schema_data.get("design_variables", {}),
                "type": "design",
            }
        elif level == "D":
            # Level D: multi-step design task
            title = schema_data.get("title", schema_data.get("topic", ""))
            description = schema_data.get("description", "")
            objectives = schema_data.get("objectives", [])
            constraints = schema_data.get("constraints", {})
            steps = schema_data.get("steps", [])
            given = schema_data.get("given", {})

            # Format step-by-step instructions
            steps_text = ""
            for i, step in enumerate(steps, 1):
                step_name = step.get("name", f"Step {i}")
                step_desc = step.get("description", "")
                steps_text += f"\n\nStep {i}: {step_name}\n{step_desc}"
                if step.get("design_variables"):
                    steps_text += "\nDesign variables for this step:"
                    for var_name, var_info in step["design_variables"].items():
                        steps_text += f"\n  - {var_name}: {var_info}"
                if step.get("requires_code"):
                    steps_text += "\n  [Requires code execution]"

            # Format constraints
            constraints_text = ""
            if isinstance(constraints, dict):
                for key, value in constraints.items():
                    constraints_text += f"\n- {key}: {value}"
            elif isinstance(constraints, list):
                constraints_text = "\n".join(f"- {con}" for con in constraints)

            problem_text = f"""
Multi-Step Design Task: {title}

Description:
{description}

Given Parameters:
{json.dumps(given, indent=2)}

Objectives:
{chr(10).join(f"- {obj}" for obj in objectives)}

System-Level Constraints:
{constraints_text}

Task Steps:{steps_text}

You must complete all steps and provide a final design solution.
"""
            return {
                "problem_text": problem_text,
                "level": "D",
                "objectives": objectives,
                "constraints": constraints,
                "steps": steps,
                "given": given,
                "expected_output_schema": schema_data.get("expected_output_schema", {}),
                "type": "multi_step_design",
            }
        else:
            # Fallback for unknown levels
            return {
                "problem_text": f"Task level {level}",
                "level": level,
                "type": "unknown",
            }

    def step(self, action) -> StepResult:
        """Execute an action in the environment."""
        from src.mechgaia_env.types import RESPOND_ACTION_NAME

        self.current_step += 1
        done = False
        reward = 0.0

        if action.name == RESPOND_ACTION_NAME:
            # Agent is responding directly
            response_content = action.kwargs.get("content", "")
            # Store response in info for later evaluation
            if not hasattr(self, "_response_content"):
                self._response_content = ""
            self._response_content = response_content
            # Don't echo back the response - just mark as done
            observation = "Response received."

            # Check if the response indicates the problem is solved
            if self.current_problem and not self.solved:
                task_type = self.current_problem.get("type", "legacy")

                if task_type == "multiple_choice":
                    # Level A task - check for correct option
                    correct_option = self.current_problem.get("correct_option")
                    num_options = len(self.current_problem.get("options", []))

                    # Use response parser to extract selected option
                    from src.mechgaia_env.response_parser import extract_selected_option

                    selected_option = extract_selected_option(
                        response_content, num_options
                    )

                    if correct_option is not None:
                        if selected_option is not None:
                            # Option was extracted - mark as done immediately, will be evaluated by LLM judge
                            self.solved = True
                            done = True
                            # Don't set reward here - let LLM judge determine final score
                            # Just mark as done to stop the conversation
                            observation = f"Task completed. Selected Option {selected_option + 1}. Response will be evaluated."
                        elif any(
                            word in response_content.lower()
                            for word in ["answer", "solution", "option", "correct"]
                        ):
                            # Response mentions answer but option not clearly extracted - mark done for LLM evaluation
                            done = True
                            self.solved = True
                            observation = "Task completed. Response will be evaluated by LLM judge."
                elif task_type == "calculation":
                    # Level B task - check for numerical answer
                    gold_answer = self.current_problem.get("gold_answer", {})
                    solution = gold_answer.get("solution")
                    if solution is not None:
                        # Check if response contains the solution value
                        if str(solution) in response_content or any(
                            word in response_content.lower()
                            for word in ["answer", "solution", "result", "complete"]
                        ):
                            if str(solution) in response_content:
                                reward = 1.0
                                self.solved = True
                                done = True
                                observation += f"\n\nCorrect! The answer is {solution}."
                            else:
                                observation += (
                                    "\n\nPlease provide the numerical answer."
                                )
                elif task_type == "design":
                    # Level C task - mark as done if response contains design information
                    # Check for design parameters, dimensions, or completion keywords
                    has_design_keywords = any(
                        word in response_content.lower()
                        for word in [
                            "design",
                            "solution",
                            "complete",
                            "answer",
                            "optimized",
                            "dimensions",
                            "configuration",
                        ]
                    )
                    # Check for design parameters (width, height, length, frequency, etc.)
                    has_design_params = any(
                        pattern in response_content.lower()
                        for pattern in [
                            "width",
                            "height",
                            "length",
                            "frequency",
                            "=",
                            "dimensions",
                        ]
                    )
                    if has_design_keywords or has_design_params:
                        done = True
                        self.solved = True
                        observation += "\n\nResponse received. Will be evaluated."
                elif task_type == "multi_step_design":
                    # Level D task - mark as done if response contains multi-component design information
                    has_multi_component_keywords = any(
                        word in response_content.lower()
                        for word in [
                            "design",
                            "solution",
                            "complete",
                            "span",
                            "component",
                            "system",
                            "metrics",
                        ]
                    )
                    # Check for JSON block (Level D should also use JSON format)
                    has_json = "```json" in response_content.lower()
                    if has_multi_component_keywords or has_json:
                        done = True
                        self.solved = True
                        observation += "\n\nResponse received. Will be evaluated."
                else:
                    # Legacy task format
                    solution = self.current_problem.get("solution")
                    if solution is not None:
                        if str(solution) in response_content or any(
                            word in response_content.lower()
                            for word in ["answer", "solution", "result", "complete"]
                        ):
                            if str(solution) in response_content:
                                reward = 1.0
                                self.solved = True
                                done = True
                                observation += (
                                    f"\n\nCorrect! The stress is {solution} Pa."
                                )
                            else:
                                observation += (
                                    "\n\nPlease provide the numerical answer."
                                )
        elif action.name == "calculator":
            # Execute calculator tool
            expression = action.kwargs.get("expression", "")
            try:
                import math

                # Simple evaluation (in production, use a safer evaluator)
                safe_dict = {
                    "__builtins__": {},
                    "math": math,
                    "sqrt": math.sqrt,
                    "sin": math.sin,
                    "cos": math.cos,
                    "tan": math.tan,
                    "pi": math.pi,
                    "e": math.e,
                }
                # Replace common operators
                expr = expression.replace("^", "**")
                result = eval(expr, safe_dict)
                observation = f"Calculator result: {result}"

                # Check if this matches the solution
                if self.current_problem:
                    task_type = self.current_problem.get("type", "legacy")
                    if task_type == "calculation":
                        gold_answer = self.current_problem.get("gold_answer", {})
                        solution = gold_answer.get("solution")
                        tolerance = gold_answer.get("tolerance", 0.01)
                        if solution is not None and abs(result - solution) < tolerance:
                            reward = 1.0
                            self.solved = True
                            done = True
                            observation += f"\n\nCorrect! The answer is {result}."
                    elif task_type == "legacy":
                        solution = self.current_problem.get("solution")
                        if solution is not None and abs(result - solution) < 0.01:
                            reward = 1.0
                            self.solved = True
                            done = True
                            observation += f"\n\nCorrect! The stress is {result} Pa."
            except Exception as e:
                observation = f"Calculator error: {str(e)}"
        elif action.name == "python_exec":
            # Execute Python code using SandboxExecutor
            code = action.kwargs.get("code", "")
            try:
                # Use SandboxExecutor which now maintains persistent state across calls
                exec_result = self.sandbox.execute(code)
                result = None

                if exec_result["error"]:
                    observation = f"Python execution error: {exec_result['error']}"
                else:
                    result = exec_result["result"]
                    stdout = exec_result["stdout"].strip()
                    stderr = exec_result["stderr"].strip()

                    # Build observation message
                    if result is not None:
                        observation = f"Python execution result: {result}"
                    elif stdout:
                        observation = f"Python execution output:\n{stdout}"
                    elif stderr:
                        observation = f"Python execution completed (stderr):\n{stderr}"
                    else:
                        observation = "Python code executed successfully (no output or result variable found)"

                    # Add stdout/stderr if present and different from result
                    if stdout and (result is None or str(result) != stdout):
                        observation += f"\n\nStandard output:\n{stdout}"
                    if stderr:
                        observation += f"\n\nStandard error:\n{stderr}"

                # Check if result matches solution
                if self.current_problem and result is not None:
                    task_type = self.current_problem.get("type", "legacy")
                    try:
                        result_value = (
                            float(result)
                            if isinstance(result, (int, float, str))
                            else None
                        )

                        if task_type == "calculation":
                            gold_answer = self.current_problem.get("gold_answer", {})
                            gold_solution = gold_answer.get("solution")
                            tolerance = gold_answer.get("tolerance", 0.01)
                            if (
                                result_value
                                and gold_solution is not None
                                and abs(result_value - gold_solution) < tolerance
                            ):
                                reward = 1.0
                                self.solved = True
                                done = True
                                observation += (
                                    f"\n\nCorrect! The answer is {result_value}."
                                )
                        elif task_type == "legacy":
                            solution = self.current_problem.get("solution")
                            if (
                                result_value
                                and solution is not None
                                and abs(result_value - solution) < 0.01
                            ):
                                reward = 1.0
                                self.solved = True
                                done = True
                                observation += (
                                    f"\n\nCorrect! The stress is {result_value} Pa."
                                )
                    except Exception:
                        pass
            except Exception as e:
                observation = f"Python execution error: {str(e)}"
        elif action.name == "get_material_properties":
            # Get material properties
            material_name = action.kwargs.get("material_name", "")
            props = self.toolbox.get_material_properties(material_name)
            if props:
                observation = f"Material properties for {material_name}:\n{json.dumps(props, indent=2)}"
            else:
                observation = f"Material '{material_name}' not found. Available materials: {', '.join(self.toolbox.materials.list_materials())}"
        else:
            observation = f"Unknown action: {action.name}"

        # Check if max steps reached
        if self.current_step >= self.max_steps:
            done = True
            if not self.solved and self.current_problem:
                task_type = self.current_problem.get("type", "legacy")
                if task_type == "multiple_choice":
                    correct_option = self.current_problem.get("correct_option")
                    if correct_option is not None:
                        observation += f"\n\nMaximum steps reached. The correct answer is Option {correct_option + 1}."
                elif task_type == "calculation":
                    gold_answer = self.current_problem.get("gold_answer", {})
                    solution = gold_answer.get("solution")
                    if solution is not None:
                        observation += f"\n\nMaximum steps reached. The correct answer is {solution}."
                elif task_type == "legacy":
                    solution = self.current_problem.get("solution")
                    if solution is not None:
                        observation += f"\n\nMaximum steps reached. The correct answer is {solution} Pa."

        # Create info with response text if available
        info = EnvInfo()
        if action.name == RESPOND_ACTION_NAME:
            info.response_text = action.kwargs.get("content", "")
        return StepResult(observation=observation, reward=reward, done=done, info=info)


def get_env(
    env_name: str,
    user_strategy: str | None = None,
    user_model: str | None = None,
    task_split: str | None = None,
    user_provider: str | None = None,
    task_index: int = 1,
    task_instance_id: str | None = None,
    level: str | None = None,
    db_path: str | None = None,
    **kwargs,
) -> MechgaiaEnv:
    """Get a MechGAIA environment instance.

    Args:
        env_name: Environment name (should be "mechgaia")
        user_strategy: User strategy (not used currently)
        user_model: User model (not used currently)
        task_split: Task split (not used currently)
        user_provider: User provider (not used currently)
        task_index: Index of the task to load (legacy)
        task_instance_id: Task instance ID from database
        level: Task level (A, B, or C)
        db_path: Database path (optional)
        **kwargs: Additional arguments (ignored)

    Returns:
        MechgaiaEnv instance
    """
    if env_name != "mechgaia":
        raise ValueError(f"Unknown environment: {env_name}. Expected 'mechgaia'.")

    return MechgaiaEnv(
        task_index=task_index,
        task_instance_id=task_instance_id,
        level=level,
        db_path=db_path,
    )
