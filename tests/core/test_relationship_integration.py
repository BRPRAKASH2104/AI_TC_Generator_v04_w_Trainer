"""Integration tests for relationship parsing with extractor"""

import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from core.extractors import REQIFArtifactExtractor


@pytest.fixture
def sample_reqifz_with_relationships():
    """Create a temporary REQIFZ file with SPEC-RELATION elements"""
    reqif_content = """<?xml version="1.0" encoding="UTF-8"?>
    <REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd"
            xmlns:xhtml="http://www.w3.org/1999/xhtml">
        <CORE-CONTENT>
            <REQ-IF-CONTENT>
                <SPEC-TYPES>
                    <SPEC-OBJECT-TYPE IDENTIFIER="OBJ-TYPE-001" LONG-NAME="System Requirement">
                        <SPEC-ATTRIBUTES>
                            <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="ATTR-FOREIGN-ID" LONG-NAME="ReqIF.ForeignID"/>
                            <ATTRIBUTE-DEFINITION-XHTML IDENTIFIER="ATTR-TEXT-001" LONG-NAME="ReqIF.Text"/>
                        </SPEC-ATTRIBUTES>
                    </SPEC-OBJECT-TYPE>
                    <SPEC-RELATION-TYPE IDENTIFIER="REL-TYPE-001" LONG-NAME="Parent-Child"/>
                </SPEC-TYPES>
                <SPEC-OBJECTS>
                    <SPEC-OBJECT IDENTIFIER="OBJ-001">
                        <TYPE>
                            <SPEC-OBJECT-TYPE-REF>OBJ-TYPE-001</SPEC-OBJECT-TYPE-REF>
                        </TYPE>
                        <VALUES>
                            <ATTRIBUTE-VALUE-STRING THE-VALUE="REQ_PARENT_001">
                                <DEFINITION>
                                    <ATTRIBUTE-DEFINITION-STRING-REF>ATTR-FOREIGN-ID</ATTRIBUTE-DEFINITION-STRING-REF>
                                </DEFINITION>
                            </ATTRIBUTE-VALUE-STRING>
                            <ATTRIBUTE-VALUE-XHTML>
                                <DEFINITION>
                                    <ATTRIBUTE-DEFINITION-XHTML-REF>ATTR-TEXT-001</ATTRIBUTE-DEFINITION-XHTML-REF>
                                </DEFINITION>
                                <THE-VALUE>
                                    <xhtml:div>Parent requirement text</xhtml:div>
                                </THE-VALUE>
                            </ATTRIBUTE-VALUE-XHTML>
                        </VALUES>
                    </SPEC-OBJECT>
                    <SPEC-OBJECT IDENTIFIER="OBJ-002">
                        <TYPE>
                            <SPEC-OBJECT-TYPE-REF>OBJ-TYPE-001</SPEC-OBJECT-TYPE-REF>
                        </TYPE>
                        <VALUES>
                            <ATTRIBUTE-VALUE-STRING THE-VALUE="REQ_CHILD_001">
                                <DEFINITION>
                                    <ATTRIBUTE-DEFINITION-STRING-REF>ATTR-FOREIGN-ID</ATTRIBUTE-DEFINITION-STRING-REF>
                                </DEFINITION>
                            </ATTRIBUTE-VALUE-STRING>
                            <ATTRIBUTE-VALUE-XHTML>
                                <DEFINITION>
                                    <ATTRIBUTE-DEFINITION-XHTML-REF>ATTR-TEXT-001</ATTRIBUTE-DEFINITION-XHTML-REF>
                                </DEFINITION>
                                <THE-VALUE>
                                    <xhtml:div>Child requirement text</xhtml:div>
                                </THE-VALUE>
                            </ATTRIBUTE-VALUE-XHTML>
                        </VALUES>
                    </SPEC-OBJECT>
                </SPEC-OBJECTS>
                <SPEC-RELATIONS>
                    <SPEC-RELATION IDENTIFIER="REL-001">
                        <TYPE>
                            <SPEC-RELATION-TYPE-REF>REL-TYPE-001</SPEC-RELATION-TYPE-REF>
                        </TYPE>
                        <SOURCE>
                            <SPEC-OBJECT-REF>OBJ-001</SPEC-OBJECT-REF>
                        </SOURCE>
                        <TARGET>
                            <SPEC-OBJECT-REF>OBJ-002</SPEC-OBJECT-REF>
                        </TARGET>
                    </SPEC-RELATION>
                </SPEC-RELATIONS>
            </REQ-IF-CONTENT>
        </CORE-CONTENT>
    </REQ-IF>
    """

    # Create temporary REQIFZ file
    temp_dir = TemporaryDirectory()
    reqifz_path = Path(temp_dir.name) / "test_relationships.reqifz"

    with zipfile.ZipFile(reqifz_path, "w") as zip_file:
        zip_file.writestr("content.reqif", reqif_content)

    yield reqifz_path

    # Cleanup
    temp_dir.cleanup()


@pytest.fixture
def sample_reqifz_without_relationships():
    """Create a temporary REQIFZ file without SPEC-RELATION elements"""
    reqif_content = """<?xml version="1.0" encoding="UTF-8"?>
    <REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd"
            xmlns:xhtml="http://www.w3.org/1999/xhtml">
        <CORE-CONTENT>
            <REQ-IF-CONTENT>
                <SPEC-TYPES>
                    <SPEC-OBJECT-TYPE IDENTIFIER="OBJ-TYPE-001" LONG-NAME="System Requirement">
                        <SPEC-ATTRIBUTES>
                            <ATTRIBUTE-DEFINITION-XHTML IDENTIFIER="ATTR-TEXT-001" LONG-NAME="ReqIF.Text"/>
                        </SPEC-ATTRIBUTES>
                    </SPEC-OBJECT-TYPE>
                </SPEC-TYPES>
                <SPEC-OBJECTS>
                    <SPEC-OBJECT IDENTIFIER="OBJ-001">
                        <TYPE>
                            <SPEC-OBJECT-TYPE-REF>OBJ-TYPE-001</SPEC-OBJECT-TYPE-REF>
                        </TYPE>
                        <VALUES>
                            <ATTRIBUTE-VALUE-XHTML>
                                <DEFINITION>
                                    <ATTRIBUTE-DEFINITION-XHTML-REF>ATTR-TEXT-001</ATTRIBUTE-DEFINITION-XHTML-REF>
                                </DEFINITION>
                                <THE-VALUE>
                                    <xhtml:div>Requirement text</xhtml:div>
                                </THE-VALUE>
                            </ATTRIBUTE-VALUE-XHTML>
                        </VALUES>
                    </SPEC-OBJECT>
                </SPEC-OBJECTS>
            </REQ-IF-CONTENT>
        </CORE-CONTENT>
    </REQ-IF>
    """

    # Create temporary REQIFZ file
    temp_dir = TemporaryDirectory()
    reqifz_path = Path(temp_dir.name) / "test_no_relationships.reqifz"

    with zipfile.ZipFile(reqifz_path, "w") as zip_file:
        zip_file.writestr("content.reqif", reqif_content)

    yield reqifz_path

    # Cleanup
    temp_dir.cleanup()


def test_extractor_with_relationships(sample_reqifz_with_relationships):
    """Test extractor parses relationships and augments artifacts"""
    extractor = REQIFArtifactExtractor()

    # Extract artifacts
    artifacts = extractor.extract_reqifz_content(sample_reqifz_with_relationships)
    assert len(artifacts) == 2

    # Parse and augment with relationships
    augmented_artifacts, relationship_info = extractor.parse_and_augment_relationships(
        sample_reqifz_with_relationships, artifacts, augment_requirements=True
    )

    # Check relationship info
    assert len(relationship_info["relationships"]) == 1
    assert "REQ_PARENT_001" in relationship_info["parent_child_map"]
    assert "REQ_CHILD_001" in relationship_info["parent_child_map"]["REQ_PARENT_001"]

    # Check augmented artifacts
    parent = next(a for a in augmented_artifacts if a["id"] == "REQ_PARENT_001")
    assert parent["parent_id"] is None
    assert "REQ_CHILD_001" in parent["child_ids"]
    assert parent["hierarchy_level"] == 0

    child = next(a for a in augmented_artifacts if a["id"] == "REQ_CHILD_001")
    assert child["parent_id"] == "REQ_PARENT_001"
    assert len(child["child_ids"]) == 0
    assert child["hierarchy_level"] == 1


def test_extractor_without_relationships(sample_reqifz_without_relationships):
    """Test extractor handles files without relationships gracefully"""
    extractor = REQIFArtifactExtractor()

    # Extract artifacts
    artifacts = extractor.extract_reqifz_content(sample_reqifz_without_relationships)
    assert len(artifacts) == 1

    # Parse and augment with relationships (should handle gracefully)
    augmented_artifacts, relationship_info = extractor.parse_and_augment_relationships(
        sample_reqifz_without_relationships, artifacts, augment_requirements=True
    )

    # Should have no relationships
    assert len(relationship_info["relationships"]) == 0
    assert len(relationship_info["parent_child_map"]) == 0

    # Artifacts should still be augmented with empty relationship data
    assert len(augmented_artifacts) == 1
    artifact = augmented_artifacts[0]
    assert artifact["parent_id"] is None
    assert len(artifact["child_ids"]) == 0
    assert artifact["hierarchy_level"] == 0


def test_extractor_with_dependency_graph(sample_reqifz_with_relationships):
    """Test extractor builds dependency graph when requested"""
    extractor = REQIFArtifactExtractor()

    # Extract artifacts
    artifacts = extractor.extract_reqifz_content(sample_reqifz_with_relationships)

    # Parse with dependency graph enabled
    augmented_artifacts, relationship_info = extractor.parse_and_augment_relationships(
        sample_reqifz_with_relationships,
        artifacts,
        augment_requirements=True,
        build_dependency_graph=True,
    )

    # Check that dependency graph is not built (parent-child is not a dependency type)
    assert "dependency_graph" in relationship_info
    dependency_graph = relationship_info["dependency_graph"]
    assert len(dependency_graph["dependencies"]) == 0
    assert len(dependency_graph["dependents"]) == 0


def test_extractor_without_augmentation(sample_reqifz_with_relationships):
    """Test extractor can parse relationships without augmenting artifacts"""
    extractor = REQIFArtifactExtractor()

    # Extract artifacts
    artifacts = extractor.extract_reqifz_content(sample_reqifz_with_relationships)

    # Parse without augmentation
    augmented_artifacts, relationship_info = extractor.parse_and_augment_relationships(
        sample_reqifz_with_relationships, artifacts, augment_requirements=False
    )

    # Should have relationship info
    assert len(relationship_info["relationships"]) == 1
    assert "REQ_PARENT_001" in relationship_info["parent_child_map"]

    # But artifacts should not be augmented
    for artifact in augmented_artifacts:
        assert "parent_id" not in artifact or artifact.get("parent_id") is None
        assert "child_ids" not in artifact or len(artifact.get("child_ids", [])) == 0
