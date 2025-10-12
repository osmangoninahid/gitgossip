"""Unit tests for ConfigService (GitGossip configuration persistence)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from ruamel.yaml import YAML

from gitgossip.config.config_service import ConfigService


class TestConfigService:
    """Verify configuration load, save, update, and initialization behaviors."""

    @pytest.fixture()
    def temp_config_path(self, tmp_path: Path) -> Path:
        """Provide a temporary config file path for isolation."""
        return tmp_path / "config.yaml"

    def test_default_config_structure(self, temp_config_path: Path) -> None:
        # given
        service = ConfigService(config_path=temp_config_path)

        # when
        cfg = service.default()

        # then
        assert "llm" in cfg
        assert "paths" in cfg
        assert "meta" in cfg
        assert "provider" in cfg["llm"]
        assert "model" in cfg["llm"]

    def test_save_and_load_roundtrip(self, temp_config_path: Path) -> None:
        # given
        service = ConfigService(config_path=temp_config_path)
        sample_config = {"llm": {"provider": "cloud", "model": "gpt-4o"}}

        # when
        service.save(sample_config)
        loaded = service.load()

        # then
        assert loaded["llm"]["provider"] == "cloud"
        assert loaded["llm"]["model"] == "gpt-4o"
        assert temp_config_path.exists()

    def test_load_returns_default_if_file_missing(self, tmp_path: Path) -> None:
        # given
        config_path = tmp_path / "nonexistent.yaml"
        service = ConfigService(config_path=config_path)

        # when
        result = service.load()

        # then
        assert isinstance(result, dict)
        assert result["llm"]["provider"] == "local"

    def test_load_invalid_yaml_returns_default(self, temp_config_path: Path) -> None:
        # given
        bad_yaml_content = "::: not valid yaml :::"
        temp_config_path.write_text(bad_yaml_content)
        service = ConfigService(config_path=temp_config_path)

        # when
        result = service.load()

        # then
        assert result["llm"]["provider"] == "local"

    def test_ensure_exists_creates_file_with_defaults(self, temp_config_path: Path) -> None:
        # given
        service = ConfigService(config_path=temp_config_path)
        assert not temp_config_path.exists()

        # when
        result = service.ensure_exists()

        # then
        assert temp_config_path.exists()
        assert "llm" in result
        loaded = service.load()
        assert loaded["llm"]["provider"] == "local"

    def test_update_merges_deeply(self, temp_config_path: Path) -> None:
        # given
        service = ConfigService(config_path=temp_config_path)
        service.save(service.default())
        update_data = {"llm": {"provider": "cloud", "api_key": "abc123"}}

        # when
        result = service.update(update_data)

        # then
        assert result["llm"]["provider"] == "cloud"
        assert result["llm"]["api_key"] == "abc123"
        assert "model" in result["llm"]

    def test_save_logs_success(self, temp_config_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        # given
        service = ConfigService(config_path=temp_config_path)
        caplog.set_level("INFO")

        # when
        service.save(service.default())

        # then
        assert "Configuration saved successfully" in caplog.text

    def test_load_handles_permission_error(self, temp_config_path: Path) -> None:
        # given
        service = ConfigService(config_path=temp_config_path)
        mock_open = MagicMock(side_effect=PermissionError("no access"))

        # when
        with patch("pathlib.Path.open", mock_open):
            result = service.load()

        # then
        assert result["llm"]["provider"] == "local"

    def test_load_handles_yaml_parsing_error(self, temp_config_path: Path) -> None:
        # given
        service = ConfigService(config_path=temp_config_path)
        bad_yaml = MagicMock(spec=YAML)
        bad_yaml.load.side_effect = Exception("YAML parse failure")

        # when
        with patch.object(service, "_yaml", bad_yaml):
            result = service.load()

        # then
        assert "llm" in result
        assert result["llm"]["provider"] == "local"
