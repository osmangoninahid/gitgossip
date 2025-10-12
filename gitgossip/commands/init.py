"""Initialize or update GitGossip configuration interactively."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Any, Dict

import psutil
from rich.console import Console
from rich.prompt import Prompt

from gitgossip.config.config_service import ConfigService

console = Console()


def _get_local_ollama_models() -> list[str]:
    """Return a list of installed Ollama models, or [] if unavailable."""
    if not shutil.which("ollama"):
        return []
    try:
        result = subprocess.run(
            ["ollama", "list", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        models = [m["model"] for m in json.loads(result.stdout)]
        return sorted(models)
    except (subprocess.SubprocessError, json.JSONDecodeError):
        return []


def _select_provider(default_provider: str) -> str:
    """Prompt user to choose between local or cloud provider."""
    provider_input = (
        Prompt.ask(
            "Select LLM provider [local/cloud]",
            default=default_provider,
        )
        .strip()
        .lower()
    )

    if provider_input in {"l", "local"}:
        return "local"
    if provider_input in {"c", "cloud"}:
        return "cloud"

    console.print("[yellow]Invalid provider input. Defaulting to 'local'.[/yellow]")
    return "local"


def _select_local_model(default_model: str) -> str:
    """Prompt user to choose or enter a local Ollama model."""
    available_models = _get_local_ollama_models()
    if not available_models:
        console.print("[yellow]No local Ollama models detected.[/yellow]")
        console.print("You can pull one later using: [cyan]ollama pull qwen2.5-coder:7b[/cyan]")
        model_choices = ["qwen2.5-coder:7b", "llama3:8b", "phi3:mini"]
    else:
        console.print(f"[green]Detected {len(available_models)} local models from Ollama.[/green]")
        model_choices = available_models

    selected_model = Prompt.ask(
        "Select or enter model name",
        choices=model_choices,
        default=default_model or model_choices[0],
    )

    _warn_if_insufficient_resources(selected_model)

    return selected_model


def _configure_cloud_llm(cfg: Dict[str, Any]) -> None:
    """Prompt user for base URL and API key for a cloud LLM."""
    base_url = Prompt.ask(
        "Enter OpenAI-compatible Base URL",
        default=cfg["llm"].get("base_url", "https://api.openai.com/v1"),
    )
    api_key = Prompt.ask(
        "Enter API key (leave blank to use)",
        default=cfg["llm"].get("api_key"),
    )

    cfg["llm"]["base_url"] = base_url
    cfg["llm"]["api_key"] = api_key


def _warn_if_insufficient_resources(model_name: str) -> None:
    """Warn user if selected model might exceed system capacity."""
    # Extract model parameter size (e.g., 7b → 7)
    match = re.search(r"(\d+)\s*b", model_name.lower())
    if not match:
        return  # can't estimate
    params_billion = int(match.group(1))

    # Approximate memory need: 1.5 GB per billion params × 1.5 overhead
    required_gb = params_billion * 1.5 * 1.5
    available_gb = psutil.virtual_memory().total / (1024**3)

    if available_gb < required_gb:
        console.print(
            f"\n[yellow]⚠️  Warning:[/yellow] The selected model [cyan]{model_name}[/cyan] "
            f"typically requires around [bold]{required_gb:.1f} GB[/bold] RAM, "
            f"but your system has only [bold]{available_gb:.1f} GB[/bold]."
        )
        console.print(
            "This may cause slow performance or failures.\n"
            "👉 Consider using a smaller model (e.g. `qwen2.5-coder:1.5b`) "
            "or switch to cloud mode for better performance.\n"
        )


def init_config_cmd() -> None:
    """Interactive configuration command for GitGossip."""
    service = ConfigService()
    cfg = service.load()

    provider = _select_provider(cfg["llm"].get("provider", "local"))
    cfg["llm"]["provider"] = provider

    if provider == "local":
        cfg["llm"]["model"] = _select_local_model(cfg["llm"].get("model", ""))
        cfg["llm"]["api_key"] = "local-dummy"  # To by-pass openai client
    else:
        _configure_cloud_llm(cfg)

    service.save(cfg)
    console.print("[green]Configuration saved successfully![/green]")
