"""Experiment dependency graph (DAG) support."""

from __future__ import annotations

from typing import Dict, List, Set

import yaml


class CycleError(Exception):
    """Raised when the dependency graph contains a cycle."""


def load_dag_from_yaml(yaml_str: str) -> Dict[str, List[str]]:
    """Load experiment dependency graph from YAML.

    Expected format:
        experiments:
          experiment_a:
            depends_on: []
          experiment_b:
            depends_on: [experiment_a]
          experiment_c:
            depends_on: [experiment_a, experiment_b]

    Returns:
        Dict mapping experiment name to list of dependencies.
    """
    data = yaml.safe_load(yaml_str)
    if not isinstance(data, dict) or "experiments" not in data:
        raise ValueError("DAG YAML must contain an 'experiments' key")

    experiments = data["experiments"]
    dag: Dict[str, List[str]] = {}
    for name, spec in experiments.items():
        if isinstance(spec, dict):
            deps = spec.get("depends_on", [])
        else:
            deps = []
        if isinstance(deps, str):
            deps = [deps]
        dag[name] = list(deps)

    return dag


def validate_dag(dag: Dict[str, List[str]]) -> List[str]:
    """Validate that the DAG is acyclic and all references exist.

    Returns list of error messages (empty if valid).
    """
    errors = []

    all_experiments = set(dag.keys())
    for name, deps in dag.items():
        for dep in deps:
            if dep not in all_experiments:
                errors.append(f"Experiment '{name}' depends on unknown experiment '{dep}'")

    if not errors:
        try:
            topological_sort(dag)
        except CycleError as e:
            errors.append(str(e))

    return errors


def topological_sort(dag: Dict[str, List[str]]) -> List[str]:
    """Return experiments in topological order. Raises CycleError if cyclic."""
    visited: Set[str] = set()
    in_stack: Set[str] = set()
    order: List[str] = []

    def visit(node: str) -> None:
        if node in in_stack:
            raise CycleError(f"Cycle detected involving experiment '{node}'")
        if node in visited:
            return
        in_stack.add(node)
        for dep in dag.get(node, []):
            visit(dep)
        in_stack.remove(node)
        visited.add(node)
        order.append(node)

    for node in dag:
        visit(node)

    return order


def generate_github_actions_dag(dag: Dict[str, List[str]], runner: str = "ubuntu-latest") -> str:
    """Generate GitHub Actions workflow YAML with needs: directives from DAG."""
    order = topological_sort(dag)

    lines = [
        "name: Autoresearch DAG Experiments",
        "on:",
        "  push:",
        "    branches: ['experiment/**']",
        "  workflow_dispatch:",
        "",
        "jobs:",
    ]

    for name in order:
        deps = dag.get(name, [])
        job_id = name.replace("-", "_").replace(" ", "_")
        lines.append(f"  {job_id}:")

        if deps:
            dep_ids = [d.replace("-", "_").replace(" ", "_") for d in deps]
            lines.append(f"    needs: [{', '.join(dep_ids)}]")

        lines.append(f"    runs-on: {runner}")
        lines.append(f"    steps:")
        lines.append(f"      - uses: actions/checkout@v4")
        lines.append(f"      - name: Run {name}")
        lines.append(f"        run: echo 'Running experiment {name}'")
        lines.append("")

    return "\n".join(lines) + "\n"
