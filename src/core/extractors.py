"""
REQIF artifact extractors for the AI Test Case Generator.

This module provides classes for extracting and processing artifacts from REQIFZ files,
with support for different artifact types commonly found in automotive requirements.
"""

from __future__ import annotations

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

    __slots__ = ("logger", "html_parser")

    def __init__(self, logger=None):
        self.logger = logger
        self.html_parser = HTMLTableParser()

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
            root = ET.fromstring(xml_content)
            
            # REQIF namespaces
            namespaces = {
                "reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd",
                "html": "http://www.w3.org/1999/xhtml",
            }
            
            artifacts = []
            
            # Find all spec objects (artifacts)
            spec_objects = root.findall(".//reqif:SPEC-OBJECT", namespaces)
            
            for spec_obj in spec_objects:
                artifact = self._extract_spec_object(spec_obj, namespaces)
                if artifact:
                    artifacts.append(artifact)
            
            if self.logger:
                self.logger.info(f"Extracted {len(artifacts)} artifacts from REQIF")
                
            return artifacts

        except ET.ParseError as e:
            if self.logger:
                self.logger.error(f"XML parsing error: {e}")
            return []

    def _extract_spec_object(self, spec_obj: ET.Element, namespaces: dict[str, str]) -> RequirementData | None:
        """Extract a single spec object as an artifact"""
        try:
            artifact = {
                "id": spec_obj.get("IDENTIFIER", "UNKNOWN"),
                "text": "",
                "type": ArtifactType.UNKNOWN,
                "heading": "",
                "table": None,
            }

            # Extract attribute values
            values = spec_obj.findall(".//reqif:ATTRIBUTE-VALUE-XHTML", namespaces)

            for value in values:
                definition = value.find(".//reqif:DEFINITION", namespaces)
                if definition is not None:
                    # Extract attribute name from ATTRIBUTE-DEFINITION-XHTML-REF
                    attr_ref = definition.find(".//reqif:ATTRIBUTE-DEFINITION-XHTML-REF", namespaces)
                    attr_name = attr_ref.text if attr_ref is not None else ""

                    # Extract XHTML content from THE-VALUE (handle any HTML element, not just div)
                    the_value = value.find(".//reqif:THE-VALUE", namespaces)
                    if the_value is not None:
                        # Look for any HTML element in THE-VALUE (p, div, span, etc.)
                        html_elements = the_value.findall(".//html:*", namespaces)
                        if html_elements:
                            content = self._extract_xhtml_content(the_value)

                            # Determine artifact type and content based on attribute reference
                            if "text" in attr_name.lower() or "info" in attr_name.lower():
                                artifact["text"] = content
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

    def _determine_artifact_type(self, content: str) -> ArtifactType:
        """Determine artifact type based on content patterns"""
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
                return ArtifactType.UNKNOWN

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
                    artifact = self._extract_spec_object(spec_obj, namespaces)
                    if artifact:
                        artifacts.append(artifact)
            else:
                # Use ThreadPoolExecutor for concurrent processing of spec objects
                artifacts = self._process_spec_objects_concurrent(spec_objects, namespaces)

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

    def _process_spec_objects_concurrent(self, spec_objects, namespaces) -> ArtifactList:
        """
        Process spec objects concurrently using ThreadPoolExecutor.

        Args:
            spec_objects: List of spec object XML elements
            namespaces: XML namespaces for parsing

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
                executor.submit(self._process_spec_object_batch, batch, namespaces): batch_idx
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
                            artifact = self._extract_spec_object(spec_obj, namespaces)
                            if artifact:
                                artifacts.append(artifact)
                    except Exception as fallback_e:
                        if self.logger:
                            self.logger.error(f"Fallback processing also failed for batch {batch_idx}: {fallback_e}")

        return artifacts

    def _process_spec_object_batch(self, spec_objects_batch, namespaces) -> ArtifactList:
        """
        Process a batch of spec objects sequentially within a single thread.

        Args:
            spec_objects_batch: Batch of spec object XML elements
            namespaces: XML namespaces for parsing

        Returns:
            List of extracted artifacts from this batch
        """
        batch_artifacts = []

        for spec_obj in spec_objects_batch:
            try:
                artifact = self._extract_spec_object(spec_obj, namespaces)
                if artifact:
                    batch_artifacts.append(artifact)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Error processing individual spec object: {e}")
                continue

        return batch_artifacts