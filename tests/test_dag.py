"""Tests for DAG module."""

import pytest
import yaml

from research_ci.dag import (
    load_dag_from_yaml,
    validate_dag,
    topological_sort,
    generate_github_actions_dag,
    CycleError,
)


class TestLoadDag:
    def test_load_simple_dag(self):
        yaml_str = """
experiments:
  train_base:
    depends_on: []
  fine_tune:
    depends_on: [train_base]
"""
        dag = load_dag_from_yaml(yaml_str)
        assert "train_base" in dag
        assert "fine_tune" in dag
        assert dag["train_base"] == []
        assert dag["fine_tune"] == ["train_base"]

    def test_load_invalid_yaml(self):
        with pytest.raises(ValueError):
            load_dag_from_yaml("not_experiments: foo")

    def test_load_string_dep(self):
        yaml_str = """
experiments:
  a:
    depends_on: b
  b:
    depends_on: []
"""
        dag = load_dag_from_yaml(yaml_str)
        assert dag["a"] == ["b"]

    def test_load_no_spec(self):
        yaml_str = """
experiments:
  a: null
  b:
    depends_on: [a]
"""
        dag = load_dag_from_yaml(yaml_str)
        assert dag["a"] == []
        assert dag["b"] == ["a"]


class TestValidateDag:
    def test_valid_dag(self):
        dag = {"a": [], "b": ["a"], "c": ["a", "b"]}
        errors = validate_dag(dag)
        assert errors == []

    def test_unknown_dependency(self):
        dag = {"a": [], "b": ["nonexistent"]}
        errors = validate_dag(dag)
        assert len(errors) == 1
        assert "nonexistent" in errors[0]

    def test_cyclic_dag(self):
        dag = {"a": ["b"], "b": ["a"]}
        errors = validate_dag(dag)
        assert len(errors) == 1
        assert "Cycle" in errors[0]


class TestTopologicalSort:
    def test_simple_sort(self):
        dag = {"a": [], "b": ["a"], "c": ["b"]}
        order = topological_sort(dag)
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")

    def test_independent_nodes(self):
        dag = {"a": [], "b": [], "c": []}
        order = topological_sort(dag)
        assert set(order) == {"a", "b", "c"}

    def test_cycle_raises(self):
        dag = {"a": ["c"], "b": ["a"], "c": ["b"]}
        with pytest.raises(CycleError):
            topological_sort(dag)


class TestGenerateGithubActionsDag:
    def test_generates_valid_yaml(self):
        dag = {"train": [], "eval": ["train"]}
        workflow = generate_github_actions_dag(dag)
        parsed = yaml.safe_load(workflow)
        assert "jobs" in parsed

    def test_needs_directive(self):
        dag = {"train": [], "eval": ["train"]}
        workflow = generate_github_actions_dag(dag)
        assert "needs:" in workflow

    def test_no_needs_for_root(self):
        dag = {"train": [], "eval": ["train"]}
        workflow = generate_github_actions_dag(dag)
        parsed = yaml.safe_load(workflow)
        assert "needs" not in parsed["jobs"]["train"]

    def test_custom_runner(self):
        dag = {"a": []}
        workflow = generate_github_actions_dag(dag, runner="self-hosted")
        assert "self-hosted" in workflow
