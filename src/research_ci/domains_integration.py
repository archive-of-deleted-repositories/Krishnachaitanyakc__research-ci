"""Optional integration with research-domains."""

from __future__ import annotations

from research_ci.config import CIConfig


DOMAIN_DEFAULTS = {
    "nlp": {
        "extra_pip_packages": ["transformers", "datasets", "tokenizers"],
        "prepare_command": "python prepare_text.py",
    },
    "cv": {
        "extra_pip_packages": ["torchvision", "albumentations", "pillow"],
        "prepare_command": "python prepare_images.py",
    },
    "rl": {
        "extra_pip_packages": ["gymnasium", "stable-baselines3"],
        "prepare_command": "python prepare_env.py",
    },
    "tabular": {
        "extra_pip_packages": ["scikit-learn", "xgboost", "lightgbm"],
        "prepare_command": "python prepare_tabular.py",
    },
}


def detect_domain(project_path: str) -> str | None:
    """Try to auto-detect the research domain from project files.

    Attempts to import research-domains for detection.
    Falls back to None if not available.
    """
    try:
        import research_domains
        return research_domains.detect_domain(project_path)
    except (ImportError, AttributeError):
        return None


def apply_domain_config(config: CIConfig, domain: str) -> CIConfig:
    """Apply domain-specific defaults to the configuration."""
    defaults = DOMAIN_DEFAULTS.get(domain, {})
    if not defaults:
        return config

    extra_pkgs = list(config.extra_pip_packages)
    for pkg in defaults.get("extra_pip_packages", []):
        if pkg not in extra_pkgs:
            extra_pkgs.append(pkg)
    config.extra_pip_packages = extra_pkgs

    if config.prepare_command == "python prepare.py":
        config.prepare_command = defaults.get("prepare_command", config.prepare_command)

    return config
