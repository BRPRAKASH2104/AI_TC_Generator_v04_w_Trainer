# Test Artifact Builder - Usage Examples

This document provides examples of how to use the test artifact builder helpers to create XHTML-formatted test data that matches production code output after vision integration (v2.2.0).

## Why These Helpers Exist

After the vision model integration, text extraction changed from plain text to raw XHTML preservation to maintain `<object>` tag references for images. Integration tests need to create mock data in this new format.

**Before (v2.1.1)**: Tests used plain text
```python
artifact = {"id": "REQ_001", "text": "Door shall lock"}
```

**After (v2.2.0)**: Tests need XHTML format
```python
artifact = {
    "id": "REQ_001",
    "text": '<THE-VALUE xmlns:ns0="..." xmlns:html="..."><html:div><html:p>Door shall lock</html:p></html:div></THE-VALUE>'
}
```

These helpers automate creating the correct XHTML format.

---

## Basic Usage

### Import the helpers

```python
from tests.helpers import (
    create_test_artifact,
    create_test_requirement,
    create_test_heading,
    create_test_information,
    create_test_interface,
    create_test_artifact_with_images,
    create_augmented_requirement,
)
```

---

## Examples

### 1. Create a Basic System Requirement

```python
def test_process_basic_requirement():
    """Test processing a simple requirement."""
    # OLD WAY (fails with XHTML format):
    # artifact = {"id": "REQ_001", "text": "Door shall lock", "type": "System Requirement"}

    # NEW WAY (works with XHTML format):
    artifact = create_test_requirement(
        requirement_text="Door shall lock when speed > 10 km/h",
        requirement_id="REQ_001"
    )

    # Process the artifact
    processor = BaseProcessor()
    result = processor.process_artifact(artifact)

    assert result is not None
```

### 2. Create a Requirement with Test Table

```python
def test_requirement_with_test_cases():
    """Test requirement that already has test cases in a table."""
    artifact = create_test_requirement(
        requirement_text="ACC shall maintain safe distance",
        requirement_id="REQ_ACC_001",
        test_table_data=[
            ["TC001", "Test safe distance at 50 km/h", "Pass"],
            ["TC002", "Test emergency brake", "Pass"]
        ]
    )

    assert "table" in artifact
    assert len(artifact["table"]["data"]) == 2
```

### 3. Create an Augmented Requirement (with Context)

This matches the output of `BaseProcessor._build_augmented_requirements()`:

```python
def test_context_aware_processing():
    """Test that context is properly included in augmented requirements."""
    # Create heading
    heading = "Door Control System"

    # Create information context
    info_list = [
        create_test_information("Safety critical component"),
        create_test_information("ASIL-D rated")
    ]

    # Create interface context
    interface_list = [
        create_test_interface("Vehicle speed signal", input_output="Input"),
        create_test_interface("Door lock signal", input_output="Output")
    ]

    # Create augmented requirement with full context
    augmented_req = create_augmented_requirement(
        requirement_text="Door shall lock when speed > 10 km/h",
        heading=heading,
        info_list=info_list,
        interface_list=interface_list,
        requirement_id="REQ_001"
    )

    # Verify context is present
    assert augmented_req["heading"] == "Door Control System"
    assert len(augmented_req["info_list"]) == 2
    assert len(augmented_req["interface_list"]) == 2

    # Process with generator (will use context in prompt)
    generator = TestCaseGenerator(config=config, ollama_client=mock_ollama)
    test_cases = generator.generate_test_cases(augmented_req)
```

### 4. Create a Requirement with Images (for Vision Model)

```python
def test_requirement_with_images():
    """Test requirement that includes images for vision model."""
    artifact = create_test_artifact_with_images(
        text="ACC state machine with 4 states: Off, Standby, Active, Error",
        image_paths=[
            "diagrams/acc_state_machine.png",
            "diagrams/acc_transitions.png"
        ],
        artifact_id="REQ_ACC_001"
    )

    # Verify image metadata
    assert artifact["has_images"] is True
    assert artifact["image_count"] == 2

    # Verify XHTML contains <object> tags (REQIF format)
    assert '<html:object data="diagrams/acc_state_machine.png"' in artifact["text"]
    assert 'type="image/png"' in artifact["text"]

    # Process with vision-enabled generator
    config.ollama.enable_vision = True
    generator = TestCaseGenerator(config=config, ollama_client=mock_ollama)

    # Should select vision model for this requirement
    model = config.get_model_for_requirement(artifact)
    assert model == "llama3.2-vision:11b"
```

### 5. Simulate Complete Processing Flow

```python
def test_complete_processing_flow():
    """Test complete flow: heading → info → interfaces → requirements."""
    # Simulate REQIF extraction order
    artifacts = [
        create_test_heading("ACC System"),
        create_test_information("Safety critical - ASIL-D"),
        create_test_information("Requires functional safety testing"),
        create_test_interface("Speed signal", input_output="Input"),
        create_test_interface("Brake signal", input_output="Output"),
        create_test_requirement(
            "ACC shall maintain safe distance",
            requirement_id="REQ_001"
        ),
        create_test_requirement(
            "ACC shall brake if distance < threshold",
            requirement_id="REQ_002"
        )
    ]

    # Process with BaseProcessor (builds augmented requirements)
    processor = BaseProcessor()
    processor.extractor = Mock()
    processor.extractor.extract_reqifz_content = Mock(return_value=artifacts)

    augmented_reqs, system_interfaces = processor._build_augmented_requirements(artifacts)

    # Verify context-aware processing
    assert len(augmented_reqs) == 2  # 2 requirements
    assert len(system_interfaces) == 2  # 2 interfaces

    # Both requirements should have same context
    for req in augmented_reqs:
        assert req["heading"] == "ACC System"
        assert len(req["info_list"]) == 2  # Reset after each requirement
        assert len(req["interface_list"]) == 2
```

### 6. Update an Existing Test File

**Before (tests/test_refactoring.py - fails)**:
```python
def test_build_augmented_requirements_with_context(self):
    processor = BaseProcessor()
    processor.extractor = Mock()

    # OLD: Plain text format
    artifacts = [
        {"type": "Heading", "text": "Door Lock System"},
        {"type": "System Requirement", "id": "REQ_001", "table": {"data": []}}
    ]

    augmented_reqs, _ = processor._build_augmented_requirements(artifacts)
    assert len(augmented_reqs) == 2  # FAILS: gets 0
```

**After (fixed with helpers - passes)**:
```python
def test_build_augmented_requirements_with_context(self):
    processor = BaseProcessor()
    processor.extractor = Mock()

    # NEW: Use helpers to create XHTML format
    artifacts = [
        create_test_heading("Door Lock System"),
        create_test_requirement("Door shall lock when speed > 10 km/h", requirement_id="REQ_001")
    ]

    augmented_reqs, _ = processor._build_augmented_requirements(artifacts)
    assert len(augmented_reqs) == 1  # PASSES
```

---

## Helper Function Reference

### `create_test_artifact(text, artifact_type, artifact_id, **kwargs)`
General-purpose artifact creator with XHTML formatting.

**Args**:
- `text` (str): Text content
- `artifact_type` (str): "System Requirement", "Heading", "Information", etc.
- `artifact_id` (str, optional): Custom ID (auto-generated if None)
- `**kwargs`: Additional fields

**Returns**: Dictionary with XHTML-formatted text

---

### `create_test_requirement(requirement_text, requirement_id, include_table, test_table_data, **kwargs)`
Creates System Requirement with optional test table.

**Args**:
- `requirement_text` (str): Requirement description
- `requirement_id` (str, optional): Custom ID
- `include_table` (bool): Add table structure (default: True)
- `test_table_data` (List[List[str]], optional): Test case rows

**Returns**: System Requirement artifact

---

### `create_test_heading(heading_text, heading_id, **kwargs)`
Creates Heading artifact.

---

### `create_test_information(info_text, info_id, **kwargs)`
Creates Information artifact.

---

### `create_test_interface(interface_text, interface_id, input_output, **kwargs)`
Creates System Interface artifact.

**Args**:
- `input_output` (str): "Input" or "Output"

---

### `create_test_artifact_with_images(text, image_paths, artifact_type, image_types, **kwargs)`
Creates artifact with embedded image references (REQIF `<object>` tags).

**Args**:
- `text` (str): Text content
- `image_paths` (List[str]): Image file paths (e.g., ["diagrams/acc.png"])
- `image_types` (List[str], optional): MIME types (default: "image/png")

**Returns**: Artifact with `has_images=True` and `<html:object>` tags in text

---

### `create_augmented_requirement(requirement_text, heading, info_list, interface_list, **kwargs)`
Creates augmented requirement with full context (matches BaseProcessor output).

**Args**:
- `requirement_text` (str): Requirement description
- `heading` (str): Current heading context
- `info_list` (List[Dict]): Information artifacts
- `interface_list` (List[Dict]): System Interface artifacts

**Returns**: Augmented requirement dictionary

---

## Tips

1. **Always use helpers for new tests**: Don't manually create XHTML strings
2. **Update existing tests gradually**: Fix one test file at a time using helpers
3. **Auto-generated IDs**: If you don't provide an ID, one will be generated
4. **Image format**: Use `create_test_artifact_with_images()` for vision model tests
5. **Context testing**: Use `create_augmented_requirement()` for context-aware tests

---

## Common Patterns

### Pattern 1: Mocking Extractor with Helpers

```python
@pytest.fixture
def mock_extractor_with_artifacts():
    """Mock extractor that returns XHTML-formatted artifacts."""
    extractor = Mock()
    extractor.extract_reqifz_content = Mock(return_value=[
        create_test_heading("ACC System"),
        create_test_requirement("ACC shall maintain distance", requirement_id="REQ_001"),
        create_test_requirement("ACC shall brake if needed", requirement_id="REQ_002")
    ])
    return extractor
```

### Pattern 2: Testing with Image Artifacts

```python
def test_vision_model_selection():
    """Test that vision model is selected for requirements with images."""
    # Requirement with images
    req_with_images = create_test_artifact_with_images(
        "State machine diagram",
        image_paths=["test.png"]
    )

    # Requirement without images
    req_without_images = create_test_requirement("Text-only requirement")

    config = ConfigManager()
    config.ollama.enable_vision = True

    # Vision model for images
    assert config.get_model_for_requirement(req_with_images) == "llama3.2-vision:11b"

    # Text model for text-only
    assert config.get_model_for_requirement(req_without_images) == "llama3.1:8b"
```

---

## Migration Guide

For detailed instructions on updating existing tests, see:
- `tests/helpers/test_artifact_builder_verification.py` - Working examples
- `TEST_MAINTENANCE_BREAKDOWN.md` - Complete migration plan

**Estimated Time**: 2-3 hours to update 28 integration tests using these helpers.
