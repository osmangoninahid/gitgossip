"""Unit tests for SummarizerService with mock RepoProvider."""

import datetime
from unittest.mock import MagicMock

from gitgossip.core.models.commit import Commit
from gitgossip.core.services.summarizer_service import SummarizerService


class TestSummarizerService:
    """Verify summarizer correctly delegates to parser."""

    def test_summarize_repository_delegates_to_commit_parser(self) -> None:
        """Should call CommitParser.get_commits and pass result to LLM analyzer."""
        # given
        mock_commit_parser = MagicMock()
        mock_llm_analyzer = MagicMock()
        mock_commit = Commit(
            hash="abc123",
            author="Test Author",
            email="test@example.com",
            date=datetime.datetime.now(datetime.timezone.utc),
            message="test",
            insertions=1,
            deletions=0,
            files_changed=1,
            changes=[],
        )
        mock_commit_parser.get_commits.return_value = [mock_commit]
        mock_llm_analyzer.analyze_commits.return_value = "mock-summary"

        service = SummarizerService(commit_parser=mock_commit_parser, llm_analyzer=mock_llm_analyzer)

        # when
        result = service.summarize_repository(author="me", since="1days", limit=5)

        # then
        mock_commit_parser.get_commits.assert_called_once_with(author="me", since="1days", limit=5)
        mock_llm_analyzer.analyze_commits.assert_called_once_with([mock_commit])
        assert result == "mock-summary"
