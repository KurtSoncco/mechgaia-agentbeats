"""Statistical analysis for benchmark results."""

import json
from typing import Any, Dict, List, Tuple

import numpy as np

from src.mechgaia_env.config import config


def bootstrap_confidence_interval(
    scores: List[float], confidence_level: float = 0.95, n_iterations: int = 1000
) -> Tuple[float, float, float]:
    """Compute bootstrap confidence interval for scores.

    Args:
        scores: List of scores
        confidence_level: Confidence level (default 0.95)
        n_iterations: Number of bootstrap iterations

    Returns:
        Tuple of (mean, lower_bound, upper_bound)
    """
    if not scores:
        return 0.0, 0.0, 0.0

    scores_array = np.array(scores)
    mean = np.mean(scores_array)

    # Bootstrap sampling
    bootstrap_means = []
    n = len(scores)

    for _ in range(n_iterations):
        sample = np.random.choice(scores_array, size=n, replace=True)
        bootstrap_means.append(np.mean(sample))

    bootstrap_means = np.array(bootstrap_means)

    # Calculate percentiles
    alpha = 1 - confidence_level
    lower = np.percentile(bootstrap_means, 100 * alpha / 2)
    upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))

    return mean, lower, upper


def aggregate_scores(
    evaluations: List[Dict[str, Any]], score_key: str = "correctness"
) -> Dict[str, Any]:
    """Aggregate scores from multiple evaluations.

    Args:
        evaluations: List of evaluation dictionaries
        score_key: Key to extract score from each evaluation

    Returns:
        Dictionary with aggregated statistics
    """
    scores = []
    for eval_dict in evaluations:
        scores_dict = eval_dict.get("scores", {})
        if isinstance(scores_dict, str):
            scores_dict = json.loads(scores_dict)
        score = scores_dict.get(score_key)
        if score is not None:
            scores.append(float(score))

    if not scores:
        return {"mean": 0.0, "std": 0.0, "n": 0, "ci_lower": 0.0, "ci_upper": 0.0}

    mean, ci_lower, ci_upper = bootstrap_confidence_interval(
        scores,
        confidence_level=config.confidence_level,
        n_iterations=config.bootstrap_iterations,
    )

    return {
        "mean": float(mean),
        "std": float(np.std(scores)),
        "n": len(scores),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "min": float(np.min(scores)),
        "max": float(np.max(scores)),
    }


def statistical_significance_test(
    scores1: List[float], scores2: List[float], alpha: float = 0.05
) -> Dict[str, Any]:
    """Perform statistical significance test between two score distributions.

    Uses bootstrap method for confidence interval comparison.

    Args:
        scores1: First set of scores
        scores2: Second set of scores
        alpha: Significance level

    Returns:
        Dictionary with test results
    """
    if not scores1 or not scores2:
        return {
            "significant": False,
            "p_value": 1.0,
            "mean_diff": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
        }

    # Bootstrap difference distribution
    n_iterations = config.bootstrap_iterations
    differences = []

    for _ in range(n_iterations):
        sample1 = np.random.choice(scores1, size=len(scores1), replace=True)
        sample2 = np.random.choice(scores2, size=len(scores2), replace=True)
        diff = np.mean(sample1) - np.mean(sample2)
        differences.append(diff)

    differences = np.array(differences)
    mean_diff = np.mean(differences)

    # Calculate confidence interval
    ci_lower = np.percentile(differences, 100 * alpha / 2)
    ci_upper = np.percentile(differences, 100 * (1 - alpha / 2))

    # Significance: CI does not contain zero
    significant = not (ci_lower <= 0 <= ci_upper)

    # Approximate p-value (proportion of differences >= 0 if mean_diff > 0)
    if mean_diff > 0:
        p_value = np.mean(differences <= 0)
    else:
        p_value = np.mean(differences >= 0)

    return {
        "significant": significant,
        "p_value": float(p_value),
        "mean_diff": float(mean_diff),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
    }


def generate_jsonl_report(evaluations: List[Dict[str, Any]], output_path: str):
    """Generate JSONL report from evaluations.

    Args:
        evaluations: List of evaluation dictionaries
        output_path: Path to output JSONL file
    """
    with open(output_path, "w") as f:
        for eval_dict in evaluations:
            # Flatten evaluation for JSONL
            record = {
                "task_instance_id": eval_dict.get("task_instance_id"),
                "model_name": eval_dict.get("model_name"),
                "scores": eval_dict.get("scores", {}),
                "timestamp": eval_dict.get("timestamp"),
            }
            f.write(json.dumps(record) + "\n")
