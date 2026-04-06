"""
Comprehensive tests for BaseProcessor - the foundation of all processing workflows.

Tests the critical context-aware processing logic that enriches requirements
with heading, information, and interface context.
"""

from pathlib import Path
from unittest.mock import Mock, patch

from src.config import ConfigManager
from src.processors.base_processor import BaseProcessor
from tests.helpers import (
    create_test_heading,
    create_test_information,
    create_test_requirement,
)


class TestBaseProcessorInitialization:
    """Test BaseProcessor initialization and configuration"""

    def test_default_initialization(self):
        """Processor initializes with default config when none provided"""
        processor = BaseProcessor()

        assert processor.config is not None
        assert isinstance(processor.config, ConfigManager)
        assert processor.logger is None  # Not initialized until file processing
        assert processor.extractor is None
        assert processor.generator is None
        assert processor.formatter is None

    def test_initialization_with_custom_config(self):
        """Processor accepts custom configuration"""
        config = ConfigManager()
        processor = BaseProcessor(config=config)

        assert processor.config is config

    def test_initialization_with_dependency_injection(self):
        """Processor accepts injected dependencies (extractor, generator, formatter)"""
        mock_extractor = Mock()
        mock_generator = Mock()
        mock_formatter = Mock()

        processor = BaseProcessor(
            extractor=mock_extractor, generator=mock_generator, formatter=mock_formatter
        )

        assert processor.extractor is mock_extractor
        assert processor.generator is mock_generator
        assert processor.formatter is mock_formatter

    def test_raft_collector_initialized_when_enabled(self):
        """RAFT collector is initialized when training.enable_raft is True"""
        config = ConfigManager()
        config.training.enable_raft = True

        with patch("src.processors.base_processor.RAFTDataCollector") as mock_raft:
            processor = BaseProcessor(config=config)
            mock_raft.assert_called_once()
            assert processor.raft_collector is not None

    def test_raft_collector_not_initialized_when_disabled(self):
        """RAFT collector is None when training.enable_raft is False"""
        config = ConfigManager()
        config.training.enable_raft = False

        processor = BaseProcessor(config=config)
        assert processor.raft_collector is None


class TestLoggerInitialization:
    """Test file-specific logger initialization"""

    def test_initialize_logger_creates_logger(self):
        """_initialize_logger creates FileProcessingLogger for specific file"""
        processor = BaseProcessor()
        reqifz_path = Path("/fake/path/test.reqifz")

        with patch("src.processors.base_processor.FileProcessingLogger") as mock_logger:
            processor._initialize_logger(reqifz_path)

            mock_logger.assert_called_once_with(
                reqifz_file="test.reqifz", input_path=str(Path("/fake/path"))
            )
            assert processor.logger is not None

    def test_initialize_logger_updates_raft_collector(self):
        """Logger is propagated to RAFT collector when enabled"""
        config = ConfigManager()
        config.training.enable_raft = True

        with patch("src.processors.base_processor.RAFTDataCollector"):
            processor = BaseProcessor(config=config)
            processor.raft_collector = Mock()

            reqifz_path = Path("/fake/path/test.reqifz")

            with patch("src.processors.base_processor.FileProcessingLogger") as mock_logger:
                mock_logger_instance = Mock()
                mock_logger.return_value = mock_logger_instance

                processor._initialize_logger(reqifz_path)

                # Logger should be propagated to RAFT collector
                assert processor.raft_collector.logger == mock_logger_instance


class TestArtifactExtraction:
    """Test artifact extraction from REQIFZ files"""

    def test_extract_artifacts_success(self):
        """Successfully extracts artifacts from REQIFZ file"""
        processor = BaseProcessor()
        processor.logger = Mock()
        processor.extractor = Mock()

        fake_artifacts = [
            create_test_heading("Test Section", heading_id="H_001"),
            create_test_requirement("Test requirement", requirement_id="REQ_001"),
        ]
        processor.extractor.extract_reqifz_content.return_value = fake_artifacts

        reqifz_path = Path("/fake/path/test.reqifz")
        result = processor._extract_artifacts(reqifz_path)

        assert result == fake_artifacts
        processor.extractor.extract_reqifz_content.assert_called_once_with(reqifz_path)
        processor.logger.info.assert_called_once()

    def test_extract_artifacts_returns_none_when_empty(self):
        """Returns None when no artifacts found"""
        processor = BaseProcessor()
        processor.logger = Mock()
        processor.extractor = Mock()
        processor.extractor.extract_reqifz_content.return_value = []

        reqifz_path = Path("/fake/path/empty.reqifz")
        result = processor._extract_artifacts(reqifz_path)

        assert result is None
        processor.logger.error.assert_called_once_with("No artifacts found in REQIFZ file")

    def test_extract_artifacts_returns_none_when_none(self):
        """Returns None when extractor returns None"""
        processor = BaseProcessor()
        processor.logger = Mock()
        processor.extractor = Mock()
        processor.extractor.extract_reqifz_content.return_value = None

        reqifz_path = Path("/fake/path/invalid.reqifz")
        result = processor._extract_artifacts(reqifz_path)

        assert result is None


class TestContextAwareProcessing:
    """
    CRITICAL TESTS: Context-aware requirement augmentation.

    This is the heart of the system - DO NOT BREAK THIS LOGIC.
    """

    def test_build_augmented_requirements_basic_flow(self):
        """Requirements are augmented with heading, info, and interface context"""
        processor = BaseProcessor()
        processor.logger = Mock()
        processor.extractor = Mock()

        # Mock classify_artifacts to return system interfaces
        processor.extractor.classify_artifacts.return_value = {
            "System Interface": [
                {"id": "IF_001", "name": "CAN Bus"},
                {"id": "IF_002", "name": "LIN Bus"},
            ]
        }

        artifacts = [
            create_test_heading("Door Control System", heading_id="H_001"),
            create_test_information("This section covers door operations", info_id="INFO_001"),
            create_test_requirement(
                "Door shall lock when vehicle speed > 10 km/h",
                requirement_id="REQ_001",
            ),
        ]

        augmented_reqs, interface_count = processor._build_augmented_requirements(artifacts)

        assert len(augmented_reqs) == 1
        assert interface_count == 2

        req = augmented_reqs[0]
        assert req["id"] == "REQ_001"
        assert "Door Control System" in req["heading"]
        assert len(req["info_list"]) == 1
        assert "This section covers door operations" in req["info_list"][0]["text"]
        assert len(req["interface_list"]) == 2

    def test_build_augmented_requirements_resets_info_after_requirement(self):
        """Information context resets after each requirement (critical!)"""
        processor = BaseProcessor()
        processor.logger = Mock()
        processor.extractor = Mock()
        processor.extractor.classify_artifacts.return_value = {"System Interface": []}

        artifacts = [
            create_test_heading("Section 1", heading_id="H_001"),
            create_test_information("Info for REQ_001", info_id="INFO_001"),
            create_test_requirement("First requirement", requirement_id="REQ_001"),
            create_test_information("Info for REQ_002", info_id="INFO_002"),
            create_test_requirement("Second requirement", requirement_id="REQ_002"),
        ]

        augmented_reqs, _ = processor._build_augmented_requirements(artifacts)

        assert len(augmented_reqs) == 2

        # REQ_001 should have first info
        assert len(augmented_reqs[0]["info_list"]) == 1
        assert "Info for REQ_001" in augmented_reqs[0]["info_list"][0]["text"]

        # REQ_002 should have second info (not both!)
        assert len(augmented_reqs[1]["info_list"]) == 1
        assert "Info for REQ_002" in augmented_reqs[1]["info_list"][0]["text"]

    def test_build_augmented_requirements_new_heading_resets_info(self):
        """New heading resets information context"""
        processor = BaseProcessor()
        processor.logger = Mock()
        processor.extractor = Mock()
        processor.extractor.classify_artifacts.return_value = {"System Interface": []}

        artifacts = [
            create_test_heading("Section 1", heading_id="H_001"),
            create_test_information("Info from Section 1", info_id="INFO_001"),
            create_test_heading("Section 2", heading_id="H_002"),  # Should reset info
            create_test_requirement("Requirement in Section 2", requirement_id="REQ_001"),
        ]

        augmented_reqs, _ = processor._build_augmented_requirements(artifacts)

        assert len(augmented_reqs) == 1
        # Should NOT have info from Section 1 (was reset)
        assert len(augmented_reqs[0]["info_list"]) == 0
        assert "Section 2" in augmented_reqs[0]["heading"]

    def test_build_augmented_requirements_skips_empty_requirements(self):
        """Requirements with no text content are skipped"""
        processor = BaseProcessor()
        processor.logger = Mock()
        processor.extractor = Mock()
        processor.extractor.classify_artifacts.return_value = {"System Interface": []}

        artifacts = [
            create_test_heading("Section 1", heading_id="H_001"),
            # Intentionally bare empty/whitespace strings to test the skip-empty logic
            {"type": "System Requirement", "id": "REQ_EMPTY1", "text": ""},
            {"type": "System Requirement", "id": "REQ_EMPTY2", "text": "   "},  # Whitespace only
            create_test_requirement("Valid requirement", requirement_id="REQ_VALID"),
        ]

        augmented_reqs, _ = processor._build_augmented_requirements(artifacts)

        # Only valid requirement should be included
        assert len(augmented_reqs) == 1
        assert augmented_reqs[0]["id"] == "REQ_VALID"

    def test_build_augmented_requirements_no_heading_uses_default(self):
        """Requirements without heading use 'No Heading' default"""
        processor = BaseProcessor()
        processor.logger = Mock()
        processor.extractor = Mock()
        processor.extractor.classify_artifacts.return_value = {"System Interface": []}

        artifacts = [
            # No heading artifact
            create_test_requirement("Requirement without heading", requirement_id="REQ_001"),
        ]

        augmented_reqs, _ = processor._build_augmented_requirements(artifacts)

        assert len(augmented_reqs) == 1
        assert augmented_reqs[0]["heading"] == "No Heading"

    def test_build_augmented_requirements_multiple_requirements_same_heading(self):
        """Multiple requirements can share same heading context"""
        processor = BaseProcessor()
        processor.logger = Mock()
        processor.extractor = Mock()
        processor.extractor.classify_artifacts.return_value = {"System Interface": []}

        artifacts = [
            create_test_heading("Shared Section", heading_id="H_001"),
            create_test_requirement("First requirement", requirement_id="REQ_001"),
            create_test_requirement("Second requirement", requirement_id="REQ_002"),
            create_test_requirement("Third requirement", requirement_id="REQ_003"),
        ]

        augmented_reqs, _ = processor._build_augmented_requirements(artifacts)

        assert len(augmented_reqs) == 3
        assert all("Shared Section" in req["heading"] for req in augmented_reqs)

    def test_build_augmented_requirements_no_system_requirements(self):
        """Returns empty list when no System Requirements found"""
        processor = BaseProcessor()
        processor.logger = Mock()
        processor.extractor = Mock()
        processor.extractor.classify_artifacts.return_value = {"System Interface": []}

        artifacts = [
            create_test_heading("Section with no requirements", heading_id="H_001"),
            create_test_information("Just some information", info_id="INFO_001"),
        ]

        augmented_reqs, interface_count = processor._build_augmented_requirements(artifacts)

        assert len(augmented_reqs) == 0
        assert interface_count == 0
        processor.logger.warning.assert_called_once()


class TestOutputPathGeneration:
    """Test output file path generation"""

    def test_generate_output_path_default_directory(self):
        """Output path uses input file's parent directory by default"""
        processor = BaseProcessor()
        reqifz_path = Path("/input/folder/test.reqifz")
        model = "llama3.1:8b"

        output_path = processor._generate_output_path(reqifz_path, model)

        assert output_path.parent == Path("/input/folder")
        assert output_path.stem.startswith("test_TCD_llama3.1_8b_")
        assert output_path.suffix == ".xlsx"

    def test_generate_output_path_custom_directory(self):
        """Output path uses custom directory when provided"""
        processor = BaseProcessor()
        reqifz_path = Path("/input/folder/test.reqifz")
        model = "llama3.1:8b"
        custom_dir = Path("/custom/output")

        output_path = processor._generate_output_path(reqifz_path, model, output_dir=custom_dir)

        assert output_path.parent == custom_dir

    def test_generate_output_path_sanitizes_model_name(self):
        """Model name with special characters is sanitized"""
        processor = BaseProcessor()
        reqifz_path = Path("/input/test.reqifz")
        model = "llama3.2-vision:11b"

        output_path = processor._generate_output_path(reqifz_path, model)

        # Colon and slash should be replaced with underscore
        assert "llama3.2-vision_11b" in str(output_path)
        assert ":" not in str(output_path)

    def test_generate_output_path_includes_timestamp(self):
        """Output filename includes timestamp for uniqueness"""
        processor = BaseProcessor()
        reqifz_path = Path("/input/test.reqifz")
        model = "llama3.1:8b"

        output_path1 = processor._generate_output_path(reqifz_path, model)
        processor._generate_output_path(reqifz_path, model)

        # Timestamps should make filenames unique (within same second they'll be equal)
        # Just verify format contains timestamp pattern YYYY-MM-DD_HH-MM-SS
        import re

        assert re.search(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}", str(output_path1))


class TestMetadataCreation:
    """Test metadata dictionary creation"""

    def test_create_metadata_with_template(self):
        """Metadata includes all provided values"""
        processor = BaseProcessor()

        metadata = processor._create_metadata(
            model="llama3.1:8b",
            template="default",
            reqifz_path=Path("/input/test.reqifz"),
            total_cases=25,
            requirements_processed=10,
            successful_requirements=9,
        )

        assert metadata["model"] == "llama3.1:8b"
        assert metadata["template"] == "default"
        assert metadata["source_file"] == str(Path("/input/test.reqifz"))
        assert metadata["total_cases"] == 25
        assert metadata["requirements_processed"] == 10
        assert metadata["successful_requirements"] == 9

    def test_create_metadata_without_template(self):
        """Metadata uses 'auto-selected' when template is None"""
        processor = BaseProcessor()

        metadata = processor._create_metadata(
            model="llama3.1:8b",
            template=None,
            reqifz_path=Path("/input/test.reqifz"),
            total_cases=15,
            requirements_processed=5,
            successful_requirements=5,
        )

        assert metadata["template"] == "auto-selected"


class TestResultCreation:
    """Test success and error result dictionary creation"""

    def test_create_success_result(self):
        """Success result contains all required fields"""
        processor = BaseProcessor()

        result = processor._create_success_result(
            output_path=Path("/output/test_TCD.xlsx"),
            total_test_cases=30,
            requirements_processed=12,
            successful_requirements=11,
            artifacts_count=25,
            processing_time=45.5,
            model="llama3.1:8b",
            template="custom",
        )

        assert result["success"] is True
        assert result["output_file"] == str(Path("/output/test_TCD.xlsx"))
        assert result["total_test_cases"] == 30
        assert result["requirements_processed"] == 12
        assert result["successful_requirements"] == 11
        assert result["artifacts_found"] == 25
        assert result["processing_time"] == 45.5
        assert result["model_used"] == "llama3.1:8b"
        assert result["template_used"] == "custom"

    def test_create_success_result_auto_template(self):
        """Success result uses 'auto-selected' when template is None"""
        processor = BaseProcessor()

        result = processor._create_success_result(
            output_path=Path("/output/test_TCD.xlsx"),
            total_test_cases=20,
            requirements_processed=8,
            successful_requirements=8,
            artifacts_count=15,
            processing_time=30.0,
            model="llama3.1:8b",
            template=None,
        )

        assert result["template_used"] == "auto-selected"

    def test_create_error_result(self):
        """Error result contains error message and success=False"""
        processor = BaseProcessor()

        result = processor._create_error_result(
            error_message="Failed to extract artifacts", processing_time=5.0
        )

        assert result["success"] is False
        assert result["error"] == "Failed to extract artifacts"
        assert result["processing_time"] == 5.0

    def test_create_error_result_default_time(self):
        """Error result defaults processing_time to 0"""
        processor = BaseProcessor()

        result = processor._create_error_result(error_message="Test error")

        assert result["processing_time"] == 0


class TestRAFTCollection:
    """Test RAFT training data collection"""

    def test_save_raft_example_when_enabled(self):
        """RAFT examples are saved when collector is enabled"""
        processor = BaseProcessor()
        processor.raft_collector = Mock()

        requirement = {
            "id": "REQ_001",
            "text": "Test requirement",
            "heading": "Test Section",
            "info_list": [],
            "interface_list": [],
        }
        test_cases = "Generated test cases..."
        model = "llama3.1:8b"

        processor._save_raft_example(requirement, test_cases, model)

        processor.raft_collector.collect_example.assert_called_once_with(
            requirement=requirement, generated_test_cases=test_cases, model=model
        )

    def test_save_raft_example_when_disabled(self):
        """RAFT example saving is no-op when collector is None"""
        processor = BaseProcessor()
        processor.raft_collector = None  # Disabled

        requirement = {"id": "REQ_001", "text": "Test"}
        test_cases = "Test cases"
        model = "llama3.1:8b"

        # Should not raise exception
        processor._save_raft_example(requirement, test_cases, model)
