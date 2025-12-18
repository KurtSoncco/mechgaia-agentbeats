"""Launcher module - initiates and coordinates the evaluation process."""

import json
import multiprocessing

from src.green_agent.agent import start_green_agent
from src.my_util import my_a2a
from src.white_agent.agent import start_white_agent


async def launch_evaluation(
    level: str | None = None,
    levels: list[str] | None = None,
):
    """Launch the complete evaluation workflow.

    Args:
        level: Single task level to evaluate (A, B, C, or D)
        levels: List of task levels to evaluate (e.g., ["A", "B", "C", "D"])
    """
    # start green agent
    print("Launching green agent...")
    green_address = ("localhost", 9001)
    green_url = f"http://{green_address[0]}:{green_address[1]}"
    p_green = multiprocessing.Process(
        target=start_green_agent, args=("mechgaia_green_agent", *green_address)
    )
    p_green.start()
    assert await my_a2a.wait_agent_ready(green_url), "Green agent not ready in time"
    print("Green agent is ready.")

    # start white agent
    print("Launching white agent...")
    white_address = ("localhost", 9002)
    white_url = f"http://{white_address[0]}:{white_address[1]}"
    p_white = multiprocessing.Process(
        target=start_white_agent, args=("general_white_agent", *white_address)
    )
    p_white.start()
    assert await my_a2a.wait_agent_ready(white_url), "White agent not ready in time"
    print("White agent is ready.")

    # send the task description
    print("Sending task description to green agent...")

    # Check if database has tasks - if so, use level-based evaluation
    # Otherwise fall back to legacy mode
    from src.mechgaia_env.database import BenchmarkDatabase

    db = BenchmarkDatabase()

    # Determine which levels to evaluate
    levels_to_evaluate = None
    if levels:
        # Use explicitly provided levels
        levels_to_evaluate = levels
    elif level:
        # Use single level
        levels_to_evaluate = [level]
    else:
        # Default: Use one instance of Level C for testing
        print("No level specified. Defaulting to one instance of Level C for testing.")
        levels_to_evaluate = ["C"]

    if levels_to_evaluate:
        # Check if we should use task_instance_ids (for default single instance test)
        # or levels (for explicit level/levels specification)
        use_single_instance = (
            not levels
            and not level
            and len(levels_to_evaluate) == 1
            and levels_to_evaluate[0] == "C"
        )

        if use_single_instance:
            # Default behavior: Get one instance of Level C
            tasks = db.get_tasks_by_level("C")
            if tasks:
                print(f"Found {len(tasks)} Level C tasks in database.")
                # Get instances for the first task
                instances = db.get_task_instances(task_id=tasks[0]["id"])
                if instances:
                    # Use only the first instance
                    single_instance_id = instances[0]["id"]
                    print(f"Using single Level C instance: {single_instance_id}")
                    task_config = {
                        "env": "mechgaia",
                        "user_strategy": "llm",
                        "user_model": "openai/gpt-4o",
                        "user_provider": "openai",
                        "task_split": "test",
                        "task_instance_ids": [single_instance_id],
                    }
                else:
                    print(
                        "Warning: No instances found for Level C tasks. Using legacy mode."
                    )
                    task_config = {
                        "env": "mechgaia",
                        "user_strategy": "llm",
                        "user_model": "openai/gpt-4o",
                        "user_provider": "openai",
                        "task_split": "test",
                        "task_ids": [1],  # Legacy mode
                    }
            else:
                print("Warning: No Level C tasks found. Using legacy mode.")
                task_config = {
                    "env": "mechgaia",
                    "user_strategy": "llm",
                    "user_model": "openai/gpt-4o",
                    "user_provider": "openai",
                    "task_split": "test",
                    "task_ids": [1],  # Legacy mode
                }
        else:
            # Explicit level/levels specified - evaluate all instances for those levels
            valid_levels = []
            for lvl in levels_to_evaluate:
                tasks = db.get_tasks_by_level(lvl)
                if tasks:
                    print(f"Found {len(tasks)} Level {lvl} tasks in database.")
                    valid_levels.append(lvl)
                else:
                    print(f"Warning: No tasks found for Level {lvl}. Skipping.")

            if valid_levels:
                print(f"Evaluating Level {', '.join(valid_levels)} tasks...")
                task_config = {
                    "env": "mechgaia",
                    "user_strategy": "llm",
                    "user_model": "openai/gpt-4o",
                    "user_provider": "openai",
                    "task_split": "test",
                    "levels": valid_levels,
                }
            else:
                # No valid levels found - use legacy mode
                print("No valid levels found. Using legacy mode.")
                task_config = {
                    "env": "mechgaia",
                    "user_strategy": "llm",
                    "user_model": "openai/gpt-4o",
                    "user_provider": "openai",
                    "task_split": "test",
                    "task_ids": [1],  # Legacy mode
                }
    else:
        # No tasks in database - use legacy mode
        print("No tasks in database. Using legacy mode.")
        task_config = {
            "env": "mechgaia",
            "user_strategy": "llm",
            "user_model": "openai/gpt-4o",
            "user_provider": "openai",
            "task_split": "test",
            "task_ids": [1],  # Legacy mode
        }
    task_text = f"""
Your task is to instantiate MechGaia to test the agent located at:
<white_agent_url>
http://{white_address[0]}:{white_address[1]}/
</white_agent_url>
You should use the following env configuration:
<env_config>
{json.dumps(task_config, indent=2)}
</env_config>
    """
    print("Task description:")
    print(task_text)
    print("Sending...")
    response = await my_a2a.send_message(green_url, task_text)
    print("Response from green agent:")
    print(response)

    print("Evaluation complete. Terminating agents...")
    p_green.terminate()
    p_green.join()
    p_white.terminate()
    p_white.join()
    print("Agents terminated.")


async def launch_remote_evaluation(
    green_url: str,
    white_url: str,
    level: str | None = None,
    levels: list[str] | None = None,
    task_instance_ids: list[str] | None = None,
    model_name: str = "openai/gpt-4o",
):
    """Launch remote evaluation with configurable parameters.

    Args:
        green_url: URL of the green agent (evaluator)
        white_url: URL of the white agent (being tested)
        level: Single task level to evaluate (A, B, C, or D). If None, uses levels, task_instance_ids or defaults to single Level C instance
        levels: List of task levels to evaluate (e.g., ["A", "B", "C", "D"]). Takes precedence over level
        task_instance_ids: Specific task instance IDs to evaluate
        model_name: Model name for tracking in results
    """
    task_config = {
        "env": "mechgaia",
        "user_strategy": "llm",
        "user_model": model_name,
        "user_provider": "openai",
        "task_split": "test",
    }

    # Add levels, level, or task_instance_ids if provided
    if levels:
        task_config["levels"] = levels
    elif level:
        task_config["level"] = level
    elif task_instance_ids:
        task_config["task_instance_ids"] = task_instance_ids
    else:
        # Default: Check database for a single Level C instance (same as launch_evaluation)
        print("No level specified. Defaulting to one instance of Level C for testing.")
        from src.mechgaia_env.database import BenchmarkDatabase

        db = BenchmarkDatabase()
        tasks = db.get_tasks_by_level("C")
        if tasks:
            print(f"Found {len(tasks)} Level C tasks in database.")
            # Get instances for the first task
            instances = db.get_task_instances(task_id=tasks[0]["id"])
            if instances:
                # Use only the first instance
                single_instance_id = instances[0]["id"]
                print(f"Using single Level C instance: {single_instance_id}")
                task_config["task_instance_ids"] = [single_instance_id]
            else:
                print(
                    "Warning: No instances found for Level C tasks. Using legacy mode."
                )
                task_config["task_ids"] = [1]  # Legacy mode
        else:
            print("Warning: No Level C tasks found. Using legacy mode.")
            task_config["task_ids"] = [1]  # Legacy mode
    task_text = f"""
Your task is to instantiate MechGaia to test the agent located at:
<white_agent_url>
{white_url}
</white_agent_url>
You should use the following env configuration:
<env_config>
{json.dumps(task_config, indent=2)}
</env_config>
    """
    print("Sending task description to green agent...")
    print(f"Task config: {json.dumps(task_config, indent=2)}")
    try:
        response = await my_a2a.send_message(green_url, task_text)
        print("Response from green agent:")
        print(response)
    except Exception:
        print(f"Error: Failed to connect to green agent at {green_url}")
        print("Make sure the green agent is running. Start it with:")
        print("  python main.py green")
        print("Or use 'python main.py launch' to start both agents automatically.")
        raise
