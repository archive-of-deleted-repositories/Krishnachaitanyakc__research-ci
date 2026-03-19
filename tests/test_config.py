"""Tests for CI configuration."""

import pytest

from research_ci.config import CIConfig


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

    def test_gpu_count_default(self):
        config = CIConfig()
        assert config.gpu_count == 1
        assert config.gpu_type == "A100"

    def test_gpu_count_from_yaml(self):
        yaml_str = "gpu_count: 4\ngpu_type: H100\n"
        config = CIConfig.from_yaml(yaml_str)
        assert config.gpu_count == 4
        assert config.gpu_type == "H100"

    def test_validate_bad_gpu_count(self):
        config = CIConfig(gpu_count=0)
        errors = config.validate()
        assert any("gpu_count" in e for e in errors)

    def test_cost_budget_from_yaml(self):
        yaml_str = "cost_budget_dollars: 50.0\n"
        config = CIConfig.from_yaml(yaml_str)
        assert config.cost_budget_dollars == 50.0

    def test_cost_budget_none_by_default(self):
        config = CIConfig()
        assert config.cost_budget_dollars is None

    def test_validate_bad_cost_budget(self):
        config = CIConfig(cost_budget_dollars=-10)
        errors = config.validate()
        assert any("cost_budget" in e for e in errors)

    def test_retry_config_from_yaml(self):
        yaml_str = "max_retries: 3\nretry_delay: 30\n"
        config = CIConfig.from_yaml(yaml_str)
        assert config.max_retries == 3
        assert config.retry_delay == 30

    def test_validate_bad_max_retries(self):
        config = CIConfig(max_retries=-1)
        errors = config.validate()
        assert any("max_retries" in e for e in errors)

    def test_template_from_yaml(self):
        yaml_str = "template: hyperparameter_sweep\n"
        config = CIConfig.from_yaml(yaml_str)
        assert config.template == "hyperparameter_sweep"

    def test_validate_bad_template(self):
        config = CIConfig(template="nonexistent")
        errors = config.validate()
        assert any("template" in e for e in errors)
