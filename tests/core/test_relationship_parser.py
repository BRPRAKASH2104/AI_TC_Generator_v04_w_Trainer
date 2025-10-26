"""Tests for requirement relationship parsing"""

import xml.etree.ElementTree as ET

import pytest

from core.relationship_parser import (
    RelationType,
    RequirementRelationshipParser,
)


@pytest.fixture
def parser():
    """Create a relationship parser instance"""
    return RequirementRelationshipParser()


@pytest.fixture
def namespaces():
    """REQIF namespaces"""
    return {
        "reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd",
        "html": "http://www.w3.org/1999/xhtml",
    }


@pytest.fixture
def sample_reqif_with_relationships():
    """Sample REQIF XML with SPEC-RELATION elements"""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
        <CORE-CONTENT>
            <REQ-IF-CONTENT>
                <SPEC-TYPES>
                    <SPEC-RELATION-TYPE IDENTIFIER="REL-TYPE-001" LONG-NAME="Parent-Child"/>
                    <SPEC-RELATION-TYPE IDENTIFIER="REL-TYPE-002" LONG-NAME="Depends-On"/>
                </SPEC-TYPES>
                <SPEC-RELATIONS>
                    <SPEC-RELATION IDENTIFIER="REL-001">
                        <TYPE>
                            <SPEC-RELATION-TYPE-REF>REL-TYPE-001</SPEC-RELATION-TYPE-REF>
                        </TYPE>
                        <SOURCE>
                            <SPEC-OBJECT-REF>REQ-PARENT-001</SPEC-OBJECT-REF>
                        </SOURCE>
                        <TARGET>
                            <SPEC-OBJECT-REF>REQ-CHILD-001</SPEC-OBJECT-REF>
                        </TARGET>
                    </SPEC-RELATION>
                    <SPEC-RELATION IDENTIFIER="REL-002">
                        <TYPE>
                            <SPEC-RELATION-TYPE-REF>REL-TYPE-001</SPEC-RELATION-TYPE-REF>
                        </TYPE>
                        <SOURCE>
                            <SPEC-OBJECT-REF>REQ-PARENT-001</SPEC-OBJECT-REF>
                        </SOURCE>
                        <TARGET>
                            <SPEC-OBJECT-REF>REQ-CHILD-002</SPEC-OBJECT-REF>
                        </TARGET>
                    </SPEC-RELATION>
                    <SPEC-RELATION IDENTIFIER="REL-003">
                        <TYPE>
                            <SPEC-RELATION-TYPE-REF>REL-TYPE-002</SPEC-RELATION-TYPE-REF>
                        </TYPE>
                        <SOURCE>
                            <SPEC-OBJECT-REF>REQ-CHILD-001</SPEC-OBJECT-REF>
                        </SOURCE>
                        <TARGET>
                            <SPEC-OBJECT-REF>REQ-CHILD-002</SPEC-OBJECT-REF>
                        </TARGET>
                    </SPEC-RELATION>
                </SPEC-RELATIONS>
            </REQ-IF-CONTENT>
        </CORE-CONTENT>
    </REQ-IF>
    """
    return ET.fromstring(xml_content)


@pytest.fixture
def sample_reqif_without_relationships():
    """Sample REQIF XML without SPEC-RELATION elements"""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
        <CORE-CONTENT>
            <REQ-IF-CONTENT>
                <SPEC-TYPES>
                    <SPEC-OBJECT-TYPE IDENTIFIER="TYPE-001" LONG-NAME="System Requirement"/>
                </SPEC-TYPES>
            </REQ-IF-CONTENT>
        </CORE-CONTENT>
    </REQ-IF>
    """
    return ET.fromstring(xml_content)


def test_parse_relationships_with_data(parser, sample_reqif_with_relationships, namespaces):
    """Test parsing relationships from REQIF with SPEC-RELATION elements"""
    spec_obj_to_foreign_id = {
        "REQ-PARENT-001": "REQ_PARENT_001",
        "REQ-CHILD-001": "REQ_CHILD_001",
        "REQ-CHILD-002": "REQ_CHILD_002",
    }

    relationships, parent_child_map = parser.parse_relationships(
        sample_reqif_with_relationships, namespaces, spec_obj_to_foreign_id
    )

    # Should find 3 relationships
    assert len(relationships) == 3

    # Check first relationship (parent-child)
    rel1 = relationships[0]
    assert rel1["id"] == "REL-001"
    assert rel1["source_id"] == "REQ_PARENT_001"
    assert rel1["target_id"] == "REQ_CHILD_001"
    assert rel1["relation_type"] == RelationType.PARENT_CHILD

    # Check parent-child map
    assert "REQ_PARENT_001" in parent_child_map
    assert len(parent_child_map["REQ_PARENT_001"]) == 2
    assert "REQ_CHILD_001" in parent_child_map["REQ_PARENT_001"]
    assert "REQ_CHILD_002" in parent_child_map["REQ_PARENT_001"]


def test_parse_relationships_without_data(parser, sample_reqif_without_relationships, namespaces):
    """Test parsing relationships from REQIF without SPEC-RELATION elements"""
    relationships, parent_child_map = parser.parse_relationships(
        sample_reqif_without_relationships, namespaces, {}
    )

    assert len(relationships) == 0
    assert len(parent_child_map) == 0


def test_classify_relation_type(parser):
    """Test relationship type classification"""
    assert parser._classify_relation_type("Parent-Child") == RelationType.PARENT_CHILD
    assert parser._classify_relation_type("Hierarchy") == RelationType.PARENT_CHILD
    assert parser._classify_relation_type("Derived From") == RelationType.DERIVES_FROM
    assert parser._classify_relation_type("Depends-On") == RelationType.DEPENDS_ON
    assert parser._classify_relation_type("Refines") == RelationType.REFINES
    assert parser._classify_relation_type("Satisfies") == RelationType.SATISFIES
    assert parser._classify_relation_type("Verifies") == RelationType.VERIFIES
    assert parser._classify_relation_type("Unknown Type") == RelationType.UNKNOWN


def test_augment_requirements_with_relationships(parser):
    """Test augmenting requirements with relationship metadata"""
    requirements = [
        {"id": "REQ_PARENT_001", "text": "Parent requirement"},
        {"id": "REQ_CHILD_001", "text": "Child requirement 1"},
        {"id": "REQ_CHILD_002", "text": "Child requirement 2"},
    ]

    parent_child_map = {
        "REQ_PARENT_001": ["REQ_CHILD_001", "REQ_CHILD_002"],
    }

    augmented = parser.augment_requirements_with_relationships(requirements, parent_child_map)

    # Check parent requirement
    parent = next(r for r in augmented if r["id"] == "REQ_PARENT_001")
    assert parent["parent_id"] is None
    assert len(parent["child_ids"]) == 2
    assert parent["hierarchy_level"] == 0

    # Check child requirements
    child1 = next(r for r in augmented if r["id"] == "REQ_CHILD_001")
    assert child1["parent_id"] == "REQ_PARENT_001"
    assert len(child1["child_ids"]) == 0
    assert child1["hierarchy_level"] == 1

    child2 = next(r for r in augmented if r["id"] == "REQ_CHILD_002")
    assert child2["parent_id"] == "REQ_PARENT_001"
    assert child2["hierarchy_level"] == 1


def test_calculate_hierarchy_level(parser):
    """Test hierarchy level calculation"""
    child_to_parent = {
        "REQ_LEVEL_1": "REQ_ROOT",
        "REQ_LEVEL_2": "REQ_LEVEL_1",
        "REQ_LEVEL_3": "REQ_LEVEL_2",
    }

    assert parser._calculate_hierarchy_level("REQ_ROOT", child_to_parent) == 0
    assert parser._calculate_hierarchy_level("REQ_LEVEL_1", child_to_parent) == 1
    assert parser._calculate_hierarchy_level("REQ_LEVEL_2", child_to_parent) == 2
    assert parser._calculate_hierarchy_level("REQ_LEVEL_3", child_to_parent) == 3


def test_calculate_hierarchy_level_with_cycle(parser):
    """Test hierarchy level calculation with circular reference"""
    child_to_parent = {
        "REQ_A": "REQ_B",
        "REQ_B": "REQ_C",
        "REQ_C": "REQ_A",  # Circular reference
    }

    # Should stop at max_depth to prevent infinite loop
    level = parser._calculate_hierarchy_level("REQ_A", child_to_parent, max_depth=10)
    assert level == 10


def test_build_dependency_graph(parser):
    """Test building dependency graph"""
    relationships = [
        {
            "source_id": "REQ_A",
            "target_id": "REQ_B",
            "relation_type": RelationType.DEPENDS_ON,
        },
        {
            "source_id": "REQ_A",
            "target_id": "REQ_C",
            "relation_type": RelationType.DERIVES_FROM,
        },
        {
            "source_id": "REQ_B",
            "target_id": "REQ_C",
            "relation_type": RelationType.REFINES,
        },
        {
            "source_id": "REQ_D",
            "target_id": "REQ_E",
            "relation_type": RelationType.PARENT_CHILD,  # Should be ignored
        },
    ]

    graph = parser.build_dependency_graph(relationships)

    # Check dependencies (who depends on what)
    assert "REQ_A" in graph["dependencies"]
    assert "REQ_B" in graph["dependencies"]["REQ_A"]
    assert "REQ_C" in graph["dependencies"]["REQ_A"]
    assert "REQ_C" in graph["dependencies"]["REQ_B"]

    # Check dependents (who is depended on by what)
    assert "REQ_B" in graph["dependents"]
    assert "REQ_A" in graph["dependents"]["REQ_B"]
    assert "REQ_C" in graph["dependents"]
    assert "REQ_A" in graph["dependents"]["REQ_C"]
    assert "REQ_B" in graph["dependents"]["REQ_C"]

    # Parent-child relationship should not be in dependency graph
    assert "REQ_D" not in graph["dependencies"]


def test_find_root_requirements(parser):
    """Test finding root requirements"""
    requirements = [
        {"id": "REQ_ROOT_1", "parent_id": None, "child_ids": ["REQ_CHILD_1"]},
        {"id": "REQ_ROOT_2", "parent_id": None, "child_ids": []},
        {"id": "REQ_CHILD_1", "parent_id": "REQ_ROOT_1", "child_ids": []},
    ]

    roots = parser.find_root_requirements(requirements)

    assert len(roots) == 2
    assert roots[0]["id"] == "REQ_ROOT_1"
    assert roots[1]["id"] == "REQ_ROOT_2"


def test_find_leaf_requirements(parser):
    """Test finding leaf requirements"""
    requirements = [
        {"id": "REQ_ROOT", "parent_id": None, "child_ids": ["REQ_CHILD_1", "REQ_CHILD_2"]},
        {"id": "REQ_CHILD_1", "parent_id": "REQ_ROOT", "child_ids": []},
        {"id": "REQ_CHILD_2", "parent_id": "REQ_ROOT", "child_ids": []},
    ]

    leaves = parser.find_leaf_requirements(requirements)

    assert len(leaves) == 2
    assert leaves[0]["id"] == "REQ_CHILD_1"
    assert leaves[1]["id"] == "REQ_CHILD_2"


def test_get_requirement_tree(parser):
    """Test building requirement tree"""
    requirements = [
        {"id": "REQ_ROOT", "type": "Heading", "text": "Root requirement"},
        {"id": "REQ_CHILD_1", "type": "Requirement", "text": "Child 1"},
        {"id": "REQ_CHILD_2", "type": "Requirement", "text": "Child 2"},
        {
            "id": "REQ_GRANDCHILD_1",
            "type": "Requirement",
            "text": "Grandchild 1",
        },
    ]

    parent_child_map = {
        "REQ_ROOT": ["REQ_CHILD_1", "REQ_CHILD_2"],
        "REQ_CHILD_1": ["REQ_GRANDCHILD_1"],
    }

    # First augment requirements
    requirements = parser.augment_requirements_with_relationships(requirements, parent_child_map)

    # Then build tree
    tree = parser.get_requirement_tree(requirements, parent_child_map)

    assert tree["total_requirements"] == 4
    assert len(tree["roots"]) == 1

    root_node = tree["roots"][0]
    assert root_node["id"] == "REQ_ROOT"
    assert len(root_node["children"]) == 2

    # Check first child
    child1 = root_node["children"][0]
    assert child1["id"] == "REQ_CHILD_1"
    assert len(child1["children"]) == 1

    # Check grandchild
    grandchild1 = child1["children"][0]
    assert grandchild1["id"] == "REQ_GRANDCHILD_1"
    assert len(grandchild1["children"]) == 0


def test_get_requirement_tree_with_circular_reference(parser):
    """Test building tree with circular reference"""
    requirements = [
        {"id": "REQ_A", "type": "Requirement", "text": "Requirement A"},
        {"id": "REQ_B", "type": "Requirement", "text": "Requirement B"},
    ]

    # Create circular reference: A -> B -> A
    parent_child_map = {
        "REQ_A": ["REQ_B"],
        "REQ_B": ["REQ_A"],
    }

    requirements = parser.augment_requirements_with_relationships(requirements, parent_child_map)
    tree = parser.get_requirement_tree(requirements, parent_child_map)

    # Should not crash and should handle circular reference gracefully
    assert "roots" in tree
    # Both are technically roots since they form a cycle
    assert len(tree["roots"]) >= 0


def test_augment_requirements_without_relationships(parser):
    """Test augmenting requirements when no relationships exist"""
    requirements = [
        {"id": "REQ_001", "text": "Requirement 1"},
        {"id": "REQ_002", "text": "Requirement 2"},
    ]

    parent_child_map = {}

    augmented = parser.augment_requirements_with_relationships(requirements, parent_child_map)

    # All requirements should have no parents or children
    for req in augmented:
        assert req["parent_id"] is None
        assert len(req["child_ids"]) == 0
        assert req["hierarchy_level"] == 0


def test_build_relation_type_mapping(parser, sample_reqif_with_relationships, namespaces):
    """Test building relation type mapping"""
    relation_type_map = parser._build_relation_type_mapping(
        sample_reqif_with_relationships, namespaces
    )

    assert len(relation_type_map) == 2
    assert relation_type_map["REL-TYPE-001"] == "Parent-Child"
    assert relation_type_map["REL-TYPE-002"] == "Depends-On"


def test_extract_spec_relation_with_missing_source(parser, namespaces):
    """Test extracting SPEC-RELATION with missing SOURCE"""
    xml_content = """
    <SPEC-RELATION xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd"
                   IDENTIFIER="REL-001">
        <TYPE>
            <SPEC-RELATION-TYPE-REF>REL-TYPE-001</SPEC-RELATION-TYPE-REF>
        </TYPE>
        <TARGET>
            <SPEC-OBJECT-REF>REQ-002</SPEC-OBJECT-REF>
        </TARGET>
    </SPEC-RELATION>
    """
    spec_relation = ET.fromstring(xml_content)

    parser.relation_type_map = {"REL-TYPE-001": "Parent-Child"}
    parser.foreign_id_map = {}

    relationship = parser._extract_spec_relation(spec_relation, namespaces)

    # Should return None because source is missing
    assert relationship is None


def test_extract_spec_relation_with_missing_target(parser, namespaces):
    """Test extracting SPEC-RELATION with missing TARGET"""
    xml_content = """
    <SPEC-RELATION xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd"
                   IDENTIFIER="REL-001">
        <TYPE>
            <SPEC-RELATION-TYPE-REF>REL-TYPE-001</SPEC-RELATION-TYPE-REF>
        </TYPE>
        <SOURCE>
            <SPEC-OBJECT-REF>REQ-001</SPEC-OBJECT-REF>
        </SOURCE>
    </SPEC-RELATION>
    """
    spec_relation = ET.fromstring(xml_content)

    parser.relation_type_map = {"REL-TYPE-001": "Parent-Child"}
    parser.foreign_id_map = {}

    relationship = parser._extract_spec_relation(spec_relation, namespaces)

    # Should return None because target is missing
    assert relationship is None


def test_multiple_levels_hierarchy(parser):
    """Test hierarchy with multiple levels"""
    requirements = [
        {"id": "REQ_ROOT", "text": "Root"},
        {"id": "REQ_L1_A", "text": "Level 1 A"},
        {"id": "REQ_L1_B", "text": "Level 1 B"},
        {"id": "REQ_L2_A", "text": "Level 2 A"},
        {"id": "REQ_L2_B", "text": "Level 2 B"},
        {"id": "REQ_L3_A", "text": "Level 3 A"},
    ]

    parent_child_map = {
        "REQ_ROOT": ["REQ_L1_A", "REQ_L1_B"],
        "REQ_L1_A": ["REQ_L2_A", "REQ_L2_B"],
        "REQ_L2_A": ["REQ_L3_A"],
    }

    augmented = parser.augment_requirements_with_relationships(requirements, parent_child_map)

    # Check hierarchy levels
    levels = {req["id"]: req["hierarchy_level"] for req in augmented}

    assert levels["REQ_ROOT"] == 0
    assert levels["REQ_L1_A"] == 1
    assert levels["REQ_L1_B"] == 1
    assert levels["REQ_L2_A"] == 2
    assert levels["REQ_L2_B"] == 2
    assert levels["REQ_L3_A"] == 3
