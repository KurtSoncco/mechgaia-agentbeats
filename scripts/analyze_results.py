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

    # Group results by level for per-level analysis
    level_results = {"A": [], "B": [], "C": [], "D": []}

    for result in results:
        task_id = result["task_id"]
        # Determine level from task_id or database
        task = next(
            (
                t
                for t in db.get_tasks_by_level("A")
                + db.get_tasks_by_level("B")
                + db.get_tasks_by_level("C")
                + db.get_tasks_by_level("D")
                if t["id"] == task_id
            ),
            None,
        )
        if task:
            level = task["level"]
            level_results[level].append(result)

    # Generate markdown report
    md_path = output_path / "report.md"
    with open(md_path, "w") as f:
        f.write("# MechGAIA Benchmark Results\n")
        f.write(
            "Comprehensive evaluation report with detailed metrics across all task levels.\n"
        )
        f.write("---\n\n")

        # Executive summary by level
        f.write("## Executive Summary\n")
        f.write(
            "| Level | Tasks | Instances | Avg Primary Score | Avg Success Rate |\n"
        )
        f.write(
            "|-------|-------|-----------|-------------------|------------------|\n"
        )

        for level in ["A", "B", "C", "D"]:
            level_data = level_results[level]
            if not level_data:
                continue

            num_tasks = len(set(r["task_id"] for r in level_data))
            total_instances = sum(r["statistics"]["n"] for r in level_data)
            avg_score = (
                sum(r["statistics"]["mean"] for r in level_data) / len(level_data)
                if level_data
                else 0.0
            )
            # Success rate: percentage with score >= 0.5
            success_count = sum(1 for r in level_data if r["statistics"]["mean"] >= 0.5)
            success_rate = (
                (success_count / len(level_data) * 100) if level_data else 0.0
            )

            f.write(
                f"| {level} | {num_tasks} | {total_instances} | "
                f"{avg_score:.3f} | {success_rate:.1f}% |\n"
            )

        f.write("\n---\n\n")

        # Per-level detailed breakdowns
        for level in ["A", "B", "C", "D"]:
            level_data = level_results[level]
            if not level_data:
                continue

            f.write(f"## Level {level} Tasks\n")
            f.write("### Overall Statistics\n")
            f.write("| Task | Model | Primary Score | Success Rate | N | CI (95%) |\n")
            f.write("|------|-------|---------------|--------------|---|----------|\n")

            for result in level_data:
                stats = result["statistics"]
                task_id = result["task_id"]
                model_name = result["model_name"]
                success_rate = (1.0 if stats["mean"] >= 0.5 else 0.0) * 100

                f.write(
                    f"| {task_id} | {model_name} | {stats['mean']:.3f} | "
                    f"{success_rate:.1f}% | {stats['n']} | "
                    f"[{stats['ci_lower']:.3f}, {stats['ci_upper']:.3f}] |\n"
                )

            # Get detailed metrics for this level
            level_evaluations = [
                e
                for e in evaluations
                if any(
                    i["id"] == e["task_instance_id"]
                    and next(
                        (
                            t
                            for t in db.get_tasks_by_level(level)
                            if t["id"] == i["task_id"]
                        ),
                        None,
                    )
                    for i in db.get_task_instances()
                )
            ]

            if level_evaluations:
                # Extract all score keys from evaluations
                all_score_keys = set()
                for eval_dict in level_evaluations:
                    scores = eval_dict.get("scores", {})
                    if isinstance(scores, str):
                        scores = json.loads(scores)
                    all_score_keys.update(scores.keys())

                # Show detailed metrics breakdown
                if all_score_keys:
                    f.write("\n### Detailed Metrics Breakdown\n")
                    # Get unique tasks for header
                    task_ids = sorted(set(r["task_id"] for r in level_data))
                    f.write("| Task | Model | ")
                    f.write(" | ".join(sorted(all_score_keys)) + " |\n")
                    f.write(
                        "|------|-------|"
                        + "|".join(["---"] * len(all_score_keys))
                        + "|\n"
                    )

                    for result in level_data:
                        task_id = result["task_id"]
                        model_name = result["model_name"]

                        # Get evaluation for this task/model
                        task_eval = next(
                            (
                                e
                                for e in level_evaluations
                                if next(
                                    (
                                        i
                                        for i in db.get_task_instances()
                                        if i["id"] == e["task_instance_id"]
                                        and i["task_id"] == task_id
                                    ),
                                    None,
                                )
                                and e["model_name"] == model_name
                            ),
                            None,
                        )

                        if task_eval:
                            scores = task_eval.get("scores", {})
                            if isinstance(scores, str):
                                scores = json.loads(scores)

                            f.write(f"| {task_id} | {model_name} | ")
                            score_values = []
                            for key in sorted(all_score_keys):
                                val = scores.get(key, 0.0)
                                if isinstance(val, (int, float)):
                                    score_values.append(f"{val:.3f}")
                                else:
                                    score_values.append(str(val))
                            f.write(" | ".join(score_values) + " |\n")

            f.write("\n---\n\n")

        # Summary statistics table
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
