"""
Unit tests for YAML prompt manager.

Tests template loading, variable substitution, and auto-selection.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from yaml_prompt_manager import YAMLPromptManager


class TestYAMLPromptManager:
    """Test YAML prompt manager functionality."""

    @patch("yaml_prompt_manager.Path.exists")
    @patch("yaml_prompt_manager.Path.open")
    @patch("yaml.safe_load")
    def test_load_prompt_templates_success(self, mock_yaml_load, mock_open_file, mock_exists):
        """Test successful loading of prompt templates."""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            "test_prompts": {
                "default_template": {
                    "prompt": "Generate test cases for {requirement_text}",
                    "description": "Default template",
                    "variables": ["requirement_text"]
                }
            }
        }
        
        manager = YAMLPromptManager()
        
        assert "default_template" in manager.test_prompts
        assert manager.test_prompts["default_template"]["prompt"] == "Generate test cases for {requirement_text}"

    def test_get_test_prompt_existing_template(self):
        """Test retrieving an existing template."""
        with patch.object(YAMLPromptManager, '_load_prompt_templates'):
            manager = YAMLPromptManager()
            manager.test_prompts = {
                "existing_template": {
                    "prompt": "Test prompt for {requirement_id}",
                    "variables": ["requirement_id"]
                }
            }
            
            result = manager.get_test_prompt("existing_template")
            
            assert result is not None
            assert result["prompt"] == "Test prompt for {requirement_id}"
            assert "requirement_id" in result["variables"]

    def test_get_test_prompt_nonexistent_template(self):
        """Test retrieving non-existent template returns default."""
        with patch.object(YAMLPromptManager, '_load_prompt_templates'):
            manager = YAMLPromptManager()
            manager.test_prompts = {
                "default": {
                    "prompt": "Default prompt",
                    "variables": []
                }
            }
            
            result = manager.get_test_prompt("nonexistent")
            
            # Should return default template
            assert result is not None
            assert result["prompt"] == "Default prompt"

    def test_substitute_variables_basic(self):
        """Test basic variable substitution."""
        with patch.object(YAMLPromptManager, '_load_prompt_templates'):
            manager = YAMLPromptManager()
            
            template = {
                "prompt": "Requirement {requirement_id}: {requirement_text}",
                "variables": ["requirement_id", "requirement_text"]
            }
            
            variables = {
                "requirement_id": "REQ_001", 
                "requirement_text": "System shall validate input"
            }
            
            result = manager._substitute_variables(template, variables)
            
            expected = "Requirement REQ_001: System shall validate input"
            assert result == expected

    def test_substitute_variables_missing_variable(self):
        """Test variable substitution with missing variables."""
        with patch.object(YAMLPromptManager, '_load_prompt_templates'):
            manager = YAMLPromptManager()
            
            template = {
                "prompt": "Requirement {requirement_id}: {missing_var}",
                "variables": ["requirement_id", "missing_var"]
            }
            
            variables = {
                "requirement_id": "REQ_001"
                # missing_var not provided
            }
            
            result = manager._substitute_variables(template, variables)
            
            # Should leave placeholder for missing variable
            assert "REQ_001" in result
            assert "{missing_var}" in result

    def test_substitute_variables_extra_variables(self):
        """Test variable substitution with extra variables provided."""
        with patch.object(YAMLPromptManager, '_load_prompt_templates'):
            manager = YAMLPromptManager()
            
            template = {
                "prompt": "Simple prompt for {requirement_id}",
                "variables": ["requirement_id"]
            }
            
            variables = {
                "requirement_id": "REQ_001",
                "extra_variable": "not used"
            }
            
            result = manager._substitute_variables(template, variables)
            
            assert result == "Simple prompt for REQ_001"

    def test_build_prompt_with_requirement(self):
        """Test building prompt from requirement data."""
        with patch.object(YAMLPromptManager, '_load_prompt_templates'):
            manager = YAMLPromptManager()
            manager.test_prompts = {
                "test_template": {
                    "prompt": "Generate tests for {requirement_id}: {requirement_text}",
                    "variables": ["requirement_id", "requirement_text"]
                }
            }
            
            requirement = {
                "id": "REQ_001",
                "text": "The system shall validate user input"
            }
            
            result = manager.build_prompt("test_template", requirement)
            
            expected = "Generate tests for REQ_001: The system shall validate user input"
            assert result == expected

    @patch("yaml_prompt_manager.Path.exists") 
    @patch("builtins.open")
    def test_load_templates_file_not_found(self, mock_open_file, mock_exists):
        """Test handling when template file doesn't exist."""
        mock_exists.return_value = False
        
        with patch("builtins.print") as mock_print:
            manager = YAMLPromptManager()
            
            # Should handle gracefully and print warning
            mock_print.assert_called()
            assert manager.test_prompts == {}

    @patch("yaml_prompt_manager.Path.exists")
    @patch("builtins.open")
    @patch("yaml.safe_load")
    def test_load_templates_yaml_error(self, mock_yaml_load, mock_open_file, mock_exists):
        """Test handling of YAML parsing errors."""
        mock_exists.return_value = True
        mock_yaml_load.side_effect = Exception("YAML parsing error")
        
        with patch("builtins.print") as mock_print:
            manager = YAMLPromptManager()
            
            # Should handle gracefully and print error
            mock_print.assert_called()
            assert manager.test_prompts == {}

    def test_get_available_templates(self):
        """Test getting list of available templates."""
        with patch.object(YAMLPromptManager, '_load_prompt_templates'):
            manager = YAMLPromptManager()
            manager.test_prompts = {
                "template1": {"prompt": "Test 1"},
                "template2": {"prompt": "Test 2"},
                "template3": {"prompt": "Test 3"}
            }
            
            templates = manager.get_available_templates()
            
            assert len(templates) == 3
            assert "template1" in templates
            assert "template2" in templates  
            assert "template3" in templates

    def test_validate_template_structure(self):
        """Test template structure validation."""
        with patch.object(YAMLPromptManager, '_load_prompt_templates'):
            manager = YAMLPromptManager()
            
            valid_template = {
                "prompt": "Valid template with {variable}",
                "variables": ["variable"],
                "description": "A valid template"
            }
            
            invalid_template = {
                "description": "Missing prompt field"
            }
            
            assert manager._validate_template(valid_template) == True
            assert manager._validate_template(invalid_template) == False

    def test_template_caching(self):
        """Test that templates are cached and not reloaded unnecessarily.""" 
        with patch.object(YAMLPromptManager, '_load_prompt_templates') as mock_load:
            manager = YAMLPromptManager()
            
            # First access should load templates
            manager.get_test_prompt("any_template")
            assert mock_load.call_count == 1
            
            # Second access should use cache
            manager.get_test_prompt("another_template") 
            assert mock_load.call_count == 1  # Should not increase