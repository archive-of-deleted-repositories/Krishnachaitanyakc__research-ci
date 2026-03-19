"""Statistical significance testing for experiment comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class SignificanceResult:
    """Result of a significance test between two experiment branches."""
    t_statistic: float
    p_value: float
    confidence_interval: Tuple[float, float]
    is_significant: bool
    mean_a: float
    mean_b: float
    effect_size: float


def compute_significance(
    values_a: List[float],
    values_b: List[float],
    alpha: float = 0.05,
) -> SignificanceResult:
    """Compute t-test between two sets of experiment results.

    Args:
        values_a: Metric values from experiment branch A.
        values_b: Metric values from experiment branch B.
        alpha: Significance level (default 0.05).

    Returns:
        SignificanceResult with t-statistic, p-value, confidence interval.
    """
    from scipy import stats

    if len(values_a) < 2 or len(values_b) < 2:
        raise ValueError("Each group must have at least 2 values for a t-test")

    t_stat, p_value = stats.ttest_ind(values_a, values_b)

    mean_a = sum(values_a) / len(values_a)
    mean_b = sum(values_b) / len(values_b)
    diff = mean_b - mean_a

    pooled_se = (
        (sum((x - mean_a) ** 2 for x in values_a) +
         sum((x - mean_b) ** 2 for x in values_b)) /
        (len(values_a) + len(values_b) - 2)
    ) ** 0.5 * (1 / len(values_a) + 1 / len(values_b)) ** 0.5

    df = len(values_a) + len(values_b) - 2
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    ci = (diff - t_crit * pooled_se, diff + t_crit * pooled_se)

    pooled_std = (
        (sum((x - mean_a) ** 2 for x in values_a) +
         sum((x - mean_b) ** 2 for x in values_b)) /
        (len(values_a) + len(values_b) - 2)
    ) ** 0.5
    effect_size = diff / pooled_std if pooled_std != 0 else 0.0

    return SignificanceResult(
        t_statistic=float(t_stat),
        p_value=float(p_value),
        confidence_interval=ci,
        is_significant=p_value < alpha,
        mean_a=mean_a,
        mean_b=mean_b,
        effect_size=effect_size,
    )


def format_significance_comment(result: SignificanceResult, metric_name: str = "metric") -> str:
    """Format a significance result as markdown for a PR comment."""
    status = "SIGNIFICANT" if result.is_significant else "NOT SIGNIFICANT"
    lines = [
        "### Statistical Significance\n",
        f"| Statistic | Value |",
        f"|-----------|-------|",
        f"| t-statistic | {result.t_statistic:.4f} |",
        f"| p-value | {result.p_value:.6f} |",
        f"| Result | **{status}** |",
        f"| Mean A ({metric_name}) | {result.mean_a:.4f} |",
        f"| Mean B ({metric_name}) | {result.mean_b:.4f} |",
        f"| Effect size (Cohen's d) | {result.effect_size:.4f} |",
        f"| 95% CI of difference | [{result.confidence_interval[0]:.4f}, {result.confidence_interval[1]:.4f}] |",
    ]
    return "\n".join(lines)
