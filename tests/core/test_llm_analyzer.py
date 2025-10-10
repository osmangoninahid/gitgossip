"""Unit tests for MockLLMAnalyzer."""

import pytest

from gitgossip.core.llm.mock_llm_analyzer import MockLLMAnalyzer
from gitgossip.core.models.commit import Commit


class TestMockLLMAnalyzer:
    """Simulates MockLLMAnalyzer."""

    @pytest.fixture
    def sample_commit(self) -> Commit:
        return Commit(
            hash="123456789abcdef",
            author="osman",
            email="e@email.com",
            message="Initial commit",
            files_changed=3,
            insertions=10,
            deletions=2,
            changes=[
                {"file": "main.py", "summary": ["added main function", "added docstring"]},
                {"file": "utils.py", "summary": ["refactored helpers"]},
            ],
        )

    def test_no_commits(self) -> None:
        analyzer = MockLLMAnalyzer()
        result = analyzer.analyze_commits([])
        assert result == "No commits found to analyze."

    def test_single_commit_summary(self, sample_commit: Commit) -> None:
        analyzer = MockLLMAnalyzer()
        result = analyzer.analyze_commits([sample_commit])

        # Should include trimmed hash (7 chars)
        assert "`1234567`" in result
        assert "by osman" in result
        assert "Initial commit" in result
        assert "(+10/-2, 3 files)" in result
        assert "Highlights" not in result  # default verbosity = 1

    def test_multiple_commits(self, sample_commit: Commit) -> None:
        other_commit = Commit(
            hash="abcdef123456789",
            author="nahid",
            email="e@email.com",
            message="Fix bug",
            files_changed=1,
            insertions=2,
            deletions=1,
        )
        analyzer = MockLLMAnalyzer()
        result = analyzer.analyze_commits([sample_commit, other_commit])
        # Expect two summaries separated by double newline
        parts = result.split("\n\n")
        assert len(parts) == 2
        assert "by osman" in parts[0]
        assert "by nahid" in parts[1]

    def test_bytes_message_handling(self) -> None:
        commit_with_bytes = Commit(
            hash="1111111111",
            author="test",
            email="e@email.com",
            message=b"Binary message",
            files_changed=1,
            insertions=1,
            deletions=0,
        )
        analyzer = MockLLMAnalyzer()
        result = analyzer.analyze_commits([commit_with_bytes])
        assert "Binary message" in result

    def test_verbose_mode_includes_highlights(self, sample_commit: Commit) -> None:
        analyzer = MockLLMAnalyzer(verbosity=2)
        result = analyzer.analyze_commits([sample_commit])

        assert "Highlights:" in result
        assert "main.py" in result
        assert "utils.py" in result
