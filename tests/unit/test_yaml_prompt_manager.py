import pytest
from pathlib import Path
from unittest.mock import mock_open, patch

from src.yaml_prompt_manager import YAMLPromptManager


@pytest.fixture
def mock_yaml_files(monkeypatch):
    """Mock the YAML configuration and template files."""
    config_content = """
file_paths:
  test_generation_prompts: "prompts/templates/test_generation.yaml"
  error_handling_prompts: "prompts/templates/error_handling.yaml"
defaults:
  template_selection: "default_template"
auto_selection:
  enabled: true
"""
    test_prompts_content = """
test_generation_prompts:
  default_template:
    name: "Default Template"
    description: "A default template."
    template: "This is the default template for {requirement_id}."
    variables:
      required: ["requirement_id"]
  special_template:
    name: "Special Template"
    description: "A special template."
    template: "This is the special template for {requirement_id} and {heading}."
    variables:
      required: ["requirement_id", "heading"]
"""
    error_prompts_content = """
error_prompts:
  validation_error:
    name: "Validation Error"
    description: "An error during validation."
    template: "Validation error: {error_message}"
    variables:
      required: ["error_message"]
"""

    def mock_open_side_effect(file, *args, **kwargs):
        if "config.yaml" in str(file):
            return mock_open(read_data=config_content).return_value
        if "test_generation.yaml" in str(file):
            return mock_open(read_data=test_prompts_content).return_value
        if "error_handling.yaml" in str(file):
            return mock_open(read_data=error_prompts_content).return_value
        return mock_open(read_data="").return_value

    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    monkeypatch.setattr("pathlib.Path.open", mock_open_side_effect)


def test_yaml_prompt_manager_init(mock_yaml_files):
    """Test the initialization of the YAMLPromptManager."""
    manager = YAMLPromptManager("prompts/config/config.yaml")
    assert manager.config is not None
    assert "default_template" in manager.test_prompts
    assert "validation_error" in manager.error_prompts

def test_get_test_prompt(mock_yaml_files):
    """Test getting a test prompt."""
    manager = YAMLPromptManager("prompts/config/config.yaml")
    prompt = manager.get_test_prompt("default_template", requirement_id="REQ-001")
    assert prompt == "This is the default template for REQ-001."

def test_get_test_prompt_with_missing_vars(mock_yaml_files):
    """Test getting a test prompt with missing required variables."""
    manager = YAMLPromptManager("prompts/config/config.yaml")
    with pytest.raises(ValueError):
        manager.get_test_prompt("special_template", requirement_id="REQ-001")

def test_get_error_prompt(mock_yaml_files):
    """Test getting an error prompt."""
    manager = YAMLPromptManager("prompts/config/config.yaml")
    prompt = manager.get_error_prompt("validation_error", error_message="Something went wrong.")
    assert prompt == "Validation error: Something went wrong."

def test_list_templates(mock_yaml_files):
    """Test listing available templates."""
    manager = YAMLPromptManager("prompts/config/config.yaml")
    templates = manager.list_templates()
    assert "default_template" in templates["test_generation"]
    assert "validation_error" in templates["error_handling"]

def test_get_template_info(mock_yaml_files):
    """Test getting information about a template."""
    manager = YAMLPromptManager("prompts/config/config.yaml")
    info = manager.get_template_info("default_template")
    assert info["name"] == "Default Template"
    assert info["description"] == "A default template."
