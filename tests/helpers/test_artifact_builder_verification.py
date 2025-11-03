"""
Verification tests for test artifact builder helpers.

This ensures the helper functions create artifacts in the correct XHTML format
that matches production code output after vision integration (v2.2.0).
"""

import pytest
from tests.helpers.test_artifact_builder import (
    create_test_artifact,
    create_test_requirement,
    create_test_heading,
    create_test_information,
    create_test_interface,
    create_test_artifact_with_images,
    create_test_table,
    create_augmented_requirement,
)


class TestArtifactBuilder:
    """Test the artifact builder helper functions."""

    def test_create_basic_artifact(self):
        """Test creating a basic artifact with XHTML format."""
        artifact = create_test_artifact(
            "Door shall lock when speed > 10 km/h",
            artifact_type="System Requirement",
            artifact_id="REQ_001"
        )

        assert artifact["id"] == "REQ_001"
        assert artifact["type"] == "System Requirement"
        assert "<THE-VALUE" in artifact["text"]
        assert "<html:div>" in artifact["text"]
        assert "<html:p>Door shall lock when speed > 10 km/h</html:p>" in artifact["text"]
        assert "xmlns:ns0" in artifact["text"]
        assert "xmlns:html" in artifact["text"]

    def test_create_requirement_with_table(self):
        """Test creating a requirement with test table."""
        req = create_test_requirement(
            "ACC shall maintain safe distance",
            requirement_id="REQ_ACC_001",
            test_table_data=[
                ["TC001", "Test safe distance", "Pass"],
                ["TC002", "Test emergency brake", "Pass"]
            ]
        )

        assert req["type"] == "System Requirement"
        assert req["id"] == "REQ_ACC_001"
        assert "table" in req
        assert len(req["table"]["data"]) == 2
        assert req["table"]["headers"] == ["Test ID", "Description", "Expected Result"]

    def test_create_heading(self):
        """Test creating a heading artifact."""
        heading = create_test_heading("Door Control System", heading_id="HEAD_001")

        assert heading["type"] == "Heading"
        assert heading["id"] == "HEAD_001"
        assert "Door Control System" in heading["text"]
        assert "<THE-VALUE" in heading["text"]

    def test_create_information(self):
        """Test creating an information artifact."""
        info = create_test_information("Safety critical component")

        assert info["type"] == "Information"
        assert "Safety critical component" in info["text"]
        assert "<THE-VALUE" in info["text"]

    def test_create_interface(self):
        """Test creating an interface artifact."""
        interface = create_test_interface(
            "Vehicle speed signal",
            interface_id="IF_001",
            input_output="Input"
        )

        assert interface["type"] == "System Interface"
        assert interface["id"] == "IF_001"
        assert interface["input_output"] == "Input"
        assert "Vehicle speed signal" in interface["text"]

    def test_create_artifact_with_images(self):
        """Test creating an artifact with embedded image references."""
        artifact = create_test_artifact_with_images(
            "ACC state machine with 4 states",
            image_paths=["diagrams/acc_states.png", "diagrams/acc_transitions.png"],
            artifact_id="REQ_001"
        )

        assert artifact["id"] == "REQ_001"
        assert artifact["has_images"] is True
        assert artifact["image_count"] == 2
        assert '<html:object data="diagrams/acc_states.png" type="image/png" />' in artifact["text"]
        assert '<html:object data="diagrams/acc_transitions.png" type="image/png" />' in artifact["text"]
        assert "ACC state machine with 4 states" in artifact["text"]

    def test_create_augmented_requirement(self):
        """Test creating an augmented requirement with full context."""
        heading = "ACC System"
        info_list = [
            create_test_information("Safety critical"),
            create_test_information("ASIL-D rated")
        ]
        interface_list = [
            create_test_interface("Speed signal", input_output="Input"),
            create_test_interface("Brake signal", input_output="Output")
        ]

        req = create_augmented_requirement(
            "ACC shall maintain safe distance",
            heading=heading,
            info_list=info_list,
            interface_list=interface_list,
            requirement_id="REQ_001"
        )

        # Verify requirement structure
        assert req["id"] == "REQ_001"
        assert req["type"] == "System Requirement"
        assert "ACC shall maintain safe distance" in req["text"]

        # Verify context fields (matching BaseProcessor output)
        assert req["heading"] == "ACC System"
        assert len(req["info_list"]) == 2
        assert len(req["interface_list"]) == 2
        assert req["info_list"][0]["type"] == "Information"
        assert req["interface_list"][0]["type"] == "System Interface"

    def test_auto_generated_ids(self):
        """Test that IDs are auto-generated when not provided."""
        artifact1 = create_test_artifact("Test 1", artifact_type="System Requirement")
        artifact2 = create_test_artifact("Test 2", artifact_type="System Requirement")

        assert "id" in artifact1
        assert "id" in artifact2
        assert artifact1["id"] != artifact2["id"]  # Should be unique
        assert artifact1["id"].startswith("SYS_")  # Type-based prefix

    def test_xhtml_format_matches_production(self):
        """Verify XHTML format matches production extractor output."""
        artifact = create_test_artifact(
            "Door shall lock",
            artifact_type="System Requirement",
            artifact_id="REQ_001"
        )

        text = artifact["text"]

        # Must have THE-VALUE wrapper
        assert text.startswith("<THE-VALUE")
        assert text.endswith("</THE-VALUE>")

        # Must have namespaces
        assert 'xmlns:ns0="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd"' in text
        assert 'xmlns:html="http://www.w3.org/1999/xhtml"' in text

        # Must have html:div and html:p structure
        assert "<html:div>" in text
        assert "<html:p>Door shall lock</html:p>" in text

    def test_object_tag_format_matches_reqif(self):
        """Verify <object> tags match REQIF format for vision model."""
        artifact = create_test_artifact_with_images(
            "Test with image",
            image_paths=["1472801/image-20240709-035006.png"],
            image_types=["image/png"]
        )

        # Must use <html:object> with data attribute (REQIF format)
        assert '<html:object data="1472801/image-20240709-035006.png"' in artifact["text"]
        assert 'type="image/png"' in artifact["text"]

        # Must NOT use <img> tag (common mistake)
        assert "<img" not in artifact["text"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
