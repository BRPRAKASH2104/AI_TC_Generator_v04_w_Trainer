import os
from pathlib import Path

import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from src.config import (ConfigManager, LoggingConfig, OllamaConfig,
                        StaticTestConfig)

def test_ollama_config_defaults():
    """Test OllamaConfig default values."""
    config = OllamaConfig()
    assert config.host == "127.0.0.1"
    assert config.port == 11434
    assert config.api_url == "http://127.0.0.1:11434/api/generate"

def test_ollama_config_validation():
    """Test OllamaConfig validation logic."""
    with pytest.raises(ValidationError):
        OllamaConfig(port=99999)  # Invalid port
    with pytest.raises(ValidationError):
        OllamaConfig(temperature=-1.0)  # Invalid temperature
    with pytest.raises(ValidationError):
        OllamaConfig(timeout=0)

def test_static_test_config_defaults():
    """Test StaticTestConfig default values."""
    config = StaticTestConfig()
    assert config.test_type == "PROVEtech"
    assert config.assignee == "ENGG"

def test_logging_config_defaults():
    """Test LoggingConfig default values."""
    config = LoggingConfig()
    assert config.log_level == "INFO"
    assert not config.log_to_file

def test_config_manager_defaults():
    """Test ConfigManager default values."""
    manager = ConfigManager()
    assert manager.ollama.port == 11434
    assert manager.static_test.project_key == "TCTOIC"

def test_config_manager_env_vars(monkeypatch):
    """Test loading configuration from environment variables."""
    monkeypatch.setenv("OLLAMA__PORT", "8080")
    monkeypatch.setenv("STATIC_TEST__ASSIGNEE", "TestUser")

    manager = ConfigManager()
    assert manager.ollama.port == 8080
    assert manager.static_test.assignee == "TestUser"

def test_config_manager_yaml_file(tmp_path: Path, monkeypatch):
    """Test loading configuration from a YAML file."""
    config_content = """
ollama:
  port: 9090
static_test:
  project_key: 'NEW_KEY'
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)

    monkeypatch.setenv("YAML_CONFIG_FILE", str(config_file))

    class TestConfigManager(ConfigManager):
        model_config = SettingsConfigDict(
            env_nested_delimiter="__",
            yaml_file=os.getenv("YAML_CONFIG_FILE"),
            case_sensitive=False,
        )

    manager = TestConfigManager()
    assert manager.ollama.port == 9090
    assert manager.static_test.project_key == "NEW_KEY"

def test_config_manager_save_and_load(tmp_path: Path, monkeypatch):
    """Test saving and loading a configuration file."""
    save_path = tmp_path / "config_to_save.yaml"
    manager = ConfigManager()
    manager.save_to_file(str(save_path))

    assert save_path.exists()

    monkeypatch.setenv("YAML_CONFIG_FILE", str(save_path))

    class TestConfigManager(ConfigManager):
        model_config = SettingsConfigDict(
            env_nested_delimiter="__",
            yaml_file=os.getenv("YAML_CONFIG_FILE"),
            case_sensitive=False,
        )

    loaded_manager = TestConfigManager()
    assert loaded_manager.ollama.port == manager.ollama.port

def test_print_summary(capsys):
    """Test the print_summary method."""
    manager = ConfigManager()
    manager.print_summary()
    captured = capsys.readouterr()
    assert "CONFIGURATION SUMMARY" in captured.out
    assert "OLLAMA CONNECTION" in captured.out
    assert "TEST CASE SETTINGS" in captured.out
