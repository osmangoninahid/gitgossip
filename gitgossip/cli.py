"""CLI entrypoint for GitGossip — human-friendly Git summaries and digests."""

from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.logging import RichHandler

from gitgossip.commands.commit import commit_cmd
from gitgossip.commands.init import init_config_cmd
from gitgossip.commands.list_authors import list_all_authors
from gitgossip.commands.prompts import prompts_init_cmd
from gitgossip.commands.summarize import summarize_cmd
from gitgossip.commands.summarize_mr import summarize_mr_cmd

console = Console()
app = typer.Typer(help="GitGossip 🧠 — AI-powered commit summaries and merge request digests.")


# Configure Rich logging
logging.basicConfig(
    level=logging.WARNING, format="%(message)s", handlers=[RichHandler(console=console, rich_tracebacks=True)]
)

# Create a named logger
logger = logging.getLogger("gitgossip")

prompts_app = typer.Typer(help="Manage custom prompt templates.")
app.add_typer(prompts_app, name="prompts", rich_help_panel="Setup & Configuration")


@prompts_app.command("init")
def prompts_init() -> None:
    """Scaffold editable prompt templates into your prompts directory."""
    prompts_init_cmd()


@app.command(help="Run the interactive setup wizard for GitGossip.", rich_help_panel="Setup & Configuration")
def init() -> None:
    """Initialize or update GitGossip configuration interactively."""
    init_config_cmd()


@app.command(help="List authors who have contributed recently.", rich_help_panel="Repository Insights")
def list_authors(
    path: str = typer.Argument(
        default_factory=Path.cwd,
        help="Path to a Git repository or a directory containing multiple repositories (default: current directory).",
    ),
    since: str = typer.Option(
        "15days",
        "--since",
        "-s",
        help="Show authors of commits since a specific time. Accepts formats like '7days' or '2025-10-01'.",
    ),
    all_commits: bool = typer.Option(
        False,
        "--all-commits",
        "-a",
        help="Include authors from all commits in history, ignoring the --since filter.",
    ),
) -> None:
    """Display all unique commit authors in one or more repositories."""
    list_all_authors(path=path, since=since, all_commits=all_commits)


@app.command(help="Summarize recent commits into a human-friendly digest.", rich_help_panel="AI Summaries")
def summarize(
    path: str = typer.Argument(
        default_factory=Path.cwd,
        help="Path to the Git repository (default: current directory).",
    ),
    author: str | None = typer.Option(
        None,
        "--author",
        "-a",
        help="Filter commits by author name or email. Use 'gitgossip list-authors' to view available authors.",
    ),
    since: str | None = typer.Option(
        None,
        "--since",
        "-s",
        help="Show commits since a specific time (e.g. '7days' or '2025-10-01'). Default: 15 days.",
    ),
    use_mock: bool = typer.Option(
        False,
        "--use-mock",
        help="Use the mock LLM analyzer (for local testing) instead of calling a real AI model.",
    ),
) -> None:
    """Generate a plain-English summary of recent Git commits."""
    summarize_cmd(path=path, author=author, since=since, use_mock=use_mock)


@app.command(help="Generate an AI-assisted Merge Request title and description.", rich_help_panel="AI Summaries")
def summarize_mr(
    target_branch: str = typer.Argument(..., help="Branch to compare against (e.g. main, develop)."),
    path: str = typer.Option(".", "--path", help="Path to the Git repository (default: current directory)."),
    pull: bool = typer.Option(False, "--pull", help="Pull the latest target branch before creating the diff."),
    use_mock: bool = typer.Option(False, "--use-mock", help="Use the mock LLM analyzer instead of a real model."),
) -> None:
    """Generate a human-readable summary for a Merge Request."""
    summarize_mr_cmd(target_branch=target_branch, path=path, pull=pull, use_mock=use_mock)


@app.command(help="Generate an AI commit message from staged changes.", rich_help_panel="AI Summaries")
def commit(
    path: str = typer.Option(".", "--path", help="Path to the Git repository (default: current directory)."),
    print_only: bool = typer.Option(False, "--print", help="Print the generated message and exit (no commit)."),
    hook_file: str | None = typer.Option(
        None, "--hook", help="prepare-commit-msg mode: write the message into the given file and exit 0."
    ),
    use_mock: bool = typer.Option(False, "--use-mock", help="Use the mock LLM analyzer instead of a real model."),
) -> None:
    """Generate a Conventional Commit message from the staged diff."""
    commit_cmd(path=path, print_only=print_only, hook_file=hook_file, use_mock=use_mock)


@app.command(rich_help_panel="Miscellaneous")
def digest() -> None:
    """(Coming soon) Generate a full developer activity digest."""
    typer.secho("🚧 Coming soon... This feature is under development.", fg=typer.colors.YELLOW, bold=True)
    raise typer.Exit(code=0)


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    """Show help when no command is provided."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()
