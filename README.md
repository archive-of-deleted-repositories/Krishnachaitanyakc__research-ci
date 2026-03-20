# research-ci

**Continuous ML research on every push.**

---

Running ML experiments manually is slow and error-prone. Copying results from terminals into spreadsheets is worse. **research-ci** turns your GitHub repo into a continuous research lab -- every push triggers experiments, results are posted as PR comments, and a leaderboard tracks the best across all branches.

## Quick Start

```bash
pip install research-ci
```

```python
from research_ci.action_generator import ActionGenerator
from research_ci.config import CIConfig

config = CIConfig(runner="self-hosted-gpu", time_budget_hours=4)
generator = ActionGenerator()
print(generator.generate_workflow(config))
```

## Features

- **One-command setup** -- generate GitHub Actions YAML for ML training, hyperparameter sweeps, or evaluation-only workflows
- **GPU runner support** -- templates for Modal, RunPod, and self-hosted GPU runners
- **Auto PR comments** -- experiment results posted directly on pull requests
- **Leaderboard builder** -- aggregate and rank results across all experiment branches
- **Workflow templates** -- ML training, hyperparameter sweep, and evaluation-only presets
- **Experiment DAGs** -- define multi-step experiment pipelines with dependency graphs
- **Cost tracking** -- estimate and report GPU costs per experiment (Modal, cloud providers)
- **Config validation** -- catch misconfiguration before wasting GPU hours
- **Retry logic** -- configurable retries with backoff for flaky training runs
- **Matrix strategies** -- multi-GPU parallel experiments via GitHub Actions matrix
- **Slack/webhook notifications** -- get notified when experiments complete
- **Domain integration** -- domain-specific workflow steps for specialized research areas
- **Statistical significance** -- built-in significance testing for result comparison

## CLI Usage

```bash
# Generate workflow YAML (writes to .github/workflows/)
research-ci init

# Use a specific template
research-ci init --template hyperparameter_sweep

# Generate with custom config
research-ci init --config research-ci.yaml --output-dir .github/workflows

# Build leaderboard from experiment branches
research-ci leaderboard /path/to/repo --direction maximize

# Generate a PR comment from results
research-ci comment results.json --baseline baseline.json

# Validate CI config (checks cost budget too)
research-ci validate research-ci.yaml

# Generate cost report from runner logs
research-ci cost-report log1.txt log2.txt --provider modal --gpu-type A100

# Generate workflow from experiment DAG
research-ci dag experiments.yaml --output .github/workflows/pipeline.yml
```

## Python API

```python
from research_ci.action_generator import ActionGenerator
from research_ci.config import CIConfig
from research_ci.leaderboard_builder import LeaderboardBuilder
from research_ci.result_commenter import ResultCommenter
from research_ci.cost_tracker import estimate_cost

# Generate workflow
config = CIConfig(
    runner="self-hosted-gpu",
    time_budget_hours=4,
    template="hyperparameter_sweep",
    gpu_type="A100",
    notify=["github_comment", "slack_webhook"],
)
generator = ActionGenerator()
workflow_yaml = generator.generate_workflow(config)

# Build leaderboard
builder = LeaderboardBuilder()
leaderboard_md = builder.build_leaderboard_from_repo("/path/to/repo", "maximize")

# Generate PR comment with baseline comparison
commenter = ResultCommenter()
comment_md = commenter.generate_pr_comment(results, baseline_data)

# Estimate costs before running
cost = estimate_cost("modal", "A100", gpu_hours=4.0, gpu_count=2)
print(f"Estimated cost: ${cost:.2f}")
```

## Generated Workflow Example

```yaml
name: Autoresearch Experiment
on:
  push:
    branches: [experiment, 'experiment/**']
  pull_request:
    branches: [main]

jobs:
  experiment:
    runs-on: self-hosted-gpu
    timeout-minutes: 240
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - run: python prepare.py
      - run: python train.py
      - uses: actions/upload-artifact@v4
        with:
          name: experiment-results
          path: results.json
```

## Comparison

| Feature | research-ci | Manual CI/CD | Custom GitHub Actions |
|---|---|---|---|
| ML-specific workflows | Yes | No | DIY |
| One-command setup | `research-ci init` | Manual YAML | Manual YAML |
| PR result comments | Built-in | No | DIY (50+ lines) |
| Leaderboard | Built-in | No | No |
| GPU runner templates | Modal, RunPod, self-hosted | N/A | DIY |
| Cost tracking | Built-in | No | No |
| Experiment DAGs | Built-in | N/A | Needs-per-workflow |
| Hyperparameter sweep matrix | Auto-generated | DIY | DIY |
| Statistical significance | Built-in | No | No |
| Config validation | Built-in | No | No |
| Maintenance burden | Zero -- generated | High | High |

## License

MIT
