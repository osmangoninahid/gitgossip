"""Unit tests for GitParser core functionality."""

from datetime import datetime

from gitgossip.core.models.commit import Commit


def test_commit_defaults() -> None:
    """Ensure Commit model uses default values for missing optional fields."""
    commit = Commit(
        hash="abc123",
        author="Osman Goni Nahid",
        email="mine@example.com",
        message="test commit msg",
        insertions=1,
        deletions=0,
        files_changed=1,
    )

    # Check default fallbacks
    assert commit.author == "Unknown author"
    assert isinstance(commit.date, datetime)
    assert commit.message == ""
    assert commit.insertions == 0
    assert commit.deletions == 0
    assert commit.files_changed == 0
