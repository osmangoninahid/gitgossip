"""CLI entrypoint for GitGossip — initializes commands and handles user input."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from gitgossip.commands.init import init_config_cmd
from gitgossip.commands.summarize import summarize_cmd
from gitgossip.commands.summarize_mr import summarize_mr_cmd

console = Console()
app = typer.Typer(help="GitGossip 🧠 — Human-friendly Git summaries and digests for developers.")


@app.command(help="Interactive setup wizard for GitGossip", rich_help_panel="Setup & Configuration")
def init() -> None:
    """Initialize or update GitGossip configuration interactively."""
    init_config_cmd()


@app.command(help="Human-friendly changes summary", rich_help_panel="Available")
def summarize(
    path: str = typer.Argument(
        default_factory=Path.cwd,
        help="Path to the Git repository (default: current directory)",
    ),
    author: str | None = typer.Option(None, "--author", "-a", help="Filter by author name or email"),
    since: str | None = typer.Option(None, "--since", "-s", help="Filter commits since (e.g. '7days' or '2025-10-01')"),
    use_mock: bool = typer.Option(False, "--use-mock", help="Use mock llm analyzer instead of real llm analyzer"),
) -> None:
    """Summarize command."""
    summarize_cmd(path=path, author=author, since=since, use_mock=use_mock)


@app.command(help="Generate Merge Request title & description", rich_help_panel="Available")
def summarize_mr(
    target_branch: str = typer.Argument(..., help="Branch to compare against (e.g., main or develop)"),
    path: str = typer.Option(".", "--path", help="Path to the Git repository"),
    pull: bool = typer.Option(False, "--pull", help="Pull latest target branch before diffing"),
    use_mock: bool = typer.Option(False, "--use-mock", help="Use mock llm analyzer instead of real llm analyzer"),
) -> None:
    """Summarize Merge Request command."""
    summarize_mr_cmd(target_branch=target_branch, path=path, pull=pull, use_mock=use_mock)


@app.command(rich_help_panel="Coming soon", options_metavar="Coming soon...")
def digest() -> None:
    """Digest tool."""
    typer.secho("🚧 Coming soon... This feature is under development.", fg=typer.colors.YELLOW, bold=True)
    raise typer.Exit(code=0)


if __name__ == "__app__":
    app()
