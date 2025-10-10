"""Summarize command — generates repository-level summaries via LLM or mock analyzer."""

from __future__ import annotations

import os
from pathlib import Path

import typer
from git import InvalidGitRepositoryError, NoSuchPathError
from rich.console import Console
from rich.panel import Panel

from gitgossip.core.llm.llm_analyzer import LLMAnalyzer
from gitgossip.core.llm.mock_llm_analyzer import MockLLMAnalyzer
from gitgossip.core.parsers.commit_parser import CommitParser
from gitgossip.core.providers.git_repo_provider import GitRepoProvider
from gitgossip.core.services.repo_discovery_service import RepoDiscoveryService
from gitgossip.core.services.summarizer_service import SummarizerService

console = Console()


def summarize_cmd(
    path: str,
    author: str | None = None,
    since: str | None = None,
    use_mock: bool = False,
) -> None:
    """Summarize recent commits for a repository (or multiple) using AI.

    Produces a single natural-language summary string describing changes.
    """
    work_dir = Path(path).expanduser().resolve()

    # Case 1: Direct git repo
    if (work_dir / ".git").exists():
        _summarize_repo(work_dir, author, since, use_mock)
        return

    # Case 2: Folder containing multiple repos
    repo_discovery = RepoDiscoveryService(base_dir=work_dir)
    repos = repo_discovery.find_repositories()
    if not repos:
        console.print(f"[red]No git repositories found in {work_dir}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[bold blue]Found {len(repos)} repositories under {work_dir}[/bold blue]\n")
    for repo in repos:
        console.rule(f"[bold cyan]{repo.name}[/bold cyan]")
        _summarize_repo(repo, author, since, use_mock)


def _summarize_repo(
    repo_path: Path,
    author: str | None,
    since: str | None,
    use_mock: bool,
) -> None:
    """Summarize commits for a single repository using the LLM analyzer."""
    try:
        # Initialize analyzer (mock or real)
        analyzer = (
            MockLLMAnalyzer()
            if use_mock
            else LLMAnalyzer(
                model="llama3:8b",
                api_key=os.getenv("OPENAI_API_KEY"),
            )
        )

        summarizer = SummarizerService(
            commit_parser=CommitParser(repo_provider=GitRepoProvider(path=repo_path)),
            llm_analyzer=analyzer,
        )

        summary_text = summarizer.summarize_repository(author=author, since=since)
    except (FileNotFoundError, InvalidGitRepositoryError, NoSuchPathError) as e:
        console.print(f"[red]Invalid repository at {repo_path}: {e}[/red]")
        return
    except (OSError, ValueError) as e:
        console.print(f"[red]Error reading commits in {repo_path}: {e}[/red]")
        return

    if not summary_text:
        console.print(f"[yellow]No commits found in {repo_path.name}.[/yellow]\n")
        return

    # Display AI summary
    _print_summary(repo_path, summary_text)


def _print_summary(repo_path: Path, summary: str) -> None:
    """Pretty-print the repository summary in a Rich panel."""
    console.print(
        Panel.fit(
            summary.strip(),
            title=f"[bold green]AI Summary for {repo_path.name}[/bold green]",
            border_style="cyan",
            padding=(1, 2),
        )
    )
