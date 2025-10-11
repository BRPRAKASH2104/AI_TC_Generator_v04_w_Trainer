"""
Prompt builder for the AI Test Case Generator.

This module provides a stateless, reusable prompt builder that handles all
prompt construction logic, decoupled from test case generators.
"""

from typing import Any

# Type aliases
type RequirementData = dict[str, Any]


class PromptBuilder:
    """Stateless prompt builder for test case generation"""

    __slots__ = ("yaml_manager",)

    def __init__(self, yaml_manager=None):
        """
        Initialize prompt builder.

        Args:
            yaml_manager: Optional YAML template manager for template-based prompts
        """
        self.yaml_manager = yaml_manager

    def build_prompt(self, requirement: RequirementData, template_name: str = None) -> str:
        """
        Build prompt from requirement data.

        Args:
            requirement: Requirement data with context
            template_name: Optional specific template to use

        Returns:
            Formatted prompt string
        """
        if self.yaml_manager:
            return self._build_from_template(requirement, template_name)
        else:
            return self._build_default(requirement)

    def _build_from_template(self, requirement: RequirementData, template_name: str = None) -> str:
        """
        Build prompt using YAML template.

        Args:
            requirement: Requirement data with context
            template_name: Optional specific template to use

        Returns:
            Formatted prompt string
        """
        try:
            # Prepare template variables with context information
            variables = {
                "requirement_id": requirement.get("id", "UNKNOWN"),
                "heading": requirement.get("heading", ""),
                "requirement_text": requirement.get("text", ""),
                "table_str": self.format_table(requirement.get("table")),
                "row_count": requirement.get("table", {}).get("rows", 0)
                if requirement.get("table")
                else 0,
                "voltage_precondition": "1. Voltage= 12V\n2. Bat-ON",  # Default automotive precondition
                # Context-aware fields (v03 restoration)
                "info_str": self.format_info_list(requirement.get("info_list", [])),
                "interface_str": self.format_interfaces(requirement.get("interface_list", [])),
            }

            # Use template manager to get formatted prompt
            if template_name:
                return self.yaml_manager.get_test_prompt(template_name, **variables)
            else:
                return self.yaml_manager.get_test_prompt(**variables)

        except Exception:
            # Fallback to default prompt on template error
            return self._build_default(requirement)

    def _build_default(self, requirement: RequirementData) -> str:
        """
        Build default prompt without template.

        FIX: Updated to match YAML template field names for consistency.

        Args:
            requirement: Requirement data

        Returns:
            Default formatted prompt string
        """
        req_id = requirement.get("id", "UNKNOWN")
        heading = requirement.get("heading", "")
        text = requirement.get("text", "")

        # Format context information if available
        info_list = requirement.get("info_list", [])
        interface_list = requirement.get("interface_list", [])

        info_str = self.format_info_list(info_list) if info_list else "None"
        interface_str = self.format_interfaces(interface_list) if interface_list else "None"

        prompt = f"""You are an expert automotive test engineer. Generate comprehensive test cases for the following requirement with provided context:

--- CONTEXTUAL INFORMATION ---
FEATURE HEADING: {heading}
ADDITIONAL INFORMATION: {info_str}
SYSTEM INTERFACES: {interface_str}

--- PRIMARY REQUIREMENT TO TEST ---
Requirement ID: {req_id}
Description: {text}

--- YOUR TASK ---
Generate test cases in JSON format with the following EXACT structure:
{{
    "test_cases": [
        {{
            "summary_suffix": "Brief descriptive title for this specific test",
            "action": "Preconditions (voltage, system state)",
            "data": "Numbered list of test steps: 1) Step one\\n2) Step two",
            "expected_result": "Specific observable outcome that indicates pass",
            "test_type": "positive or negative"
        }}
    ]
}}

REQUIREMENTS:
1. Generate BOTH positive (valid inputs) AND negative (invalid/boundary/error) test cases
2. Use "action" field for preconditions (e.g., "1. Voltage=12V\\n2. IGN ON")
3. Use "data" field for numbered test steps
4. Each test case MUST include "test_type" field marking it as "positive" or "negative"
5. Focus on:
   - Boundary value testing
   - Positive and negative scenarios
   - Automotive-specific conditions (voltage, temperature, CAN signals)
   - Error handling and safety considerations

Return ONLY valid JSON with the exact field names shown above."""

        return prompt

    @staticmethod
    def format_table(table_data: dict[str, Any] | None) -> str:
        """
        Format table data for inclusion in prompts.

        Args:
            table_data: Table data dictionary with "data" key

        Returns:
            Formatted table string
        """
        if not table_data or "data" not in table_data:
            return "No table data available"

        try:
            rows = table_data["data"]
            if not rows:
                return "Empty table"

            # Get headers from first row
            headers = list(rows[0].keys()) if rows else []

            # Format as simple table
            formatted = "Table Data:\n"
            formatted += " | ".join(headers) + "\n"
            formatted += "-" * (len(" | ".join(headers))) + "\n"

            for row in rows[:10]:  # Limit to first 10 rows
                values = [str(row.get(header, "")) for header in headers]
                formatted += " | ".join(values) + "\n"

            if len(rows) > 10:
                formatted += f"... ({len(rows) - 10} more rows)\n"

            return formatted

        except Exception as e:
            return f"Error formatting table: {e}"

    @staticmethod
    def format_info_list(info_list: list[dict[str, Any]]) -> str:
        """
        Format information list for inclusion in prompt (v03 restoration).

        Args:
            info_list: List of information artifacts collected since last heading

        Returns:
            Formatted string for prompt template
        """
        if not info_list:
            return "None"

        return "\n".join([f"- {info.get('text', '')}" for info in info_list])

    @staticmethod
    def format_interfaces(interface_list: list[dict[str, Any]]) -> str:
        """
        Format system interface list for inclusion in prompt (v03 restoration).

        Args:
            interface_list: List of system interface artifacts (global context)

        Returns:
            Formatted string for prompt template
        """
        if not interface_list:
            return "None"

        return "\n".join(
            [
                f"- {interface.get('id', 'UNKNOWN')}: {interface.get('text', '')}"
                for interface in interface_list
            ]
        )
