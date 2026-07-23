"""
Tests for PromptBuilder template rendering and table formatting.

Regression coverage for two prompt-layer defects:
1. image_context was built and passed to the template but no YAML template
   contained an {image_context} placeholder, so vision analysis guidance
   never reached the model.
2. format_table truncated tables >50 rows to first/last 10 while the template
   demanded one positive test per row — an unsatisfiable instruction.
"""

import json
import re

from core.prompt_builder import MAX_PROMPT_TABLE_ROWS, PromptBuilder
from yaml_prompt_manager import YAMLPromptManager


def _requirement(**overrides):
    requirement = {
        "id": "REQ_PB_001",
        "heading": "Door Lock Control",
        "text": "The system shall lock all doors when vehicle speed exceeds 10 km/h.",
        "info_list": [],
        "interface_list": [],
    }
    requirement.update(overrides)
    return requirement


class TestImageContextRendering:
    """The adaptive template must render the image_context variable."""

    def test_image_context_rendered_for_requirement_with_images(self):
        manager = YAMLPromptManager()
        builder = PromptBuilder(manager)

        requirement = _requirement(
            has_images=True,
            images=[{"format": "png", "saved_path": "/tmp/diagram.png"}],
        )

        prompt = builder.build_prompt(requirement)

        assert "1 diagram(s) attached" in prompt, (
            "image_context guidance missing from rendered prompt — "
            "check {image_context} placeholder in the adaptive template"
        )
        assert "When analyzing the diagram" in prompt

    def test_image_context_default_for_requirement_without_images(self):
        manager = YAMLPromptManager()
        builder = PromptBuilder(manager)

        prompt = builder.build_prompt(_requirement())

        assert "No diagrams or images provided." in prompt


class TestRelationshipRendering:
    """The adaptive template must render parsed traceability relationships."""

    def test_relationships_rendered_for_requirement_with_parent_and_children(self):
        manager = YAMLPromptManager()
        builder = PromptBuilder(manager)

        requirement = _requirement(
            parent_id="REQ_PARENT_001",
            child_ids=["REQ_CHILD_001", "REQ_CHILD_002"],
            hierarchy_level=2,
        )

        prompt = builder.build_prompt(requirement)

        assert "REQUIREMENT RELATIONSHIPS" in prompt
        assert "REQ_PARENT_001" in prompt
        assert "REQ_CHILD_001" in prompt
        assert "REQ_CHILD_002" in prompt
        assert "Hierarchy level: 2" in prompt

    def test_relationships_default_none_for_unrelated_requirement(self):
        """A requirement with no parent/children renders the 'None' placeholder."""
        manager = YAMLPromptManager()
        builder = PromptBuilder(manager)

        prompt = builder.build_prompt(_requirement())

        # Section header present, but no traceability IDs invented
        assert "REQUIREMENT RELATIONSHIPS" in prompt

    def test_format_relationships_returns_none_when_no_relationships(self):
        assert PromptBuilder.format_relationships({}) == "None"
        assert PromptBuilder.format_relationships({"child_ids": [], "parent_id": None}) == "None"

    def test_format_relationships_parent_only(self):
        result = PromptBuilder.format_relationships({"parent_id": "REQ_P"})
        assert "Parent requirement: REQ_P" in result
        assert "Child requirements" not in result

    def test_format_relationships_children_only(self):
        result = PromptBuilder.format_relationships({"child_ids": ["A", "B"]})
        assert "Child requirements: A, B" in result
        assert "Parent requirement" not in result

    def test_format_relationships_omits_zero_hierarchy_level(self):
        """Level 0 (top-level) is the default and should not add noise."""
        result = PromptBuilder.format_relationships({"child_ids": ["A"], "hierarchy_level": 0})
        assert "Hierarchy level" not in result


class TestFormatTableCoverageConsistency:
    """Table display must be consistent with the row-coverage instructions."""

    def test_all_rows_shown_up_to_max_prompt_table_rows(self):
        """Tables within the limit are shown in full (previously cut at >50)."""
        table_data = {"data": [{"col": f"val{i:03d}"} for i in range(75)]}

        result = PromptBuilder.format_table(table_data)

        assert "val000" in result
        assert "val037" in result  # middle row, previously truncated away
        assert "val074" in result
        assert "TRUNCATED" not in result

    def test_boundary_table_at_limit_shows_all_rows(self):
        table_data = {"data": [{"col": f"val{i:03d}"} for i in range(MAX_PROMPT_TABLE_ROWS)]}

        result = PromptBuilder.format_table(table_data)

        assert f"val{MAX_PROMPT_TABLE_ROWS - 1:03d}" in result
        assert "TRUNCATED" not in result

    def test_oversized_table_truncation_is_explicit_about_displayed_rows(self):
        """Beyond the limit, the truncation note must scope coverage to displayed rows."""
        table_data = {"data": [{"col": f"val{i:03d}"} for i in range(150)]}

        result = PromptBuilder.format_table(table_data)

        assert "val009" in result  # first 10 kept
        assert "val140" in result  # last 10 kept
        assert "val075" not in result  # middle removed
        assert "TRUNCATED" in result
        assert "displayed" in result.lower()

    def test_json_example_in_rendered_prompt_is_valid_json(self):
        """The JSON example shown to the model must itself be valid JSON.

        Regression: voltage_precondition contained a raw newline, which is an
        illegal control character inside a JSON string literal — the prompt
        demanded valid JSON while showing an invalid example.
        """
        manager = YAMLPromptManager()
        builder = PromptBuilder(manager)

        prompt = builder.build_prompt(_requirement())

        match = re.search(r"```json\s*(\{.*?\})\s*```", prompt, re.DOTALL)
        assert match, "JSON example block not found in rendered prompt"

        parsed = json.loads(match.group(1))
        assert "test_cases" in parsed
        # The precondition must arrive as a JSON \n escape, not a raw newline
        assert parsed["test_cases"][0]["preconditions"] == "1. Voltage= 12V\n2. Bat-ON"

    def test_template_coverage_wording_scoped_to_displayed_rows(self):
        """The adaptive template must not demand coverage of rows the model cannot see."""
        manager = YAMLPromptManager()
        builder = PromptBuilder(manager)

        requirement = _requirement(
            table={"rows": 150, "data": [{"col": f"val{i:03d}"} for i in range(150)]}
        )

        prompt = builder.build_prompt(requirement)

        assert "displayed" in prompt.lower()
        assert "must equal 150 for complete coverage" not in prompt.lower()
