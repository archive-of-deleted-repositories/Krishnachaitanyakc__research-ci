"""Tests for runner configuration generation."""

import pytest

from autoresearch_ci.config import CIConfig
from autoresearch_ci.runner_config import RunnerConfig


class TestRunnerConfig:
    def setup_method(self):
        self.runner = RunnerConfig()
        self.config = CIConfig(time_budget_hours=2.0, python_version="3.11")

    def test_modal_config_has_app(self):
        script = self.runner.generate_modal_config(self.config)
        assert "modal.App" in script

    def test_modal_config_has_gpu(self):
        script = self.runner.generate_modal_config(self.config)
        assert "A100" in script

    def test_modal_config_has_timeout(self):
        script = self.runner.generate_modal_config(self.config)
        assert "7200" in script  # 2 hours in seconds

    def test_modal_config_valid_python(self):
        script = self.runner.generate_modal_config(self.config)
        # Should be syntactically valid Python
        compile(script, "<modal>", "exec")

    def test_runpod_config_has_shebang(self):
        script = self.runner.generate_runpod_config(self.config)
        assert script.startswith("#!/bin/bash")

    def test_runpod_config_has_commands(self):
        script = self.runner.generate_runpod_config(self.config)
        assert "prepare.py" in script
        assert "train.py" in script

    def test_runpod_config_has_timeout(self):
        script = self.runner.generate_runpod_config(self.config)
        assert "timeout" in script

    def test_self_hosted_setup(self):
        script = self.runner.generate_self_hosted_setup(self.config)
        assert "nvidia-smi" in script
        assert "venv" in script

    def test_python_version_used(self):
        config = CIConfig(python_version="3.12")
        script = self.runner.generate_modal_config(config)
        assert "3.12" in script
