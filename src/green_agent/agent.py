"""Green agent - MechGaia assessment controller."""

import re
import tomllib
import traceback
from pathlib import Path

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message

from src.my_util import my_a2a


class MechGaiaGreenAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        print("Green agent: Received task, forwarding to white agent...")
        user_input = context.get_user_input()

        # Extract white agent URL from task description if present
        # Default to localhost for local testing, or use the public URL
        white_agent_url = "http://localhost:9002"
        if "<white_agent_url>" in user_input:
            match = re.search(
                r"<white_agent_url>\s*(.+?)\s*</white_agent_url>", user_input
            )
            if match:
                white_agent_url = match.group(1).strip()
        elif "white.mechgaia.org" in user_input:
            white_agent_url = "https://white.mechgaia.org"

        try:
            # Use the my_a2a utility to send message properly
            # Don't pass task_id - the white agent will create its own task
            # context_id can be passed to maintain conversation context if needed
            response = await my_a2a.send_message(
                white_agent_url,
                user_input,
                task_id=None,
                context_id=None,
            )

            # Extract the response text from the A2A response
            # The response is a SendMessageResponse which may have a result field
            response_text = ""
            result = getattr(response, "result", None)
            if result:
                parts = getattr(result, "parts", None)
                if parts:
                    response_text = "\n".join(
                        getattr(part, "text", str(part)) for part in parts
                    )
                else:
                    text = getattr(result, "text", None)
                    if text:
                        response_text = text
                    else:
                        response_text = str(result)
            else:
                response_text = str(response)

            await event_queue.enqueue_event(
                new_agent_text_message(f"✅ White agent response:\n{response_text}")
            )
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error details: {error_details}")
            await event_queue.enqueue_event(
                new_agent_text_message(
                    f"❌ Error communicating with white agent: {str(e)}"
                )
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError


def create_green_agent_app():
    """Create and return the green agent Starlette app."""
    # Load agent card from TOML file
    toml_path = Path(__file__).parent / "mechgaia_green_agent.toml"
    with toml_path.open("rb") as f:
        config = tomllib.load(f)

    # Parse capabilities
    capabilities_config = config.get("capabilities", {})
    capabilities = AgentCapabilities(
        streaming=capabilities_config.get("streaming", False)
    )

    # Parse skills
    skills = []
    for skill_config in config.get("skills", []):
        skills.append(
            AgentSkill(
                id=skill_config.get("id", ""),
                name=skill_config.get("name", ""),
                description=skill_config.get("description", ""),
                tags=skill_config.get("tags", []),
                examples=skill_config.get("examples", []),
            )
        )

    # Create agent card with URL override
    card = AgentCard(
        name=config.get("name", ""),
        description=config.get("description", ""),
        url="https://green.mechgaia.org",
        version=config.get("version", ""),
        capabilities=capabilities,
        default_input_modes=config.get("defaultInputModes", ["text"]),
        default_output_modes=config.get("defaultOutputModes", ["text"]),
        skills=skills,
    )

    app = A2AStarletteApplication(
        agent_card=card,
        http_handler=DefaultRequestHandler(
            agent_executor=MechGaiaGreenAgentExecutor(),
            task_store=InMemoryTaskStore(),
        ),
    )

    built_app = app.build()

    # Add POST support for agent-card endpoint (AgentBeats uses POST)
    # The A2A SDK only adds GET/HEAD, so we need to add POST manually
    from starlette.routing import Route

    # Find the existing agent-card route handler
    agent_card_handler = None
    for route in built_app.routes:
        # Check if this is a Route (not Mount or other route types)
        if isinstance(route, Route):
            if hasattr(route, "path") and route.path == "/.well-known/agent-card.json":
                if hasattr(route, "endpoint"):
                    agent_card_handler = route.endpoint
                    break

    if agent_card_handler:
        # Add POST route for the same endpoint
        async def handle_post_agent_card(request):
            # Use the same handler as GET
            response = await agent_card_handler(request)
            return response

        # Add POST route
        built_app.routes.append(
            Route(
                "/.well-known/agent-card.json", handle_post_agent_card, methods=["POST"]
            )
        )

    return built_app


def start_green_agent(agent_name="mechgaia_green_agent", host="0.0.0.0", port=9001):
    """Start the green agent server."""
    print("Starting MechGaia Green Agent...")
    app = create_green_agent_app()
    uvicorn.run(app, host=host, port=port)


# Expose app for earthshaker controller
app = create_green_agent_app()
