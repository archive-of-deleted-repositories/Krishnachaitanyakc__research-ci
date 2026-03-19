"""Tests for cost tracking module."""

import pytest

from research_ci.cost_tracker import (
    estimate_cost,
    parse_gpu_time_from_log,
    CostEntry,
    CostReport,
)


class TestEstimateCost:
    def test_modal_a100(self):
        cost = estimate_cost("modal", "A100", 1.0)
        assert cost == pytest.approx(3.73)

    def test_runpod_t4(self):
        cost = estimate_cost("runpod", "T4", 2.0)
        assert cost == pytest.approx(0.88)

    def test_multi_gpu(self):
        cost = estimate_cost("modal", "A100", 1.0, gpu_count=4)
        assert cost == pytest.approx(3.73 * 4)

    def test_unknown_provider(self):
        cost = estimate_cost("unknown_provider", "A100", 1.0)
        assert cost == 0.0

    def test_unknown_gpu(self):
        cost = estimate_cost("modal", "V100", 1.0)
        assert cost == 0.0

    def test_github_actions(self):
        cost = estimate_cost("github_actions", "ubuntu-latest", 1.0)
        assert cost == pytest.approx(0.008)


class TestParseGpuTime:
    def test_parse_hours(self):
        log = "Some output\nGPU time: 1.5 hours\nDone"
        assert parse_gpu_time_from_log(log) == pytest.approx(1.5)

    def test_parse_minutes(self):
        log = "Duration: 90 minutes"
        assert parse_gpu_time_from_log(log) == pytest.approx(1.5)

    def test_parse_seconds(self):
        log = "Elapsed: 3600 seconds"
        assert parse_gpu_time_from_log(log) == pytest.approx(1.0)

    def test_no_match(self):
        log = "Some random log output"
        assert parse_gpu_time_from_log(log) is None

    def test_parse_h_shorthand(self):
        log = "GPU time: 2.5h"
        assert parse_gpu_time_from_log(log) == pytest.approx(2.5)


class TestCostReport:
    def test_empty_report(self):
        report = CostReport()
        md = report.to_markdown()
        assert "No cost data" in md

    def test_report_with_entries(self):
        report = CostReport(entries=[
            CostEntry("modal", "A100", 1.0, 3.73, "exp1"),
            CostEntry("modal", "A100", 2.0, 7.46, "exp2"),
        ])
        assert report.total_cost == pytest.approx(11.19)
        assert report.total_gpu_hours == pytest.approx(3.0)
        md = report.to_markdown()
        assert "exp1" in md
        assert "exp2" in md
        assert "$11.19" in md
