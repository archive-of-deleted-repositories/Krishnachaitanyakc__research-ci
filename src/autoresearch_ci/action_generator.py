"""Generate GitHub Actions workflow YAML."""

from __future__ import annotations

from autoresearch_ci.config import CIConfig


class ActionGenerator:
    """Generate GitHub Actions workflow YAML for continuous research."""

    def generate_workflow(self, config: CIConfig) -> str:
        """Generate a complete workflow YAML string."""
        extra_pip = ""
        if config.extra_pip_packages:
            pkgs = " ".join(config.extra_pip_packages)
            extra_pip = f"\n      - name: Install extra packages\n        run: pip install {pkgs}"

        timeout_minutes = int(config.time_budget_hours * 60)

        notify_step = ""
        if "github_comment" in config.notify:
            notify_step = """
      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const results = fs.readFileSync('results.json', 'utf8');
            const data = JSON.parse(results);
            const body = `## Experiment Results\\n\\n` +
              `**Metric:** ${data.metric_name}\\n` +
              `**Value:** ${data.metric_value}\\n`;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });"""

        workflow = f"""name: Autoresearch Experiment
on:
  push:
    branches:
      - {config.experiment_branch}
      - '{config.experiment_branch}/**'
  pull_request:
    branches:
      - {config.base_branch}

jobs:
  experiment:
    runs-on: {config.runner}
    timeout-minutes: {timeout_minutes}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '{config.python_version}'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt 2>/dev/null || true{extra_pip}

      - name: Prepare data
        run: {config.prepare_command}

      - name: Run training
        run: {config.train_command}

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: experiment-results
          path: results.json
          retention-days: {config.artifact_retention_days}{notify_step}
"""
        return workflow
