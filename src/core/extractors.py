"""
REQIF artifact extractors for the AI Test Case Generator.

This module provides classes for extracting and processing artifacts from REQIFZ files,
with support for different artifact types commonly found in automotive requirements.
"""

import xml.etree.ElementTree as ET
import zipfile
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .image_extractor import RequirementImageExtractor
from .parsers import HTMLTableParser
from .relationship_parser import RequirementRelationshipParser

if TYPE_CHECKING:
    from src.config import ConfigManager

# Type aliases for better readability (PEP 695 style)
type RequirementData = dict[str, Any]
type ArtifactList = list[RequirementData]


class ArtifactType(StrEnum):
    """Enumeration of REQIF artifact types"""

    HEADING = "Heading"
    INFORMATION = "Information"
    DESIGN_INFORMATION = "Design Information"
    APPLICATION_PARAMETER = "Application Parameter"
    SYSTEM_INTERFACE = "System Interface"
    SYSTEM_REQUIREMENT = "System Requirement"
    UNKNOWN = "Unknown"


class REQIFArtifactExtractor:
    """Extracts and processes artifacts from REQIFZ files"""

    __slots__ = ("logger", "html_parser", "use_streaming", "config")

    def __init__(
        self, logger=None, use_streaming: bool = False, config: ConfigManager | None = None
    ):
        self.logger = logger
        self.html_parser = HTMLTableParser()
        # use_streaming is retained for interface compatibility only; the
        # streaming parser was removed (it was never enabled and re-read the
        # already-in-memory XML twice)
        self.use_streaming = use_streaming
        self.config = config

    def extract_reqifz_content(self, reqifz_file_path: Path) -> ArtifactList:
        """
        Extract all artifacts from a REQIFZ file.

        Args:
            reqifz_file_path: Path to the REQIFZ file

        Returns:
            List of extracted artifacts with metadata
        """
        try:
            with zipfile.ZipFile(reqifz_file_path, "r") as zip_file:
                reqif_files = [f for f in zip_file.namelist() if f.endswith(".reqif")]

                if not reqif_files:
                    if self.logger:
                        self.logger.warning(f"No .reqif files found in {reqifz_file_path}")
                    return []

                # Process the first REQIF file found
                reqif_content = zip_file.read(reqif_files[0])
                artifacts = self._parse_reqif_xml(reqif_content)

            artifacts = self._extract_and_augment_images(reqifz_file_path, artifacts)
            return self._augment_relationships_if_enabled(reqifz_file_path, artifacts)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error extracting REQIFZ file {reqifz_file_path}: {e}")
            return []

    def _augment_relationships_if_enabled(self, reqifz_file_path: Path, artifacts: list) -> list:
        """Parse SPEC-RELATION elements and augment artifacts when enabled in config."""
        if not (
            self.config and self.config.relationships.enable_relationship_parsing and artifacts
        ):
            return artifacts

        if self.logger:
            self.logger.info("🔗 Parsing requirement relationships (SPEC-RELATION)...")

        artifacts, relationship_info = self.parse_and_augment_relationships(
            reqifz_file_path,
            artifacts,
            augment_requirements=self.config.relationships.augment_requirements,
            build_dependency_graph=self.config.relationships.build_dependency_graph,
        )

        if self.logger:
            self.logger.info(
                f"🔗 Found {len(relationship_info.get('relationships', []))} relationship(s)"
            )

        return artifacts

    def _extract_and_augment_images(self, reqifz_file_path: Path, artifacts: list) -> list:
        """Extract images and augment artifacts using the shared configuration."""
        if self.config and self.config.image_extraction.enable_image_extraction:
            if self.logger:
                self.logger.info("🖼️  Extracting images from REQIFZ file...")

            image_extractor = RequirementImageExtractor(
                logger=self.logger,
                output_dir=Path(self.config.image_extraction.output_dir),
                save_images=self.config.image_extraction.save_images,
                validate_images=self.config.image_extraction.validate_images,
            )

            images, report = image_extractor.extract_images_from_reqifz(reqifz_file_path)

            if self.logger:
                self.logger.info(
                    f"🖼️  Extracted {report.get('total_images', 0)} images: "
                    f"{report.get('external_files', 0)} external, "
                    f"{report.get('embedded_images', 0)} embedded"
                )

            # Augment artifacts with image references if enabled
            if self.config.image_extraction.augment_artifacts and images:
                artifacts = image_extractor.augment_artifacts_with_images(artifacts, images)
                if self.logger:
                    self.logger.info(
                        f"🔗 Augmented artifacts with image metadata "
                        f"({sum(1 for a in artifacts if a.get('has_images', False))} artifacts have images)"
                    )
        return artifacts

    def _parse_reqif_xml(self, xml_content: bytes) -> ArtifactList:
        """Parse REQIF XML content and extract artifacts"""
        try:
            # DOM-based parsing
            root = ET.fromstring(xml_content)

            # REQIF namespaces
            namespaces = {
                "reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd",
                "html": "http://www.w3.org/1999/xhtml",
            }

            # Build all necessary mappings
            spec_type_map = self._build_spec_type_mapping(root, namespaces)
            foreign_id_map = self._build_foreign_id_mapping(root, namespaces)
            attr_def_map = self._build_attribute_definition_mapping(root, namespaces)

            artifacts = []

            # Find all spec objects (artifacts)
            spec_objects = root.findall(".//reqif:SPEC-OBJECT", namespaces)

            for spec_obj in spec_objects:
                artifact = self._extract_spec_object(
                    spec_obj, namespaces, spec_type_map, foreign_id_map, attr_def_map
                )
                if artifact:
                    artifacts.append(artifact)

            if self.logger:
                self.logger.info(f"Extracted {len(artifacts)} artifacts from REQIF")

            return artifacts

        except ET.ParseError as e:
            if self.logger:
                self.logger.error(f"XML parsing error: {e}")
            return []

    def _build_spec_type_mapping(
        self, root: ET.Element, namespaces: dict[str, str]
    ) -> dict[str, str]:
        """Build a mapping of SPEC-OBJECT-TYPE identifiers to their LONG-NAME values"""
        spec_type_map = {}

        # Find all SPEC-OBJECT-TYPE elements
        spec_types = root.findall(".//reqif:SPEC-OBJECT-TYPE", namespaces)

        for spec_type in spec_types:
            identifier = spec_type.get("IDENTIFIER")
            long_name = spec_type.get("LONG-NAME")

            if identifier and long_name:
                spec_type_map[identifier] = long_name

        if self.logger:
            self.logger.debug(f"Found {len(spec_type_map)} SPEC-OBJECT-TYPE definitions")

        return spec_type_map

    def _build_foreign_id_mapping(
        self, root: ET.Element, namespaces: dict[str, str]
    ) -> dict[str, str]:
        """Build mapping from SPEC-OBJECT-TYPE IDs to their ReqIF.ForeignID attribute identifiers"""
        foreign_id_map = {}

        for spec_type in root.findall(".//reqif:SPEC-OBJECT-TYPE", namespaces):
            type_id = spec_type.get("IDENTIFIER")
            foreign_id_def = spec_type.find(
                ".//reqif:ATTRIBUTE-DEFINITION-STRING[@LONG-NAME='ReqIF.ForeignID']",
                namespaces,
            )
            if foreign_id_def is not None:
                foreign_id_map[type_id] = foreign_id_def.get("IDENTIFIER")

        if self.logger:
            self.logger.debug(f"Found {len(foreign_id_map)} ReqIF.ForeignID attribute definitions")

        return foreign_id_map

    def _build_attribute_definition_mapping(
        self, root: ET.Element, namespaces: dict[str, str]
    ) -> dict[str, str]:
        """Build mapping from ATTRIBUTE-DEFINITION identifiers to their LONG-NAME values"""
        attr_def_map = {}

        # Find all ATTRIBUTE-DEFINITION-XHTML elements
        for attr_def in root.findall(".//reqif:ATTRIBUTE-DEFINITION-XHTML", namespaces):
            identifier = attr_def.get("IDENTIFIER")
            long_name = attr_def.get("LONG-NAME")
            if identifier and long_name:
                attr_def_map[identifier] = long_name

        # Find all ATTRIBUTE-DEFINITION-STRING elements
        for attr_def in root.findall(".//reqif:ATTRIBUTE-DEFINITION-STRING", namespaces):
            identifier = attr_def.get("IDENTIFIER")
            long_name = attr_def.get("LONG-NAME")
            if identifier and long_name:
                attr_def_map[identifier] = long_name

        if self.logger:
            self.logger.debug(f"Found {len(attr_def_map)} attribute definitions")

        return attr_def_map

    def _extract_foreign_id(
        self, values_container, target_foreign_id_ref: str, default_id: str
    ) -> str:
        """Extract foreign ID from VALUES container"""
        if not target_foreign_id_ref:
            return default_id

        for attr_value in values_container.findall(
            "reqif:ATTRIBUTE-VALUE-STRING",
            {"reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd"},
        ):
            definition_ref_node = attr_value.find(
                "reqif:DEFINITION/reqif:ATTRIBUTE-DEFINITION-STRING-REF",
                {"reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd"},
            )
            if (
                definition_ref_node is not None
                and definition_ref_node.text == target_foreign_id_ref
            ):
                return attr_value.get("THE-VALUE", default_id)

        return default_id

    def _extract_spec_object(
        self,
        spec_obj: ET.Element,
        namespaces: dict[str, str],
        spec_type_map: dict[str, str] | None = None,
        foreign_id_map: dict[str, str] | None = None,
        attr_def_map: dict[str, str] | None = None,
    ) -> RequirementData | None:
        """Extract a single spec object as an artifact"""
        try:
            artifact = {
                "id": spec_obj.get("IDENTIFIER", "UNKNOWN"),
                "text": "",
                "type": ArtifactType.UNKNOWN,
                "heading": "",
                "table": None,
            }

            # Determine object type and get type reference for foreign ID extraction
            spec_object_type_ref = None
            type_element = spec_obj.find(".//reqif:TYPE", namespaces)
            if type_element is not None:
                type_ref_element = type_element.find(".//reqif:SPEC-OBJECT-TYPE-REF", namespaces)
                if type_ref_element is not None and spec_type_map:
                    spec_object_type_ref = type_ref_element.text
                    type_name = spec_type_map.get(spec_object_type_ref, "")

                    # Map REQIF type names to our ArtifactType enum
                    artifact["type"] = self._map_reqif_type_to_artifact_type(type_name)

            # Extract VALUES container for both foreign ID and content extraction
            values_container = spec_obj.find("reqif:VALUES", namespaces)
            # Extract foreign ID if available - THIS IS THE KEY FIX
            if values_container is not None and foreign_id_map and spec_object_type_ref:
                target_foreign_id_ref = foreign_id_map.get(spec_object_type_ref)
                if target_foreign_id_ref:
                    foreign_id = self._extract_foreign_id(
                        values_container, target_foreign_id_ref, artifact["id"]
                    )
                    artifact["id"] = foreign_id  # Use foreign ID instead of internal ID

            # Extract attribute values
            values = spec_obj.findall(".//reqif:ATTRIBUTE-VALUE-XHTML", namespaces)

            for value in values:
                definition = value.find(".//reqif:DEFINITION", namespaces)
                if definition is not None:
                    # Extract attribute identifier from ATTRIBUTE-DEFINITION-XHTML-REF
                    attr_ref = definition.find(
                        ".//reqif:ATTRIBUTE-DEFINITION-XHTML-REF", namespaces
                    )
                    attr_identifier = attr_ref.text if attr_ref is not None else ""

                    # Resolve attribute name using the mapping
                    attr_name = (
                        attr_def_map.get(attr_identifier, attr_identifier)
                        if attr_def_map
                        else attr_identifier
                    )

                    # Extract XHTML content from THE-VALUE (handle any HTML element, not just div)
                    the_value = value.find(".//reqif:THE-VALUE", namespaces)
                    if the_value is not None:
                        # Look for any HTML element in THE-VALUE (p, div, span, etc.)
                        html_elements = the_value.findall(".//html:*", namespaces)
                        if html_elements:
                            content = self._extract_xhtml_content(the_value)

                            # Determine artifact content based on attribute reference
                            attr_name_lower = attr_name.lower()
                            if any(
                                keyword in attr_name_lower
                                for keyword in ["text", "info", "desc", "req", "content", "detail"]
                            ):
                                artifact["text"] = content
                                # If type is still unknown, try content-based classification as fallback
                                if artifact["type"] == ArtifactType.UNKNOWN:
                                    artifact["type"] = self._determine_artifact_type(content)
                            elif "heading" in attr_name_lower or "name" in attr_name_lower:
                                artifact["heading"] = content
                                if artifact["type"] == ArtifactType.UNKNOWN:
                                    artifact["type"] = ArtifactType.HEADING

            # Extract tables if present
            if "<table" in artifact["text"]:
                tables = self.html_parser.extract_tables_from_html(artifact["text"])
                if tables:
                    artifact["table"] = {"rows": len(tables), "data": tables}

            return artifact

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error extracting spec object: {e}")
            return None

    def _extract_xhtml_content(self, the_value_element: ET.Element) -> str:
        """
        Extract content from THE-VALUE element containing XHTML.

        Returns raw XHTML string to preserve image references (<object> tags)
        which are needed for vision model integration.
        """
        # Convert THE-VALUE element to string to preserve all tags including <object>
        # This is crucial for image linking in augment_artifacts_with_images()
        xhtml_string = ET.tostring(the_value_element, encoding="unicode", method="xml")

        # Return the raw XHTML content
        # The vision module will parse <object data="..."> tags to link images
        return xhtml_string

    def _map_reqif_type_to_artifact_type(self, reqif_type_name: str) -> ArtifactType:
        """Map REQIF SPEC-OBJECT-TYPE LONG-NAME to our ArtifactType enum"""
        type_name_lower = reqif_type_name.lower()

        # Direct mapping based on REQIF type names
        match type_name_lower:
            case name if "requirement" in name:
                return ArtifactType.SYSTEM_REQUIREMENT
            case name if "heading" in name:
                return ArtifactType.HEADING
            case name if "information" in name:
                return ArtifactType.INFORMATION
            case name if "design information" in name or "design" in name:
                return ArtifactType.DESIGN_INFORMATION
            case name if "application parameter" in name or "parameter" in name:
                return ArtifactType.APPLICATION_PARAMETER
            case name if "system interface" in name or "interface" in name:
                return ArtifactType.SYSTEM_INTERFACE
            case _:
                return ArtifactType.UNKNOWN

    def _determine_artifact_type(self, content: str) -> ArtifactType:
        """
        Determine artifact type based on content patterns.

        FIX: More lenient classification to match v03 behavior.
        If content has substance, default to SYSTEM_REQUIREMENT instead of UNKNOWN.
        """
        content_lower = content.lower()

        # Pattern matching for artifact classification (PEP 634)
        # Note: Order matters - more specific patterns should come first
        match True:
            case _ if any(keyword in content_lower for keyword in ["heading", "title", "section"]):
                return ArtifactType.HEADING
            case _ if any(
                keyword in content_lower
                for keyword in [
                    "requirement",
                    "shall",
                    "must",
                    "should",
                    "will",
                    "required",
                    "provides",
                    "ensures",
                    "controls",
                    "manages",
                    "performs",
                ]
            ):
                return ArtifactType.SYSTEM_REQUIREMENT
            case _ if any(
                keyword in content_lower for keyword in ["design", "architecture", "diagram", "ecu"]
            ):
                return ArtifactType.DESIGN_INFORMATION
            case _ if any(
                keyword in content_lower
                for keyword in [
                    "parameter",
                    "variable",
                    "setting",
                    "threshold",
                    "value",
                    "constant",
                ]
            ):
                return ArtifactType.APPLICATION_PARAMETER
            case _ if any(
                keyword in content_lower
                for keyword in ["interface", "input", "output", "signal", "boolean", "command"]
            ):
                return ArtifactType.SYSTEM_INTERFACE
            case _ if any(
                keyword in content_lower for keyword in ["information", "note", "description"]
            ):
                return ArtifactType.INFORMATION
            case _:
                # FIX: v03 compatibility - if content has substance (>50 chars), treat as requirement
                # This ensures we don't drop valid requirements due to conservative classification
                if len(content.strip()) > 50:
                    return ArtifactType.SYSTEM_REQUIREMENT
                return ArtifactType.UNKNOWN

    def classify_artifacts(self, artifacts: ArtifactList) -> dict[ArtifactType, ArtifactList]:
        """Classify artifacts by type"""
        classified: dict[ArtifactType, ArtifactList] = {}

        for artifact_type in ArtifactType:
            classified[artifact_type] = []

        for artifact in artifacts:
            artifact_type = artifact.get("type", ArtifactType.UNKNOWN)
            classified[artifact_type].append(artifact)

        return classified

    def parse_and_augment_relationships(
        self,
        reqifz_file_path: Path,
        artifacts: ArtifactList,
        augment_requirements: bool = True,
        build_dependency_graph: bool = False,
    ) -> tuple[ArtifactList, dict[str, Any]]:
        """
        Parse SPEC-RELATION elements and augment artifacts with relationship metadata.

        Args:
            reqifz_file_path: Path to the REQIFZ file
            artifacts: List of artifacts to augment
            augment_requirements: Whether to augment requirements with parent/child metadata
            build_dependency_graph: Whether to build dependency graph

        Returns:
            Tuple of (augmented_artifacts, relationship_info)
            - augmented_artifacts: Artifacts with relationship metadata
            - relationship_info: Dict with relationships, parent_child_map, and optionally dependency_graph
        """
        try:
            with zipfile.ZipFile(reqifz_file_path, "r") as zip_file:
                reqif_files = [f for f in zip_file.namelist() if f.endswith(".reqif")]

                if not reqif_files:
                    if self.logger:
                        self.logger.warning(f"No .reqif files found in {reqifz_file_path}")
                    return artifacts, {"relationships": [], "parent_child_map": {}}

                # Parse REQIF XML
                reqif_content = zip_file.read(reqif_files[0])
                root = ET.fromstring(reqif_content)

                # REQIF namespaces
                namespaces = {
                    "reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd",
                    "html": "http://www.w3.org/1999/xhtml",
                }

                # Build mapping from internal SPEC-OBJECT identifiers to foreign IDs
                spec_obj_to_foreign_id = {}
                spec_objects = root.findall(".//reqif:SPEC-OBJECT", namespaces)
                for spec_obj in spec_objects:
                    internal_id = spec_obj.get("IDENTIFIER")
                    # Look for foreign ID in VALUES
                    values_container = spec_obj.find("reqif:VALUES", namespaces)
                    if values_container is not None:
                        for attr_value in values_container.findall(
                            "reqif:ATTRIBUTE-VALUE-STRING", namespaces
                        ):
                            definition_ref_node = attr_value.find(
                                "reqif:DEFINITION/reqif:ATTRIBUTE-DEFINITION-STRING-REF", namespaces
                            )
                            if definition_ref_node is not None:
                                attr_def_id = definition_ref_node.text
                                # Check if this is a ReqIF.ForeignID attribute
                                attr_def = root.find(
                                    f".//reqif:ATTRIBUTE-DEFINITION-STRING[@IDENTIFIER='{attr_def_id}']",
                                    namespaces,
                                )
                                if (
                                    attr_def is not None
                                    and attr_def.get("LONG-NAME") == "ReqIF.ForeignID"
                                ):
                                    foreign_id = attr_value.get("THE-VALUE")
                                    if foreign_id:
                                        spec_obj_to_foreign_id[internal_id] = foreign_id
                                        break

                # Create relationship parser
                relationship_parser = RequirementRelationshipParser(logger=self.logger)

                # Parse relationships
                relationships, parent_child_map = relationship_parser.parse_relationships(
                    root, namespaces, spec_obj_to_foreign_id
                )

                relationship_info = {
                    "relationships": relationships,
                    "parent_child_map": parent_child_map,
                }

                # Augment requirements with relationship metadata
                if augment_requirements:
                    artifacts = relationship_parser.augment_requirements_with_relationships(
                        artifacts, parent_child_map
                    )

                # Build dependency graph if requested
                if build_dependency_graph and relationships:
                    dependency_graph = relationship_parser.build_dependency_graph(relationships)
                    relationship_info["dependency_graph"] = dependency_graph

                return artifacts, relationship_info

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error parsing relationships from {reqifz_file_path}: {e}")
            return artifacts, {"relationships": [], "parent_child_map": {}}


class HighPerformanceREQIFArtifactExtractor(REQIFArtifactExtractor):
    """Extractor used by the HP pipeline.

    Historically this class parallelized XML parsing with a ThreadPoolExecutor,
    but ElementTree traversal is pure-Python and GIL-bound, so the threads
    serialized anyway and only added overhead. Extraction is now identical to
    the base class; the HP pipeline's real parallelism is the async Ollama
    calls across requirements.
    """

    def __init__(self, logger=None, max_workers: int = 4, config: ConfigManager | None = None):
        super().__init__(logger, use_streaming=False, config=config)
        # Retained for interface compatibility; no longer used for threading
        self.max_workers = max_workers
