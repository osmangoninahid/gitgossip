"""Summarize command — displays commit summaries in human-readable or JSON form."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from git import InvalidGitRepositoryError, NoSuchPathError
from rich.console import Console

from gitgossip.core.models.commit import Commit
from gitgossip.core.parsers.commit_parser import CommitParser
from gitgossip.core.providers.git_repo_provider import GitRepoProvider
from gitgossip.core.services.repo_discovery_service import RepoDiscoveryService
from gitgossip.core.services.summarizer_service import SummarizerService

console = Console()


def summarize_cmd(
    path: str,
    author: str | None = None,
    since: str | None = None,
    json_output: bool = False,
) -> None:
    """Summarize recent commits for a repository or multiple repositories."""
    work_dir = Path(path).expanduser().resolve()

    # Case 1: If this path *is* a git repo, handle directly
    if (work_dir / ".git").exists():
        _summarize_repo(work_dir, author, since, json_output)
        return

    # Case 2: Otherwise, check for nested repositories using discovery service
    repo_discovery = RepoDiscoveryService(base_dir=work_dir)
    repos = repo_discovery.find_repositories()
    if not repos:
        console.print(f"[red]No git repositories found in {work_dir}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[bold blue]Found {len(repos)} repositories under {work_dir}[/bold blue]\n")
    for repo in repos:
        console.rule(f"[bold cyan]{repo.name}[/bold cyan]")
        _summarize_repo(repo, author, since, json_output)


def _summarize_repo(
    repo_path: Path,
    author: str | None,
    since: str | None,
    json_output: bool,
) -> None:
    """Summarize commits for a single repository using the summarizer service."""
    try:
        summarizer = SummarizerService(commit_parser=CommitParser(repo_provider=GitRepoProvider(path=repo_path)))
        commits = summarizer.summarize_repository(author=author, since=since)
    except (FileNotFoundError, InvalidGitRepositoryError, NoSuchPathError) as e:
        console.print(f"[red]Invalid repository at {repo_path}: {e}[/red]")
        return
    except (OSError, ValueError) as e:
        console.print(f"[red]Error while reading commits for {repo_path}: {e}[/red]")
        return
    if not commits:
        console.print(f"[yellow]No commits found in {repo_path.name}.[/yellow]\n")
        return

    if json_output:
        console.print_json(json.dumps([c.model_dump(mode="json") for c in commits], indent=2))
    else:
        _print_commit_list(commits)


def _print_commit_list(commits: list[Commit]) -> None:
    """Pretty-print a list of commits in consistent format."""
    for commit in commits:
        msg = commit.message.decode() if isinstance(commit.message, bytes) else str(commit.message)
        console.print(f"[yellow]{commit.hash[:7]}[/yellow] [cyan]{commit.author}[/cyan] • {commit.date:%Y-%m-%d %H:%M}")
        console.print(f"    {msg}  (+{commit.insertions} / -{commit.deletions}, {commit.files_changed} files)\n")
