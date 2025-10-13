"""Generate an AI-powered Merge Request title and description."""

from __future__ import annotations

from pathlib import Path

import typer
from git import GitCommandError, Repo
from rich.console import Console
from rich.panel import Panel

from gitgossip.core.factories.llm_analyzer_factory import LLMAnalyzerFactory
from gitgossip.core.parsers.commit_parser import CommitParser
from gitgossip.core.providers.git_repo_provider import GitRepoProvider
from gitgossip.core.services.summarizer_service import SummarizerService

console = Console()


def summarize_mr_cmd(target_branch: str, path: str, pull: bool = False, use_mock: bool = False) -> None:
    """Generate a professional Merge Request title & description from code differences."""
    console.print(f"[bold green]Preparing to generate MR summary for target branch:[/bold green] {target_branch}")

    if pull:
        try:
            repo = Repo(path)
            current_branch = repo.active_branch.name
            console.print(f"[blue]Fetching latest updates for '{target_branch}'...[/blue]")
            repo.git.fetch("origin", target_branch)
            repo.git.checkout(target_branch)
            repo.git.pull("origin", target_branch)
            repo.git.checkout(current_branch)
            console.print(f"[green]✅ Refreshed target branch '{target_branch}' successfully.[/green]\n")
        except GitCommandError as e:
            console.print(f"[red]Failed to update target branch: {e}[/red]")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[red]Unexpected error while pulling branch: {e}[/red]")
            raise typer.Exit(code=1)
    try:
        analyzer = LLMAnalyzerFactory().get_analyzer(use_mock=use_mock)

        summarizer = SummarizerService(
            commit_parser=CommitParser(repo_provider=GitRepoProvider(path=Path(path))),
            llm_analyzer=analyzer,
        )

        title, description = summarizer.summarize_for_merge_request(target_branch)
        console.print(
            Panel.fit(
                f"[bold underline]{title}[/bold underline]\n\n{description.strip()}",
                title=f"[green]Merge Request Summary — {Path(path).name}[/green]",
                border_style="cyan",
                padding=(1, 2),
            )
        )

        if title.startswith("[LLM ERROR]") or title.startswith("[SYSTEM ERROR]"):
            console.print(f"[red]❌ Failed to generate MR summary: {description}[/red]")
            raise typer.Exit(code=1)

        console.print("\n[green]✨ Merge Request summary generated successfully![/green]")

    except Exception as e:
        console.print(f"[red]Error generating MR summary: {e}[/red]")
        raise typer.Exit(code=1)
