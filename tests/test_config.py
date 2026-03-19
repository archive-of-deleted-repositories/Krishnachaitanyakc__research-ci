"""Tests for CI configuration."""

import pytest

from autoresearch_ci.config import CIConfig


class TestCIConfig:
    def test_default_values(self):
        config = CIConfig()
        assert config.runner == "ubuntu-latest"
        assert config.time_budget_hours == 2.0
        assert config.base_branch == "main"

    def test_from_yaml(self):
        yaml_str = """
runner: self-hosted-gpu
time_budget_hours: 4.0
experiment_branch: exp
base_branch: main
notify:
  - github_comment
  - slack_webhook
artifact_retention_days: 7
"""
        config = CIConfig.from_yaml(yaml_str)
        assert config.runner == "self-hosted-gpu"
        assert config.time_budget_hours == 4.0
        assert config.experiment_branch == "exp"
        assert "slack_webhook" in config.notify
        assert config.artifact_retention_days == 7

    def test_from_yaml_partial(self):
        yaml_str = "runner: ubuntu-latest\n"
        config = CIConfig.from_yaml(yaml_str)
        assert config.runner == "ubuntu-latest"
        assert config.time_budget_hours == 2.0  # default

    def test_from_yaml_invalid(self):
        with pytest.raises(ValueError):
            CIConfig.from_yaml("just a string")

    def test_to_yaml(self):
        config = CIConfig(runner="self-hosted-gpu", time_budget_hours=3.0)
        yaml_str = config.to_yaml()
        assert "self-hosted-gpu" in yaml_str
        assert "3.0" in yaml_str

    def test_roundtrip(self):
        original = CIConfig(runner="gpu-runner", time_budget_hours=5.0,
                            experiment_branch="exp-v2")
        yaml_str = original.to_yaml()
        loaded = CIConfig.from_yaml(yaml_str)
        assert loaded.runner == original.runner
        assert loaded.time_budget_hours == original.time_budget_hours
        assert loaded.experiment_branch == original.experiment_branch

    def test_validate_valid(self):
        config = CIConfig()
        errors = config.validate()
        assert errors == []

    def test_validate_bad_time_budget(self):
        config = CIConfig(time_budget_hours=-1)
        errors = config.validate()
        assert any("time_budget" in e for e in errors)

    def test_validate_bad_notify(self):
        config = CIConfig(notify=["telegram"])
        errors = config.validate()
        assert any("telegram" in e for e in errors)

    def test_validate_bad_retention(self):
        config = CIConfig(artifact_retention_days=0)
        errors = config.validate()
        assert any("retention" in e for e in errors)
