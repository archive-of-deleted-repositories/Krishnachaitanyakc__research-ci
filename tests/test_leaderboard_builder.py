"""Tests for the leaderboard builder."""

import pytest

from autoresearch_ci.leaderboard_builder import LeaderboardBuilder, BranchResult


class TestLeaderboardBuilder:
    def setup_method(self):
        self.builder = LeaderboardBuilder()

    def test_build_leaderboard_empty(self):
        md = self.builder.build_leaderboard([])
        assert "No experiment results" in md

    def test_build_leaderboard_maximize(self):
        results = [
            BranchResult("experiment/v1", "accuracy", 0.85, "abc1234", "2024-01-01"),
            BranchResult("experiment/v2", "accuracy", 0.92, "def5678", "2024-01-02"),
            BranchResult("experiment/v3", "accuracy", 0.88, "ghi9012", "2024-01-03"),
        ]
        md = self.builder.build_leaderboard(results, direction="maximize")
        assert "Leaderboard" in md
        assert "Rank" in md
        # v2 should be ranked first (highest accuracy)
        lines = md.split("\n")
        rank1_line = [l for l in lines if "| 1 |" in l][0]
        assert "experiment/v2" in rank1_line
        assert "BEST" in rank1_line

    def test_build_leaderboard_minimize(self):
        results = [
            BranchResult("experiment/v1", "loss", 0.5, "abc", ""),
            BranchResult("experiment/v2", "loss", 0.1, "def", ""),
        ]
        md = self.builder.build_leaderboard(results, direction="minimize")
        lines = md.split("\n")
        rank1_line = [l for l in lines if "| 1 |" in l][0]
        assert "experiment/v2" in rank1_line

    def test_build_leaderboard_total_count(self):
        results = [
            BranchResult("experiment/a", "acc", 0.7, "", ""),
            BranchResult("experiment/b", "acc", 0.8, "", ""),
        ]
        md = self.builder.build_leaderboard(results)
        assert "Total experiments:** 2" in md

    def test_scan_branches_nonexistent_repo(self):
        results = self.builder.scan_branches("/nonexistent/path")
        assert results == []

    def test_build_leaderboard_from_repo_nonexistent(self):
        md = self.builder.build_leaderboard_from_repo("/nonexistent/path")
        assert "No experiment results" in md
