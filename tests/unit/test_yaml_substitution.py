"""Regression tests for template variable substitution."""

from yaml_prompt_manager import YAMLPromptManager


def test_variable_values_containing_placeholders_are_not_resubstituted():
    """A variable value that happens to contain {other_var} text must stay literal.

    The old sequential str.replace cascaded: after substituting {a} the
    resulting text was scanned again for later placeholders, so requirement
    text containing brace patterns could be silently rewritten.
    """
    manager = YAMLPromptManager.__new__(YAMLPromptManager)  # skip file loading

    result = manager._substitute_variables(
        "A: {a}, B: {b}",
        {"a": "value with literal {b} inside", "b": "SECOND"},
    )

    assert result == "A: value with literal {b} inside, B: SECOND"


def test_unknown_placeholders_are_left_intact():
    manager = YAMLPromptManager.__new__(YAMLPromptManager)

    result = manager._substitute_variables("Known: {a}, Unknown: {missing}", {"a": "X"})

    assert result == "Known: X, Unknown: {missing}"
