"""CLI for autoresearch-ci."""

from __future__ import annotations

import json
import os

import click

from autoresearch_ci.config import CIConfig
from autoresearch_ci.action_generator import ActionGenerator
from autoresearch_ci.result_commenter import ResultCommenter
from autoresearch_ci.leaderboard_builder import LeaderboardBuilder


@click.group()
def cli():
    """GitHub Actions integration for continuous research."""


@cli.command()
@click.option("--config", "config_file", type=click.Path(), default=None,
              help="Path to autoresearch-ci.yaml config file")
@click.option("--output-dir", type=click.Path(), default=".github/workflows",
              help="Output directory for workflow YAML")
@click.option("--template", type=click.Choice(["ml_training", "hyperparameter_sweep", "evaluation_only"]),
              default=None, help="Workflow template to use")
@click.option("--domain", default=None, help="Research domain for domain-specific steps")
def init(config_file, output_dir, template, domain):
    """Generate GitHub Actions workflow YAML."""
    if config_file and os.path.exists(config_file):
        config = CIConfig.from_file(config_file)
    else:
        config = CIConfig()

    if template:
        config.template = template

    if domain:
        try:
            from autoresearch_ci.domains_integration import apply_domain_config
            config = apply_domain_config(config, domain)
        except ImportError:
            click.echo(f"Warning: autoresearch-domains not available, --domain ignored")

    generator = ActionGenerator()
    workflow = generator.generate_workflow(config)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "autoresearch.yml")
    with open(output_path, "w") as f:
        f.write(workflow)

    click.echo(f"Generated workflow at: {output_path}")


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("--direction", type=click.Choice(["maximize", "minimize"]), default="maximize")
@click.option("--output", type=click.Path(), default=None, help="Output file for LEADERBOARD.md")
def leaderboard(repo_path, direction, output):
    """Build leaderboard from experiment branches."""
    builder = LeaderboardBuilder()
    md = builder.build_leaderboard_from_repo(repo_path, direction)

    if output:
        with open(output, "w") as f:
            f.write(md)
        click.echo(f"Leaderboard written to: {output}")
    else:
        click.echo(md)


@cli.command()
@click.argument("results_file", type=click.Path(exists=True))
@click.option("--baseline", type=click.Path(exists=True), default=None,
              help="Baseline results for comparison")
def comment(results_file, baseline):
    """Generate PR comment from experiment results."""
    with open(results_file) as f:
        results = json.load(f)

    baseline_data = None
    if baseline:
        with open(baseline) as f:
            baseline_data = json.load(f)

    commenter = ResultCommenter()
    md = commenter.generate_pr_comment(results, baseline_data)
    click.echo(md)


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
def validate(config_file):
    """Validate a CI configuration file."""
    config = CIConfig.from_file(config_file)
    errors = config.validate()

    if config.cost_budget_dollars is not None:
        from autoresearch_ci.cost_tracker import estimate_cost
        provider = "github_actions"
        if "gpu" in config.runner.lower() or "self-hosted" in config.runner.lower():
            provider = "modal"
        estimated = estimate_cost(provider, config.gpu_type, config.time_budget_hours, config.gpu_count)
        if estimated > config.cost_budget_dollars:
            errors.append(
                f"Estimated cost ${estimated:.2f} exceeds budget ${config.cost_budget_dollars:.2f}"
            )
        else:
            click.echo(f"Estimated cost: ${estimated:.2f} (budget: ${config.cost_budget_dollars:.2f})")

    if errors:
        click.echo("Configuration errors:")
        for err in errors:
            click.echo(f"  - {err}")
        raise SystemExit(1)
    else:
        click.echo("Configuration is valid.")


@cli.command(name="cost-report")
@click.argument("log_files", nargs=-1, type=click.Path(exists=True))
@click.option("--provider", default="modal", help="Cloud provider name")
@click.option("--gpu-type", default="A100", help="GPU type used")
def cost_report(log_files, provider, gpu_type):
    """Generate cost report from runner logs."""
    from autoresearch_ci.cost_tracker import (
        CostReport, CostEntry, estimate_cost, parse_gpu_time_from_log
    )

    report = CostReport()
    for log_file in log_files:
        with open(log_file) as f:
            log_text = f.read()
        gpu_hours = parse_gpu_time_from_log(log_text)
        if gpu_hours is None:
            click.echo(f"Warning: Could not parse GPU time from {log_file}")
            continue
        cost = estimate_cost(provider, gpu_type, gpu_hours)
        report.entries.append(CostEntry(
            provider=provider,
            gpu_type=gpu_type,
            gpu_hours=gpu_hours,
            cost_dollars=cost,
            experiment_name=os.path.basename(log_file),
        ))

    click.echo(report.to_markdown())


@cli.command()
@click.argument("dag_file", type=click.Path(exists=True))
@click.option("--runner", default="ubuntu-latest", help="GitHub Actions runner")
@click.option("--output", type=click.Path(), default=None, help="Output workflow file")
def dag(dag_file, runner, output):
    """Generate workflow from experiment dependency graph."""
    from autoresearch_ci.dag import load_dag_from_yaml, validate_dag, generate_github_actions_dag

    with open(dag_file) as f:
        dag_data = load_dag_from_yaml(f.read())

    errors = validate_dag(dag_data)
    if errors:
        click.echo("DAG validation errors:")
        for err in errors:
            click.echo(f"  - {err}")
        raise SystemExit(1)

    workflow = generate_github_actions_dag(dag_data, runner)

    if output:
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w") as f:
            f.write(workflow)
        click.echo(f"DAG workflow written to: {output}")
    else:
        click.echo(workflow)
