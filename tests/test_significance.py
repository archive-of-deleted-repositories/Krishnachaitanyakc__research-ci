"""Tests for statistical significance module."""

import pytest

from research_ci.significance import (
    compute_significance,
    format_significance_comment,
    SignificanceResult,
)


class TestComputeSignificance:
    def test_significant_difference(self):
        values_a = [1.0, 1.1, 1.0, 0.9, 1.0]
        values_b = [2.0, 2.1, 2.0, 1.9, 2.0]
        result = compute_significance(values_a, values_b)
        assert result.is_significant
        assert result.p_value < 0.05
        assert result.mean_b > result.mean_a

    def test_not_significant(self):
        values_a = [1.0, 2.0, 3.0, 4.0, 5.0]
        values_b = [1.1, 2.1, 2.9, 3.9, 5.1]
        result = compute_significance(values_a, values_b)
        assert not result.is_significant
        assert result.p_value > 0.05

    def test_requires_min_two_values(self):
        with pytest.raises(ValueError):
            compute_significance([1.0], [2.0, 3.0])
        with pytest.raises(ValueError):
            compute_significance([1.0, 2.0], [3.0])

    def test_confidence_interval(self):
        values_a = [1.0, 1.1, 1.0, 0.9, 1.0]
        values_b = [2.0, 2.1, 2.0, 1.9, 2.0]
        result = compute_significance(values_a, values_b)
        ci_low, ci_high = result.confidence_interval
        assert ci_low < ci_high
        diff = result.mean_b - result.mean_a
        assert ci_low <= diff <= ci_high

    def test_effect_size_computed(self):
        values_a = [1.0, 1.1, 0.9, 1.0, 1.0]
        values_b = [2.0, 2.1, 1.9, 2.0, 2.0]
        result = compute_significance(values_a, values_b)
        assert result.effect_size > 0

    def test_custom_alpha(self):
        values_a = [1.0, 1.5, 2.0, 1.8, 1.2]
        values_b = [1.5, 2.0, 2.5, 2.3, 1.7]
        result_strict = compute_significance(values_a, values_b, alpha=0.001)
        result_lenient = compute_significance(values_a, values_b, alpha=0.5)
        # Same p-value, different significance threshold
        assert result_strict.p_value == result_lenient.p_value


class TestFormatSignificanceComment:
    def test_format_significant(self):
        result = SignificanceResult(
            t_statistic=-5.0,
            p_value=0.001,
            confidence_interval=(0.5, 1.5),
            is_significant=True,
            mean_a=1.0,
            mean_b=2.0,
            effect_size=1.5,
        )
        md = format_significance_comment(result, "accuracy")
        assert "SIGNIFICANT" in md
        assert "accuracy" in md
        assert "t-statistic" in md
        assert "p-value" in md

    def test_format_not_significant(self):
        result = SignificanceResult(
            t_statistic=-0.5,
            p_value=0.6,
            confidence_interval=(-0.5, 0.8),
            is_significant=False,
            mean_a=1.0,
            mean_b=1.1,
            effect_size=0.1,
        )
        md = format_significance_comment(result)
        assert "NOT SIGNIFICANT" in md
