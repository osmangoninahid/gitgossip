"""Unit tests for the commit command."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import typer

from gitgossip.commands.commit import commit_cmd


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@t.com"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "t"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "commit.gpgsign", "false"], check=True)
    (path / "a.txt").write_text("one\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "a.txt"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "init"], check=True, capture_output=True)


@pytest.fixture()
def staged_repo(tmp_path: Path) -> Path:
    """Create a temp git repo with a staged change."""
    _init_repo(tmp_path)
    (tmp_path / "a.txt").write_text("one\ntwo\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "a.txt"], check=True)
    return tmp_path


@pytest.fixture()
def clean_repo(tmp_path: Path) -> Path:
    """Create a temp git repo with nothing staged."""
    _init_repo(tmp_path)
    return tmp_path


def _log_last_subject(repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "log", "-1", "--pretty=%s"], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


class TestCommitCmd:
    """Verify commit command behavior."""

    def test_nothing_staged_exits_1(self, clean_repo: Path) -> None:
        # when / then
        with pytest.raises(typer.Exit) as exc_info:
            commit_cmd(path=str(clean_repo), print_only=False, hook_file=None, use_mock=True)
        assert exc_info.value.exit_code == 1

    def test_print_only_outputs_message(self, staged_repo: Path, capsys) -> None:
        # when
        commit_cmd(path=str(staged_repo), print_only=True, hook_file=None, use_mock=True)

        # then
        captured = capsys.readouterr()
        assert "chore: mock commit message" in captured.out

    @patch("gitgossip.commands.commit.Prompt.ask", return_value="a")
    def test_accept_commits_staged_changes(self, _mock_ask, staged_repo: Path) -> None:
        # when
        commit_cmd(path=str(staged_repo), print_only=False, hook_file=None, use_mock=True)

        # then
        assert _log_last_subject(staged_repo) == "chore: mock commit message (1 files changed)"

    @patch("gitgossip.commands.commit.Prompt.ask", return_value="q")
    def test_quit_does_not_commit(self, _mock_ask, staged_repo: Path) -> None:
        # when
        with pytest.raises(typer.Exit) as exc_info:
            commit_cmd(path=str(staged_repo), print_only=False, hook_file=None, use_mock=True)

        # then
        assert exc_info.value.exit_code == 0
        assert _log_last_subject(staged_repo) == "init"

    @patch("gitgossip.commands.commit.click.edit", return_value="fix(a): edited message\n")
    @patch("gitgossip.commands.commit.Prompt.ask", side_effect=["e", "a"])
    def test_edit_then_accept_uses_edited_message(self, _mock_ask, _mock_edit, staged_repo: Path) -> None:
        # when
        commit_cmd(path=str(staged_repo), print_only=False, hook_file=None, use_mock=True)

        # then
        assert _log_last_subject(staged_repo) == "fix(a): edited message"
