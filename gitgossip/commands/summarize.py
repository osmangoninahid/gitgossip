"""Summarize command — displays commit summaries in human-readable or JSON form."""

from __future__ import annotations

import json
import os
from pathlib import Path

import typer
from git.exc import InvalidGitRepositoryError, NoSuchPathError
from rich.console import Console

from gitgossip.core.git_parser import GitParser
from gitgossip.core.models.commit import Commit

console = Console()


def summarize_cmd(
    path: str,
    author: str | None = None,
    since: str | None = None,
    json_output: bool = False,
) -> None:
    """Summarize recent commits for a repository or multiple repositories."""
    repo_path = Path(path).expanduser().resolve()

    # Case 1: If this path *is* a git repo, handle directly
    if (repo_path / ".git").exists():
        _summarize_single_repo(repo_path, author, since, json_output)
        return

    # Case 2: Otherwise, check for nested repositories
    repos = _find_git_repos(repo_path, recursive=False)
    if not repos:
        console.print(f"[red]No git repositories found in {repo_path}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[bold blue]Found {len(repos)} repositories under {repo_path}[/bold blue]\n")
    for repo in repos:
        console.rule(f"[bold cyan]{repo.name}[/bold cyan]")
        _summarize_single_repo(repo, author, since, json_output)


def _print_commit_list(commits: list[Commit]) -> None:
    """Pretty-print a list of commits in consistent format."""
    for commit in commits:
        msg = commit.message.decode() if isinstance(commit.message, bytes) else str(commit.message)
        console.print(f"[yellow]{commit.hash[:7]}[/yellow] [cyan]{commit.author}[/cyan] • {commit.date:%Y-%m-%d %H:%M}")
        console.print(f"    {msg}  (+{commit.insertions} / -{commit.deletions}, {commit.files_changed} files)\n")


def _find_git_repos(base_dir: Path, recursive: bool) -> list[Path]:
    """Find Git repositories inside a directory."""
    repos: list[Path] = []
    for sub in base_dir.iterdir():
        if (sub / ".git").exists():
            repos.append(sub)
        elif recursive and sub.is_dir():
            for root, dirs, _ in os.walk(sub):
                if ".git" in dirs:
                    repos.append(Path(root))
                    dirs.clear()  # avoid going deeper once repo found
                    break
    return repos


def _summarize_single_repo(repo_path: Path, author: str | None, since: str | None, json_output: bool) -> None:
    """Summarize commits for a single repository."""
    try:
        parser = GitParser(str(repo_path))
        if not parser.has_commits:
            console.print(f"[yellow]Skipping {repo_path.name}: no commits yet.[/yellow]\n")
            return
        commits = parser.get_commits(author=author, since=since)
    except (InvalidGitRepositoryError, NoSuchPathError) as e:
        console.print(f"[red]Invalid repository at {repo_path}: {e}[/red]")
        return
    except OSError as e:
        console.print(f"[red]Filesystem error reading {repo_path}: {e}[/red]")
        return

    if not commits:
        console.print("[yellow]No commits found.[/yellow]\n")
        return

    if json_output:
        console.print_json(json.dumps([c.model_dump(mode="json") for c in commits], indent=2))
        return

    _print_commit_list(commits)
