"""Build leaderboards from experiment branches."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class BranchResult:
    """Result from a single experiment branch."""
    branch: str
    metric_name: str
    metric_value: float
    commit_hash: str = ""
    timestamp: str = ""


class LeaderboardBuilder:
    """Build leaderboards from experiment branch results."""

    def scan_branches(self, repo_path: str, results_file: str = "results.json") -> List[BranchResult]:
        """Scan git branches for experiment results.

        Looks for results_file in each branch that starts with 'experiment'.
        """
        results = []

        try:
            output = subprocess.run(
                ["git", "branch", "-a", "--format=%(refname:short)"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            branches = [b.strip() for b in output.stdout.strip().split("\n") if b.strip()]
        except (subprocess.CalledProcessError, FileNotFoundError):
            return results

        for branch in branches:
            if not branch.startswith("experiment"):
                continue

            try:
                show_output = subprocess.run(
                    ["git", "show", f"{branch}:{results_file}"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                data = json.loads(show_output.stdout)

                log_output = subprocess.run(
                    ["git", "log", branch, "-1", "--format=%H %aI"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                parts = log_output.stdout.strip().split(" ", 1)
                commit_hash = parts[0] if parts else ""
                timestamp = parts[1] if len(parts) > 1 else ""

                results.append(BranchResult(
                    branch=branch,
                    metric_name=data.get("metric_name", "unknown"),
                    metric_value=float(data.get("metric_value", 0)),
                    commit_hash=commit_hash[:8],
                    timestamp=timestamp,
                ))
            except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError):
                continue

        return results

    def build_leaderboard(self, results: List[BranchResult],
                          direction: str = "maximize") -> str:
        """Build a markdown leaderboard table from branch results.

        direction: 'maximize' (higher is better) or 'minimize' (lower is better)
        """
        if not results:
            return "# Leaderboard\n\nNo experiment results found.\n"

        reverse = direction == "maximize"
        sorted_results = sorted(results, key=lambda r: r.metric_value, reverse=reverse)

        lines = ["# Leaderboard\n"]
        if sorted_results:
            lines.append(f"**Metric:** {sorted_results[0].metric_name} ({direction})\n")

        lines.append("| Rank | Branch | Value | Commit | Timestamp |")
        lines.append("|------|--------|-------|--------|-----------|")

        for i, r in enumerate(sorted_results):
            medal = ""
            if i == 0:
                medal = " [BEST]"
            lines.append(
                f"| {i+1} | {r.branch}{medal} | {r.metric_value:.4f} | "
                f"{r.commit_hash} | {r.timestamp} |"
            )

        lines.append(f"\n**Total experiments:** {len(sorted_results)}")
        return "\n".join(lines) + "\n"

    def build_leaderboard_from_repo(self, repo_path: str,
                                     direction: str = "maximize") -> str:
        """Convenience: scan branches and build leaderboard."""
        results = self.scan_branches(repo_path)
        return self.build_leaderboard(results, direction)
