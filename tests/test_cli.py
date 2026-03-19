"""Tests for the CI CLI."""

import json
import os
import tempfile

from click.testing import CliRunner

from autoresearch_ci.cli import cli


class TestCLI:
    def setup_method(self):
        self.runner = CliRunner()

    def test_init_creates_workflow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, ".github/workflows")
            result = self.runner.invoke(cli, ["init", "--output-dir", output_dir])
            assert result.exit_code == 0
            assert os.path.isfile(os.path.join(output_dir, "autoresearch.yml"))

    def test_init_with_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "ci-config.yaml")
            with open(config_path, "w") as f:
                f.write("runner: self-hosted-gpu\ntime_budget_hours: 4\n")
            output_dir = os.path.join(tmpdir, "workflows")
            result = self.runner.invoke(cli, ["init", "--config", config_path, "--output-dir", output_dir])
            assert result.exit_code == 0
            with open(os.path.join(output_dir, "autoresearch.yml")) as f:
                content = f.read()
            assert "self-hosted-gpu" in content

    def test_comment_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = os.path.join(tmpdir, "results.json")
            with open(results_path, "w") as f:
                json.dump({"metric_name": "accuracy", "metric_value": 0.95}, f)
            result = self.runner.invoke(cli, ["comment", results_path])
            assert result.exit_code == 0
            assert "accuracy" in result.output
            assert "0.95" in result.output

    def test_comment_with_baseline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = os.path.join(tmpdir, "results.json")
            baseline_path = os.path.join(tmpdir, "baseline.json")
            with open(results_path, "w") as f:
                json.dump({"metric_name": "accuracy", "metric_value": 0.95}, f)
            with open(baseline_path, "w") as f:
                json.dump({"metric_name": "accuracy", "metric_value": 0.90}, f)
            result = self.runner.invoke(cli, ["comment", results_path, "--baseline", baseline_path])
            assert result.exit_code == 0
            assert "Baseline" in result.output

    def test_validate_valid_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            with open(config_path, "w") as f:
                f.write("runner: ubuntu-latest\ntime_budget_hours: 2\n")
            result = self.runner.invoke(cli, ["validate", config_path])
            assert result.exit_code == 0
            assert "valid" in result.output.lower()

    def test_validate_invalid_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            with open(config_path, "w") as f:
                f.write("runner: ubuntu-latest\ntime_budget_hours: -1\n")
            result = self.runner.invoke(cli, ["validate", config_path])
            assert result.exit_code != 0

    def test_leaderboard_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(cli, ["leaderboard", tmpdir])
            # tmpdir won't be a git repo, so it should handle gracefully
            assert result.exit_code == 0
