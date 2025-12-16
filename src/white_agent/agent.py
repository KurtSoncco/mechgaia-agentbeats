"""White agent implementation - the target agent being tested."""

import tomllib
from pathlib import Path

import dotenv
import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message

dotenv.load_dotenv()


class MechGaiaWhiteAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        print("White agent: Received task, solving mechanical engineering problem...")
        user_input = context.get_user_input()
        print(f"White agent solving: {user_input[:100]}...")

        # Simple beam deflection example
        # For a simply supported beam with point load at center
        # Deflection formula: δ = (P * L^3) / (48 * E * I)

        # Example beam parameters
        span_length = 2.0  # Span length in meters
        point_load = 100.0  # Point load in kN
        youngs_modulus = 200e9  # Young's modulus for steel in Pa (200 GPa)
        moment_of_inertia = 8.33e-6  # Second moment of area in m^4 (for a rectangular beam 200mm x 200mm)

        # Calculate deflection
        load_N = point_load * 1000  # Convert kN to N
        deflection = (load_N * span_length**3) / (
            48 * youngs_modulus * moment_of_inertia
        )  # Deflection in meters
        deflection_mm = deflection * 1000  # Convert to mm

        # Calculate maximum bending moment
        max_bending_moment = (
            load_N * span_length
        ) / 4  # Maximum bending moment at center

        # Format solution
        solution = f"""Beam Deflection Analysis:

Beam Configuration:
- Span length (L): {span_length} m
- Point load (P): {point_load} kN
- Material: Steel (E = 200 GPa)
- Cross-section: 200mm × 200mm rectangular

Results:
- Maximum deflection: {deflection_mm:.2f} mm
- Maximum bending moment: {max_bending_moment / 1000:.2f} kN·m
- Deflection at center: {deflection_mm:.2f} mm

Note: This is a simply supported beam with point load at center."""

        await event_queue.enqueue_event(
            new_agent_text_message(solution, context_id=context.context_id)
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError


def create_white_agent_app():
    """Create and return the white agent Starlette app."""
    # Load agent card from TOML file
    toml_path = Path(__file__).parent / "mechgaia_white_agent.toml"
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
        url=config.get("url", "https://white.mechgaia.org"),
        version=config.get("version", ""),
        capabilities=capabilities,
        default_input_modes=config.get("defaultInputModes", ["text"]),
        default_output_modes=config.get("defaultOutputModes", ["text"]),
        skills=skills,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=MechGaiaWhiteAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=card,
        http_handler=request_handler,
    )

    built_app = app.build()

    # Add POST support for agent-card endpoint (AgentBeats uses POST)
    # The A2A SDK only adds GET/HEAD, so we need to add POST manually
    from starlette.responses import JSONResponse
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

    # Add root endpoint (/) that returns AgentCard JSON (AgentBeats expects this)
    async def root_handler(request):
        return JSONResponse(card.model_dump())

    built_app.routes.append(Route("/", root_handler, methods=["GET"]))

    # Add health endpoint (AgentBeats expects this)
    async def health_handler(request):
        return JSONResponse({"status": "healthy", "ready": True})

    built_app.routes.append(Route("/health", health_handler, methods=["GET"]))

    return built_app


def start_white_agent(agent_name="general_white_agent", host="0.0.0.0", port=9003):
    """Start the white agent server (defaults to port 9003, controller uses 9002)."""
    print("Starting white agent...")
    app = create_white_agent_app()
    uvicorn.run(app, host=host, port=port)


# Expose app for earthshaker controller
app = create_white_agent_app()
