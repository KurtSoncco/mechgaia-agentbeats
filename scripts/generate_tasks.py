#!/usr/bin/env python3
"""CLI script to generate and populate tasks in the database."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import typer

from src.mechgaia_env.database import BenchmarkDatabase
from src.mechgaia_env.task_generator import TaskGenerator

app = typer.Typer()


@app.command()
def generate(
    level: str = typer.Option(
        ..., "--level", "-l", help="Level to generate (A, B, C, or D)"
    ),
    num_tasks: int = typer.Option(
        5, "--num-tasks", "-n", help="Number of tasks to generate (ignored for Level D)"
    ),
    num_instances: int = typer.Option(
        10, "--num-instances", "-i", help="Number of instances per task"
    ),
    db_path: str = typer.Option(
        None, "--db-path", help="Database path (default: config default)"
    ),
    examples_dir: str = typer.Option(
        None,
        "--examples-dir",
        help="Directory containing Level D example JSON files (default: data/level_d/examples)",
    ),
):
    """Generate tasks for the specified level."""
    db = BenchmarkDatabase(db_path) if db_path else BenchmarkDatabase()
    generator = TaskGenerator(db)

    level_upper = level.upper()

    if level_upper == "A":
        typer.echo(f"Generating {num_tasks} Level {level} tasks...")
        generator.generate_level_a_tasks(num_tasks=num_tasks)
    elif level_upper == "B":
        typer.echo(f"Generating {num_tasks} Level {level} tasks...")
        generator.generate_level_b_tasks(num_tasks=num_tasks)
    elif level_upper == "C":
        typer.echo(f"Generating {num_tasks} Level {level} tasks...")
        generator.generate_level_c_tasks(num_tasks=num_tasks)
    elif level_upper == "D":
        typer.echo("Loading Level D tasks from JSON example files...")
        loaded_task_ids = generator.generate_level_d_tasks(examples_dir=examples_dir)
        if not loaded_task_ids:
            typer.echo("⚠ No Level D tasks found in examples directory.", err=True)
            raise typer.Exit(1)
        typer.echo(
            f"✓ Loaded {len(loaded_task_ids)} Level D tasks: {', '.join(loaded_task_ids)}"
        )
    else:
        typer.echo(f"Invalid level: {level}. Must be A, B, C, or D.", err=True)
        raise typer.Exit(1)

    if level_upper != "D":
        typer.echo(f"✓ Generated {num_tasks} Level {level} tasks")

    # Generate instances for each task
    tasks = db.get_tasks_by_level(level_upper)
    typer.echo(f"Generating {num_instances} instances per task...")

    for task in tasks:
        generator.generate_task_instances(task["id"], num_instances=num_instances)
        typer.echo(f"  ✓ Generated instances for {task['id']}")

    typer.echo(
        f"✓ Complete! Generated {len(tasks)} tasks with {num_instances} instances each"
    )


@app.command()
def list_tasks(
    level: str = typer.Option(
        None, "--level", "-l", help="Filter by level (A, B, C, or D)"
    ),
    db_path: str = typer.Option(None, "--db-path", help="Database path"),
):
    """List all tasks in the database."""
    db = BenchmarkDatabase(db_path) if db_path else BenchmarkDatabase()

    if level:
        tasks = db.get_tasks_by_level(level.upper())
        typer.echo(f"Tasks for Level {level.upper()}:")
    else:
        tasks_a = db.get_tasks_by_level("A")
        tasks_b = db.get_tasks_by_level("B")
        tasks_c = db.get_tasks_by_level("C")
        tasks_d = db.get_tasks_by_level("D")
        tasks = tasks_a + tasks_b + tasks_c + tasks_d
        typer.echo("All tasks:")

    for task in tasks:
        topic = task.get("topic", task.get("title", "Unknown"))
        typer.echo(f"  - {task['id']}: {topic} (Level {task['level']})")


if __name__ == "__main__":
    app()
