"""Format experiment results as PR comments."""

from __future__ import annotations

from typing import Dict, List, Optional


class ResultCommenter:
    """Format experiment results as markdown for PR comments."""

    def format_results_as_markdown(self, results: Dict) -> str:
        """Format a results dict as a markdown summary.

        Expected keys: metric_name, metric_value, and optionally config, history.
        """
        lines = ["## Experiment Results\n"]

        metric_name = results.get("metric_name", "metric")
        metric_value = results.get("metric_value", "N/A")

        lines.append(f"**Metric:** {metric_name}")
        lines.append(f"**Value:** {metric_value}\n")

        # Config summary
        config = results.get("config", {})
        if config:
            lines.append("### Configuration\n")
            lines.append("| Parameter | Value |")
            lines.append("|-----------|-------|")
            for k, v in sorted(config.items()):
                lines.append(f"| {k} | {v} |")
            lines.append("")

        # History / improvement chart (ASCII)
        history = results.get("history", [])
        if history:
            lines.append("### Training Progress\n")
            lines.append(self._ascii_chart(history))
            lines.append("")

        return "\n".join(lines)

    def generate_pr_comment(self, results: Dict,
                            baseline: Optional[Dict] = None) -> str:
        """Generate a full PR comment with optional baseline comparison."""
        lines = [self.format_results_as_markdown(results)]

        if baseline:
            lines.append("### Comparison with Baseline\n")
            base_val = baseline.get("metric_value", 0)
            curr_val = results.get("metric_value", 0)

            if isinstance(base_val, (int, float)) and isinstance(curr_val, (int, float)):
                diff = curr_val - base_val
                pct = (diff / abs(base_val) * 100) if base_val != 0 else 0
                direction = "improvement" if diff > 0 else "regression"
                lines.append(f"| | Baseline | Current | Change |")
                lines.append(f"|---|---------|---------|--------|")
                metric_name = results.get("metric_name", "metric")
                lines.append(f"| {metric_name} | {base_val} | {curr_val} | {diff:+.4f} ({pct:+.1f}%, {direction}) |")
            else:
                lines.append(f"- Baseline: {base_val}")
                lines.append(f"- Current: {curr_val}")

        return "\n".join(lines)

    def _ascii_chart(self, values: List[float], width: int = 40, height: int = 8) -> str:
        """Generate a simple ASCII chart of values."""
        if not values:
            return "(no data)"

        min_val = min(values)
        max_val = max(values)
        val_range = max_val - min_val if max_val != min_val else 1.0

        lines = ["```"]
        for row in range(height - 1, -1, -1):
            threshold = min_val + (row / (height - 1)) * val_range
            chars = []
            step = max(1, len(values) // width)
            for i in range(0, min(len(values), width * step), step):
                if values[i] >= threshold:
                    chars.append("#")
                else:
                    chars.append(" ")
            label = f"{threshold:8.3f} |"
            lines.append(label + "".join(chars))

        lines.append("         +" + "-" * min(len(values), width))
        lines.append("```")
        return "\n".join(lines)
