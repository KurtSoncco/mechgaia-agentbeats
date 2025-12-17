#!/usr/bin/env python3
"""Enhanced report generator for MechGAIA benchmark results."""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import typer

from src.mechgaia_env.database import BenchmarkDatabase
from src.mechgaia_env.statistics import aggregate_scores

app = typer.Typer()


def get_level_metrics(level: str) -> Dict[str, List[str]]:
    """Get the relevant metrics for each level."""
    metrics = {
        "A": {
            "primary": "correctness",
            "secondary": [
                "technical_accuracy",
                "conceptual_clarity",
                "distractor_analysis",
                "reasoning_quality",
                "overall_score",
            ],
        },
        "B": {
            "primary": "correctness",
            "secondary": [
                "value_tolerance",
                "unit_consistency",
                "code_execution",
                "mej_technical_accuracy",
                "mej_mathematical_rigor",
                "mej_problem_solving_approach",
                "mej_engineering_judgment",
                "mej_overall_score",
            ],
        },
        "C": {
            "primary": "overall_score",
            "secondary": [
                "technical_accuracy",
                "safety_constraint_awareness",
                "reasoning_quality",
                "engineering_judgment",
            ],
        },
        "D": {
            "primary": "overall_score",
            "secondary": [
                "technical_accuracy",
                "multi_step_coordination",
                "system_constraint_awareness",
                "engineering_judgment",
            ],
        },
    }
    return metrics.get(level, {"primary": "overall_score", "secondary": []})


def calculate_success_rate(scores: List[float], threshold: float = 0.6) -> float:
    """Calculate success rate based on threshold."""
    if not scores:
        return 0.0
    return sum(1 for s in scores if s >= threshold) / len(scores)


def format_score(value: float | None) -> str:
    """Format score value for display."""
    if value is None:
        return "N/A"
    return f"{value:.3f}"


def format_percentage(value: float) -> str:
    """Format percentage value."""
    return f"{value * 100:.1f}%"


def generate_level_section(
    level: str,
    task_results: Dict[str, Dict[str, Any]],
    db: BenchmarkDatabase,
) -> str:
    """Generate markdown section for a specific level."""
    metrics_config = get_level_metrics(level)
    primary_key = metrics_config["primary"]
    secondary_keys = metrics_config["secondary"]

    lines = [f"## Level {level} Tasks\n"]

    # Get task names
    tasks = db.get_tasks_by_level(level)
    task_names = {t["id"]: t.get("title", t.get("topic", t["id"])) for t in tasks}

    # Overall statistics table
    lines.append("### Overall Statistics\n")
    lines.append("| Task | Model | Primary Score | Success Rate | N | CI (95%) |\n")
    lines.append("|------|-------|---------------|--------------|---|----------|\n")

    for key in sorted(task_results.keys()):
        result = task_results[key]
        task_id = result.get("task_id", key.split("_")[0] if "_" in key else key)
        stats = result.get("statistics", {})
        primary_scores = result.get("scores", {}).get(primary_key, [])
        success_rate = calculate_success_rate(primary_scores)
        mean = stats.get("mean", 0.0)
        ci_lower = stats.get("ci_lower", 0.0)
        ci_upper = stats.get("ci_upper", 0.0)
        n = stats.get("n", 0)

        task_name = task_names.get(task_id, task_id)
        model_name = result.get("model_name", "unknown")

        lines.append(
            f"| {task_name} | {model_name} | {format_score(mean)} | "
            f"{format_percentage(success_rate)} | {n} | "
            f"[{format_score(ci_lower)}, {format_score(ci_upper)}] |\n"
        )

    # Detailed metrics breakdown
    if secondary_keys:
        lines.append("\n### Detailed Metrics Breakdown\n")
        header = "| Task | Model | " + " | ".join(secondary_keys) + " |\n"
        lines.append(header)
        lines.append(
            "|------|-------|" + "|".join(["---"] * len(secondary_keys)) + "|\n"
        )

        for task_id in sorted(task_results.keys()):
            result = task_results[task_id]
            all_scores = result.get("all_scores", [])
            model_name = result.get("model_name", "unknown")
            task_name = task_names.get(task_id, task_id)

            # Calculate mean for each secondary metric
            metric_values = []
            for metric_key in secondary_keys:
                values = [
                    s.get(metric_key)
                    for s in all_scores
                    if isinstance(s, dict) and s.get(metric_key) is not None
                ]
                if values:
                    mean_val = sum(values) / len(values)
                    metric_values.append(format_score(mean_val))
                else:
                    metric_values.append("N/A")

            lines.append(
                f"| {task_name} | {model_name} | " + " | ".join(metric_values) + " |\n"
            )

    return "".join(lines)


@app.command()
def generate(
    output_dir: str = typer.Option(
        "results", "--output", "-o", help="Output directory for reports"
    ),
    db_path: str = typer.Option(None, "--db-path", help="Database path"),
):
    """Generate comprehensive markdown report with all metrics."""
    db = BenchmarkDatabase(db_path) if db_path else BenchmarkDatabase()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    typer.echo("Generating comprehensive report...")

    # Get all evaluations
    evaluations = db.get_evaluations()

    if not evaluations:
        typer.echo("No evaluations found in database.", err=True)
        raise typer.Exit(1)

    # Group by level, task, and model
    level_task_model_data: Dict[str, Dict[str, Dict[str, List[Dict]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )

    for eval_dict in evaluations:
        task_instance_id = eval_dict["task_instance_id"]
        model_name = eval_dict["model_name"]

        # Get task_id and level from instance
        instances = db.get_task_instances()
        instance = next((i for i in instances if i["id"] == task_instance_id), None)
        if not instance:
            continue

        task_id = instance["task_id"]
        level = instance["level"]

        scores = eval_dict.get("scores", {})
        if isinstance(scores, str):
            scores = json.loads(scores)

        level_task_model_data[level][task_id][model_name].append(scores)

    # Process each level
    report_lines = [
        "# MechGAIA Benchmark Results\n",
        "Comprehensive evaluation report with detailed metrics across all task levels.\n",
        "---\n",
    ]

    # Summary across all levels
    report_lines.append("## Executive Summary\n")
    report_lines.append(
        "| Level | Tasks | Instances | Avg Primary Score | Avg Success Rate |\n"
    )
    report_lines.append(
        "|-------|-------|-----------|-------------------|------------------|\n"
    )

    for level in ["A", "B", "C", "D"]:
        if level not in level_task_model_data:
            continue

        level_data = level_task_model_data[level]
        metrics_config = get_level_metrics(level)
        primary_key = metrics_config["primary"]

        all_primary_scores = []
        total_instances = 0

        for task_id, model_data in level_data.items():
            for model_name, scores_list in model_data.items():
                for scores in scores_list:
                    if primary_key in scores and scores[primary_key] is not None:
                        all_primary_scores.append(scores[primary_key])
                    total_instances += 1

        if all_primary_scores:
            avg_score = sum(all_primary_scores) / len(all_primary_scores)
            success_rate = calculate_success_rate(all_primary_scores)
            num_tasks = len(level_data)
            report_lines.append(
                f"| {level} | {num_tasks} | {total_instances} | "
                f"{format_score(avg_score)} | {format_percentage(success_rate)} |\n"
            )

    report_lines.append("\n---\n\n")

    # Detailed sections for each level
    for level in ["A", "B", "C", "D"]:
        if level not in level_task_model_data:
            continue

        level_data = level_task_model_data[level]
        metrics_config = get_level_metrics(level)
        primary_key = metrics_config["primary"]

        # Prepare task results
        task_results: Dict[str, Dict[str, Any]] = {}

        for task_id, model_data in level_data.items():
            for model_name, scores_list in model_data.items():
                if task_id not in task_results:
                    task_results[task_id] = {
                        "task_id": task_id,
                        "model_name": model_name,
                        "scores": defaultdict(list),
                        "all_scores": [],
                    }

                for scores in scores_list:
                    task_results[task_id]["all_scores"].append(scores)
                    for score_key, score_value in scores.items():
                        if score_value is not None:
                            task_results[task_id]["scores"][score_key].append(
                                score_value
                            )

        # Aggregate primary scores
        for key, result in task_results.items():
            primary_scores = result["scores"][primary_key]
            if primary_scores:
                aggregated = aggregate_scores(
                    [{"scores": {primary_key: s}} for s in primary_scores],
                    score_key=primary_key,
                )
                result["statistics"] = aggregated

        # Generate level section
        report_lines.append(generate_level_section(level, task_results, db))
        report_lines.append("\n---\n\n")

    # Write report
    md_path = output_path / "report.md"
    with open(md_path, "w") as f:
        f.write("".join(report_lines))

    typer.echo(f"✓ Generated comprehensive markdown report: {md_path}")
    typer.echo("Report generation complete!")


if __name__ == "__main__":
    app()
