"""CLI entry point for mechgaia-agentbeats."""

import asyncio
import os

import typer
from pydantic_settings import BaseSettings

from src.green_agent.agent import start_green_agent
from src.launcher import launch_evaluation, launch_remote_evaluation
from src.white_agent.agent import start_white_agent


class MechgaiaSettings(BaseSettings):
    role: str = "unspecified"
    host: str = "127.0.0.1"
    agent_port: int = 9000

    class Config:
        env_prefix = ""  # No prefix, read ROLE, HOST, AGENT_PORT directly
        case_sensitive = False

    def get_port(self) -> int:
        """Get the port to use, considering PORT env var (Cloud Run) and role-based defaults."""
        # Cloud Run sets PORT environment variable - prioritize this
        port_env = os.getenv("PORT")
        if port_env:
            return int(port_env)

        # Role-based defaults
        if self.role == "green":
            return 9001
        elif self.role == "white":
            return 9002

        # Fallback to configured agent_port
        return self.agent_port


app = typer.Typer(help="MechGaia AgentBeats - Standardized agent assessment framework")


@app.command()
def green():
    """Start the green agent (assessment manager)."""
    start_green_agent()


@app.command()
def white():
    """Start the white agent (target being tested)."""
    start_white_agent()


@app.command()
def run(
    role: str = typer.Option(
        None, "--role", "-r", help="Agent role: 'green' or 'white'"
    ),
):
    """Start an agent (green or white).

    Role can be specified via --role flag or ROLE environment variable.
    Default ports: green=9001, white=9002 (or PORT env var for Cloud Run).
    """
    settings = MechgaiaSettings()
    # Use command-line argument if provided, otherwise use settings (from env var)
    agent_role = role if role else settings.role

    # Update settings role if provided via CLI
    if role:
        settings.role = role

    # Get port using settings method (handles PORT env var and role-based defaults)
    port = settings.get_port()

    if agent_role == "green":
        start_green_agent(host=settings.host, port=port)
    elif agent_role == "white":
        start_white_agent(host=settings.host, port=port)
    else:
        raise ValueError(
            f"Unknown role: {agent_role}. "
            f"Please specify --role green or --role white, or set ROLE environment variable."
        )
    return


@app.command()
def launch(
    level: str = typer.Option(
        None, "--level", "-l", help="Single task level (A, B, C, or D)"
    ),
    levels: str = typer.Option(
        None, "--levels", help="Comma-separated levels (e.g., 'A,B,C')"
    ),
):
    """Launch the complete evaluation workflow.

    If no levels are specified, all available levels in the database will be evaluated.
    """
    levels_list = None
    if levels:
        levels_list = [level.strip().upper() for level in levels.split(",")]

    if level:
        level = level.upper()

    asyncio.run(launch_evaluation(level=level, levels=levels_list))


@app.command()
def launch_remote(
    green_url: str = "http://localhost:9001",
    white_url: str = "http://localhost:9002",
    level: str = typer.Option(
        None, "--level", "-l", help="Single task level (A, B, C, or D)"
    ),
    levels: str = typer.Option(
        None, "--levels", help="Comma-separated levels (e.g., 'A,B,C')"
    ),
    model: str = typer.Option("openai/gpt-4o", "--model", "-m", help="Model name"),
):
    """Launch remote evaluation workflow.

    Assumes green and white agents are already running.
    """
    levels_list = None
    if levels:
        levels_list = [level.strip() for level in levels.split(",")]

    asyncio.run(
        launch_remote_evaluation(
            green_url, white_url, level=level, levels=levels_list, model_name=model
        )
    )


if __name__ == "__main__":
    app()
