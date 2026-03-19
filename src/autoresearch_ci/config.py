"""CI configuration for autoresearch workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import yaml


@dataclass
class CIConfig:
    """Configuration for autoresearch CI workflows."""
    runner: str = "ubuntu-latest"  # 'ubuntu-latest', 'self-hosted-gpu', etc.
    time_budget_hours: float = 2.0
    experiment_branch: str = "experiment"
    base_branch: str = "main"
    notify: List[str] = field(default_factory=lambda: ["github_comment"])
    artifact_retention_days: int = 30
    prepare_command: str = "python prepare.py"
    train_command: str = "python train.py"
    python_version: str = "3.11"
    extra_pip_packages: List[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> CIConfig:
        """Load config from YAML string."""
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            raise ValueError("Config YAML must be a mapping")
        return cls(
            runner=data.get("runner", "ubuntu-latest"),
            time_budget_hours=float(data.get("time_budget_hours", 2.0)),
            experiment_branch=data.get("experiment_branch", "experiment"),
            base_branch=data.get("base_branch", "main"),
            notify=data.get("notify", ["github_comment"]),
            artifact_retention_days=int(data.get("artifact_retention_days", 30)),
            prepare_command=data.get("prepare_command", "python prepare.py"),
            train_command=data.get("train_command", "python train.py"),
            python_version=data.get("python_version", "3.11"),
            extra_pip_packages=data.get("extra_pip_packages", []),
        )

    @classmethod
    def from_file(cls, path: str) -> CIConfig:
        """Load config from YAML file."""
        with open(path) as f:
            return cls.from_yaml(f.read())

    def to_yaml(self) -> str:
        """Serialize config to YAML string."""
        data = {
            "runner": self.runner,
            "time_budget_hours": self.time_budget_hours,
            "experiment_branch": self.experiment_branch,
            "base_branch": self.base_branch,
            "notify": self.notify,
            "artifact_retention_days": self.artifact_retention_days,
            "prepare_command": self.prepare_command,
            "train_command": self.train_command,
            "python_version": self.python_version,
            "extra_pip_packages": self.extra_pip_packages,
        }
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    def validate(self) -> List[str]:
        """Validate configuration. Returns list of error messages."""
        errors = []
        if not self.runner:
            errors.append("runner must not be empty")
        if self.time_budget_hours <= 0:
            errors.append("time_budget_hours must be positive")
        if not self.experiment_branch:
            errors.append("experiment_branch must not be empty")
        if not self.base_branch:
            errors.append("base_branch must not be empty")
        if self.artifact_retention_days < 1:
            errors.append("artifact_retention_days must be at least 1")
        valid_notify = {"github_comment", "slack_webhook"}
        for n in self.notify:
            if n not in valid_notify:
                errors.append(f"Unknown notify method: {n}")
        return errors
