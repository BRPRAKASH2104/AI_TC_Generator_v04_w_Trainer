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
                # Vision model support (v2.2.0)
                "image_context": self.format_image_context(requirement.get("images", [])),
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
        image_context = self.format_image_context(requirement.get("images", []))

        prompt = f"""You are an expert automotive test engineer. Generate comprehensive test cases for the following requirement with provided context:

--- CONTEXTUAL INFORMATION ---
FEATURE HEADING: {heading}
ADDITIONAL INFORMATION: {info_str}
SYSTEM INTERFACES: {interface_str}
VISUAL DIAGRAMS: {image_context}

--- PRIMARY REQUIREMENT TO TEST ---
Requirement ID: {req_id}
Description: {text}

--- YOUR TASK ---
Generate test cases in JSON format with the following EXACT structure:
{{
    "analysis": "Chain of thought: Analyze the requirement, break it into functional blocks, describe any visual diagrams, identify boundary conditions, and list all edge cases/negative scenarios before generating the test cases.",
    "test_cases": [
        {{
            "summary_suffix": "Brief descriptive title for this specific test",
            "preconditions": "Preconditions (voltage, system state)",
            "test_steps": "Numbered list of test steps: 1) Step one\\n2) Step two",
            "expected_result": "Specific observable outcome that indicates pass",
            "test_type": "positive or negative"
        }}
    ]
}}

REQUIREMENTS:
1. Generate BOTH positive (valid inputs) AND negative (invalid/boundary/error) test cases
2. Use "preconditions" field for preconditions (e.g., "1. Voltage=12V\\n2. IGN ON")
3. Use "test_steps" field for numbered test steps
4. Each test case MUST include "test_type" field marking it as "positive" or "negative"
5. Focus on:
   - Boundary value testing
   - Positive and negative scenarios
   - Automotive-specific conditions (voltage, temperature, CAN signals)
   - Error handling and safety considerations
6. If diagrams are provided, analyze them to understand:
   - System state machines and transitions
   - Signal flows and timing sequences
   - Parameter tables and threshold values
   - Architectural dependencies and interactions
   - UI behaviors and expected responses

Return ONLY valid JSON with the exact field names shown above."""

        return prompt

    @staticmethod
    def format_table(table_data: dict[str, Any] | None) -> str:
        """
        Format table data for inclusion in prompts.

        Enhanced version that shows ALL rows with intelligent formatting:
        - For 20 rows or fewer: Show all rows
        - For 21-50 rows: Show all rows with compact formatting
        - For 51+ rows: Show first 10 and last 10 rows with center truncation

        Args:
            table_data: Table data dictionary with "data" key

        Returns:
            Formatted table string showing all rows
        """
        if not table_data or "data" not in table_data:
            return "No table data available"

        try:
            rows = table_data["data"]
            if not rows:
                return "Empty table"

            total_rows = len(rows)
            # Get headers from first row
            headers = list(rows[0].keys()) if rows else []

            # Format as simple table
            formatted = "Table Data:\n"
            formatted += " | ".join(headers) + "\n"
            formatted += "-" * (len(" | ".join(headers))) + "\n"

            # Intelligent row display based on table size
            if total_rows <= 20:
                # Show all rows
                for i, row in enumerate(rows):
                    values = [str(row.get(header, "")) for header in headers]
                    formatted += " | ".join(values) + " | Row " + str(i + 1) + "\n"
            elif total_rows <= 50:
                # Show all rows but with compact numbering
                for i, row in enumerate(rows):
                    values = [str(row.get(header, "")) for header in headers]
                    formatted += f"R{i + 1:02d}: " + " | ".join(values) + "\n"
            else:
                # Large table: Show first 10, truncation indicator, last 10
                # First 10 rows
                for i, row in enumerate(rows[:10]):
                    values = [str(row.get(header, "")) for header in headers]
                    formatted += f"R{i + 1:02d}: " + " | ".join(values) + "\n"

                # Truncation indicator
                formatted += f"... (showing first 10 and last 10 of {total_rows} total rows) ...\n"

                # Last 10 rows
                start_last = max(10, total_rows - 10)
                for i, row in enumerate(rows[start_last:], start=start_last):
                    values = [str(row.get(header, "")) for header in headers]
                    formatted += f"R{i + 1:02d}: " + " | ".join(values) + "\n"

            formatted += f"\nTable contains {total_rows} rows total."
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

    @staticmethod
    def format_image_context(images: list[dict[str, Any]]) -> str:
        """
        Format image context with specific analysis guidance for vision models (v2.3.0).

        Provides structured instructions tailored to different diagram types to help
        vision models extract actionable test information from visual requirements.

        Args:
            images: List of image metadata dictionaries

        Returns:
            Formatted string with image count, formats, and specific analysis instructions
        """
        if not images:
            return "No diagrams or images provided."

        image_count = len(images)
        formats = ", ".join(sorted({img.get("format", "unknown").upper() for img in images}))

        # Build context header
        context = f"{image_count} diagram(s) attached ({formats}). "

        # Specific instructions based on count
        if image_count == 1:
            context += "\n\nWhen analyzing the diagram:\n"
        else:
            context += "\n\nWhen analyzing the diagrams:\n"

        context += """1. DESCRIBE what you see - identify the type of diagram (state machine, flowchart, timing diagram, architecture, UI mockup, table)
2. EXTRACT key information:
   - For state machines: List all states and transitions with conditions
   - For flowcharts: Identify decision points and branches
   - For timing diagrams: Note signal sequences and timing constraints
   - For tables: Extract parameter values and thresholds
   - For UI mockups: Describe expected user interactions
3. CROSS-REFERENCE the diagram with the requirement text to identify:
   - Test scenarios that validate the visual logic
   - Edge cases visible in the diagram but not explicit in text
   - Boundary values from any numerical data shown
4. Describe your visual analysis explicitly in the "analysis" field of the JSON output.
5. If the diagram contradicts or extends the text description, note this in your test cases."""

        return context
