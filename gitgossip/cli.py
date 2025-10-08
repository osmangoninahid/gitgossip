"""CLI entrypoint for GitGossip — initializes commands and handles user input."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from gitgossip.commands.summarize import summarize_cmd

console = Console()
app = typer.Typer(help="GitGossip 🧠 — Human-friendly Git summaries and digests for developers.")


@app.command(help="Human-friendly changes summary", rich_help_panel="Available")
def summarize(
    path: str = typer.Argument(
        default_factory=Path.cwd,
        help="Path to the Git repository (default: current directory)",
    ),
    author: str | None = typer.Option(None, "--author", "-a", help="Filter by author name or email"),
    since: str | None = typer.Option(None, "--since", "-s", help="Filter commits since (e.g. '7days' or '2025-10-01')"),
    json_output: bool = typer.Option(False, "--json", help="Output commits as JSON instead of text"),
) -> None:
    """Summarize command."""
    summarize_cmd(path=path, author=author, since=since, json_output=json_output)


@app.command(rich_help_panel="Coming soon", options_metavar="Coming soon...")
def digest() -> None:
    """Digest tool."""
    typer.secho("🚧 Coming soon... This feature is under development.", fg=typer.colors.YELLOW, bold=True)
    raise typer.Exit(code=0)


if __name__ == "__app__":
    app()
