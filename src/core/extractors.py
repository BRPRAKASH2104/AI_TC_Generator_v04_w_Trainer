"""
REQIF artifact extractors for the AI Test Case Generator.

This module provides classes for extracting and processing artifacts from REQIFZ files,
with support for different artifact types commonly found in automotive requirements.
"""


import io
import xml.etree.ElementTree as ET
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import StrEnum
from pathlib import Path
from typing import Any

from core.parsers import HTMLTableParser

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

    __slots__ = ("logger", "html_parser", "use_streaming")

    def __init__(self, logger=None, use_streaming: bool = False):
        self.logger = logger
        self.html_parser = HTMLTableParser()
        self.use_streaming = use_streaming

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
                return self._parse_reqif_xml(reqif_content)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error extracting REQIFZ file {reqifz_file_path}: {e}")
            return []

    def _parse_reqif_xml(self, xml_content: bytes) -> ArtifactList:
        """Parse REQIF XML content and extract artifacts"""
        try:
            # Use streaming if enabled
            if self.use_streaming:
                return self._parse_reqif_xml_streaming(xml_content)

            # Traditional DOM-based parsing
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
                artifact = self._extract_spec_object(spec_obj, namespaces, spec_type_map, foreign_id_map, attr_def_map)
                if artifact:
                    artifacts.append(artifact)

            if self.logger:
                self.logger.info(f"Extracted {len(artifacts)} artifacts from REQIF")

            return artifacts

        except ET.ParseError as e:
            if self.logger:
                self.logger.error(f"XML parsing error: {e}")
            return []

    def _build_spec_type_mapping(self, root: ET.Element, namespaces: dict[str, str]) -> dict[str, str]:
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

    def _build_foreign_id_mapping(self, root: ET.Element, namespaces: dict[str, str]) -> dict[str, str]:
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

    def _build_attribute_definition_mapping(self, root: ET.Element, namespaces: dict[str, str]) -> dict[str, str]:
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

    def _extract_foreign_id(self, values_container, target_foreign_id_ref: str, default_id: str) -> str:
        """Extract foreign ID from VALUES container"""
        if not target_foreign_id_ref:
            return default_id

        for attr_value in values_container.findall("reqif:ATTRIBUTE-VALUE-STRING", {"reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd"}):
            definition_ref_node = attr_value.find(
                "reqif:DEFINITION/reqif:ATTRIBUTE-DEFINITION-STRING-REF",
                {"reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd"}
            )
            if (definition_ref_node is not None and
                definition_ref_node.text == target_foreign_id_ref):
                return attr_value.get("THE-VALUE", default_id)

        return default_id

    def _extract_spec_object(self, spec_obj: ET.Element, namespaces: dict[str, str], spec_type_map: dict[str, str] = None, foreign_id_map: dict[str, str] = None, attr_def_map: dict[str, str] = None) -> RequirementData | None:
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
            if values_container is not None:
                # Extract foreign ID if available - THIS IS THE KEY FIX
                if foreign_id_map and spec_object_type_ref:
                    target_foreign_id_ref = foreign_id_map.get(spec_object_type_ref)
                    if target_foreign_id_ref:
                        foreign_id = self._extract_foreign_id(values_container, target_foreign_id_ref, artifact["id"])
                        artifact["id"] = foreign_id  # Use foreign ID instead of internal ID

            # Extract attribute values
            values = spec_obj.findall(".//reqif:ATTRIBUTE-VALUE-XHTML", namespaces)

            for value in values:
                definition = value.find(".//reqif:DEFINITION", namespaces)
                if definition is not None:
                    # Extract attribute identifier from ATTRIBUTE-DEFINITION-XHTML-REF
                    attr_ref = definition.find(".//reqif:ATTRIBUTE-DEFINITION-XHTML-REF", namespaces)
                    attr_identifier = attr_ref.text if attr_ref is not None else ""

                    # Resolve attribute name using the mapping
                    attr_name = attr_def_map.get(attr_identifier, attr_identifier) if attr_def_map else attr_identifier

                    # Extract XHTML content from THE-VALUE (handle any HTML element, not just div)
                    the_value = value.find(".//reqif:THE-VALUE", namespaces)
                    if the_value is not None:
                        # Look for any HTML element in THE-VALUE (p, div, span, etc.)
                        html_elements = the_value.findall(".//html:*", namespaces)
                        if html_elements:
                            content = self._extract_xhtml_content(the_value)

                            # Determine artifact content based on attribute reference
                            if "text" in attr_name.lower() or "info" in attr_name.lower():
                                artifact["text"] = content
                                # If type is still unknown, try content-based classification as fallback
                                if artifact["type"] == ArtifactType.UNKNOWN:
                                    artifact["type"] = self._determine_artifact_type(content)
                            elif "heading" in attr_name.lower() or "name" in attr_name.lower():
                                artifact["heading"] = content
                                if artifact["type"] == ArtifactType.UNKNOWN:
                                    artifact["type"] = ArtifactType.HEADING

            # Extract tables if present
            if "<table" in artifact["text"]:
                tables = self.html_parser.extract_tables_from_html(artifact["text"])
                if tables:
                    artifact["table"] = {
                        "rows": len(tables),
                        "data": tables
                    }

            return artifact

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error extracting spec object: {e}")
            return None

    def _extract_xhtml_content(self, the_value_element: ET.Element) -> str:
        """Extract text content from THE-VALUE element containing XHTML"""
        # Find all HTML elements within THE-VALUE
        html_elements = the_value_element.findall(".//html:*", {"html": "http://www.w3.org/1999/xhtml"})

        if not html_elements:
            # Fallback to extracting all text content
            return "".join(the_value_element.itertext()).strip()

        # Extract content from HTML elements
        content_parts = []
        for html_elem in html_elements:
            # Get text content while preserving some structure
            elem_text = "".join(html_elem.itertext()).strip()
            if elem_text:
                content_parts.append(elem_text)

        # Join all content parts
        content = " ".join(content_parts)

        # Clean up extra whitespace
        content = " ".join(content.split())

        return content

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
            case _ if any(keyword in content_lower for keyword in [
                "requirement", "shall", "must", "should", "will", "required",
                "provides", "ensures", "controls", "manages", "performs"
            ]):
                return ArtifactType.SYSTEM_REQUIREMENT
            case _ if any(keyword in content_lower for keyword in ["design", "architecture", "diagram", "ecu"]):
                return ArtifactType.DESIGN_INFORMATION
            case _ if any(keyword in content_lower for keyword in [
                "parameter", "variable", "setting", "threshold", "value", "constant"
            ]):
                return ArtifactType.APPLICATION_PARAMETER
            case _ if any(keyword in content_lower for keyword in [
                "interface", "input", "output", "signal", "boolean", "command"
            ]):
                return ArtifactType.SYSTEM_INTERFACE
            case _ if any(keyword in content_lower for keyword in ["information", "note", "description"]):
                return ArtifactType.INFORMATION
            case _:
                # FIX: v03 compatibility - if content has substance (>50 chars), treat as requirement
                # This ensures we don't drop valid requirements due to conservative classification
                if len(content.strip()) > 50:
                    return ArtifactType.SYSTEM_REQUIREMENT
                return ArtifactType.UNKNOWN

    def _parse_reqif_xml_streaming(self, xml_content: bytes) -> ArtifactList:
        """
        Parse REQIF XML content using streaming parsing to reduce memory usage.

        This method uses iterparse() to process XML elements as they are encountered,
        rather than loading the entire DOM into memory. This provides significant
        memory savings for large REQIF files.

        Strategy:
        1. First pass: Build type mappings using streaming
        2. Second pass: Process spec objects using streaming
        """
        try:
            # REQIF namespaces
            namespaces = {
                "reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd",
                "html": "http://www.w3.org/1999/xhtml",
            }

            # Pass 1: Build mappings using streaming
            spec_type_map, foreign_id_map = self._build_mappings_streaming(xml_content, namespaces)

            # Pass 2: Extract spec objects using streaming
            artifacts = self._extract_spec_objects_streaming(xml_content, namespaces, spec_type_map, foreign_id_map)

            if self.logger:
                self.logger.info(f"Extracted {len(artifacts)} artifacts from REQIF using streaming parsing")

            return artifacts

        except ET.ParseError as e:
            if self.logger:
                self.logger.error(f"Streaming XML parsing error: {e}")
            return []

    def _build_mappings_streaming(self, xml_content: bytes, namespaces: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
        """Build type mappings using streaming XML parsing."""
        spec_type_map = {}
        foreign_id_map = {}

        try:
            # Build SPEC-OBJECT-TYPE mapping
            for _, elem in ET.iterparse(io.BytesIO(xml_content), events=('end',)):
                if elem.tag.endswith('}SPEC-OBJECT-TYPE'):
                    type_id = elem.get("IDENTIFIER")
                    long_name = elem.get("LONG-NAME")

                    if type_id and long_name:
                        spec_type_map[type_id] = long_name

                    # Check for ReqIF.ForeignID attribute definition
                    for attr_def in elem.findall(".//reqif:ATTRIBUTE-DEFINITION-STRING[@LONG-NAME='ReqIF.ForeignID']", namespaces):
                        foreign_id = attr_def.get("IDENTIFIER")
                        if foreign_id:
                            foreign_id_map[type_id] = foreign_id

                # Clear element to save memory
                elem.clear()
                while elem.getprevious() is not None:
                    del elem.getparent()[0]

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error in streaming mapping build: {e}")
            # Fall back to empty mappings

        if self.logger:
            self.logger.debug(f"Built mappings via streaming: {len(spec_type_map)} types, {len(foreign_id_map)} foreign IDs")

        return spec_type_map, foreign_id_map

    def _extract_spec_objects_streaming(self, xml_content: bytes, namespaces: dict[str, str],
                                        spec_type_map: dict[str, str], foreign_id_map: dict[str, str]) -> ArtifactList:
        """Extract spec objects using streaming XML parsing."""
        artifacts = []

        try:
            for _, elem in ET.iterparse(io.BytesIO(xml_content), events=('end',)):
                if elem.tag.endswith('}SPEC-OBJECT'):
                    # Extract this spec object
                    artifact = self._extract_spec_object(elem, namespaces, spec_type_map, foreign_id_map)
                    if artifact:
                        artifacts.append(artifact)

                # Clear element to save memory (important for streaming)
                elem.clear()
                while elem.getprevious() is not None:
                    del elem.getparent()[0]

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error in streaming spec object extraction: {e}")

        return artifacts

    def classify_artifacts(self, artifacts: ArtifactList) -> dict[ArtifactType, ArtifactList]:
        """Classify artifacts by type"""
        classified = {}

        for artifact_type in ArtifactType:
            classified[artifact_type] = []

        for artifact in artifacts:
            artifact_type = artifact.get("type", ArtifactType.UNKNOWN)
            classified[artifact_type].append(artifact)

        return classified


class HighPerformanceREQIFArtifactExtractor(REQIFArtifactExtractor):
    """
    High-performance version with concurrent XML processing using ThreadPoolExecutor.

    This class provides significant performance improvements for large REQIF files by:
    - Processing spec objects concurrently in batches
    - Parallelizing attribute extraction and processing
    - Using thread-safe XML parsing operations
    - Implementing intelligent fallback to sequential processing when needed
    """

    def __init__(self, logger=None, max_workers: int = 4):
        super().__init__(logger)
        self.max_workers = max_workers

    def extract_reqifz_content(self, reqifz_file_path: Path) -> ArtifactList:
        """
        Enhanced extraction with parallel XML processing for large REQIF files.

        Uses ThreadPoolExecutor to process multiple spec objects concurrently,
        providing significant performance improvement for large files.
        """
        try:
            with zipfile.ZipFile(reqifz_file_path, "r") as zip_file:
                reqif_files = [f for f in zip_file.namelist() if f.endswith(".reqif")]

                if not reqif_files:
                    if self.logger:
                        self.logger.warning(f"No .reqif files found in {reqifz_file_path}")
                    return []

                # Process the first REQIF file found with enhanced parallel processing
                reqif_content = zip_file.read(reqif_files[0])
                return self._parse_reqif_xml_parallel(reqif_content)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error extracting REQIFZ file {reqifz_file_path}: {e}")
            return []

    def _parse_reqif_xml_parallel(self, xml_content: bytes) -> ArtifactList:
        """
        Parse REQIF XML content using parallel processing for spec objects.

        This method splits the XML parsing into concurrent tasks:
        1. Parse the XML structure (single-threaded)
        2. Extract spec objects concurrently (multi-threaded)
        3. Process artifact attributes in parallel (multi-threaded)
        """
        try:
            # Step 1: Parse XML structure (must be single-threaded)
            root = ET.fromstring(xml_content)

            # REQIF namespaces
            namespaces = {
                "reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd",
                "html": "http://www.w3.org/1999/xhtml",
            }

            # Build SPEC-OBJECT-TYPE mapping and foreign ID mapping
            spec_type_map = self._build_spec_type_mapping(root, namespaces)
            foreign_id_map = self._build_foreign_id_mapping(root, namespaces)

            # Step 2: Find all spec objects
            spec_objects = root.findall(".//reqif:SPEC-OBJECT", namespaces)

            if not spec_objects:
                if self.logger:
                    self.logger.warning("No SPEC-OBJECT elements found in REQIF")
                return []

            if self.logger:
                self.logger.debug(f"Found {len(spec_objects)} spec objects, processing with {self.max_workers} workers")

            # Step 3: Process spec objects concurrently
            artifacts = []

            # For small numbers of spec objects, use sequential processing to avoid overhead
            if len(spec_objects) < 10:
                for spec_obj in spec_objects:
                    artifact = self._extract_spec_object(spec_obj, namespaces, spec_type_map, foreign_id_map)
                    if artifact:
                        artifacts.append(artifact)
            else:
                # Use ThreadPoolExecutor for concurrent processing of spec objects
                artifacts = self._process_spec_objects_concurrent(spec_objects, namespaces, spec_type_map, foreign_id_map)

            if self.logger:
                self.logger.info(f"Extracted {len(artifacts)} artifacts from REQIF using parallel processing")

            return artifacts

        except ET.ParseError as e:
            if self.logger:
                self.logger.error(f"XML parsing error: {e}")
            return []
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in parallel XML parsing: {e}")
            # Fallback to sequential processing if parallel processing fails
            return super()._parse_reqif_xml(xml_content)

    def _process_spec_objects_concurrent(self, spec_objects, namespaces, spec_type_map: dict[str, str] = None, foreign_id_map: dict[str, str] = None) -> ArtifactList:
        """
        Process spec objects concurrently using ThreadPoolExecutor.

        Args:
            spec_objects: List of spec object XML elements
            namespaces: XML namespaces for parsing
            spec_type_map: Mapping of SPEC-OBJECT-TYPE IDs to names

        Returns:
            List of extracted artifacts
        """
        artifacts = []

        # Create batches of spec objects for more efficient processing
        batch_size = max(1, len(spec_objects) // self.max_workers)
        batches = [spec_objects[i:i + batch_size] for i in range(0, len(spec_objects), batch_size)]

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit batch processing tasks
            future_to_batch = {
                executor.submit(self._process_spec_object_batch, batch, namespaces, spec_type_map, foreign_id_map): batch_idx
                for batch_idx, batch in enumerate(batches)
            }

            # Collect results as they complete
            for future in as_completed(future_to_batch):
                batch_idx = future_to_batch[future]
                try:
                    batch_artifacts = future.result()
                    artifacts.extend(batch_artifacts)

                    if self.logger:
                        self.logger.debug(f"Completed batch {batch_idx + 1}/{len(batches)}, "
                                        f"extracted {len(batch_artifacts)} artifacts")

                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Error processing batch {batch_idx}: {e}")

                    # Fallback: process this batch sequentially
                    try:
                        batch = batches[batch_idx]
                        for spec_obj in batch:
                            artifact = self._extract_spec_object(spec_obj, namespaces, spec_type_map, foreign_id_map)
                            if artifact:
                                artifacts.append(artifact)
                    except Exception as fallback_e:
                        if self.logger:
                            self.logger.error(f"Fallback processing also failed for batch {batch_idx}: {fallback_e}")

        return artifacts

    def _process_spec_object_batch(self, spec_objects_batch, namespaces, spec_type_map: dict[str, str] = None, foreign_id_map: dict[str, str] = None) -> ArtifactList:
        """
        Process a batch of spec objects sequentially within a single thread.

        Args:
            spec_objects_batch: Batch of spec object XML elements
            namespaces: XML namespaces for parsing
            spec_type_map: Mapping of SPEC-OBJECT-TYPE IDs to names

        Returns:
            List of extracted artifacts from this batch
        """
        batch_artifacts = []

        for spec_obj in spec_objects_batch:
            try:
                artifact = self._extract_spec_object(spec_obj, namespaces, spec_type_map, foreign_id_map)
                if artifact:
                    batch_artifacts.append(artifact)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Error processing individual spec object: {e}")
                continue

        return batch_artifacts
