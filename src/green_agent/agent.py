"""Green agent implementation - manages assessment and evaluation."""

import json
import os
import time
import tomllib
import uuid

import dotenv
import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, Message, SendMessageSuccessResponse
from a2a.utils import get_text_parts, new_agent_text_message

from src.mechgaia_env import RESPOND_ACTION_NAME, Action, SolveResult, get_env
from src.mechgaia_env.database import BenchmarkDatabase
from src.mechgaia_env.evaluators import LLMJudgeGrader, UnitTestGrader
from src.my_util import my_a2a, parse_tags

dotenv.load_dotenv()


def load_agent_card_toml(agent_name):
    current_dir = __file__.rsplit("/", 1)[0]
    with open(f"{current_dir}/{agent_name}.toml", "rb") as f:
        return tomllib.load(f)


async def ask_agent_to_solve(white_agent_url, env, task_index, max_num_steps=30):
    total_cost = 0.0
    env_reset_res = env.reset(task_index=task_index)
    obs = env_reset_res.observation
    info = env_reset_res.info.model_dump()
    reward = 0.0
    format_failure_count = 0  # Track format failures for metrics
    max_format_retries = 1  # Allow one retry for format issues

    # messages = [
    #     {"role": "system", "content": env.wiki},
    #     {"role": "user", "content": obs},
    # ]

    # Here, instead of calling white agent like calling an LLM, we need to present
    #   the assessment scenario to the white agent as if it is a independent task
    # Specifically, here we provide the tool information for the agent to reply with
    task_description = f"""
{env.wiki}

**CRITICAL: You MUST use tools to solve problems before providing final answers.**

Here's a list of tools you can use (you can use at most one tool at a time):
{json.dumps(env.tools_info, indent=2)}

**Response Format Requirements:**
You MUST respond in JSON format, wrapped with <json>...</json> tags.

**Example Tool Call:**
<json>
{{"name": "calculator", "kwargs": {{"expression": "100 * 2"}}}}
</json>

**Example Python Code Execution:**
<json>
{{"name": "python_exec", "kwargs": {{"code": "import math\\nresult = math.sqrt(16)\\nprint(result)"}}}}
</json>

**Example Final Answer (after using tools):**
<json>
{{"name": "{RESPOND_ACTION_NAME}", "kwargs": {{"content": "After calculating using the tools, the answer is 4.0 Pa. The calculation was performed using the formula stress = force / area."}}}}
</json>

**IMPORTANT FOR CALCULATION PROBLEMS (Level B):**
1. First, use calculator or python_exec to perform your calculations
2. Wait for the tool result
3. Then provide your final answer using the "respond" action
4. Your final response MUST clearly state the numerical answer with units (e.g., "The answer is 123.45 Pa" or "Result: 123.45 Pa")
5. Include both the numerical value AND units in your answer

**IMPORTANT FOR DESIGN PROBLEMS (Level C):**
1. Use tools to perform calculations and evaluate design options
2. After completing your analysis, you MUST output exactly one fenced code block tagged ```json
3. The content of that block MUST be a single JSON object with keys: "design", "rationale", and "code"
4. The "design" object should contain all design parameters (e.g., height_m, frequency_Hz, deflection_m, mass_kg, max_stress_MPa, safety_factor)
5. Do not include any additional text before or after the ```json code block
6. Example format:
   ```json
   {{
     "design": {{"height_m": 0.25, "frequency_Hz": 38.5, ...}},
     "rationale": "Your explanation here",
     "code": "Your Python code here"
   }}
   ```

**IMPORTANT FOR MULTI-STEP DESIGN PROBLEMS (Level D):**
1. Use tools to perform calculations for each step (material selection, serviceability checks, system evaluation)
2. After completing all steps, you MUST output exactly one fenced code block tagged ```json
3. The content of that block MUST be a single JSON object with keys: "design", "system_metrics", "rationale", and "code"
4. The "design" object should contain component-level design parameters (e.g., span_1: {{material, height_m}}, span_2: {{material, height_m}})
5. The "system_metrics" object should contain system-level metrics (max_deflection_m, max_stress_span_1_MPa, max_stress_span_2_MPa, min_frequency_Hz, total_mass_kg)
6. Do not include any additional text before or after the ```json code block
7. Example format:
   ```json
   {{
     "design": {{"span_1": {{"material": "Steel A", "height_m": 0.25}}, "span_2": {{"material": "Aluminum", "height_m": 0.30}}}},
     "system_metrics": {{"max_deflection_m": 0.004, "max_stress_span_1_MPa": 120.5, ...}},
     "rationale": "Your multi-step explanation here",
     "code": "Your Python code here"
   }}
   ```

**JSON Structure (for tool calls):**
- "name": the tool call function name (calculator, python_exec, get_material_properties), or "{RESPOND_ACTION_NAME}" for final answers
- "kwargs": the arguments for the tool call, or {{"content": "your message here"}} for final answers

Next, I'll provide you with the user message and tool call results.
User message: {obs}
    """

    next_green_message = task_description
    context_id = None
    for _ in range(max_num_steps):
        # # --> messages (message history)
        # res = completion(
        #     messages=messages,
        #     model=self.model,
        #     custom_llm_provider=self.provider,
        #     tools=self.tools_info,
        #     temperature=self.temperature,
        # )
        # next_message = res.choices[0].message.model_dump()
        # total_cost += res._hidden_params["response_cost"] or 0
        # action = message_to_action(next_message)
        # # --> action (to be executed in the environment)
        print(
            f"@@@ Green agent: Sending message to white agent{'ctx_id=' + str(context_id) if context_id else ''}... -->\n{next_green_message}"
        )
        white_agent_response = await my_a2a.send_message(
            white_agent_url, next_green_message, context_id=context_id
        )
        res_root = white_agent_response.root
        assert isinstance(res_root, SendMessageSuccessResponse)
        res_result = res_root.result
        assert isinstance(
            res_result, Message
        )  # though, a robust design should also support Task
        if context_id is None:
            context_id = res_result.context_id
        else:
            assert context_id == res_result.context_id, (
                "Context ID should remain the same in a conversation"
            )

        text_parts = get_text_parts(res_result.parts)
        assert len(text_parts) == 1, (
            "Expecting exactly one text part from the white agent"
        )
        white_text = text_parts[0]
        print(f"@@@ White agent response:\n{white_text}")
        # parse the action out
        white_tags = parse_tags(white_text)

        # Handle case where white agent doesn't provide JSON tags
        should_break = False
        parse_failed = False  # Track if parsing actually failed vs successfully handled as final response
        needs_retry = False  # Track if we need to retry due to format issues

        if "json" not in white_tags:
            # Check if this might be a Level C or D final response with ```json code block
            import re

            from src.mechgaia_env.response_parser import extract_json_from_response

            json_code_block_match = re.search(
                r"```json\s*\n(.*?)```", white_text, re.DOTALL
            )

            if json_code_block_match:
                # Found ```json code block - this is likely a Level C or D final response
                # Extract it and treat as respond action with the full response
                print(
                    "@@@ Found JSON code block in response (Level C/D format). Treating as final response."
                )
                action = Action(
                    name=RESPOND_ACTION_NAME,
                    kwargs={
                        "content": white_text  # Use full response including JSON block
                    },
                )
                should_break = True  # Break after this step (successfully handled)
                parse_failed = False  # This is successful handling, not a failure
            else:
                # Check if this is a Level C/D task that should have JSON but doesn't
                # Try to extract JSON from response and retry if needed
                parsed_json = extract_json_from_response(white_text)

                if parsed_json is None and format_failure_count < max_format_retries:
                    # This might be a Level C/D response missing JSON formatting
                    # Check if response contains design-related keywords
                    if any(
                        keyword in white_text.lower()
                        for keyword in [
                            "design",
                            "rationale",
                            "code",
                            "height_m",
                            "frequency",
                        ]
                    ):
                        print(
                            "@@@ Potential Level C/D response missing JSON formatting. Attempting retry..."
                        )
                        format_failure_count += 1
                        # Send repair message
                        repair_message = """Your response appears to be missing proper JSON formatting. 

For Level C and Level D tasks, you MUST output your final answer in this exact format:

```json
{
  "design": { ... },
  "rationale": "...",
  "code": "..."
}
```

Please provide your complete answer again, ensuring it is wrapped in ```json code fences."""
                        # Send repair message and restart loop to get retry response
                        next_green_message = repair_message
                        continue  # Skip rest of loop, wait for retry response

                # Try to extract JSON from the response text directly (for tool calls)
                if not needs_retry:
                    print(
                        f"@@@ Warning: White agent response missing JSON tags. Response: {white_text[:200]}..."
                    )
                    json_match = re.search(
                        r'\{[^{}]*"name"[^{}]*\}', white_text, re.DOTALL
                    )
                    if json_match:
                        try:
                            action_dict = json.loads(json_match.group(0))
                            action = Action(**action_dict)
                            # Successfully parsed - don't break, continue conversation
                        except (json.JSONDecodeError, ValueError) as e:
                            print(f"@@@ Error parsing JSON from response: {e}")
                            format_failure_count += 1
                            # If we can't parse, treat as a respond action
                            action = Action(
                                name=RESPOND_ACTION_NAME,
                                kwargs={
                                    "content": white_text  # Use full response text, not truncated
                                },
                            )
                            should_break = True  # Break after this step to prevent infinite retries
                            parse_failed = True  # This is a parsing failure
                    else:
                        # No JSON found - treat as a respond action
                        print(
                            "@@@ No JSON found in response. Treating as final response."
                        )
                        action = Action(
                            name=RESPOND_ACTION_NAME,
                            kwargs={
                                "content": white_text  # Use full response text, not truncated
                            },
                        )
                        should_break = (
                            True  # Break after this step (successfully handled)
                        )
                        parse_failed = (
                            False  # This is successful handling, not a failure
                        )
        else:
            action_json = white_tags["json"]
            try:
                # Try to parse JSON - handle cases where there's extra text after JSON
                # First try direct parsing
                action_dict = json.loads(action_json)
                # Validate structure before creating Action
                if (
                    not isinstance(action_dict, dict)
                    or "name" not in action_dict
                    or "kwargs" not in action_dict
                ):
                    raise ValueError(
                        f"Invalid action structure: missing 'name' or 'kwargs'. Got keys: {list(action_dict.keys()) if isinstance(action_dict, dict) else 'not a dict'}"
                    )
                action = Action(**action_dict)
            except json.JSONDecodeError as e:
                # JSON parsing failed - try to extract just the JSON object
                print(f"@@@ Error parsing JSON from tags: {e}")
                print(
                    f"@@@ Attempting to extract JSON object from: {action_json[:200]}..."
                )

                # Try multiple strategies to extract valid JSON
                import re

                action_dict = None

                # Strategy 1: Try to find the first complete JSON object by matching braces
                # This handles cases where there's extra text after the JSON
                brace_count = 0
                start_idx = -1
                for i, char in enumerate(action_json):
                    if char == "{":
                        if start_idx == -1:
                            start_idx = i
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0 and start_idx != -1:
                            # Found complete JSON object
                            try:
                                extracted_json = action_json[start_idx : i + 1]
                                action_dict = json.loads(extracted_json)
                                # Validate it has the required structure
                                if (
                                    isinstance(action_dict, dict)
                                    and "name" in action_dict
                                    and "kwargs" in action_dict
                                ):
                                    print(
                                        "@@@ Successfully extracted complete JSON object using brace matching"
                                    )
                                    break
                                else:
                                    action_dict = (
                                        None  # Invalid structure, try next strategy
                                    )
                            except json.JSONDecodeError:
                                action_dict = None  # Invalid JSON, try next strategy
                            start_idx = -1
                            brace_count = 0

                # Strategy 2: If brace matching failed, try regex (but validate structure)
                if action_dict is None:
                    json_obj_match = re.search(
                        r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", action_json, re.DOTALL
                    )
                    if json_obj_match:
                        try:
                            extracted_json = json_obj_match.group(0)
                            potential_dict = json.loads(extracted_json)
                            # Validate it has the required structure (name and kwargs)
                            if (
                                isinstance(potential_dict, dict)
                                and "name" in potential_dict
                                and "kwargs" in potential_dict
                            ):
                                action_dict = potential_dict
                                print(
                                    "@@@ Successfully extracted JSON object using regex"
                                )
                            else:
                                print(
                                    f"@@@ Extracted JSON missing required keys (name/kwargs): {list(potential_dict.keys()) if isinstance(potential_dict, dict) else 'not a dict'}"
                                )
                        except (json.JSONDecodeError, ValueError) as e2:
                            print(f"@@@ Failed to parse extracted JSON: {e2}")

                if action_dict:
                    try:
                        action = Action(**action_dict)
                        print("@@@ Successfully created Action from extracted JSON")
                    except (ValueError, TypeError) as e2:
                        print(f"@@@ Failed to create Action: {e2}")
                        # Fallback: treat as respond action with full text
                        action = Action(
                            name=RESPOND_ACTION_NAME, kwargs={"content": white_text}
                        )
                        should_break = True
                        parse_failed = True
                else:
                    # No valid JSON object found - treat as respond action with full text
                    print("@@@ No valid JSON object found in extracted content")
                    action = Action(
                        name=RESPOND_ACTION_NAME, kwargs={"content": white_text}
                    )
                    should_break = True
                    parse_failed = True  # This is a parsing failure
            except (ValueError, TypeError) as e:
                print(f"@@@ Error creating Action from parsed JSON: {e}")
                # Fallback: treat as respond action with full text
                action = Action(
                    name=RESPOND_ACTION_NAME, kwargs={"content": white_text}
                )
                should_break = True
                parse_failed = True  # This is a parsing failure

        env_response = env.step(action)
        reward = env_response.reward
        info_dict = env_response.info.model_dump()
        info = {**info, **info_dict}

        # Store the response text for evaluation (from action or info)
        if action.name == RESPOND_ACTION_NAME:
            response_text = action.kwargs.get("content", "")
            info["last_response"] = response_text
            info["response_text"] = response_text
            print(
                f"@@@ Stored response text (length {len(response_text)}): {response_text[:150]}..."
            )
        elif "response_text" in info_dict and info_dict.get("response_text"):
            # Also check if environment stored it
            stored_text = info_dict.get("response_text", "")
            info["last_response"] = stored_text
            info["response_text"] = stored_text
            print(
                f"@@@ Stored response text from env (length {len(stored_text)}): {stored_text[:150]}..."
            )
        else:
            # For tool calls, also store the observation in case it contains the final answer
            # This helps when the agent doesn't provide a final "respond" action
            if action.name in ["calculator", "python_exec"]:
                tool_result = env_response.observation
                # Store tool results for potential answer extraction
                if "tool_results" not in info:
                    info["tool_results"] = []
                info["tool_results"].append(
                    {
                        "tool": action.name,
                        "result": tool_result,
                        "observation": tool_result,
                    }
                )
                # If this looks like a final answer, also store it as potential response
                # Check if observation contains a clear numerical result
                from src.mechgaia_env.response_parser import extract_numerical_answer

                potential_answer = extract_numerical_answer(tool_result)
                if potential_answer is not None and env_response.done:
                    # This might be the final answer from tool execution
                    info["last_response"] = tool_result
                    info["response_text"] = tool_result
                    print(
                        f"@@@ Stored tool result as potential final answer: {tool_result[:150]}..."
                    )

        # Stop if task is done or if we couldn't parse the response - don't send more messages
        if env_response.done or should_break:
            if should_break and parse_failed:
                # Actually failed to parse - show error message
                print(
                    "@@@ Could not parse white agent response. Stopping conversation."
                )
            elif should_break:
                # Successfully handled as final response (e.g., found JSON code block)
                print("@@@ Response handled as final answer. Stopping conversation.")
            else:
                print("@@@ Task marked as done. Stopping conversation.")
            break

        # instead of maintain history, just prepare the next message with the latest observation
        if action.name != RESPOND_ACTION_NAME:
            next_green_message = f"""
Tool call result:
{env_response.observation}
            """
        else:
            # For respond action, if environment marked it as done, we're finished
            # Otherwise, the environment should have marked it done
            if env_response.done:
                break
            # If not done yet, don't send another message - wait for environment to mark done
            # This prevents the loop issue
            print(
                "@@@ Response received but task not marked done yet. Breaking to prevent loop."
            )
            break

    # Add format_failure_count to info for metrics
    info["format_failure_count"] = format_failure_count

    return SolveResult(
        reward=reward,
        info=info,
        messages=[],  # incompatible, thus removed
        total_cost=total_cost,
    )


class MechgaiaGreenAgentExecutor(AgentExecutor):
    def __init__(self, db_path: str | None = None):
        self.db = BenchmarkDatabase(db_path)
        self.llm_judge = LLMJudgeGrader()
        self.unit_test_grader = UnitTestGrader()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # parse the task
        print("Green agent: Received a task, parsing...")
        user_input = context.get_user_input()
        tags = parse_tags(user_input)
        white_agent_url = tags["white_agent_url"]
        env_config_str = tags["env_config"]
        env_config = json.loads(env_config_str)

        # set up the environment
        print("Green agent: Setting up the environment...")

        # Support both legacy task_ids and new task_instance_ids
        task_ids = env_config.get("task_ids", [])
        task_instance_ids = env_config.get("task_instance_ids", [])
        level = env_config.get("level")
        levels = env_config.get("levels", [])  # Support multiple levels

        # Determine which tasks to evaluate
        if task_instance_ids:
            instances_to_evaluate = task_instance_ids
        elif levels:
            # Evaluate all specified levels - get ALL tasks and instances
            instances_to_evaluate = []
            for level in levels:
                tasks = self.db.get_tasks_by_level(level)
                print(f"  Found {len(tasks)} tasks for Level {level}")
                for task in tasks:  # Evaluate ALL tasks for this level
                    instances = self.db.get_task_instances(task_id=task["id"])
                    if instances:
                        # Add all instances for each task, not just the first one
                        instances_to_evaluate.extend([inst["id"] for inst in instances])

            # For testing: Limit Level C and D to 2 instances each
            if "C" in levels or "D" in levels:
                # Get instance levels from database for proper subsampling
                all_instances_data = self.db.get_task_instances()
                instance_level_map = {
                    inst["id"]: inst["level"] for inst in all_instances_data
                }

                # Separate instances by level
                c_instances = [
                    inst
                    for inst in instances_to_evaluate
                    if instance_level_map.get(inst) == "C"
                ]
                d_instances = [
                    inst
                    for inst in instances_to_evaluate
                    if instance_level_map.get(inst) == "D"
                ]
                other_instances = [
                    inst
                    for inst in instances_to_evaluate
                    if inst not in c_instances + d_instances
                ]

                # Limit C and D instances
                if "C" in levels and len(c_instances) > 2:
                    print(
                        f"  Limiting Level C evaluation to 2 instances for testing (found {len(c_instances)} total)"
                    )
                    c_instances = c_instances[:2]
                if "D" in levels and len(d_instances) > 2:
                    print(
                        f"  Limiting Level D evaluation to 2 instances for testing (found {len(d_instances)} total)"
                    )
                    d_instances = d_instances[:2]

                instances_to_evaluate = c_instances + d_instances + other_instances

            print(f"  Total instances to evaluate: {len(instances_to_evaluate)}")
        elif level:
            # Get all instances for a single level - evaluate ALL tasks
            tasks = self.db.get_tasks_by_level(level)
            instances_to_evaluate = []
            for task in tasks:  # Evaluate ALL tasks for this level
                instances = self.db.get_task_instances(task_id=task["id"])
                if instances:
                    # Add all instances for each task, not just the first one
                    instances_to_evaluate.extend([inst["id"] for inst in instances])

            # For testing: Limit Level C and D to 2 instances
            if level == "C" and len(instances_to_evaluate) > 2:
                print(
                    f"  Limiting Level C evaluation to 2 instances for testing (found {len(instances_to_evaluate)} total)"
                )
                instances_to_evaluate = instances_to_evaluate[:2]
            elif level == "D" and len(instances_to_evaluate) > 2:
                print(
                    f"  Limiting Level D evaluation to 2 instances for testing (found {len(instances_to_evaluate)} total)"
                )
                instances_to_evaluate = instances_to_evaluate[:2]
        elif task_ids:
            # Try to find instances in database first
            instances_to_evaluate = []
            all_tasks = (
                self.db.get_tasks_by_level("A")
                + self.db.get_tasks_by_level("B")
                + self.db.get_tasks_by_level("C")
                + self.db.get_tasks_by_level("D")
            )

            for task_id in task_ids:
                # Check if task_id is a string (database ID) or int (legacy)
                if isinstance(task_id, str):
                    # Database task ID - get instances for this specific task
                    instances = self.db.get_task_instances(task_id=task_id)
                    if instances:
                        instances_to_evaluate.extend(
                            [
                                inst["id"] for inst in instances[:1]
                            ]  # First instance per task
                        )
                else:
                    # Legacy integer task_id (e.g., 1, 2, 3)
                    # Check if database has tasks
                    if all_tasks:
                        # Database has tasks - evaluate ALL tasks (not just first one)
                        # This allows evaluating all generated tasks when legacy IDs are provided
                        for task in all_tasks:
                            instances = self.db.get_task_instances(task_id=task["id"])
                            if instances:
                                # Take first instance of each task
                                instances_to_evaluate.append(instances[0]["id"])
                        # Break after first legacy ID to avoid duplicates
                        break
                    # If no tasks in database, will fall through to legacy mode

            # If no instances found, use legacy mode
            if not instances_to_evaluate:
                instances_to_evaluate = [None]  # Use legacy mode
        else:
            # Fallback to legacy single task
            instances_to_evaluate = [None]  # Use legacy mode

        metrics = {}
        all_results = []

        print(f"Green agent: Evaluating {len(instances_to_evaluate)} task instances...")
        timestamp_started = time.time()

        model_name = env_config.get("user_model", "unknown")

        for instance_id in instances_to_evaluate:
            if instance_id is None:
                # Legacy mode
                task_index = env_config.get("task_ids", [1])[0]
                env = get_env(
                    env_name=env_config["env"],
                    user_strategy=env_config["user_strategy"],
                    user_model=env_config["user_model"],
                    task_split=env_config["task_split"],
                    user_provider=env_config.get("user_provider", None),
                    task_index=task_index,
                )
                res = await ask_agent_to_solve(white_agent_url, env, task_index)
                all_results.append({"reward": res.reward, "task_index": task_index})
            else:
                # Database mode
                instance = next(
                    (i for i in self.db.get_task_instances() if i["id"] == instance_id),
                    None,
                )
                if not instance:
                    print(f"Warning: Instance {instance_id} not found, skipping")
                    continue

                # Get task schema
                tasks = self.db.get_tasks_by_level(instance["level"])
                task = next((t for t in tasks if t["id"] == instance["task_id"]), None)
                if not task:
                    print(f"Warning: Task {instance['task_id']} not found, skipping")
                    continue

                db_path_str = (
                    str(self.db.db_path) if hasattr(self.db, "db_path") else None
                )
                env = get_env(
                    env_name=env_config["env"],
                    task_instance_id=instance_id,
                    level=instance["level"],
                    db_path=db_path_str,
                )

                res = await ask_agent_to_solve(white_agent_url, env, task_index=None)

                # Evaluate response
                schema_data = (
                    json.loads(task["schema_data"])
                    if isinstance(task["schema_data"], str)
                    else task["schema_data"]
                )

                # Extract response from agent messages
                from src.mechgaia_env.response_parser import parse_response

                # Determine task type
                if instance["level"] == "A":
                    task_type = "multiple_choice"
                    num_options = len(schema_data.get("options", []))
                elif instance["level"] == "B":
                    task_type = "calculation"
                    num_options = 0
                elif instance["level"] == "C":
                    task_type = "design"
                    num_options = 0
                elif instance["level"] == "D":
                    task_type = "multi_step_design"
                    num_options = 0
                else:
                    task_type = "unknown"
                    num_options = 0

                # Get the response text from the result info
                response_text = res.info.get("last_response", "") or res.info.get(
                    "response_text", ""
                )

                if not response_text:
                    print(
                        f"Warning: No response text found for instance {instance_id}. Info keys: {list(res.info.keys())}"
                    )
                    # Try to get from the SolveResult's info directly
                    if hasattr(res, "info") and isinstance(res.info, dict):
                        response_text = res.info.get(
                            "last_response", ""
                        ) or res.info.get("response_text", "")

                    # Fallback: Check tool results for potential answers
                    if not response_text and "tool_results" in res.info:
                        tool_results = res.info.get("tool_results", [])
                        # Use the last tool result as potential response
                        if tool_results:
                            last_result = tool_results[-1]
                            response_text = last_result.get(
                                "result", ""
                            ) or last_result.get("observation", "")
                            print(
                                f"@@@ Using tool result as response text: {response_text[:150]}..."
                            )

                    if not response_text:
                        print(
                            f"Warning: Still no response text. Skipping evaluation for {instance_id}"
                        )
                        # Skip evaluation if no response
                        all_results.append(
                            {
                                "instance_id": instance_id,
                                "reward": 0.0,
                                "scores": {},
                                "success": False,
                                "error": "No response text found",
                            }
                        )
                        continue

                print(
                    f"@@@ Parsing response for instance {instance_id} (length: {len(response_text)}): {response_text[:100]}..."
                )

                # Parse the response
                response = parse_response(response_text, task_type, num_options)
                if instance["level"] == "C":
                    # For Level C, log design parameters
                    design = response.get("design", {})
                    print(
                        f"@@@ Parsed response: design={design}, rationale_length={len(response.get('rationale', ''))}, has_code={bool(response.get('code'))}"
                    )
                elif instance["level"] == "D":
                    # For Level D, log multi-component design parameters
                    design = response.get("design", {})
                    system_metrics = response.get("system_metrics", {})
                    print(
                        f"@@@ Parsed response: design={design}, system_metrics={system_metrics}, rationale_length={len(response.get('rationale', ''))}, has_code={bool(response.get('code'))}"
                    )
                else:
                    print(
                        f"@@@ Parsed response: selected_option={response.get('selected_option')}, answer={response.get('answer')}"
                    )

                try:
                    if instance["level"] == "A":
                        print("@@@ Evaluating Level A task with MEJ (LLM judge)...")
                        scores = self.llm_judge.evaluate_level_a(schema_data, response)
                        print(f"@@@ MEJ scores: {scores}")
                    elif instance["level"] == "B":
                        print("@@@ Evaluating Level B task with unit test grader...")
                        unit_test_scores = self.unit_test_grader.evaluate_level_b(
                            schema_data,
                            instance["parameters"],
                            instance["gold_answer"],
                            response,
                        )
                        print(f"@@@ Unit test grader scores: {unit_test_scores}")

                        # Also evaluate with MEJ for qualitative assessment
                        print("@@@ Evaluating Level B task with MEJ (LLM judge)...")
                        mej_scores = self.llm_judge.evaluate_level_b(
                            schema_data,
                            instance["parameters"],
                            instance["gold_answer"],
                            response,
                        )
                        print(f"@@@ MEJ scores: {mej_scores}")

                        # Combine both evaluations
                        scores = {**unit_test_scores, **mej_scores}
                    elif instance["level"] == "C":
                        print("@@@ Evaluating Level C task with MEJ (LLM judge)...")
                        scores = self.llm_judge.evaluate_level_c(schema_data, response)
                        print(f"@@@ MEJ scores: {scores}")

                        # Calculate criteria breakdown for Level C
                        criteria_threshold = 0.6  # Threshold for "passing" a criterion
                        criteria_names = [
                            "technical_accuracy",
                            "safety_constraint_awareness",
                            "reasoning_quality",
                            "engineering_judgment",
                        ]
                        passed_criteria = [
                            name
                            for name in criteria_names
                            if scores.get(name, 0) >= criteria_threshold
                        ]
                        criteria_percentage = (
                            len(passed_criteria) / len(criteria_names)
                        ) * 100

                        print("@@@ Level C Criteria Breakdown:")
                        for name in criteria_names:
                            score = scores.get(name, 0)
                            status = (
                                "✓ PASS" if score >= criteria_threshold else "✗ FAIL"
                            )
                            print(f"  - {name}: {score:.2f} ({status})")
                        print(
                            f"@@@ Criteria Met: {len(passed_criteria)}/{len(criteria_names)} ({criteria_percentage:.1f}%)"
                        )
                    elif instance["level"] == "D":
                        print("@@@ Evaluating Level D task with MEJ (LLM judge)...")
                        scores = self.llm_judge.evaluate_level_d(schema_data, response)
                        print(f"@@@ MEJ scores: {scores}")

                        # Calculate criteria breakdown for Level D
                        criteria_threshold = 0.6  # Threshold for "passing" a criterion
                        criteria_names = [
                            "technical_accuracy",
                            "multi_step_coordination",
                            "system_constraint_awareness",
                            "engineering_judgment",
                        ]
                        passed_criteria = [
                            name
                            for name in criteria_names
                            if scores.get(name, 0) >= criteria_threshold
                        ]
                        criteria_percentage = (
                            len(passed_criteria) / len(criteria_names)
                        ) * 100

                        print("@@@ Level D Criteria Breakdown:")
                        for name in criteria_names:
                            score = scores.get(name, 0)
                            status = (
                                "✓ PASS" if score >= criteria_threshold else "✗ FAIL"
                            )
                            print(f"  - {name}: {score:.2f} ({status})")
                        print(
                            f"@@@ Criteria Met: {len(passed_criteria)}/{len(criteria_names)} ({criteria_percentage:.1f}%)"
                        )
                    else:
                        print(
                            f"@@@ Unknown level: {instance['level']}, skipping evaluation"
                        )
                        scores = {"error": f"Unknown level: {instance['level']}"}
                except Exception as e:
                    print(f"@@@ Error during evaluation: {e}")
                    import traceback

                    traceback.print_exc()
                    scores = {"error": str(e)}

                # Store evaluation
                eval_id = str(uuid.uuid4())
                self.db.add_evaluation(
                    eval_id=eval_id,
                    task_instance_id=instance_id,
                    model_name=model_name,
                    response=response,
                    scores=scores,
                )

                # Determine success based on scores, not just environment reward
                # For Level A: correctness > 0.5 OR overall_score > 0.7 OR technical_accuracy > 0.7
                # For Level B: (correctness > 0.9 AND value_tolerance == 1.0) OR MEJ_overall > 0.7
                #   (quantitative correctness OR qualitative MEJ evaluation)
                # For Level C: overall_score > 0.7
                if instance["level"] == "A":
                    correctness = scores.get("correctness", 0)
                    overall_score = scores.get("overall_score", 0)
                    technical_accuracy = scores.get("technical_accuracy", 0)
                    success = (
                        correctness > 0.5
                        or overall_score > 0.7
                        or technical_accuracy > 0.7
                    )
                    print(
                        f"@@@ Level A evaluation: correctness={correctness:.2f}, overall={overall_score:.2f}, technical={technical_accuracy:.2f}, success={success}"
                    )
                elif instance["level"] == "B":
                    correctness = scores.get("correctness", 0)
                    value_tolerance = scores.get("value_tolerance", 0)
                    mej_overall = scores.get("mej_overall_score", 0)

                    # Success criteria: quantitative correctness OR high MEJ score
                    # Quantitative: correctness > 0.9 AND value_tolerance == 1.0 (within tolerance)
                    # Qualitative: MEJ overall score > 0.6 (moderate engineering judgment)
                    #   OR correctness > 0.5 (partial credit for close answers)
                    quantitative_pass = correctness > 0.9 and value_tolerance >= 1.0
                    qualitative_pass = mej_overall > 0.6
                    partial_credit = (
                        correctness > 0.5
                    )  # Give partial credit for close answers
                    success = quantitative_pass or qualitative_pass or partial_credit

                    print(
                        f"@@@ Level B evaluation: correctness={correctness:.2f}, value_tolerance={value_tolerance:.2f}, "
                        f"MEJ_overall={mej_overall:.2f}, quantitative_pass={quantitative_pass}, "
                        f"qualitative_pass={qualitative_pass}, partial_credit={partial_credit}, success={success}"
                    )
                elif instance["level"] == "C":
                    overall_score = scores.get("overall_score", 0)
                    # Success if overall_score > 0.7 OR all criteria pass (>= 0.6)
                    criteria_threshold = 0.6
                    criteria_names = [
                        "technical_accuracy",
                        "safety_constraint_awareness",
                        "reasoning_quality",
                        "engineering_judgment",
                    ]
                    all_criteria_pass = all(
                        scores.get(name, 0) >= criteria_threshold
                        for name in criteria_names
                    )
                    success = overall_score > 0.7 or (
                        overall_score >= 0.6 and all_criteria_pass
                    )
                    print(
                        f"@@@ Level C evaluation: overall_score={overall_score:.2f}, all_criteria_pass={all_criteria_pass}, success={success}"
                    )
                elif instance["level"] == "D":
                    overall_score = scores.get("overall_score", 0)
                    # Success if overall_score > 0.7 OR all criteria pass (>= 0.6)
                    criteria_threshold = 0.6
                    criteria_names = [
                        "technical_accuracy",
                        "multi_step_coordination",
                        "system_constraint_awareness",
                        "engineering_judgment",
                    ]
                    all_criteria_pass = all(
                        scores.get(name, 0) >= criteria_threshold
                        for name in criteria_names
                    )
                    success = overall_score > 0.7 or (
                        overall_score >= 0.6 and all_criteria_pass
                    )
                    print(
                        f"@@@ Level D evaluation: overall_score={overall_score:.2f}, all_criteria_pass={all_criteria_pass}, success={success}"
                    )
                else:
                    print(f"@@@ Unknown level: {instance['level']}, marking as failed")
                    success = False

                all_results.append(
                    {
                        "instance_id": instance_id,
                        "reward": 1.0 if success else 0.0,
                        "scores": scores,
                        "success": success,
                    }
                )

        metrics["time_used"] = time.time() - timestamp_started
        metrics["num_tasks"] = len(instances_to_evaluate)
        metrics["success_rate"] = (
            sum(1 for r in all_results if r.get("success", False)) / len(all_results)
            if all_results
            else 0
        )

        result_emoji = "✅" if metrics["success_rate"] > 0.5 else "❌"

        print("Green agent: Evaluation complete.")
        await event_queue.enqueue_event(
            new_agent_text_message(
                f"Finished. Evaluation results: {result_emoji}\n"
                f"Success rate: {metrics['success_rate']:.2%}\n"
                f"Tasks evaluated: {metrics['num_tasks']}\n"
                f"Time: {metrics['time_used']:.2f}s\n"
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError


def start_green_agent(agent_name="mechgaia_green_agent", host="localhost", port=9001):
    print("Starting green agent...")
    agent_card_dict = load_agent_card_toml(agent_name)

    # Determine agent URL: check AGENT_URL_GREEN, then AGENT_URL, then default to localhost
    agent_url = os.getenv("AGENT_URL_GREEN") or os.getenv("AGENT_URL")
    if not agent_url:
        agent_url = f"http://{host}:{port}"
    agent_url = agent_url.rstrip("/")
    agent_card_dict["url"] = agent_url

    request_handler = DefaultRequestHandler(
        agent_executor=MechgaiaGreenAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=AgentCard(**agent_card_dict),
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=host, port=port)
