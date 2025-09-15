"""
Unit tests for YAML prompt manager - Fixed to match actual implementation.

Tests template loading, variable substitution, and auto-selection using real interface.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from yaml_prompt_manager import YAMLPromptManager


class TestYAMLPromptManagerFixed:
    """Test YAML prompt manager functionality using actual interface."""

    def test_initialization_success(self):
        """Test successful initialization."""
        with patch.object(YAMLPromptManager, 'load_configuration') as mock_load_config:
            with patch.object(YAMLPromptManager, 'load_all_prompts') as mock_load_prompts:
                manager = YAMLPromptManager()
                
                mock_load_config.assert_called_once()
                mock_load_prompts.assert_called_once()
                assert manager.test_prompts == {}
                assert manager.config == {}

    @patch('yaml_prompt_manager.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_configuration_success(self, mock_yaml_load, mock_file, mock_exists):
        """Test successful configuration loading."""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            "file_paths": {"test_generation_prompts": "prompts/test.yaml"},
            "defaults": {"template_selection": "default_template"}
        }
        
        with patch.object(YAMLPromptManager, 'load_all_prompts'):
            manager = YAMLPromptManager()
            
            # Check that configuration was loaded
            assert "file_paths" in manager.config
            assert "defaults" in manager.config

    def test_get_test_prompt_basic(self):
        """Test getting a test prompt without template specification."""
        with patch.object(YAMLPromptManager, 'load_configuration'):
            with patch.object(YAMLPromptManager, 'load_all_prompts'):
                manager = YAMLPromptManager()
                manager.test_prompts = {
                    "default": {
                        "prompt": "Generate test cases for {requirement_text}",
                        "variables": ["requirement_text"]
                    }
                }
                
                result = manager.get_test_prompt(requirement_text="Test requirement")
                
                assert "Test requirement" in result
                assert "Generate test cases" in result

    def test_get_test_prompt_with_template_name(self):
        """Test getting a specific template.""" 
        with patch.object(YAMLPromptManager, 'load_configuration'):
            with patch.object(YAMLPromptManager, 'load_all_prompts'):
                manager = YAMLPromptManager()
                manager.test_prompts = {
                    "custom_template": {
                        "prompt": "Custom prompt for {requirement_id}",
                        "variables": ["requirement_id"]
                    }
                }
                
                result = manager.get_test_prompt("custom_template", requirement_id="REQ_001")
                
                assert "REQ_001" in result
                assert "Custom prompt" in result

    def test_substitute_variables_basic(self):
        """Test basic variable substitution."""
        with patch.object(YAMLPromptManager, 'load_configuration'):
            with patch.object(YAMLPromptManager, 'load_all_prompts'):
                manager = YAMLPromptManager()
                
                template = "Test for {requirement_id}: {requirement_text}"
                variables = {
                    "requirement_id": "REQ_001",
                    "requirement_text": "System shall validate input"
                }
                
                result = manager._substitute_variables(template, variables)
                
                expected = "Test for REQ_001: System shall validate input"
                assert result == expected

    def test_substitute_variables_missing_variable(self):
        """Test variable substitution with missing variables."""
        with patch.object(YAMLPromptManager, 'load_configuration'):
            with patch.object(YAMLPromptManager, 'load_all_prompts'):
                manager = YAMLPromptManager()
                
                template = "Test {requirement_id}: {missing_var}"
                variables = {"requirement_id": "REQ_001"}
                
                result = manager._substitute_variables(template, variables)
                
                # Should leave placeholder for missing variable
                assert "REQ_001" in result
                assert "{missing_var}" in result

    def test_list_templates(self):
        """Test listing available templates."""
        with patch.object(YAMLPromptManager, 'load_configuration'):
            with patch.object(YAMLPromptManager, 'load_all_prompts'):
                manager = YAMLPromptManager()
                manager.test_prompts = {
                    "template1": {"prompt": "Test 1"},
                    "template2": {"prompt": "Test 2"}
                }
                manager.error_prompts = {
                    "error1": {"prompt": "Error 1"}
                }
                
                templates = manager.list_templates()
                
                assert "test_generation" in templates
                assert "error_handling" in templates
                assert "template1" in templates["test_generation"]
                assert "template2" in templates["test_generation"]

    def test_get_template_info(self):
        """Test getting template information."""
        with patch.object(YAMLPromptManager, 'load_configuration'):
            with patch.object(YAMLPromptManager, 'load_all_prompts'):
                manager = YAMLPromptManager()
                manager.test_prompts = {
                    "test_template": {
                        "prompt": "Test prompt",
                        "description": "A test template",
                        "variables": ["var1", "var2"]
                    }
                }
                
                info = manager.get_template_info("test_template")
                
                assert info["description"] == "A test template"
                assert "var1" in info["variables"]
                assert "var2" in info["variables"]

    def test_get_template_usage_summary(self):
        """Test getting template usage summary."""
        with patch.object(YAMLPromptManager, 'load_configuration'):
            with patch.object(YAMLPromptManager, 'load_all_prompts'):
                manager = YAMLPromptManager()
                manager.template_usage_count = {
                    "template1": 5,
                    "template2": 3
                }
                
                usage = manager.get_template_usage_summary()
                
                assert usage["template1"] == 5
                assert usage["template2"] == 3

    def test_reset_template_usage(self):
        """Test resetting template usage counters."""
        with patch.object(YAMLPromptManager, 'load_configuration'):
            with patch.object(YAMLPromptManager, 'load_all_prompts'):
                manager = YAMLPromptManager()
                manager.template_usage_count = {"template1": 5}
                
                manager.reset_template_usage()
                
                assert manager.template_usage_count == {}

    @patch('builtins.print')
    def test_load_configuration_file_not_found(self, mock_print):
        """Test handling when configuration file doesn't exist."""
        with patch.object(Path, 'exists', return_value=False):
            with patch.object(YAMLPromptManager, 'load_all_prompts'):
                manager = YAMLPromptManager()
                
                # Should use default configuration
                assert manager.config != {}

    @patch('builtins.print')
    @patch('yaml.safe_load')
    @patch('builtins.open')
    def test_load_configuration_yaml_error(self, mock_open_file, mock_yaml_load, mock_print):
        """Test handling of YAML parsing errors."""
        with patch.object(Path, 'exists', return_value=True):
            mock_yaml_load.side_effect = Exception("YAML parsing error")
            
            with patch.object(YAMLPromptManager, 'load_all_prompts'):
                manager = YAMLPromptManager()
                
                # Should handle gracefully and use defaults
                mock_print.assert_called()