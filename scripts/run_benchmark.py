#!/usr/bin/env python3
"""Convenience script to run the complete benchmark workflow."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import typer

from src.launcher import launch_remote_evaluation

app = typer.Typer()


@app.command()
def run(
    level: str = typer.Option(
        None, "--level", "-l", help="Single task level to evaluate (A, B, or C)"
    ),
    levels: str = typer.Option(
        None, "--levels", help="Comma-separated levels to evaluate (e.g., 'A,B,C')"
    ),
    green_url: str = typer.Option(
        "http://localhost:9001", "--green-url", help="Green agent URL"
    ),
    white_url: str = typer.Option(
        "http://localhost:9002", "--white-url", help="White agent URL"
    ),
    model_name: str = typer.Option(
        "openai/gpt-4o", "--model", help="Model name for tracking"
    ),
):
    """Run benchmark evaluation.

    Make sure both green and white agents are running before calling this.

    Examples:
        # Evaluate Level A tasks
        python scripts/run_benchmark.py --level A

        # Evaluate all levels
        python scripts/run_benchmark.py --levels A,B,C

        # Evaluate with custom URLs
        python scripts/run_benchmark.py --level B --green-url http://localhost:9001 --white-url http://localhost:9002
    """
    typer.echo("Starting benchmark evaluation...")
    typer.echo(f"  Green agent: {green_url}")
    typer.echo(f"  White agent: {white_url}")

    levels_list = None
    if levels:
        levels_list = [l.strip() for l in levels.split(",")]
        typer.echo(f"  Levels: {', '.join(levels_list)}")
    else:
        typer.echo(f"  Level: {level or 'All'}")

    typer.echo(f"  Model: {model_name}")

    asyncio.run(
        launch_remote_evaluation(
            green_url=green_url,
            white_url=white_url,
            level=level,
            levels=levels_list,
            model_name=model_name,
        )
    )

    typer.echo("✓ Benchmark evaluation complete!")
    typer.echo("Run 'python scripts/analyze_results.py' to generate reports.")


if __name__ == "__main__":
    app()

