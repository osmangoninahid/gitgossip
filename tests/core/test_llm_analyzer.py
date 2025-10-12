"""Unit tests for MockLLMAnalyzer covering all implemented behaviors."""

import pytest

from gitgossip.core.llm.mock_llm_analyzer import MockLLMAnalyzer
from gitgossip.core.models.commit import Commit


class TestMockLLMAnalyzer:
    """Verify mock analyzer behavior end-to-end."""

    @pytest.fixture()
    def sample_commit(self) -> Commit:
        """Return a sample Commit object."""
        return Commit(
            hash="abc123def456",
            author="osman",
            email="osman@example.com",
            message="Refactor code",
            files_changed=2,
            insertions=8,
            deletions=3,
            changes=[
                {"file": "main.py", "summary": ["refactored main function"]},
                {"file": "utils.py", "summary": ["simplified helpers"]},
            ],
        )

    def test_analyze_commits_no_commits(self) -> None:
        # given
        analyzer = MockLLMAnalyzer()

        # when
        result = analyzer.analyze_commits([])

        # then
        assert result == "No commits found to analyze."

    def test_analyze_commits_single_commit(self, sample_commit: Commit) -> None:
        # given
        analyzer = MockLLMAnalyzer()

        # when
        result = analyzer.analyze_commits([sample_commit])

        # then
        assert "by osman" in result
        assert "`abc123d`" in result
        assert "Refactor code" in result
        assert "(+8/-3, 2 files)" in result

    def test_analyze_commits_verbose_mode(self, sample_commit: Commit) -> None:
        # given
        analyzer = MockLLMAnalyzer(verbosity=2)

        # when
        result = analyzer.analyze_commits([sample_commit])

        # then
        assert "Highlights:" in result
        assert "main.py" in result
        assert "utils.py" in result

    def test_summarize_diff_chunk_basic(self) -> None:
        # given
        analyzer = MockLLMAnalyzer()
        diff_text = "+ added feature\n- removed bug"

        # when
        result = analyzer.summarize_diff_chunk(diff_text, metadata="[Part 1/2]")

        # then
        assert "Mock Summary" in result
        assert "[Part 1/2]" in result
        assert "lines changed" in result

    def test_summarize_diff_chunk_empty(self) -> None:
        # given
        analyzer = MockLLMAnalyzer()

        # when
        result = analyzer.summarize_diff_chunk("", metadata="[Part 1/1]")

        # then
        assert "No changes" in result

    def test_synthesize_chunk_summaries_combines_chunks(self) -> None:
        # given
        analyzer = MockLLMAnalyzer()
        summaries = ["chunk A summary", "chunk B summary"]

        # when
        result = analyzer.synthesize_chunk_summaries(summaries)

        # then
        assert "Mock Synthesized Summary" in result
        assert "Combined 2 chunk summaries" in result
        assert "chunk A summary" in result

    def test_synthesize_chunk_summaries_empty(self) -> None:
        # given
        analyzer = MockLLMAnalyzer()

        # when
        result = analyzer.synthesize_chunk_summaries([])

        # then
        assert "No summaries" in result
