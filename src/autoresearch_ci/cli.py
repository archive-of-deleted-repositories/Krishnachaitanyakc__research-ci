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
def init(config_file, output_dir):
    """Generate GitHub Actions workflow YAML."""
    if config_file and os.path.exists(config_file):
        config = CIConfig.from_file(config_file)
    else:
        config = CIConfig()

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

    if errors:
        click.echo("Configuration errors:")
        for err in errors:
            click.echo(f"  - {err}")
        raise SystemExit(1)
    else:
        click.echo("Configuration is valid.")
