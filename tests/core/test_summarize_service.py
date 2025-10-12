"""Unit tests for SummarizerService verifying hierarchical summarization flow."""

import datetime
import itertools
from unittest.mock import MagicMock

from gitgossip.core.models.commit import Commit
from gitgossip.core.services.summarizer_service import SummarizerService


class TestSummarizerService:
    """Validate chunk-based summarization and MR summary delegation."""

    def test_summarize_repository_delegates_to_analyzer(self) -> None:
        # given (arrange)
        mock_parser = MagicMock()
        mock_analyzer = MagicMock()

        mock_commit = Commit(
            hash="abc123",
            author="Nahid",
            email="test@example.com",
            date=datetime.datetime.now(datetime.timezone.utc),
            message="test",
            insertions=5,
            deletions=1,
            files_changed=1,
            changes=[],
        )
        mock_parser.get_commits.return_value = [mock_commit]
        mock_analyzer.analyze_commits.return_value = "commit-summary"

        service = SummarizerService(mock_parser, mock_analyzer)

        # when (act)
        result = service.summarize_repository(author="me", since="2days")

        # then (assert)
        mock_parser.get_commits.assert_called_once_with(author="me", since="2days", limit=100)
        mock_analyzer.analyze_commits.assert_called_once_with([mock_commit])
        assert result == "commit-summary"

    def test_summarize_for_merge_request_large_diff(self) -> None:
        """Should call chunk summarization, synthesis, and final MR summary."""
        # given (arrange)
        mock_parser = MagicMock()
        mock_analyzer = MagicMock()

        # Create a fake diff of ~1000 lines
        mock_parser.repo_provider.get_diff_between_branches.return_value = "+ added code line\n" * 1000

        mock_analyzer.summarize_diff_chunk.side_effect = itertools.cycle(["chunk summary 1", "chunk summary 2"])
        mock_analyzer.synthesize_chunk_summaries.return_value = "merged synthesis"
        mock_analyzer.generate_mr_summary.return_value = (
            "Mock Title",
            "- bullet1\n- bullet2",
        )

        service = SummarizerService(mock_parser, mock_analyzer, chunk_size=100)

        # when (act)
        title, desc = service.summarize_for_merge_request(target_branch="main")

        # then (assert)
        # Summarization called many times but at least once
        assert mock_analyzer.summarize_diff_chunk.call_count > 1
        mock_analyzer.synthesize_chunk_summaries.assert_called_once()
        mock_analyzer.generate_mr_summary.assert_called_once()

        # Check the input to synthesis is an aggregated list of summaries
        args, _ = mock_analyzer.synthesize_chunk_summaries.call_args
        synthesized_input = args[0]
        assert isinstance(synthesized_input, list)
        assert len(synthesized_input) >= 2
        assert any("chunk summary 1" in s for s in synthesized_input)
        assert any("chunk summary 2" in s for s in synthesized_input)

        # Validate MR output
        assert "Mock Title" in title
        assert "- bullet1" in desc

    def test_summarize_for_merge_request_no_diff(self) -> None:
        # given
        mock_parser = MagicMock()
        mock_analyzer = MagicMock()
        mock_parser.repo_provider.get_diff_between_branches.return_value = "   "

        service = SummarizerService(mock_parser, mock_analyzer)

        # when
        title, desc = service.summarize_for_merge_request(target_branch="main")

        # then
        assert "No code changes" in title
        assert "no differences" in desc.lower()
