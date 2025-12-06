"""
Relationship parser for REQIF SPEC-RELATION elements.

This module provides functionality to parse and extract requirement relationships
from REQIFZ files, building parent-child hierarchies and dependency graphs.
"""

from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import xml.etree.ElementTree as ET

# Type aliases for better readability (PEP 695 style)
type RelationshipData = dict[str, Any]
type RelationshipList = list[RelationshipData]
type RelationshipMap = dict[str, list[str]]


class RelationType(StrEnum):
    """Enumeration of common REQIF relationship types"""

    PARENT_CHILD = "parent_child"
    DERIVES_FROM = "derives_from"
    DEPENDS_ON = "depends_on"
    REFINES = "refines"
    SATISFIES = "satisfies"
    VERIFIES = "verifies"
    UNKNOWN = "unknown"


class RequirementRelationshipParser:
    """Parses requirement relationships from REQIF SPEC-RELATION elements"""

    __slots__ = ("logger", "relation_type_map", "foreign_id_map")

    def __init__(self, logger=None):
        self.logger = logger
        self.relation_type_map: dict[str, str] = {}
        self.foreign_id_map: dict[str, str] = {}

    def parse_relationships(
        self, root: ET.Element, namespaces: dict[str, str], spec_obj_to_foreign_id: dict[str, str]
    ) -> tuple[RelationshipList, RelationshipMap]:
        """
        Parse all SPEC-RELATION elements from REQIF XML.

        Args:
            root: Root XML element of REQIF document
            namespaces: XML namespaces dictionary
            spec_obj_to_foreign_id: Mapping of SPEC-OBJECT identifiers to foreign IDs

        Returns:
            Tuple of (relationships_list, parent_child_map)
            - relationships_list: List of all relationship data
            - parent_child_map: Dict mapping parent IDs to lists of child IDs
        """
        # Build relation type mapping
        self.relation_type_map = self._build_relation_type_mapping(root, namespaces)
        self.foreign_id_map = spec_obj_to_foreign_id

        # Find all SPEC-RELATION elements
        spec_relations = root.findall(".//reqif:SPEC-RELATION", namespaces)

        if not spec_relations:
            if self.logger:
                self.logger.debug("No SPEC-RELATION elements found in REQIF")
            return [], {}

        if self.logger:
            self.logger.info(f"Found {len(spec_relations)} SPEC-RELATION elements")

        # Extract relationships
        relationships = []
        parent_child_map: RelationshipMap = {}

        for spec_relation in spec_relations:
            relationship = self._extract_spec_relation(spec_relation, namespaces)
            if relationship:
                relationships.append(relationship)

                # Build parent-child map
                if relationship["relation_type"] == RelationType.PARENT_CHILD:
                    parent_id = relationship["source_id"]
                    child_id = relationship["target_id"]

                    if parent_id not in parent_child_map:
                        parent_child_map[parent_id] = []
                    parent_child_map[parent_id].append(child_id)

        if self.logger:
            self.logger.info(
                f"Parsed {len(relationships)} relationships, "
                f"{len(parent_child_map)} parent-child relationships"
            )

        return relationships, parent_child_map

    def _build_relation_type_mapping(
        self, root: ET.Element, namespaces: dict[str, str]
    ) -> dict[str, str]:
        """Build mapping of SPEC-RELATION-TYPE identifiers to their LONG-NAME values"""
        relation_type_map = {}

        # Find all SPEC-RELATION-TYPE elements
        relation_types = root.findall(".//reqif:SPEC-RELATION-TYPE", namespaces)

        for relation_type in relation_types:
            identifier = relation_type.get("IDENTIFIER")
            long_name = relation_type.get("LONG-NAME")

            if identifier and long_name:
                relation_type_map[identifier] = long_name

        if self.logger:
            self.logger.debug(f"Found {len(relation_type_map)} SPEC-RELATION-TYPE definitions")

        return relation_type_map

    def _extract_spec_relation(
        self, spec_relation: ET.Element, namespaces: dict[str, str]
    ) -> RelationshipData | None:
        """Extract a single SPEC-RELATION element"""
        try:
            relationship = {
                "id": spec_relation.get("IDENTIFIER", "UNKNOWN"),
                "source_id": "",
                "target_id": "",
                "relation_type": RelationType.UNKNOWN,
                "relation_type_name": "",
            }

            # Extract SOURCE (parent/origin)
            source = spec_relation.find(".//reqif:SOURCE", namespaces)
            if source is not None:
                source_ref = source.find(".//reqif:SPEC-OBJECT-REF", namespaces)
                if source_ref is not None and source_ref.text:
                    # Resolve to foreign ID if available
                    internal_id = source_ref.text
                    relationship["source_id"] = self.foreign_id_map.get(internal_id, internal_id)

            # Extract TARGET (child/destination)
            target = spec_relation.find(".//reqif:TARGET", namespaces)
            if target is not None:
                target_ref = target.find(".//reqif:SPEC-OBJECT-REF", namespaces)
                if target_ref is not None and target_ref.text:
                    # Resolve to foreign ID if available
                    internal_id = target_ref.text
                    relationship["target_id"] = self.foreign_id_map.get(internal_id, internal_id)

            # Extract TYPE (relationship type)
            type_element = spec_relation.find(".//reqif:TYPE", namespaces)
            if type_element is not None:
                type_ref = type_element.find(".//reqif:SPEC-RELATION-TYPE-REF", namespaces)
                if type_ref is not None and type_ref.text:
                    relation_type_id = type_ref.text
                    relation_type_name = self.relation_type_map.get(relation_type_id, "")
                    relationship["relation_type_name"] = relation_type_name
                    relationship["relation_type"] = self._classify_relation_type(relation_type_name)

            # Validate that we have source and target
            if not relationship["source_id"] or not relationship["target_id"]:
                if self.logger:
                    self.logger.warning(
                        f"Skipping relationship {relationship['id']}: missing source or target"
                    )
                return None

            return relationship

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error extracting SPEC-RELATION: {e}")
            return None

    def _classify_relation_type(self, relation_type_name: str) -> RelationType:
        """Classify relationship type based on type name"""
        if not relation_type_name:
            return RelationType.UNKNOWN

        name_lower = relation_type_name.lower()

        # Pattern matching for relationship classification
        match True:
            case _ if any(
                keyword in name_lower for keyword in ["parent", "child", "hierarchy", "contains"]
            ):
                return RelationType.PARENT_CHILD
            case _ if any(keyword in name_lower for keyword in ["derive", "derived", "from"]):
                return RelationType.DERIVES_FROM
            case _ if any(keyword in name_lower for keyword in ["depend", "requires", "needs"]):
                return RelationType.DEPENDS_ON
            case _ if "refine" in name_lower:
                return RelationType.REFINES
            case _ if any(keyword in name_lower for keyword in ["satisfy", "satisfies"]):
                return RelationType.SATISFIES
            case _ if any(keyword in name_lower for keyword in ["verify", "verifies", "test"]):
                return RelationType.VERIFIES
            case _:
                return RelationType.UNKNOWN

    def augment_requirements_with_relationships(
        self, requirements: list[dict[str, Any]], parent_child_map: RelationshipMap
    ) -> list[dict[str, Any]]:
        """
        Augment requirements with relationship metadata.

        Args:
            requirements: List of requirement artifacts
            parent_child_map: Mapping of parent IDs to child IDs

        Returns:
            List of requirements augmented with relationship metadata
        """
        # Build reverse map (child -> parent)
        child_to_parent: dict[str, str] = {}
        for parent_id, children in parent_child_map.items():
            for child_id in children:
                child_to_parent[child_id] = parent_id

        # Augment each requirement
        for requirement in requirements:
            req_id = requirement.get("id", "")

            # Add parent ID if this requirement is a child
            requirement["parent_id"] = child_to_parent.get(req_id)

            # Add list of child IDs if this requirement is a parent
            requirement["child_ids"] = parent_child_map.get(req_id, [])

            # Add hierarchy level (depth in tree)
            requirement["hierarchy_level"] = self._calculate_hierarchy_level(
                req_id, child_to_parent
            )

        if self.logger:
            parents_count = len([r for r in requirements if r.get("child_ids")])
            children_count = len([r for r in requirements if r.get("parent_id")])
            self.logger.info(
                f"Augmented requirements: {parents_count} parents, {children_count} children"
            )

        return requirements

    def _calculate_hierarchy_level(
        self, req_id: str, child_to_parent: dict[str, str], max_depth: int = 10
    ) -> int:
        """
        Calculate hierarchy level (depth) of a requirement.

        Args:
            req_id: Requirement ID
            child_to_parent: Mapping of child IDs to parent IDs
            max_depth: Maximum depth to prevent infinite loops

        Returns:
            Hierarchy level (0 = root, 1 = first level child, etc.)
        """
        level = 0
        current_id = req_id

        # Traverse up the parent chain
        while current_id in child_to_parent and level < max_depth:
            current_id = child_to_parent[current_id]
            level += 1

        return level

    def build_dependency_graph(
        self, relationships: RelationshipList
    ) -> dict[str, dict[str, list[str]]]:
        """
        Build a dependency graph from relationships.

        Args:
            relationships: List of relationship data

        Returns:
            Dict with 'dependencies' and 'dependents' keys, each mapping IDs to lists of related IDs
        """
        dependencies: RelationshipMap = {}  # req_id -> list of IDs it depends on
        dependents: RelationshipMap = {}  # req_id -> list of IDs that depend on it

        for relationship in relationships:
            source_id = relationship["source_id"]
            target_id = relationship["target_id"]
            rel_type = relationship["relation_type"]

            # Only process dependency-type relationships
            if rel_type in [
                RelationType.DEPENDS_ON,
                RelationType.DERIVES_FROM,
                RelationType.REFINES,
            ]:
                # source depends on target
                if source_id not in dependencies:
                    dependencies[source_id] = []
                dependencies[source_id].append(target_id)

                # target is depended on by source
                if target_id not in dependents:
                    dependents[target_id] = []
                dependents[target_id].append(source_id)

        if self.logger:
            self.logger.debug(
                f"Built dependency graph: {len(dependencies)} nodes with dependencies, "
                f"{len(dependents)} nodes with dependents"
            )

        return {"dependencies": dependencies, "dependents": dependents}

    def find_root_requirements(self, requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Find root requirements (those with no parent).

        Args:
            requirements: List of requirement artifacts

        Returns:
            List of root requirements
        """
        root_requirements = [r for r in requirements if not r.get("parent_id")]

        if self.logger:
            self.logger.debug(f"Found {len(root_requirements)} root requirements")

        return root_requirements

    def find_leaf_requirements(self, requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Find leaf requirements (those with no children).

        Args:
            requirements: List of requirement artifacts

        Returns:
            List of leaf requirements
        """
        leaf_requirements = [r for r in requirements if not r.get("child_ids")]

        if self.logger:
            self.logger.debug(f"Found {len(leaf_requirements)} leaf requirements")

        return leaf_requirements

    def get_requirement_tree(
        self, requirements: list[dict[str, Any]], parent_child_map: RelationshipMap
    ) -> dict[str, Any]:
        """
        Build a tree representation of requirements.

        Args:
            requirements: List of requirement artifacts
            parent_child_map: Mapping of parent IDs to child IDs

        Returns:
            Tree structure with roots and nested children
        """
        # Create ID to requirement mapping
        req_by_id = {r["id"]: r for r in requirements}

        # Find root requirements
        root_requirements = self.find_root_requirements(requirements)

        # Build tree recursively
        def build_subtree(req_id: str, visited: set[str]) -> dict[str, Any] | None:
            """Build subtree for a requirement"""
            if req_id in visited:
                # Prevent infinite loops from circular references
                return None

            visited.add(req_id)
            requirement = req_by_id.get(req_id)

            if not requirement:
                return None

            tree_node = {
                "id": req_id,
                "type": requirement.get("type"),
                "text": requirement.get("text", "")[:100],  # Truncate for readability
                "children": [],
            }

            # Add children recursively
            child_ids = parent_child_map.get(req_id, [])
            for child_id in child_ids:
                child_subtree = build_subtree(child_id, visited.copy())
                if child_subtree:
                    tree_node["children"].append(child_subtree)

            return tree_node

        # Build tree from all roots
        tree = {"roots": [], "total_requirements": len(requirements)}

        for root_req in root_requirements:
            root_id = root_req["id"]
            subtree = build_subtree(root_id, set())
            if subtree:
                tree["roots"].append(subtree)

        if self.logger:
            self.logger.debug(f"Built requirement tree with {len(tree['roots'])} root nodes")

        return tree
