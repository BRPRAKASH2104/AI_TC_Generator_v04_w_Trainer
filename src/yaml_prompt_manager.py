#!/usr/bin/env python3
"""
YAML Prompt Manager - External prompt template management with YAML
File: src/yaml_prompt_manager.py

This module provides YAML-based prompt template management for the AI Test Case Generator.
It supports automatic template selection, variable substitution, and template validation.
"""

from pathlib import Path
from typing import Any

import yaml


class YAMLPromptManager:
    """Simple YAML-based prompt manager with variable substitution and auto-selection"""

    def __init__(self, config_file: str = "prompts/config/prompt_config.yaml"):
        """
        Initialize YAML Prompt Manager

        Args:
            config_file: Path to prompt configuration file
        """
        self.config_file = self._resolve_config_path(config_file)
        self.config: dict[str, Any] = {}
        self.test_prompts: dict[str, Any] = {}
        self.error_prompts: dict[str, Any] = {}
        self.last_selected_template: str | None = None
        self.template_usage_count: dict[str, int] = {}  # Track template usage for summary

        self.load_configuration()
        self.load_all_prompts()

    def _resolve_config_path(self, config_file: str) -> Path:
        """
        Resolve configuration file path, checking multiple locations

        Args:
            config_file: Configuration file path

        Returns:
            Resolved path to configuration file
        """
        config_path = Path(config_file)

        # If absolute path exists, use it
        if config_path.is_absolute() and config_path.exists():
            return config_path

        # Try current directory
        if config_path.exists():
            return config_path

        # Try parent directory (if running from src/)
        parent_path = Path("..") / config_file
        if parent_path.exists():
            return parent_path

        # Try from script directory
        script_dir = Path(__file__).parent
        script_path = script_dir / config_file
        if script_path.exists():
            return script_path

        # Try from script parent directory
        script_parent_path = script_dir.parent / config_file
        if script_parent_path.exists():
            return script_parent_path

        # Return original path (will fail gracefully)
        return config_path

    def load_configuration(self) -> None:
        """Load main configuration file"""
        try:
            if self.config_file.exists():
                with self.config_file.open(encoding="utf-8") as f:
                    self.config = yaml.safe_load(f)
                print(f"✅ Loaded prompt configuration from {self.config_file}")
            else:
                print(f"⚠️  Config file not found: {self.config_file}, using defaults")
                self._set_default_config()
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            self._set_default_config()

    def _set_default_config(self) -> None:
        """Set default configuration if config file is missing"""
        self.config = {
            "file_paths": {
                "test_generation_prompts": "prompts/templates/test_generation.yaml",
                "error_handling_prompts": "prompts/templates/error_handling.yaml",
            },
            "defaults": {
                "template_selection": "driver_information_default",
                "variable_format": "{variable_name}",
            },
            "auto_selection": {"enabled": True, "fallback_to_default": True},
        }

    def load_all_prompts(self) -> None:
        """Load all prompt templates from YAML files"""
        # Load test generation prompts
        test_file = self.config["file_paths"]["test_generation_prompts"]
        try:
            test_path = self._resolve_config_path(test_file)
            if test_path.exists():
                with test_path.open(encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    self.test_prompts = data.get("test_generation_prompts", {})
                print(f"✅ Loaded {len(self.test_prompts)} test generation templates")
            else:
                print(f"⚠️  Test prompts file not found: {test_file}")
                self.test_prompts = {}
        except Exception as e:
            print(f"❌ Error loading test prompts: {e}")
            self.test_prompts = {}

        # Load error handling prompts (optional)
        error_file = self.config["file_paths"].get("error_handling_prompts", "")
        if error_file:
            try:
                error_path = self._resolve_config_path(error_file)
                if error_path.exists():
                    with error_path.open(encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        self.error_prompts = data.get("error_prompts", {})
                    print(f"✅ Loaded {len(self.error_prompts)} error handling templates")
                else:
                    self.error_prompts = {}
            except Exception as e:
                print(f"⚠️  Could not load error prompts: {e}")
                self.error_prompts = {}

    def get_test_prompt(self, template_name: str | None = None, **variables) -> str:
        """
        Get a test generation prompt with variable substitution

        Args:
            template_name: Specific template name (if None, auto-select)
            **variables: Variables to substitute in template

        Returns:
            Rendered prompt string
        """
        # Auto-select template if not specified
        if template_name is None:
            template_name = self._auto_select_template(variables)
            # Template selection will be summarized at file level, not per requirement

        self.last_selected_template = template_name

        # Track template usage for summary
        self.template_usage_count[template_name] = (
            self.template_usage_count.get(template_name, 0) + 1
        )

        # Get template data
        template_data = self.test_prompts.get(template_name)
        if not template_data:
            print(f"❌ Template '{template_name}' not found, using default")
            template_name = self.config["defaults"]["template_selection"]
            template_data = self.test_prompts.get(template_name)

        if not template_data:
            raise ValueError("No templates available - check template files")

        # Validate required variables
        self._validate_variables(template_data, variables)

        # Apply defaults for optional variables
        final_variables = self._apply_defaults(template_data, variables)

        # Substitute variables in template
        template_str = template_data.get("template") or template_data.get("prompt")
        rendered_prompt = self._substitute_variables(template_str, final_variables)

        return rendered_prompt

    def get_error_prompt(self, error_type: str, **variables) -> str:
        """Get an error handling prompt"""
        template_data = self.error_prompts.get(error_type)
        if not template_data:
            # Return simple error message if no template
            return (
                f"Error processing requirement: {variables.get('error_message', 'Unknown error')}"
            )

        # Apply defaults and substitute
        final_variables = self._apply_defaults(template_data, variables)
        return self._substitute_variables(template_data["template"], final_variables)

    def _auto_select_template(self, variables: dict[str, Any]) -> str:
        """Automatically select appropriate template based on context"""
        if not self.config.get("auto_selection", {}).get("enabled", True):
            defaults = self.config.get("defaults", {})
            return defaults.get("template_selection", "default")

        heading = variables.get("heading", "").lower()
        req_id = variables.get("requirement_id", "").upper()

        # Load selection rules from test prompts file
        try:
            test_file = self.config["file_paths"]["test_generation_prompts"]
            test_path = self._resolve_config_path(test_file)
            with test_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
                selection_rules = data.get("prompt_selection", {})
        except Exception:
            defaults = self.config.get("defaults", {})
            return defaults.get("template_selection", "default")

        # Check heading keywords
        heading_rules = selection_rules.get("heading_keywords", {})
        for category, rule_data in heading_rules.items():
            keywords = rule_data.get("keywords", [])
            if any(keyword.lower() in heading for keyword in keywords):
                template = rule_data.get("template")
                if template in self.test_prompts:
                    return template

        # Check requirement ID patterns
        id_rules = selection_rules.get("requirement_id_patterns", {})
        for category, rule_data in id_rules.items():
            patterns = rule_data.get("patterns", [])
            if any(pattern in req_id for pattern in patterns):
                template = rule_data.get("template")
                if template in self.test_prompts:
                    return template

        # Return default
        return selection_rules.get(
            "default_template", self.config["defaults"]["template_selection"]
        )

    def _validate_variables(self, template_data: dict[str, Any], variables: dict[str, Any]):
        """Validate that required variables are provided"""
        template_vars = template_data.get("variables", [])

        # Handle both old format (list) and new format (dict with required key)
        if isinstance(template_vars, list):
            required = template_vars
        else:
            required = template_vars.get("required", [])

        missing = [var for var in required if var not in variables]
        if missing:
            raise ValueError(f"Missing required variables for template: {missing}")

    def _apply_defaults(
        self, template_data: dict[str, Any], variables: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply default values for optional variables"""
        template_vars = template_data.get("variables", {})

        # Handle both old format (list) and new format (dict with defaults key)
        if isinstance(template_vars, list):
            defaults = {}
        else:
            defaults = template_vars.get("defaults", {})

        final_variables = variables.copy()
        for var, default_value in defaults.items():
            value = final_variables.get(var, None)
            if (
                var not in final_variables
                or value is None
                or value == ""
                or str(value).lower() == "none"
            ):
                final_variables[var] = default_value

        return final_variables

    def _substitute_variables(self, template_str: str, variables: dict[str, Any]) -> str:
        """Substitute variables in template string using {variable_name} format"""
        rendered = template_str

        # Simple variable substitution using {variable_name} format
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            rendered = rendered.replace(placeholder, str(var_value))

        return rendered

    def list_templates(self) -> dict[str, list[str]]:
        """List available templates"""
        return {
            "test_generation": list(self.test_prompts.keys()),
            "error_handling": list(self.error_prompts.keys()),
        }

    def get_template_info(self, template_name: str) -> dict[str, Any]:
        """Get information about a specific template"""
        template_data = self.test_prompts.get(template_name, {})
        return {
            "name": template_data.get("name", ""),
            "description": template_data.get("description", ""),
            "category": template_data.get("category", ""),
            "tags": template_data.get("tags", []),
            "variables": template_data.get("variables", {}),
            "validation": template_data.get("validation", {}),
        }

    def get_selected_template(self) -> str:
        """Get the name of the last selected template"""
        return self.last_selected_template or "unknown"

    def get_template_usage_summary(self) -> dict[str, int]:
        """Get template usage summary for current processing"""
        return self.template_usage_count.copy()

    def reset_template_usage(self):
        """Reset template usage counter (call at start of new file processing)"""
        self.template_usage_count.clear()

    def reload_prompts(self):
        """Reload all prompt templates (useful for development)"""
        self.load_all_prompts()
        print("🔄 All prompt templates reloaded")

    def validate_template_file(self, file_path: str) -> list[str]:
        """Validate a YAML template file and return any errors"""
        errors = []

        # Resolve the file path
        resolved_path = self._resolve_config_path(file_path)

        try:
            with resolved_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error: {e}")
            return errors
        except FileNotFoundError:
            errors.append(f"File not found: {file_path}")
            return errors
        except Exception as e:
            errors.append(f"File reading error: {e}")
            return errors

        # Validate structure for test generation prompts
        if "test_generation_prompts" in data:
            prompts = data["test_generation_prompts"]
            for template_name, template_data in prompts.items():
                # Check required fields
                required_fields = ["name", "description", "template", "variables"]
                for field in required_fields:
                    if field not in template_data:
                        errors.append(f"Template '{template_name}' missing required field: {field}")

                # Check variables structure
                if "variables" in template_data:
                    variables = template_data["variables"]
                    if "required" not in variables:
                        errors.append(f"Template '{template_name}' missing required variables list")

                    # Check for variable placeholders in template
                    template_str = template_data.get("template", "")
                    required_vars = variables.get("required", [])
                    for var in required_vars:
                        placeholder = f"{{{var}}}"
                        if placeholder not in template_str:
                            errors.append(
                                f"Template '{template_name}' missing placeholder for required variable: {var}"
                            )

        return errors
