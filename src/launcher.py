"""Launcher module - initiates and coordinates the evaluation process."""

import json
import multiprocessing

from src.green_agent.agent import start_green_agent
from src.my_util import my_a2a
from src.white_agent.agent import start_white_agent


async def launch_evaluation(use_cloudflare: bool = False):
    """
    Launch evaluation workflow.
    
    Args:
        use_cloudflare: If True, use Cloudflare URLs (https://green.mechgaia.org, etc.)
                       and don't start local agents. If False, start local agents.
    """
    if use_cloudflare:
        print("Using Cloudflare URLs for evaluation...")
        green_url = "https://green.mechgaia.org"
        white_url = "https://white.mechgaia.org"
        
        # Check if agents are accessible via Cloudflare
        print(f"Checking green agent at {green_url}...")
        assert await my_a2a.wait_agent_ready(green_url, timeout=30), "Green agent not ready via Cloudflare"
        print("Green agent is ready via Cloudflare.")
        
        print(f"Checking white agent at {white_url}...")
        assert await my_a2a.wait_agent_ready(white_url, timeout=30), "White agent not ready via Cloudflare"
        print("White agent is ready via Cloudflare.")
        
        p_green = None
        p_white = None
    else:
        # Check if agents are already running before starting new ones
        green_address = ("localhost", 9001)
        green_url = f"http://{green_address[0]}:{green_address[1]}"
        white_address = ("localhost", 9003)
        white_url = f"http://{white_address[0]}:{white_address[1]}"
        
        # Check if agents are already running
        green_running = await my_a2a.wait_agent_ready(green_url, timeout=2)
        white_running = await my_a2a.wait_agent_ready(white_url, timeout=2)
        
        p_green = None
        p_white = None
        
        if green_running:
            print(f"✅ Green agent is already running at {green_url}")
        else:
            # start green agent
            print("Launching green agent locally...")
            p_green = multiprocessing.Process(
                target=start_green_agent, args=("mechgaia_green_agent", *green_address)
            )
            p_green.start()
            assert await my_a2a.wait_agent_ready(green_url), "Green agent not ready in time"
            print("Green agent is ready.")

        if white_running:
            print(f"✅ White agent is already running at {white_url}")
        else:
            # start white agent (on port 9003, controller uses 9002)
            print("Launching white agent locally...")
            p_white = multiprocessing.Process(
                target=start_white_agent, args=("general_white_agent", *white_address)
            )
            p_white.start()
            assert await my_a2a.wait_agent_ready(white_url), "White agent not ready in time"
            print("White agent is ready.")

    # send the task description
    print("Sending task description to green agent...")
    task_config = {
        "env": "retail",
        "user_strategy": "llm",
        "user_model": "openai/gpt-4o",
        "user_provider": "openai",
        "task_split": "test",
        "task_ids": [1],
    }
    task_text = f"""
Your task is to test the MechGaia agent located at:
<white_agent_url>
{white_url}/
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
    print("\n" + "=" * 60)
    print("Response from green agent:")
    print("=" * 60)
    response_text = my_a2a.extract_response_text(response)
    print(response_text)
    print("=" * 60)

    print("Evaluation complete. Terminating agents...")
    if p_green:
        p_green.terminate()
        p_green.join()
    if p_white:
        p_white.terminate()
        p_white.join()
    print("Agents terminated.")
