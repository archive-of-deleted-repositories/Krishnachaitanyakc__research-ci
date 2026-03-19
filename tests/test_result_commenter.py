"""Tests for the result commenter."""

import pytest

from autoresearch_ci.result_commenter import ResultCommenter


class TestResultCommenter:
    def setup_method(self):
        self.commenter = ResultCommenter()

    def test_format_basic_results(self):
        results = {"metric_name": "accuracy", "metric_value": 0.95}
        md = self.commenter.format_results_as_markdown(results)
        assert "accuracy" in md
        assert "0.95" in md
        assert "Experiment Results" in md

    def test_format_with_config(self):
        results = {
            "metric_name": "loss",
            "metric_value": 0.123,
            "config": {"lr": 0.001, "epochs": 10},
        }
        md = self.commenter.format_results_as_markdown(results)
        assert "Configuration" in md
        assert "lr" in md
        assert "epochs" in md

    def test_format_with_history(self):
        results = {
            "metric_name": "loss",
            "metric_value": 0.1,
            "history": [1.0, 0.8, 0.5, 0.3, 0.1],
        }
        md = self.commenter.format_results_as_markdown(results)
        assert "Training Progress" in md
        assert "```" in md

    def test_generate_pr_comment_no_baseline(self):
        results = {"metric_name": "f1", "metric_value": 0.85}
        md = self.commenter.generate_pr_comment(results)
        assert "f1" in md
        assert "0.85" in md

    def test_generate_pr_comment_with_baseline(self):
        results = {"metric_name": "accuracy", "metric_value": 0.95}
        baseline = {"metric_name": "accuracy", "metric_value": 0.90}
        md = self.commenter.generate_pr_comment(results, baseline)
        assert "Baseline" in md
        assert "improvement" in md

    def test_generate_pr_comment_regression(self):
        results = {"metric_name": "accuracy", "metric_value": 0.80}
        baseline = {"metric_name": "accuracy", "metric_value": 0.90}
        md = self.commenter.generate_pr_comment(results, baseline)
        assert "regression" in md

    def test_ascii_chart(self):
        values = [1.0, 0.8, 0.6, 0.4, 0.2]
        chart = self.commenter._ascii_chart(values)
        assert "```" in chart
        assert "#" in chart

    def test_ascii_chart_empty(self):
        chart = self.commenter._ascii_chart([])
        assert "no data" in chart
