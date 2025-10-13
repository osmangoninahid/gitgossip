"""List all unique Git authors within one or more repositories."""

from __future__ import annotations

from pathlib import Path
from typing import Set

import typer
from git import Repo
from rich.console import Console

from gitgossip.core.services.repo_discovery_service import RepoDiscoveryService
from gitgossip.utils.parse import parse_since

console = Console()


def list_all_authors(path: str, since: str, all_commits: bool = False) -> None:
    """Display all unique commit authors in one or more repositories.

    Args:
        path: Path to a Git repository or a directory containing multiple repos.
        since: Time filter for commits (e.g. "7days" or "2025-10-01"). Ignored if `all_commits` is True.
        all_commits: Whether to include all commits in history, bypassing time filtering.
    """
    work_dir = Path(path).expanduser().resolve()

    # Case 1: Single Git repository
    if (work_dir / ".git").exists():
        _get_authors_from_commits(work_dir, since, all_commits)
        return

    # Case 2: Directory containing multiple Git repositories
    repo_discovery = RepoDiscoveryService(base_dir=work_dir)
    repos = repo_discovery.find_repositories()
    if not repos:
        console.print(f"[red]No Git repositories found in {work_dir}[/red]")
        raise typer.Exit(code=1)


def _get_authors_from_commits(path: Path, since: str, all_commits: bool) -> None:
    """Extract authors from Git commit history and print them."""
    since_date = None if all_commits else parse_since(since)
    repo = Repo(path)
    authors: Set[str] = set()

    for commit in repo.iter_commits(since=since_date):
        authors.add(f"{commit.author.name} <{commit.author.email}>")

    if not authors:
        console.print("[yellow]No commits found in the given range.[/yellow]")
        raise typer.Exit(code=0)

    header = f"Authors from the last {since}" if not all_commits else "All authors in repository"
    console.print(f"\n[bold]{header}[/bold]\n")

    for idx, author in enumerate(sorted(authors), start=1):
        console.print(f"[cyan]{idx}.[/cyan] {author}")

    console.print(f"\n[green]Total unique authors: {len(authors)}[/green]")
