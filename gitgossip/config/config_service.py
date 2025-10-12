"""Handles reading and writing of GitGossip configuration (e.g., LLM setup, prompt paths)."""

from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError


class ConfigService:
    """Manages GitGossip configuration persistence."""

    DEFAULT_CONFIG_PATH = Path.home() / ".gitgossip" / "config.yaml"

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize the ConfigService with optional custom config path."""
        self._yaml = YAML()
        self._yaml.default_flow_style = False
        self._yaml.indent(mapping=2, sequence=4, offset=2)
        self._path = config_path or self.DEFAULT_CONFIG_PATH
        self._logger = logging.getLogger(self.__class__.__name__)

    def load(self) -> Dict[str, Any]:
        """Load config from disk. Returns an empty default if missing or invalid."""
        if not self._path.exists():
            self._logger.info("No config file found at %s. Returning default config.", self._path)
            return self._default_config()

        try:
            with self._path.open("r", encoding="utf-8") as f:
                config = self._yaml.load(f)
                if not isinstance(config, dict):
                    raise ValueError("Invalid config format (expected mapping).")
                return config
        except (FileNotFoundError, PermissionError, OSError, ValueError, YAMLError) as e:
            self._logger.warning("Failed to load config at %s: %s", self._path, e)
            return self._default_config()

    def save(self, config: Dict[str, Any]) -> None:
        """Persist the given configuration dictionary to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            self._yaml.dump(config, f)
        self._logger.info("Configuration saved successfully to %s", self._path)

    def ensure_exists(self) -> Dict[str, Any]:
        """Ensure config file exists, returning it or initializing defaults."""
        if not self._path.exists():
            self._logger.info("Initializing default GitGossip config at %s", self._path)
            default = self._default_config()
            self.save(default)
            return default
        return self.load()

    def update(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Merge updates into existing config and save."""
        current = self.ensure_exists()
        self._deep_update(current, updates)
        self.save(current)
        return current

    def default(self) -> Dict[str, Any]:
        """Public wrapper to retrieve default config (for tests or CLI init)."""
        return self._default_config()

    @staticmethod
    def _deep_update(base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Recursively update nested dictionaries."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigService._deep_update(base[key], value)
            else:
                base[key] = value

    @staticmethod
    def _default_config() -> Dict[str, Any]:
        """Return a default configuration structure."""
        return {
            "llm": {
                "provider": "local",  # or "cloud"
                "model": "qwen2.5-coder:1.5b",
                "base_url": "http://localhost:11434/v1",
                "api_key": None,
            },
            "paths": {
                "prompts": str(Path.home() / ".gitgossip" / "prompts"),
            },
            "meta": {
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
                "version": "1.0",
            },
        }
