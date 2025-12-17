"""CLI entry point for mechgaia-agentbeats."""

import asyncio

import typer
from pydantic_settings import BaseSettings

from src.green_agent.agent import start_green_agent
from src.launcher import launch_evaluation, launch_remote_evaluation
from src.white_agent.agent import start_white_agent


class MechgaiaSettings(BaseSettings):
    role: str = "unspecified"
    host: str = "127.0.0.1"
    agent_port: int = 9000


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
def run():
    settings = MechgaiaSettings()
    if settings.role == "green":
        start_green_agent(host=settings.host, port=settings.agent_port)
    elif settings.role == "white":
        start_white_agent(host=settings.host, port=settings.agent_port)
    else:
        raise ValueError(f"Unknown role: {settings.role}")
    return


@app.command()
def launch():
    """Launch the complete evaluation workflow."""
    asyncio.run(launch_evaluation())


@app.command()
def launch_remote(
    green_url: str = "http://localhost:9001",
    white_url: str = "http://localhost:9002",
    level: str = typer.Option(
        None, "--level", "-l", help="Single task level (A, B, or C)"
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
        levels_list = [l.strip() for l in levels.split(",")]

    asyncio.run(
        launch_remote_evaluation(
            green_url, white_url, level=level, levels=levels_list, model_name=model
        )
    )


if __name__ == "__main__":
    app()
