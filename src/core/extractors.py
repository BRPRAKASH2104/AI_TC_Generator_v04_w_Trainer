"""
REQIF artifact extractors for the AI Test Case Generator.

This module provides classes for extracting and processing artifacts from REQIFZ files,
with support for different artifact types commonly found in automotive requirements.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from enum import StrEnum
from pathlib import Path
from typing import Any, NotRequired, TypedDict

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
                    attr_name = definition.get("LONG-NAME", "")
                    
                    # Extract XHTML content
                    xhtml_div = value.find(".//reqif:THE-VALUE/html:div", namespaces)
                    if xhtml_div is not None:
                        content = self._extract_xhtml_content(xhtml_div)
                        
                        # Determine artifact type and content
                        if "ReqIF.Text" in attr_name or "Description" in attr_name:
                            artifact["text"] = content
                            artifact["type"] = self._determine_artifact_type(content)
                        elif "Name" in attr_name or "Heading" in attr_name:
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

    def _extract_xhtml_content(self, xhtml_element: ET.Element) -> str:
        """Extract text content from XHTML element"""
        # Convert element back to string to preserve HTML structure
        content = ET.tostring(xhtml_element, encoding="unicode", method="html")
        
        # Clean up namespace references
        content = content.replace(' xmlns:html="http://www.w3.org/1999/xhtml"', '')
        content = content.replace('html:', '')
        
        return content

    def _determine_artifact_type(self, content: str) -> ArtifactType:
        """Determine artifact type based on content patterns"""
        content_lower = content.lower()
        
        # Pattern matching for artifact classification (PEP 634)
        match True:
            case _ if any(keyword in content_lower for keyword in ["heading", "title", "section"]):
                return ArtifactType.HEADING
            case _ if any(keyword in content_lower for keyword in ["information", "note", "description"]):
                return ArtifactType.INFORMATION
            case _ if any(keyword in content_lower for keyword in ["design", "architecture", "diagram"]):
                return ArtifactType.DESIGN_INFORMATION
            case _ if any(keyword in content_lower for keyword in ["parameter", "variable", "setting"]):
                return ArtifactType.APPLICATION_PARAMETER
            case _ if any(keyword in content_lower for keyword in ["interface", "input", "output", "signal"]):
                return ArtifactType.SYSTEM_INTERFACE
            case _ if any(keyword in content_lower for keyword in ["requirement", "shall", "must", "should"]):
                return ArtifactType.SYSTEM_REQUIREMENT
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
    """High-performance version with optimizations for large files"""

    def __init__(self, logger=None, max_workers: int = 4):
        super().__init__(logger)
        self.max_workers = max_workers

    def extract_reqifz_content(self, reqifz_file_path: Path) -> ArtifactList:
        """Optimized extraction with parallel processing capabilities"""
        # For now, use the base implementation
        # Could be enhanced with concurrent.futures for parallel XML processing
        return super().extract_reqifz_content(reqifz_file_path)