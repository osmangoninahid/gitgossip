"""Scaffold user-editable prompt templates."""

from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from gitgossip.config.config_service import ConfigService
from gitgossip.core.llm import prompt_builder

console = Console()

DEFAULT_TEMPLATES_DIR = Path(prompt_builder.__file__).parent / "prompts"


def prompts_init_cmd() -> None:
    """Copy the default prompt templates into the user prompts directory for editing."""
    cfg = ConfigService().load()
    prompts_path = cfg.get("paths", {}).get("prompts") or str(Path.home() / ".gitgossip" / "prompts")
    target_dir = Path(prompts_path)
    target_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    skipped: list[str] = []
    for template in sorted(DEFAULT_TEMPLATES_DIR.glob("*.txt")):
        destination = target_dir / template.name
        if destination.exists():
            skipped.append(template.name)
            continue
        shutil.copyfile(template, destination)
        copied.append(template.name)

    if copied:
        console.print(f"[green]Created:[/green] {', '.join(copied)} → {target_dir}")
    if skipped:
        console.print(f"[yellow]Skipped (already exist):[/yellow] {', '.join(skipped)}")
    console.print("Edit these files to customize tone and structure; gitgossip picks them up automatically.")
