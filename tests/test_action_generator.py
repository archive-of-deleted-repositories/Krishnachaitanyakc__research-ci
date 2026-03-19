"""Tests for the action generator."""

import yaml
import pytest

from autoresearch_ci.config import CIConfig
from autoresearch_ci.action_generator import ActionGenerator


class TestActionGenerator:
    def setup_method(self):
        self.gen = ActionGenerator()

    def test_generates_valid_yaml(self):
        config = CIConfig()
        workflow = self.gen.generate_workflow(config)
        parsed = yaml.safe_load(workflow)
        assert isinstance(parsed, dict)
        assert "name" in parsed
        assert "jobs" in parsed

    def test_uses_configured_runner(self):
        config = CIConfig(runner="self-hosted-gpu")
        workflow = self.gen.generate_workflow(config)
        assert "self-hosted-gpu" in workflow

    def test_uses_configured_python_version(self):
        config = CIConfig(python_version="3.12")
        workflow = self.gen.generate_workflow(config)
        assert "3.12" in workflow

    def test_includes_prepare_command(self):
        config = CIConfig(prepare_command="python my_prepare.py")
        workflow = self.gen.generate_workflow(config)
        assert "my_prepare.py" in workflow

    def test_includes_train_command(self):
        config = CIConfig(train_command="python my_train.py --epochs 10")
        workflow = self.gen.generate_workflow(config)
        assert "my_train.py" in workflow

    def test_timeout_from_budget(self):
        config = CIConfig(time_budget_hours=3.0)
        workflow = self.gen.generate_workflow(config)
        assert "timeout-minutes: 180" in workflow

    def test_artifact_retention(self):
        config = CIConfig(artifact_retention_days=14)
        workflow = self.gen.generate_workflow(config)
        assert "retention-days: 14" in workflow

    def test_branch_triggers(self):
        config = CIConfig(experiment_branch="exp", base_branch="main")
        workflow = self.gen.generate_workflow(config)
        assert "exp" in workflow
        assert "main" in workflow

    def test_github_comment_notification(self):
        config = CIConfig(notify=["github_comment"])
        workflow = self.gen.generate_workflow(config)
        assert "Comment on PR" in workflow

    def test_no_comment_without_notify(self):
        config = CIConfig(notify=[])
        workflow = self.gen.generate_workflow(config)
        assert "Comment on PR" not in workflow

    def test_extra_pip_packages(self):
        config = CIConfig(extra_pip_packages=["torch", "transformers"])
        workflow = self.gen.generate_workflow(config)
        assert "torch" in workflow
        assert "transformers" in workflow
