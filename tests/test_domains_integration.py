"""Tests for domains integration module."""

import pytest

from research_ci.config import CIConfig
from research_ci.domains_integration import apply_domain_config, detect_domain


class TestApplyDomainConfig:
    def test_nlp_domain(self):
        config = CIConfig()
        config = apply_domain_config(config, "nlp")
        assert "transformers" in config.extra_pip_packages
        assert "datasets" in config.extra_pip_packages
        assert "prepare_text" in config.prepare_command

    def test_cv_domain(self):
        config = CIConfig()
        config = apply_domain_config(config, "cv")
        assert "torchvision" in config.extra_pip_packages
        assert "prepare_images" in config.prepare_command

    def test_rl_domain(self):
        config = CIConfig()
        config = apply_domain_config(config, "rl")
        assert "gymnasium" in config.extra_pip_packages

    def test_tabular_domain(self):
        config = CIConfig()
        config = apply_domain_config(config, "tabular")
        assert "scikit-learn" in config.extra_pip_packages

    def test_unknown_domain(self):
        config = CIConfig()
        original_pkgs = list(config.extra_pip_packages)
        config = apply_domain_config(config, "unknown_domain")
        assert config.extra_pip_packages == original_pkgs

    def test_does_not_duplicate_packages(self):
        config = CIConfig(extra_pip_packages=["transformers"])
        config = apply_domain_config(config, "nlp")
        assert config.extra_pip_packages.count("transformers") == 1

    def test_preserves_custom_prepare_command(self):
        config = CIConfig(prepare_command="python my_custom.py")
        config = apply_domain_config(config, "nlp")
        assert config.prepare_command == "python my_custom.py"


class TestDetectDomain:
    def test_returns_none_without_package(self):
        result = detect_domain("/nonexistent/path")
        assert result is None
