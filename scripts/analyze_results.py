#!/usr/bin/env python3
"""CLI script to analyze evaluation results and generate reports."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import typer

from src.mechgaia_env.database import BenchmarkDatabase
from src.mechgaia_env.statistics import aggregate_scores, generate_jsonl_report

app = typer.Typer()


@app.command()
def analyze(
    output_dir: str = typer.Option(
        "results", "--output", "-o", help="Output directory for reports"
    ),
    db_path: str = typer.Option(None, "--db-path", help="Database path"),
    score_key: str = typer.Option(
        "correctness", "--score-key", help="Score key to aggregate"
    ),
):
    """Analyze evaluation results and generate reports."""
    db = BenchmarkDatabase(db_path) if db_path else BenchmarkDatabase()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    typer.echo("Analyzing evaluation results...")

    # Get all evaluations
    evaluations = db.get_evaluations()

    if not evaluations:
        typer.echo("No evaluations found in database.", err=True)
        raise typer.Exit(1)

    # Group by task and model
    task_model_scores = {}

    for eval_dict in evaluations:
        task_instance_id = eval_dict["task_instance_id"]
        model_name = eval_dict["model_name"]

        # Get task_id from instance
        instances = db.get_task_instances()
        instance = next((i for i in instances if i["id"] == task_instance_id), None)
        if not instance:
            continue

        task_id = instance["task_id"]
        key = (task_id, model_name)

        if key not in task_model_scores:
            task_model_scores[key] = []

        scores = eval_dict.get("scores", {})
        if isinstance(scores, str):
            scores = json.loads(scores)

        score = scores.get(score_key)
        if score is not None:
            task_model_scores[key].append(score)

    # Aggregate scores
    results = []
    for (task_id, model_name), scores in task_model_scores.items():
        aggregated = aggregate_scores(
            [{"scores": {score_key: s}} for s in scores], score_key=score_key
        )

        results.append(
            {"task_id": task_id, "model_name": model_name, "statistics": aggregated}
        )

        # Update database
        result_id = f"{task_id}_{model_name}"
        db.update_result(
            result_id=result_id,
            task_id=task_id,
            model_name=model_name,
            mean_score=aggregated["mean"],
            ci_lower=aggregated["ci_lower"],
            ci_upper=aggregated["ci_upper"],
            n_samples=aggregated["n"],
        )

    # Generate JSONL report
    jsonl_path = output_path / "results.jsonl"
    generate_jsonl_report(evaluations, str(jsonl_path))
    typer.echo(f"✓ Generated JSONL report: {jsonl_path}")

    # Generate markdown report
    md_path = output_path / "report.md"
    with open(md_path, "w") as f:
        f.write("# MechGAIA Benchmark Results\n\n")
        f.write(f"Score Key: `{score_key}`\n\n")
        f.write("## Summary Statistics\n\n")
        f.write("| Task ID | Model | Mean | CI Lower | CI Upper | N |\n")
        f.write("|---------|-------|------|----------|----------|---|\n")

        for result in results:
            stats = result["statistics"]
            f.write(
                f"| {result['task_id']} | {result['model_name']} | "
                f"{stats['mean']:.3f} | {stats['ci_lower']:.3f} | "
                f"{stats['ci_upper']:.3f} | {stats['n']} |\n"
            )

    typer.echo(f"✓ Generated markdown report: {md_path}")
    typer.echo("Analysis complete!")


if __name__ == "__main__":
    # Make analyze the default command
    import sys

    if len(sys.argv) == 1:
        sys.argv.append("analyze")
    app()
