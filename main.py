"""CLI entry point for MechGaia agent beats."""

import asyncio
import subprocess
import sys
from pathlib import Path

import typer

from controller_main import start_controller
from src.green_agent import start_green_agent
from src.launcher import launch_evaluation
from src.white_agent import start_white_agent

app = typer.Typer(help="MechGaia Agent Beats - Mechanical Engineering Agent Framework")


@app.command()
def green(host: str = "0.0.0.0", port: int = 9001):
    """Start the green agent (assessment manager)."""
    start_green_agent(host=host, port=port)


@app.command()
def white(host: str = "0.0.0.0", port: int = 9003):
    """Start the white agent (target being tested). Defaults to port 9003."""
    start_white_agent(host=host, port=port)


@app.command()
def controller(host: str = "0.0.0.0", port: int = 9002):
    """Start the controller (proxies to white agent, serves at white.mechgaia.org)."""
    start_controller(host=host, port=port)


@app.command()
def launch():
    """Launch the complete evaluation workflow (local)."""
    asyncio.run(launch_evaluation(use_cloudflare=False))


@app.command(name="launch-cloudflare")
def launch_cloudflare():
    """Launch the complete evaluation workflow via Cloudflare URLs.

    Make sure:
    1. Both agents are running locally (green on port 9001, white on port 9002)
    2. Cloudflared tunnel is running (use 'run-ctrl' command)
    """
    asyncio.run(launch_evaluation(use_cloudflare=True))


@app.command(name="run-ctrl")
def run_ctrl():
    """Start cloudflared tunnel (run in Terminal 1)."""
    config_path = Path(__file__).parent / "cloudflared.yml"
    tunnel_id = "77a45c21-fa38-4ef9-b101-5fd554ddaaa3"

    if not config_path.exists():
        typer.echo(f"Error: Config file not found: {config_path}", err=True)
        sys.exit(1)

    # Check if cloudflared is already running
    try:
        result = subprocess.run(
            ["pgrep", "-f", "cloudflared tunnel"], capture_output=True, text=True
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split("\n")
            typer.echo("✅ Cloudflared tunnel is already running!")
            typer.echo(f"   Process ID(s): {', '.join(pids)}")
            typer.echo("")
            typer.echo("Tunnel is active and forwarding:")
            typer.echo("  - https://green.mechgaia.org → http://localhost:9001")
            typer.echo("  - https://white.mechgaia.org → http://localhost:9002")
            typer.echo("")
            typer.echo("To restart, stop it first with:")
            typer.echo(f"   kill {' '.join(pids)}")
            typer.echo("   or: pkill -f 'cloudflared tunnel'")
            sys.exit(0)
    except FileNotFoundError:
        # pgrep not available, continue anyway
        pass

    typer.echo("Starting cloudflared tunnel...")
    typer.echo(f"  Config: {config_path}")
    typer.echo(f"  Tunnel ID: {tunnel_id}")
    typer.echo("")
    typer.echo("Tunnel will forward:")
    typer.echo("  - https://green.mechgaia.org → http://localhost:9001")
    typer.echo("  - https://white.mechgaia.org → http://localhost:9002")
    typer.echo("")
    typer.echo("Press Ctrl+C to stop the tunnel")
    typer.echo("")

    # Run cloudflared (this will block until Ctrl+C)
    try:
        subprocess.run(
            ["cloudflared", "tunnel", "--config", str(config_path), "run", tunnel_id],
            check=True,
        )
    except KeyboardInterrupt:
        typer.echo("\n\nStopping cloudflared tunnel...")
    except FileNotFoundError:
        typer.echo(
            "Error: cloudflared not found. Please install cloudflared.", err=True
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error: cloudflared exited with code {e.returncode}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    app()
