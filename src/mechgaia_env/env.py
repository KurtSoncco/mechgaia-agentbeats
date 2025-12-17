"""MechGAIA environment implementation."""

# Type hints are handled inline

from pydantic import BaseModel


class EnvInfo(BaseModel):
    """Environment info returned by reset/step."""

    pass


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

    def __init__(self, task_index: int = 1):
        self.task_index = task_index
        self.current_step = 0
        self.max_steps = 30

        # Wiki/documentation for the environment
        self.wiki = """
You are working with MechGAIA, a mechanical engineering problem-solving environment.
You have access to scientific computing tools including:
- Calculator for basic arithmetic
- Python scipy for scientific computing
- Python numpy for numerical operations
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

        # Simple problem templates (for now, simple problems)
        self.problems = {
            1: {
                "question": "Calculate the stress in a steel beam with a cross-sectional area of 0.01 m² under a load of 5000 N. Use the formula: stress = force / area.",
                "solution": 500000.0,  # 5000 / 0.01 = 500000 Pa
                "steps_to_solve": 2,
            }
        }

        self.current_problem = None
        self.solved = False

    def reset(self, task_index: int | None = None) -> ResetResult:
        """Reset the environment for a new task."""
        if task_index is None:
            task_index = self.task_index

        self.task_index = task_index
        self.current_step = 0
        self.solved = False

        if task_index not in self.problems:
            raise ValueError(
                f"Task {task_index} not found. Available tasks: {list(self.problems.keys())}"
            )

        self.current_problem = self.problems[task_index]

        observation = f"""
Mechanical Engineering Problem:

{self.current_problem["question"]}

Use the available tools to solve this problem step by step.
"""

        info = EnvInfo()
        return ResetResult(observation=observation, info=info)

    def step(self, action) -> StepResult:
        """Execute an action in the environment."""
        from src.mechgaia_env.types import RESPOND_ACTION_NAME

        self.current_step += 1
        done = False
        reward = 0.0

        if action.name == RESPOND_ACTION_NAME:
            # Agent is responding directly
            response_content = action.kwargs.get("content", "")
            observation = f"Your response: {response_content}"

            # Check if the response indicates the problem is solved
            if self.current_problem and not self.solved:
                # Simple check: if response contains the answer or indicates completion
                if str(self.current_problem["solution"]) in response_content or any(
                    word in response_content.lower()
                    for word in ["answer", "solution", "result", "complete"]
                ):
                    # Verify the answer is correct
                    if str(self.current_problem["solution"]) in response_content:
                        reward = 1.0
                        self.solved = True
                        done = True
                        observation += f"\n\nCorrect! The stress is {self.current_problem['solution']} Pa."
                    else:
                        observation += "\n\nPlease provide the numerical answer."
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
                if (
                    self.current_problem
                    and abs(result - self.current_problem["solution"]) < 0.01
                ):
                    reward = 1.0
                    self.solved = True
                    done = True
                    observation += f"\n\nCorrect! The stress is {result} Pa."
            except Exception as e:
                observation = f"Calculator error: {str(e)}"
        elif action.name == "python_exec":
            # Execute Python code
            code = action.kwargs.get("code", "")
            try:
                # Execute in a safe namespace
                namespace = {
                    "numpy": __import__("numpy"),
                    "np": __import__("numpy"),
                    "scipy": __import__("scipy"),
                    "math": __import__("math"),
                }
                exec(code, namespace)
                result = namespace.get("result", "Code executed successfully")
                observation = f"Python execution result: {result}"

                # Check if result matches solution
                if self.current_problem:
                    try:
                        result_value = (
                            float(result)
                            if isinstance(result, (int, float, str))
                            else None
                        )
                        if (
                            result_value
                            and abs(result_value - self.current_problem["solution"])
                            < 0.01
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
        else:
            observation = f"Unknown action: {action.name}"

        # Check if max steps reached
        if self.current_step >= self.max_steps:
            done = True
            if not self.solved and self.current_problem:
                observation += f"\n\nMaximum steps reached. The correct answer is {self.current_problem['solution']} Pa."

        info = EnvInfo()
        return StepResult(observation=observation, reward=reward, done=done, info=info)


def get_env(
    env_name: str,
    user_strategy: str | None = None,
    user_model: str | None = None,
    task_split: str | None = None,
    user_provider: str | None = None,
    task_index: int = 1,
    **kwargs,
) -> MechgaiaEnv:
    """Get a MechGAIA environment instance.

    Args:
        env_name: Environment name (should be "mechgaia")
        user_strategy: User strategy (not used currently)
        user_model: User model (not used currently)
        task_split: Task split (not used currently)
        user_provider: User provider (not used currently)
        task_index: Index of the task to load
        **kwargs: Additional arguments (ignored)

    Returns:
        MechgaiaEnv instance
    """
    if env_name != "mechgaia":
        raise ValueError(f"Unknown environment: {env_name}. Expected 'mechgaia'.")

    return MechgaiaEnv(task_index=task_index)
