"""CLI entrypoint for GitGossip — initializes commands and handles user input."""

from __future__ import annotations

import typer
from rich.console import Console

from gitgossip.commands import summarize

console = Console()

app = typer.Typer(help="GitGossip 🧠 — Human-friendly Git summaries and digests for developers.")

# Register subcommands
app.add_typer(summarize.app, name="summarize", help="Summarize commits in repositories.")


def main() -> None:
    """CLI entrypoint for GitGossip."""
    app()


if __name__ == "__main__":
    main()
