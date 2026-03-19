"""Track and estimate costs for GPU experiment runs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


PROVIDER_PRICING: Dict[str, Dict[str, float]] = {
    "modal": {
        "A100": 3.73,
        "A10G": 1.10,
        "T4": 0.59,
        "H100": 6.98,
    },
    "runpod": {
        "A100": 3.29,
        "A10G": 0.74,
        "T4": 0.44,
        "H100": 5.49,
    },
    "github_actions": {
        "ubuntu-latest": 0.008,
        "self-hosted-gpu": 0.0,
    },
}


@dataclass
class CostEntry:
    """A single cost record for an experiment run."""
    provider: str
    gpu_type: str
    gpu_hours: float
    cost_dollars: float
    experiment_name: str = ""


@dataclass
class CostReport:
    """Aggregated cost report."""
    entries: List[CostEntry] = field(default_factory=list)

    @property
    def total_cost(self) -> float:
        return sum(e.cost_dollars for e in self.entries)

    @property
    def total_gpu_hours(self) -> float:
        return sum(e.gpu_hours for e in self.entries)

    def to_markdown(self) -> str:
        if not self.entries:
            return "# Cost Report\n\nNo cost data recorded.\n"

        lines = ["# Cost Report\n"]
        lines.append("| Experiment | Provider | GPU | Hours | Cost ($) |")
        lines.append("|------------|----------|-----|-------|----------|")
        for e in self.entries:
            lines.append(
                f"| {e.experiment_name} | {e.provider} | {e.gpu_type} | "
                f"{e.gpu_hours:.2f} | ${e.cost_dollars:.2f} |"
            )
        lines.append(f"\n**Total GPU hours:** {self.total_gpu_hours:.2f}")
        lines.append(f"**Total cost:** ${self.total_cost:.2f}")
        return "\n".join(lines) + "\n"


def estimate_cost(
    provider: str,
    gpu_type: str,
    hours: float,
    gpu_count: int = 1,
) -> float:
    """Estimate cost for a given provider, GPU type, and duration."""
    provider_rates = PROVIDER_PRICING.get(provider, {})
    rate = provider_rates.get(gpu_type, 0.0)
    return rate * hours * gpu_count


def parse_gpu_time_from_log(log_text: str) -> Optional[float]:
    """Parse GPU time in hours from runner log output.

    Looks for patterns like:
      - "GPU time: 1.5h"
      - "Duration: 90 minutes"
      - "Elapsed: 5400 seconds"
    """
    hour_match = re.search(r"(?:GPU time|Duration|Elapsed)[:\s]+([0-9.]+)\s*h(?:ours?)?", log_text, re.IGNORECASE)
    if hour_match:
        return float(hour_match.group(1))

    min_match = re.search(r"(?:GPU time|Duration|Elapsed)[:\s]+([0-9.]+)\s*min(?:utes?)?", log_text, re.IGNORECASE)
    if min_match:
        return float(min_match.group(1)) / 60.0

    sec_match = re.search(r"(?:GPU time|Duration|Elapsed)[:\s]+([0-9.]+)\s*s(?:econds?)?", log_text, re.IGNORECASE)
    if sec_match:
        return float(sec_match.group(1)) / 3600.0

    return None
