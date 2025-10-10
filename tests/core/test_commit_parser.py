"""Unit tests for MockLLMAnalyzer simulation behavior."""

from __future__ import annotations

import pytest

from gitgossip.core.llm.mock_llm_analyzer import MockLLMAnalyzer
from gitgossip.core.models.commit import Commit


class TestMockLLMAnalyzer:  # noqa: D101
    """Test suite for MockLLMAnalyzer."""

    @pytest.fixture()
    def sample_commit(self) -> Commit:
        """Return a standard mock commit for testing."""
        return Commit(
            hash="123456789abcdef",
            author="osman",
            email="abcd",
            message="Initial commit",
            files_changed=3,
            insertions=10,
            deletions=2,
            changes=[
                {"file": "main.py", "summary": ["added function", "added docstring"]},
                {"file": "utils.py", "summary": ["refactored helper methods"]},
            ],
        )

    def test_analyze_commits_empty(self) -> None:
        """Should return a default message for empty commit list."""
        analyzer = MockLLMAnalyzer()
        result = analyzer.analyze_commits([])
        assert result == "No commits found to analyze."

    def test_analyze_single_commit_basic(self, sample_commit: Commit) -> None:
        """Should summarize a single commit."""
        analyzer = MockLLMAnalyzer()
        result = analyzer.analyze_commits([sample_commit])

        assert "`1234567`" in result  # trimmed hash
        assert "by osman" in result
        assert "Initial commit" in result
        assert "(+10/-2, 3 files)" in result
        assert "Highlights:" not in result

    def test_analyze_multiple_commits(self, sample_commit: Commit) -> None:
        """Should join multiple commit summaries with blank line."""
        second_commit = Commit(
            hash="abcdef987654321",
            email="abcd",
            author="nahid",
            message="Fix bug",
            files_changed=1,
            insertions=2,
            deletions=1,
        )

        analyzer = MockLLMAnalyzer()
        result = analyzer.analyze_commits([sample_commit, second_commit])

        summaries = result.split("\n\n")
        assert len(summaries) == 2
        assert "osman" in summaries[0]
        assert "nahid" in summaries[1]

    def test_bytes_message_decoding(self) -> None:
        """Should decode commit messages in bytes."""
        commit = Commit(
            hash="abc111",
            email="abcd",
            author="tester",
            message=b"Binary data message",
            files_changed=1,
            insertions=1,
            deletions=0,
        )
        analyzer = MockLLMAnalyzer()
        result = analyzer.analyze_commits([commit])

        assert "Binary data message" in result
        assert isinstance(result, str)

    def test_verbose_mode_includes_highlights(self, sample_commit: Commit) -> None:
        """Should include highlights when verbosity > 1."""
        analyzer = MockLLMAnalyzer(verbosity=2)
        result = analyzer.analyze_commits([sample_commit])

        assert "Highlights:" in result
        assert "main.py" in result
        assert "utils.py" in result
