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

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("run", hidden=True)
def summarize_run() -> None:
    """(internal fallback)."""
    typer.echo("Use: gitgossip summarize <repo_path>")


@app.callback(invoke_without_command=True)
def summarize_command(
    path: str = typer.Argument(
        ".",
        help="Path to the Git repository (default: current directory)",
    ),
    author: str | None = typer.Option(None, "--author", "-a", help="Filter by author name or email"),
    since: str | None = typer.Option(None, "--since", "-s", help="Filter commits since (e.g. '7days' or '2025-10-01')"),
    json_output: bool = typer.Option(False, "--json", help="Output commits as JSON instead of text"),
) -> None:
    """Summarize recent commits for a repository."""
    repo_path = Path(path).expanduser().resolve()

    try:
        parser = GitParser(str(repo_path))
        commits = parser.get_commits(author=author, since=since)
    except (InvalidGitRepositoryError, NoSuchPathError) as e:
        console.print(f"[red]Invalid repository: {e}[/red]")
        raise typer.Exit(code=1)
    except OSError as e:
        console.print(f"[red]Filesystem error: {e}[/red]")
        raise typer.Exit(code=1)

    if not commits:
        console.print("[yellow]No commits found for the given filters.[/yellow]")
        raise typer.Exit()

    if json_output:
        console.print_json(json.dumps([c.model_dump(mode="json") for c in commits], indent=2))
        return

    console.rule(f"[bold blue]Summary for {repo_path.name}[/bold blue]")
    _print_commit_list(commits)


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
