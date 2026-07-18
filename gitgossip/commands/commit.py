"""Generate an AI commit message from staged changes."""

from __future__ import annotations

import logging
from pathlib import Path

import click
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from gitgossip.core.factories.llm_analyzer_factory import LLMAnalyzerFactory
from gitgossip.core.providers.git_repo_provider import GitRepoProvider

console = Console()


def commit_cmd(path: str, print_only: bool, hook_file: str | None, use_mock: bool) -> None:
    """Generate a Conventional Commit message from the staged diff and optionally commit."""
    if hook_file is not None:
        _run_hook_mode(msg_file=Path(hook_file), path=path, use_mock=use_mock)
        return

    provider = GitRepoProvider(path=Path(path))
    diff_text = provider.get_staged_diff()
    if not diff_text.strip():
        console.print("[yellow]Nothing staged. Stage changes first, e.g. [cyan]git add -p[/cyan].[/yellow]")
        raise typer.Exit(code=1)

    analyzer = LLMAnalyzerFactory().get_analyzer(use_mock=use_mock)
    file_summary = ", ".join(provider.get_staged_files())
    message = analyzer.generate_commit_message(diff_text, file_summary)

    if message.startswith("[LLM ERROR]"):
        console.print(f"[red]Failed to generate commit message: {message}[/red]")
        raise typer.Exit(code=1)

    if print_only:
        typer.echo(message)
        return

    while True:
        console.print(Panel.fit(message, title="[green]Proposed commit message[/green]", border_style="cyan"))
        choice = Prompt.ask("[a]ccept / [e]dit / [r]egenerate / [q]uit", choices=["a", "e", "r", "q"], default="a")

        if choice == "a":
            provider.get_repo().git.commit("-m", message)
            console.print("[green]✅ Committed.[/green]")
            return
        if choice == "e":
            edited = click.edit(message)
            if edited is not None and edited.strip():
                message = edited.strip()
        elif choice == "r":
            message = analyzer.generate_commit_message(diff_text, file_summary)
            if message.startswith("[LLM ERROR]"):
                console.print(f"[red]Regeneration failed: {message}[/red]")
                raise typer.Exit(code=1)
        else:
            console.print("[yellow]Aborted. Nothing committed.[/yellow]")
            raise typer.Exit(code=0)


def _run_hook_mode(msg_file: Path, path: str, use_mock: bool) -> None:
    """Fill the commit-message file for prepare-commit-msg.

    Fail-open by design: any error leaves the file untouched and returns
    normally so a broken model can never block a commit.
    """
    try:
        existing = msg_file.read_text(encoding="utf-8") if msg_file.exists() else ""
        has_real_message = any(line.strip() and not line.lstrip().startswith("#") for line in existing.splitlines())
        if has_real_message:
            return

        provider = GitRepoProvider(path=Path(path))
        diff_text = provider.get_staged_diff()
        if not diff_text.strip():
            return

        analyzer = LLMAnalyzerFactory().get_analyzer(use_mock=use_mock)
        message = analyzer.generate_commit_message(diff_text, ", ".join(provider.get_staged_files()))
        if message.startswith("[LLM ERROR]"):
            return

        msg_file.write_text(f"{message}\n{existing}", encoding="utf-8")
    except Exception:  # noqa: BLE001 — fail-open is the hook contract
        logging.getLogger("gitgossip.commit-hook").debug("Hook mode failed; leaving message file untouched.")
