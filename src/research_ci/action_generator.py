"""Generate GitHub Actions workflow YAML."""

from __future__ import annotations

from research_ci.config import CIConfig


class ActionGenerator:
    """Generate GitHub Actions workflow YAML for continuous research."""

    def generate_workflow(self, config: CIConfig) -> str:
        """Generate a complete workflow YAML string based on the template."""
        template = config.template
        if template == "hyperparameter_sweep":
            return self._generate_hyperparameter_sweep(config)
        elif template == "evaluation_only":
            return self._generate_evaluation_only(config)
        else:
            return self._generate_ml_training(config)

    def _build_common_header(self, config: CIConfig) -> str:
        return f"""name: Autoresearch Experiment
on:
  push:
    branches:
      - {config.experiment_branch}
      - '{config.experiment_branch}/**'
  pull_request:
    branches:
      - {config.base_branch}
"""

    def _build_extra_pip(self, config: CIConfig) -> str:
        if config.extra_pip_packages:
            pkgs = " ".join(config.extra_pip_packages)
            return f"\n      - name: Install extra packages\n        run: pip install {pkgs}"
        return ""

    def _build_notify_steps(self, config: CIConfig) -> str:
        steps = ""
        if "github_comment" in config.notify:
            steps += """
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
        if "slack_webhook" in config.notify:
            steps += """
      - name: Notify via webhook
        if: always()
        run: |
          RESULTS=$(cat results.json 2>/dev/null || echo '{"metric_name":"unknown","metric_value":"N/A"}')
          METRIC_NAME=$(echo "$RESULTS" | python -c "import sys,json; print(json.load(sys.stdin).get('metric_name','unknown'))")
          METRIC_VALUE=$(echo "$RESULTS" | python -c "import sys,json; print(json.load(sys.stdin).get('metric_value','N/A'))")
          PAYLOAD=$(python -c "import json; print(json.dumps({'text': f'Experiment complete: {}'+'$METRIC_NAME'+' = '+'$METRIC_VALUE', 'content': f'Experiment complete: {}'+'$METRIC_NAME'+' = '+'$METRIC_VALUE'}))")
          curl -s -X POST -H 'Content-Type: application/json' -d "$PAYLOAD" "${{ secrets.WEBHOOK_URL }}" || true"""
        return steps

    def _build_retry_wrapper(self, config: CIConfig, step_name: str, command: str) -> str:
        if config.max_retries > 0:
            return f"""
      - name: {step_name}
        run: |
          attempt=0
          max_retries={config.max_retries}
          while [ $attempt -le $max_retries ]; do
            if {command}; then
              exit 0
            fi
            attempt=$((attempt + 1))
            if [ $attempt -le $max_retries ]; then
              echo "Attempt $attempt failed, retrying in {config.retry_delay}s..."
              sleep {config.retry_delay}
            fi
          done
          echo "All attempts failed"
          exit 1
        continue-on-error: false"""
        return f"""
      - name: {step_name}
        run: {command}"""

    def _build_matrix_strategy(self, config: CIConfig) -> str:
        if config.gpu_count > 1:
            indices = list(range(config.gpu_count))
            return f"""
    strategy:
      matrix:
        gpu_index: {indices}"""
        return ""

    def _generate_ml_training(self, config: CIConfig) -> str:
        extra_pip = self._build_extra_pip(config)
        timeout_minutes = int(config.time_budget_hours * 60)
        notify_steps = self._build_notify_steps(config)
        matrix = self._build_matrix_strategy(config)
        train_step = self._build_retry_wrapper(config, "Run training", config.train_command)

        workflow = self._build_common_header(config)
        workflow += f"""
jobs:
  experiment:
    runs-on: {config.runner}
    timeout-minutes: {timeout_minutes}{matrix}
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
{train_step}

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: experiment-results
          path: results.json
          retention-days: {config.artifact_retention_days}{notify_steps}
"""
        return workflow

    def _generate_hyperparameter_sweep(self, config: CIConfig) -> str:
        extra_pip = self._build_extra_pip(config)
        timeout_minutes = int(config.time_budget_hours * 60)
        notify_steps = self._build_notify_steps(config)

        workflow = self._build_common_header(config)
        workflow += f"""
jobs:
  sweep:
    runs-on: {config.runner}
    timeout-minutes: {timeout_minutes}
    strategy:
      matrix:
        learning_rate: [0.001, 0.01, 0.1]
        batch_size: [16, 32, 64]
      fail-fast: false
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
        env:
          LEARNING_RATE: ${{{{ matrix.learning_rate }}}}
          BATCH_SIZE: ${{{{ matrix.batch_size }}}}

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: sweep-results-lr${{{{ matrix.learning_rate }}}}-bs${{{{ matrix.batch_size }}}}
          path: results.json
          retention-days: {config.artifact_retention_days}{notify_steps}
"""
        return workflow

    def _generate_evaluation_only(self, config: CIConfig) -> str:
        extra_pip = self._build_extra_pip(config)
        timeout_minutes = int(config.time_budget_hours * 60)
        notify_steps = self._build_notify_steps(config)

        workflow = self._build_common_header(config)
        workflow += f"""
jobs:
  evaluate:
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

      - name: Run evaluation
        run: {config.prepare_command}

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: evaluation-results
          path: results.json
          retention-days: {config.artifact_retention_days}{notify_steps}
"""
        return workflow
