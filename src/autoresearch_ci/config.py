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
    gpu_count: int = 1
    gpu_type: str = "A100"
    cost_budget_dollars: Optional[float] = None
    max_retries: int = 0
    retry_delay: int = 60
    template: str = "ml_training"

    @classmethod
    def from_yaml(cls, yaml_str: str) -> CIConfig:
        """Load config from YAML string."""
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            raise ValueError("Config YAML must be a mapping")
        budget = data.get("cost_budget_dollars")
        if budget is not None:
            budget = float(budget)
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
            gpu_count=int(data.get("gpu_count", 1)),
            gpu_type=data.get("gpu_type", "A100"),
            cost_budget_dollars=budget,
            max_retries=int(data.get("max_retries", 0)),
            retry_delay=int(data.get("retry_delay", 60)),
            template=data.get("template", "ml_training"),
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
            "gpu_count": self.gpu_count,
            "gpu_type": self.gpu_type,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "template": self.template,
        }
        if self.cost_budget_dollars is not None:
            data["cost_budget_dollars"] = self.cost_budget_dollars
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
        if self.gpu_count < 1:
            errors.append("gpu_count must be at least 1")
        if self.cost_budget_dollars is not None and self.cost_budget_dollars <= 0:
            errors.append("cost_budget_dollars must be positive")
        if self.max_retries < 0:
            errors.append("max_retries must be non-negative")
        if self.retry_delay < 0:
            errors.append("retry_delay must be non-negative")
        valid_templates = {"ml_training", "hyperparameter_sweep", "evaluation_only"}
        if self.template not in valid_templates:
            errors.append(f"Unknown template: {self.template}")
        return errors
