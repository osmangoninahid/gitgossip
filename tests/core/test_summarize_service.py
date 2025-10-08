"""Unit tests for SummarizerService with mock RepoProvider."""

import datetime
from unittest.mock import MagicMock

from gitgossip.core.models.commit import Commit
from gitgossip.core.services.summarizer_service import SummarizerService


class TestSummarizerService:
    """Verify summarizer correctly delegates to parser."""

    def test_summarize_repository_delegates_to_commit_parser(self) -> None:
        """Should call CommitParser.get_commits with correct params."""
        # given
        mock_commit_parser = MagicMock()
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
        service = SummarizerService(commit_parser=mock_commit_parser)

        # when
        result = service.summarize_repository(author="me", since="1days", limit=5)

        # then
        assert result == [mock_commit]
        mock_commit_parser.get_commits.assert_called_once_with(author="me", since="1days", limit=5)
