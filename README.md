# research-ci

GitHub Actions integration for continuous research on every push. Generates workflow files, builds leaderboards from experiment branches, and creates PR comments with experiment results.

## Features

- Generate GitHub Actions YAML for continuous research
- Support custom GPU runners (Modal, RunPod templates)
- Auto-generate PR comments with experiment results
- Build leaderboards from experiment branches
- Validate CI configuration

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

### CLI

```bash
# Generate workflow YAML
research-ci init

# Build leaderboard from experiment branches
research-ci leaderboard /path/to/repo

# Generate PR comment from results
research-ci comment results.json

# Validate CI config
research-ci validate research-ci.yaml
```

### Python API

```python
from research_ci.action_generator import ActionGenerator
from research_ci.config import CIConfig

config = CIConfig(runner="self-hosted-gpu", time_budget_hours=4)
generator = ActionGenerator()
workflow_yaml = generator.generate_workflow(config)
```
