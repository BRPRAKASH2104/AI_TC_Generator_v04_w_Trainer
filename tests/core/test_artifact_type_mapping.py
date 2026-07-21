"""Regression tests for REQIF SPEC-OBJECT-TYPE -> ArtifactType mapping.

Guards review 2026-07-20 finding 10: the generic ``"information"`` branch in
``_map_reqif_type_to_artifact_type`` was ordered before ``"design information"``,
and since ``"design information"`` contains ``"information"`` the generic branch
shadowed it — so every ``Design Information`` artifact was misclassified as
generic ``INFORMATION`` and ``DESIGN_INFORMATION`` was effectively dead. The
``"design"`` test must precede the generic ``"information"`` test.
"""

from src.core.extractors import ArtifactType, REQIFArtifactExtractor


class TestReqifTypeMapping:
    """SPEC-OBJECT-TYPE LONG-NAME classification precedence."""

    def setup_method(self) -> None:
        self.extractor = REQIFArtifactExtractor()

    def test_design_information_maps_to_design_information(self) -> None:
        """The exact regression: 'Design Information' must not become INFORMATION."""
        assert (
            self.extractor._map_reqif_type_to_artifact_type("Design Information")
            == ArtifactType.DESIGN_INFORMATION
        )

    def test_plain_information_maps_to_information(self) -> None:
        assert (
            self.extractor._map_reqif_type_to_artifact_type("Information")
            == ArtifactType.INFORMATION
        )

    def test_design_only_maps_to_design_information(self) -> None:
        assert (
            self.extractor._map_reqif_type_to_artifact_type("Architectural Design")
            == ArtifactType.DESIGN_INFORMATION
        )

    def test_requirement_precedence_over_design(self) -> None:
        """'requirement' is matched first, so a 'Design Requirement' stays a requirement."""
        assert (
            self.extractor._map_reqif_type_to_artifact_type("Design Requirement")
            == ArtifactType.SYSTEM_REQUIREMENT
        )

    def test_heading_precedence(self) -> None:
        assert (
            self.extractor._map_reqif_type_to_artifact_type("Chapter Heading")
            == ArtifactType.HEADING
        )
