"""
Context-Rich Test Case Generator with Enhanced Logging

Version: v1.3 - YAML Prompt Management, XLSX Output, and Rich Console Interface

Improvements:
- Integrated structured logging system with progress indicators
- Debug and verbose modes controlled by command-line flags
- Rich console output with colors and progress bars
- Maintained 100% backward compatibility with existing functionality
- Enhanced error handling and user feedback
"""

import argparse
import json
import logging
import re
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from enum import StrEnum
from pathlib import Path

# Modern type aliases with enhanced constraints (Python 3.13.7+)
from typing import Any, NotRequired, TypedDict

import pandas as pd
import requests
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn, TimeElapsedColumn
from rich.text import Text

# Import the file processing logger
from file_processing_logger import FileProcessingLogger

type JSONObj[T] = dict[str, T]
type JSONResponse = dict[str, str | int | float | bool | None]


class RequirementData(TypedDict):
    id: str
    text: str
    type: str
    table: NotRequired[dict[str, Any] | None]


class TestCaseData(TypedDict):
    summary_suffix: str
    action: str
    data: str
    expected_result: str


type Table = dict[str, str | list[list[str]]]
type Artifact = RequirementData
type ArtifactList = list[Artifact]
type TestCase = TestCaseData
type TestCaseList = list[TestCase]


class ArtifactType(StrEnum):
    HEADING = "Heading"
    INFORMATION = "Information"
    SYSTEM_INTERFACE = "System Interface"
    SYSTEM_REQUIREMENT = "System Requirement"


# =================================================================
# ENHANCED LOGGING SYSTEM
# =================================================================


class AITestLogger:
    """
    Centralized logging system for AI Test Case Generator
    Provides progress tracking, debug modes, and clean console output
    """

    def __init__(self, verbose: bool = False, debug: bool = False, log_file: str | None = None):
        self.console = Console()
        self.verbose = verbose
        self.debug_enabled = debug
        self.progress: Progress | None = None
        self.current_task: TaskID | None = None

        # Setup logging
        self._setup_logging(log_file)

        # Setup rich progress bar
        self._setup_progress()

    def _setup_logging(self, log_file: str | None) -> None:
        """Setup logging configuration"""
        # Determine log level
        if self.debug_enabled:
            level = logging.DEBUG
        elif self.verbose:
            level = logging.INFO
        else:
            level = logging.WARNING

        # Create logger
        self.logger = logging.getLogger("ai_test_generator")
        self.logger.setLevel(logging.DEBUG)  # Allow all levels to be processed

        # Clear existing handlers
        self.logger.handlers.clear()

        # Console handler with Rich formatting
        console_handler = RichHandler(
            console=self.console,
            show_path=self.debug_enabled,
            show_time=self.debug_enabled,
            rich_tracebacks=True,
            tracebacks_show_locals=self.debug_enabled,
        )
        console_handler.setLevel(level)

        # Create formatters
        if self.debug_enabled:
            console_format = "%(name)s: %(message)s"
        else:
            console_format = "%(message)s"

        console_handler.setFormatter(logging.Formatter(console_format))
        self.logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
                file_handler.setLevel(logging.DEBUG)
                file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                file_handler.setFormatter(logging.Formatter(file_format))
                self.logger.addHandler(file_handler)
                self.info(f"Logging to file: {log_file}")
            except Exception as e:
                self.warning(f"Could not setup file logging: {e}")

    def _setup_progress(self) -> None:
        """Setup rich progress bar"""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
            expand=True,
        )

    # Banner and initialization
    def print_banner(self) -> None:
        """Print application banner"""
        banner_text = Text()
        banner_text.append("AI Test Case Generator v1.3 (Unified)\n", style="bold blue")
        banner_text.append(
            "YAML Prompt Management + XLSX Output + Enhanced Logging\n", style="cyan"
        )
        banner_text.append("Context-Rich Test Case Generation from REQIFZ Files", style="white")

        panel = Panel(banner_text, title="🚀 Application Started", expand=False)
        self.console.print(panel)

    def print_configuration_summary(
        self, model: str, template: str = "auto-select", files: list = None
    ) -> None:
        """Print configuration summary"""
        if self.verbose or self.debug_enabled:
            self.console.print("\n📋 [bold]Configuration Summary:[/bold]")
            self.console.print(f"  • Model: [cyan]{model}[/cyan]")
            self.console.print(f"  • Template: [cyan]{template}[/cyan]")
            if files and self.debug_enabled:
                self.console.print(f"  • Files to process: [cyan]{len(files)}[/cyan]")
                for i, file in enumerate(files, 1):
                    self.console.print(f"    {i}. {Path(file).name}")

    # Progress tracking
    def start_progress(self, description: str, total: int | None = None) -> TaskID:
        """Start a new progress task"""
        if not self.progress:
            return None

        self.progress.start()
        self.current_task = self.progress.add_task(description, total=total)
        return self.current_task

    def update_progress(
        self, task_id: TaskID, advance: int = 1, description: str | None = None
    ) -> None:
        """Update progress task"""
        if self.progress and task_id is not None:
            self.progress.update(task_id, advance=advance, description=description)

    def finish_progress(self) -> None:
        """Finish progress tracking"""
        if self.progress:
            self.progress.stop()

    # Core logging methods
    def info(self, message: str, **kwargs) -> None:
        """Log info message (always shown)"""
        self.console.print(message, **kwargs)
        self.logger.info(message)

    def success(self, message: str) -> None:
        """Log success message with green checkmark"""
        self.console.print(f"✅ {message}", style="green")
        self.logger.info(f"SUCCESS: {message}")

    def warning(self, message: str) -> None:
        """Log warning message (always shown)"""
        self.console.print(f"⚠️  {message}", style="yellow")
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error message (always shown)"""
        self.console.print(f"❌ {message}", style="red bold")
        self.logger.error(message)

    def debug(self, message: str) -> None:
        """Log debug message (only in debug mode)"""
        if self.debug_enabled:
            self.console.print(f"🔍 DEBUG: {message}", style="dim blue")
        self.logger.debug(message)

    def verbose_log(self, message: str) -> None:
        """Log verbose message (in verbose or debug mode)"""
        if self.verbose or self.debug_enabled:
            self.console.print(f"📋 {message}", style="dim")
        self.logger.info(f"VERBOSE: {message}")

    # File processing specific methods
    def start_file_processing(
        self, files: list, model_name: str, template: str = "auto-select"
    ) -> None:
        """Start file processing with summary"""
        self.info(f"📁 Found {len(files)} .reqifz file(s) to process")
        self.info(f"🤖 Using AI model: [cyan]{model_name}[/cyan]")
        self.print_configuration_summary(model_name, template, files)

    def start_single_file(self, filename: str, index: int, total: int) -> TaskID:
        """Start processing a single file"""
        self.info(f"\n[bold][{index}/{total}] Processing: {filename}[/bold]")
        return self.start_progress(f"Processing {filename}", total=100)

    def log_file_analysis(self, filename: str, objects_found: int, interfaces_found: int) -> None:
        """Log file analysis results"""
        self.verbose_log(f"  📊 Found {objects_found} objects in {filename}")
        self.verbose_log(f"  🔗 Found {interfaces_found} system interface definitions")

    def log_requirement_processing(self, req_id: str, index: int, total: int) -> None:
        """Log requirement processing"""
        self.verbose_log(f"  🔍 Analyzing Requirement {index + 1}/{total} (ID: {req_id})")

    def log_ai_generation(self, req_id: str, model_name: str, template_name: str) -> None:
        """Log AI generation attempt"""
        self.verbose_log(f"    🤖 Generating test cases for '{req_id}' using {model_name}")
        if template_name and template_name != "unknown":
            self.verbose_log(f"    🎯 Using template: {template_name}")

    def log_test_case_results(self, req_id: str, test_count: int) -> None:
        """Log test case generation results"""
        if test_count > 0:
            self.verbose_log(f"    ✅ Generated {test_count} test cases")
        else:
            self.warning(f"    ❌ Failed to generate test cases for {req_id}")

    # Ollama API specific methods
    def log_ollama_call(self, model_name: str, prompt_length: int, is_json: bool = False) -> None:
        """Log Ollama API call details"""
        self.debug(
            f"Ollama API Call: Model={model_name}, Prompt={prompt_length} chars, JSON={is_json}"
        )

    def log_ollama_error(self, error_type: str, model_name: str, details: str) -> None:
        """Log Ollama API errors"""
        self.error(f"Ollama {error_type} with model {model_name}: {details}")

    # Template management methods
    def log_template_selection(self, template_name: str, auto_selected: bool = False) -> None:
        """Log template selection"""
        if auto_selected:
            self.verbose_log(f"    🎯 Auto-selected template: {template_name}")
        else:
            self.info(f"🎯 Using specified template: [cyan]{template_name}[/cyan]")

    def log_template_validation(self, template_file: str, errors: list) -> None:
        """Log template validation results"""
        if errors:
            self.error(f"Template validation failed for {template_file}:")
            for error in errors:
                self.error(f"  - {error}")
        else:
            self.success(f"Template {template_file} is valid")

    # Output and completion methods
    def log_output_generation(self, output_path: str, test_count: int) -> None:
        """Log output file generation"""
        self.success(f"Generated {test_count} test cases")
        self.info(f"📄 Saved to: [cyan]{Path(output_path).name}[/cyan]")

    def log_completion_summary(self, files_processed: int, total_tests: int = 0) -> None:
        """Log final completion summary"""
        self.console.print("\n🎉 [bold green]Processing Complete![/bold green]")
        self.console.print(f"📊 Processed {files_processed} file(s)")
        if total_tests > 0:
            self.console.print(f"📋 Generated {total_tests} total test cases")
        self.console.print("📁 Look for files ending with '_YAML.xlsx' in your input directories")


# Global logger instance
_logger_instance: AITestLogger | None = None


def get_logger() -> AITestLogger:
    """Get the global logger instance"""
    if _logger_instance is None:
        raise RuntimeError("Logger not initialized. Call setup_logger() first.")
    return _logger_instance


def setup_logger(
    verbose: bool = False, debug: bool = False, log_file: str | None = None
) -> AITestLogger:
    """Setup and return the global logger instance"""
    global _logger_instance
    _logger_instance = AITestLogger(verbose=verbose, debug=debug, log_file=log_file)
    return _logger_instance


# Import YAML prompt manager
try:
    from yaml_prompt_manager import YAMLPromptManager
except ImportError as e:
    print(f"❌ Error: Could not import YAML prompt manager: {e}")
    sys.exit(1)

# Import configuration
try:
    from config import ConfigManager, OllamaConfig, StaticTestConfig
except ImportError:
    # Fallback to inline configuration if config.py is not available
    from dataclasses import dataclass

    @dataclass(slots=True)
    class StaticTestConfig:
        VOLTAGE_PRECONDITION: str = "1. Voltage= 12V\n2. Bat-ON"
        TEST_TYPE: str = "PROVEtech"
        ISSUE_TYPE: str = "Test"
        PROJECT_KEY: str = "TCTOIC"
        ASSIGNEE: str = "ENGG"
        PLANNED_EXECUTION: str = "Manual"
        TEST_CASE_TYPE: str = "Feature Functional"
        COMPONENTS: str = "SW_DI_FV"
        LABELS: str = "AI Generated TC"

    @dataclass(slots=True)
    class OllamaConfig:
        host: str = "127.0.0.1"
        port: int = 11434
        timeout: int = 600
        temperature: float = 0.0

        @property
        def api_url(self) -> str:
            return f"http://{self.host}:{self.port}/api/generate"

    class ConfigManager:
        def __init__(self):
            self.static_test = StaticTestConfig()
            self.ollama = OllamaConfig()


# =================================================================
# OLLAMA API CLIENT WITH LOGGING
# =================================================================


class OllamaClient:
    """Handles all interactions with Ollama API with enhanced logging"""

    __slots__ = ("config", "proxies", "_session")

    def __init__(self, config: OllamaConfig = None):
        self.config = config or OllamaConfig()
        self.proxies = {"http": None, "https": None}
        # Reuse session for better performance (Python 3.13.7+ optimization)
        self._session = requests.Session()
        self._session.proxies.update(self.proxies)

    def generate_response(self, model_name: str, prompt: str, is_json: bool = False) -> str:
        """Generate response from Ollama model with comprehensive logging"""
        logger = get_logger()
        logger.log_ollama_call(model_name, len(prompt), is_json)

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.config.keep_alive,  # Ollama v0.11.10+ optimization
            "options": {
                "temperature": self.config.temperature,
                "num_ctx": self.config.num_ctx,  # Context window size
                "num_predict": self.config.num_predict,  # Response length limit
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        }

        if is_json:
            payload["format"] = "json"

        try:
            response = self._session.post(
                self.config.api_url,
                json=payload,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            try:
                data: JSONResponse = response.json()
            except ValueError:
                # Fallback if response is not JSON
                data = {}
            return str(data.get("response", ""))
        except (requests.ConnectionError, requests.Timeout) as e:
            logger.log_ollama_error("CONNECTION ERROR", model_name, str(e))
            return ""
        except requests.HTTPError as e:
            status_code = getattr(e.response, "status_code", "unknown")
            logger.log_ollama_error(f"HTTP ERROR {status_code}", model_name, str(e))
            return ""
        except requests.RequestException as e:
            logger.log_ollama_error("REQUEST ERROR", model_name, str(e))
            return ""
        except Exception as e:
            logger.log_ollama_error("UNEXPECTED ERROR", model_name, str(e))
            return ""


# =================================================================
# JSON RESPONSE PARSER
# =================================================================


class JSONResponseParser:
    """Handles parsing JSON responses from AI models"""

    __slots__ = ()

    @staticmethod
    def extract_json_from_response(response_text: str) -> dict[str, Any] | None:
        """
        Extract and parse JSON from AI model response

        Args:
            response_text: Raw response text from model

        Returns:
            Parsed JSON dictionary or None if parsing fails
        """
        try:
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            return None
        except (json.JSONDecodeError, IndexError):
            return None


# =================================================================
# HTML TABLE PARSER
# =================================================================


class HTMLTableParser:
    """Handles parsing of HTML tables from REQIF XML content"""

    __slots__ = ("namespaces",)

    def __init__(self, namespaces: dict[str, str]):
        self.namespaces = namespaces

    def _process_cell_content(self, element) -> str:
        """Process cell content using pattern matching (Python 3.13.7+)"""
        tag_name = element.tag.split("}")[-1] if "}" in element.tag else element.tag

        match tag_name.lower():
            case "td" | "th":
                return "".join(element.itertext()).strip()
            case "table":
                # Handle nested table
                nested_table = self.parse_html_table(element)
                return (
                    f"[Nested table: {len(nested_table.get('rows', []))} rows]"
                    if nested_table
                    else ""
                )
            case _:
                return str(element.text or "").strip()

    def parse_html_table(self, table_element) -> dict[str, Any] | None:
        """
        Parse HTML table element into structured data

        Args:
            table_element: XML table element

        Returns:
            Dictionary with 'headers' and 'rows' keys, or None if parsing fails
        """
        headers, data_rows = [], []
        raw_rows = table_element.findall(".//html:tr", self.namespaces)

        if not raw_rows:
            return None

        # Create grid to handle colspan/rowspan
        grid = [[] for _ in range(len(raw_rows))]

        # Process each row and cell
        for r, tr in enumerate(raw_rows):
            for td in tr.findall(".//html:td", self.namespaces) + tr.findall(
                ".//html:th", self.namespaces
            ):
                c = 0
                while c < len(grid[r]):
                    c += 1

                text = "".join(td.itertext()).strip()
                colspan = int(td.get("colspan", 1))
                rowspan = int(td.get("rowspan", 1))

                # Fill grid cells for colspan/rowspan
                for i in range(r, r + rowspan):
                    j_start = c
                    while len(grid[i]) < j_start + colspan:
                        grid[i].append("")
                    for j in range(j_start, j_start + colspan):
                        grid[i][j] = text

        # Fill empty cells with previous row values
        for r_idx, row in enumerate(grid):
            for c_idx, cell in enumerate(row):
                if cell == "" and r_idx > 0 and c_idx < len(grid[r_idx - 1]):
                    grid[r_idx][c_idx] = grid[r_idx - 1][c_idx]

        # Process headers and data rows
        if len(grid) >= 2:
            header_row1, header_row2 = grid[0], grid[1]
            data_rows = grid[2:]
            merged_headers = []

            c = 0
            while c < len(header_row1):
                span_text = header_row1[c]
                span_count = 1

                while (
                    c + span_count < len(header_row1) and header_row1[c + span_count] == span_text
                ):
                    span_count += 1

                if span_text and span_text not in ["Input", "Output", "No."]:
                    for i in range(span_count):
                        merged_headers.append(header_row2[c + i])
                else:
                    for i in range(span_count):
                        merged_headers.append(f"{span_text} - {header_row2[c + i]}")

                c += span_count

            headers = merged_headers

        return {"headers": headers, "rows": data_rows}


# =================================================================
# REQIF ARTIFACT EXTRACTOR
# =================================================================


class REQIFArtifactExtractor:
    """Handles extraction of artifacts from REQIFZ files"""

    __slots__ = ("namespaces", "table_parser")

    def __init__(self, namespaces: dict[str, str] | None = None):
        self.namespaces = namespaces or {
            "reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd",
            "html": "http://www.w3.org/1999/xhtml",
        }
        self.table_parser = HTMLTableParser(self.namespaces)

    def _determine_artifact_type(self, type_name: str) -> str:
        """Determine artifact type using pattern matching (Python 3.13.7+)"""
        name_lower = type_name.lower()

        match name_lower:
            case name if "heading" in name:
                return ArtifactType.HEADING
            case name if "interface" in name:
                return ArtifactType.SYSTEM_INTERFACE
            case name if "requirement" in name:
                return ArtifactType.SYSTEM_REQUIREMENT
            case name if "info" in name:
                return ArtifactType.INFORMATION
            case _:
                return ArtifactType.INFORMATION

    def extract_all_artifacts(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Extract all artifacts from a REQIFZ file

        Args:
            file_path: Path to the REQIFZ file

        Returns:
            List of artifact dictionaries
        """
        logger = get_logger()
        all_objects = []

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                reqif_filename = self._find_reqif_file(zf)

                with zf.open(reqif_filename) as reqif_file:
                    tree = ET.parse(reqif_file)
                    root = tree.getroot()

                    # Build type mappings
                    type_map = self._build_type_map(root)
                    type_to_foreign_id_map, type_to_text_def_map = self._build_attribute_maps(root)

                    # Extract all spec objects
                    for spec_object in root.findall(
                        ".//reqif:SPEC-OBJECTS//reqif:SPEC-OBJECT", self.namespaces
                    ):
                        artifact = self._process_spec_object(
                            spec_object, type_map, type_to_foreign_id_map, type_to_text_def_map
                        )
                        all_objects.append(artifact)

        except Exception as e:
            logger.error(f"Error processing XML in '{file_path.name}': {e}")
            logger.debug(f"Full error details: {str(e)}")

        return all_objects

    def _find_reqif_file(self, zip_file) -> str:
        """Find the .reqif file within the ZIP archive"""
        reqif_filename = next(
            (name for name in zip_file.namelist() if name.endswith(".reqif")), None
        )
        if not reqif_filename:
            raise FileNotFoundError("No .reqif file found in the archive.")
        return reqif_filename

    def _build_type_map(self, root) -> dict[str, str]:
        """Build mapping from type IDs to type names"""
        return {
            t.get("IDENTIFIER"): t.get("LONG-NAME")
            for t in root.findall(".//reqif:SPEC-OBJECT-TYPE", self.namespaces)
        }

    def _build_attribute_maps(self, root) -> tuple[dict[str, str], dict[str, str]]:
        """Build mappings for foreign ID and text definition attributes"""
        type_to_foreign_id_map, type_to_text_def_map = {}, {}

        for spec_type in root.findall(".//reqif:SPEC-OBJECT-TYPE", self.namespaces):
            type_id = spec_type.get("IDENTIFIER")

            foreign_id_def = spec_type.find(
                ".//reqif:ATTRIBUTE-DEFINITION-STRING[@LONG-NAME='ReqIF.ForeignID']",
                self.namespaces,
            )
            if foreign_id_def is not None:
                type_to_foreign_id_map[type_id] = foreign_id_def.get("IDENTIFIER")

            text_def = spec_type.find(
                ".//reqif:ATTRIBUTE-DEFINITION-XHTML[@LONG-NAME='ReqIF.Text']", self.namespaces
            )
            if text_def is not None:
                type_to_text_def_map[type_id] = text_def.get("IDENTIFIER")

        return type_to_foreign_id_map, type_to_text_def_map

    def _process_spec_object(
        self,
        spec_object,
        type_map: dict[str, str],
        foreign_id_map: dict[str, str],
        text_def_map: dict[str, str],
    ) -> dict[str, Any]:
        """Process a single spec object and extract its data"""
        internal_id = spec_object.get("IDENTIFIER")
        req_id, req_text, req_type, table_data = internal_id, "", "Unknown", None

        # Get object type
        type_ref_node = spec_object.find("reqif:TYPE/reqif:SPEC-OBJECT-TYPE-REF", self.namespaces)
        if type_ref_node is not None:
            spec_object_type_ref = type_ref_node.text
            type_name = type_map.get(spec_object_type_ref, "Unknown")
            req_type = self._determine_artifact_type(type_name)

            # Extract attributes
            values_container = spec_object.find("reqif:VALUES", self.namespaces)
            if values_container is not None:
                req_id = self._extract_foreign_id(
                    values_container, foreign_id_map.get(spec_object_type_ref), req_id
                )
                req_text, table_data = self._extract_text_and_table(
                    values_container, text_def_map.get(spec_object_type_ref)
                )

        return {"id": req_id, "text": req_text.strip(), "type": req_type, "table": table_data}

    def _extract_foreign_id(
        self, values_container, target_foreign_id_ref: str, default_id: str
    ) -> str:
        """Extract foreign ID from values container"""
        if not target_foreign_id_ref:
            return default_id

        for attr_value in values_container.findall("reqif:ATTRIBUTE-VALUE-STRING", self.namespaces):
            definition_ref_node = attr_value.find(
                "reqif:DEFINITION/reqif:ATTRIBUTE-DEFINITION-STRING-REF", self.namespaces
            )
            if (
                definition_ref_node is not None
                and definition_ref_node.text == target_foreign_id_ref
            ):
                return attr_value.get("THE-VALUE", default_id)

        return default_id

    def _extract_text_and_table(
        self, values_container, target_text_def_ref: str
    ) -> tuple[str, dict[str, Any] | None]:
        """Extract text content and table data from values container"""
        if not target_text_def_ref:
            return "", None

        for attr_value in values_container.findall(
            ".//reqif:ATTRIBUTE-VALUE-XHTML", self.namespaces
        ):
            definition_ref_node = attr_value.find(
                "reqif:DEFINITION/reqif:ATTRIBUTE-DEFINITION-XHTML-REF", self.namespaces
            )
            if definition_ref_node is not None and definition_ref_node.text == target_text_def_ref:
                the_value = attr_value.find("reqif:THE-VALUE", self.namespaces)
                if the_value is not None:
                    full_text = "".join(the_value.itertext()).strip()

                    # Check for table
                    table_element = the_value.find(".//html:table", self.namespaces)
                    table_data = None
                    if table_element is not None:
                        table_data = self.table_parser.parse_html_table(table_element)

                    return full_text, table_data

        return "", None


# =================================================================
# TEST CASE GENERATOR WITH YAML PROMPTS AND LOGGING
# =================================================================


class TestCaseGenerator:
    """Handles generation of test cases using AI models with YAML prompt templates and enhanced logging"""

    def __init__(
        self,
        model_name: str,
        yaml_prompt_manager: YAMLPromptManager,
        ollama_client: OllamaClient | None = None,
        config: StaticTestConfig | None = None,
    ):
        self.model_name = model_name
        self.yaml_prompt_manager = yaml_prompt_manager
        self.ollama_client = ollama_client or OllamaClient()
        self.config = config or StaticTestConfig()
        self.json_parser = JSONResponseParser()

    def generate_tests_with_context(
        self,
        requirement: dict[str, Any],
        heading: str,
        info_list: list[dict[str, Any]],
        interface_list: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate test cases using YAML prompt templates with comprehensive logging"""
        logger = get_logger()

        table = requirement.get("table")
        if not table:
            logger.debug(f"No table found in requirement {requirement['id']}")
            return []

        # Prepare context for prompt template
        template_variables = {
            "heading": heading,
            "requirement_id": requirement["id"],
            "table_str": self._format_table_for_prompt(table),
            "row_count": len(table["rows"]),
            "voltage_precondition": self.config.voltage_precondition.replace("\n", "\\n"),
            "info_str": self._format_info_for_prompt(info_list),
            "interface_str": self._format_interfaces_for_prompt(interface_list),
        }

        logger.debug(
            f"Template variables prepared for {requirement['id']}: "
            f"rows={len(table['rows'])}, heading='{heading[:50]}...'"
        )

        # Get rendered prompt from YAML template
        try:
            prompt = self.yaml_prompt_manager.get_test_prompt(**template_variables)
            selected_template = self.yaml_prompt_manager.get_selected_template()
            logger.log_ai_generation(requirement["id"], self.model_name, selected_template)
        except Exception as e:
            logger.error(f"Prompt template error for {requirement['id']}: {e}")
            logger.debug(f"Template variables that failed: {template_variables}")
            return []

        # Call AI model
        response_str = self.ollama_client.generate_response(self.model_name, prompt, is_json=True)

        if not response_str:
            logger.warning(f"Empty response from Ollama for {requirement['id']}")
            return []

        # Parse response
        parsed_json = self.json_parser.extract_json_from_response(response_str)
        test_cases = parsed_json.get("test_cases", []) if parsed_json else []

        if not test_cases and parsed_json:
            logger.debug(
                f"No test_cases key found in response for {requirement['id']}. "
                f"Available keys: {list(parsed_json.keys())}"
            )

        logger.log_test_case_results(requirement["id"], len(test_cases))
        return test_cases

    def _format_table_for_prompt(self, table: dict[str, Any]) -> str:
        """Format table data for inclusion in prompt"""
        table_str = "Headers: " + ", ".join(table["headers"]) + "\n"
        for i, row in enumerate(table["rows"]):
            table_str += f"Row {i + 1}: {row}\n"
        return table_str

    def _format_interfaces_for_prompt(self, interface_list: list[dict[str, Any]]) -> str:
        """Format interface list for inclusion in prompt"""
        if not interface_list:
            return "None"
        return "\n".join([f"- {i['id']}: {i['text']}" for i in interface_list])

    def _format_info_for_prompt(self, info_list: list[dict[str, Any]]) -> str:
        """Format information list for inclusion in prompt"""
        if not info_list:
            return "None"
        return "\n".join([f"- {i['text']}" for i in info_list])


# =================================================================
# TEST CASE FORMATTER
# =================================================================


class TestCaseFormatter:
    """Handles formatting of test cases for output"""

    def __init__(self, config: StaticTestConfig | None = None):
        self.config = config or StaticTestConfig()

    def format_test_case(
        self, test: dict[str, Any], requirement_id: str, issue_id: int
    ) -> dict[str, Any]:
        """
        Format a single test case for Excel output

        Args:
            test: Raw test case from AI model
            requirement_id: ID of the source requirement
            issue_id: Sequential issue ID number

        Returns:
            Formatted test case dictionary
        """
        # Format Data field to have each step on a separate line
        data_field = test.get("data", "N/A")
        if isinstance(data_field, str) and data_field.startswith("1)"):
            # Convert numbered list format to line breaks for Excel
            data_field = (
                data_field.replace(", ", "\n")
                .replace("2)", "\n2)")
                .replace("3)", "\n3)")
                .replace("4)", "\n4)")
                .replace("5)", "\n5)")
            )
        elif isinstance(data_field, list):
            # Convert list format to line-separated format
            data_field = "\n".join(str(step) for step in data_field)

        return {
            "Issue ID": issue_id,
            "Summary": f"[{requirement_id}] {test.get('summary_suffix', 'Generated Test')}",
            "Test Type": self.config.TEST_TYPE,
            "Issue Type": self.config.ISSUE_TYPE,
            "Project Key": self.config.PROJECT_KEY,
            "Assignee": self.config.ASSIGNEE,
            "Description": "",
            "Action": test.get("action", self.config.voltage_precondition),
            "Data": data_field,
            "Expected Result": test.get("expected_result", "N/A"),
            "Planned Execution": self.config.PLANNED_EXECUTION,
            "Test Case Type": self.config.TEST_CASE_TYPE,
            "Components": self.config.COMPONENTS,
            "Labels": self.config.LABELS,
            "Tests": requirement_id,
        }


# =================================================================
# FILE PROCESSOR ORCHESTRATOR WITH ENHANCED LOGGING
# =================================================================


class REQIFZFileProcessor:
    """Main orchestrator for processing REQIFZ files with YAML prompt management, XLSX output, and enhanced logging"""

    def __init__(
        self,
        model_name: str,
        config_manager: ConfigManager | None = None,
        yaml_prompt_manager: YAMLPromptManager | None = None,
    ):
        logger = get_logger()
        logger.debug(f"Initializing REQIFZFileProcessor with model: '{model_name}'")

        self.model_name = model_name
        self.config_manager = config_manager or ConfigManager()
        self.yaml_prompt_manager = yaml_prompt_manager or YAMLPromptManager()

        # Initialize components with configuration
        self.extractor = REQIFArtifactExtractor()
        self.test_generator = TestCaseGenerator(
            model_name,
            self.yaml_prompt_manager,
            OllamaClient(self.config_manager.ollama),
            self.config_manager.static_test,
        )
        self.formatter = TestCaseFormatter(self.config_manager.static_test)

        logger.debug("REQIFZFileProcessor initialization complete")

    def process_file(self, reqifz_file: Path, file_index: int = 1, total_files: int = 1) -> int:
        """
        Process a single REQIFZ file and generate test cases in XLSX format

        Args:
            reqifz_file: Path to the REQIFZ file to process
            file_index: Current file index (for progress tracking)
            total_files: Total number of files (for progress tracking)

        Returns:
            Number of test cases generated
        """
        logger = get_logger()

        # Start file processing progress
        logger.start_single_file(reqifz_file.name, file_index, total_files)

        # Generate output file path
        output_xlsx_path = self._generate_output_path(reqifz_file)

        # Initialize processing logger
        processing_logger = FileProcessingLogger(
            reqifz_file=reqifz_file.name,
            input_path=str(reqifz_file),
            output_file=str(output_xlsx_path),
            version="v002_unified",
            ai_model=self.model_name,
        )

        try:
            logger.debug(f"Output path: {output_xlsx_path}")

            # Phase 1: XML Parsing
            processing_logger.start_phase("xml_parsing")
            all_objects = self.extractor.extract_all_artifacts(reqifz_file)
            processing_logger.end_phase("xml_parsing")

            if not all_objects:
                logger.warning(f"No objects found in {reqifz_file.name}. Skipping.")
                processing_logger.add_warning("No objects found in REQIFZ file")
                processing_logger.end_processing(success=False)
                processing_logger.save_log()
                return 0

            # Update artifact counts
            processing_logger.total_artifacts_found = len(all_objects)
            for obj in all_objects:
                artifact_type = obj.get("type", "Unknown")
                processing_logger.artifacts_by_type[artifact_type] = (
                    processing_logger.artifacts_by_type.get(artifact_type, 0) + 1
                )

            # Separate artifacts by type
            system_interfaces, processing_list = self._separate_artifacts(all_objects)
            logger.log_file_analysis(reqifz_file.name, len(all_objects), len(system_interfaces))

            # Count requirements to be processed
            requirements_to_process = [
                obj for obj in processing_list if obj.get("type") == "System Requirement"
            ]
            processing_logger.requirements_processed_total = len(requirements_to_process)

            # Phase 2: AI Generation
            processing_logger.start_phase("ai_generation")
            master_test_list = self._process_artifacts_with_logging(
                processing_list, system_interfaces, processing_logger
            )
            processing_logger.end_phase("ai_generation")

            # Phase 3: Excel Output
            processing_logger.start_phase("excel_output")
            test_count = len(master_test_list)
            if master_test_list:
                logger.debug(f"Saving {test_count} test cases to Excel file")
                try:
                    df = pd.DataFrame(master_test_list)
                    df.to_excel(output_xlsx_path, index=False, engine="openpyxl")
                    logger.log_output_generation(str(output_xlsx_path), test_count)
                except Exception as e:
                    logger.error(f"Failed to save Excel file: {e}")
                    processing_logger.add_warning(f"Excel save failed: {str(e)}")
                    processing_logger.end_processing(success=False)
                    processing_logger.save_log()
                    return 0
            else:
                logger.warning(f"No test cases generated for {reqifz_file.name}")
                processing_logger.add_warning("No test cases generated")
                processing_logger.end_processing(success=False)
                processing_logger.save_log()
                return 0
            processing_logger.end_phase("excel_output")

            # Record template used
            processing_logger.template_used = self.yaml_prompt_manager.get_selected_template()

            # Mark as successful
            processing_logger.end_processing(success=True)

            return test_count

        except Exception as e:
            logger.error(f"Error processing file {reqifz_file.name}: {e}")
            logger.debug(f"Full error details: {str(e)}")
            processing_logger.add_warning(f"Processing failed: {str(e)}")
            processing_logger.end_processing(success=False)
            return 0
        finally:
            logger.finish_progress()
            # Always save the processing log
            log_path = processing_logger.save_log()
            if log_path:
                logger.debug(f"Processing log saved: {Path(log_path).name}")
            processing_logger.update_system_metrics()

    def _generate_output_path(self, reqifz_file: Path) -> Path:
        """Generate output XLSX file path with fixed timestamp format"""
        logger = get_logger()

        safe_model_name = self.model_name.replace(":", "_").replace(".", "_")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        output_path = reqifz_file.with_name(
            f"{reqifz_file.stem}_TCD_{safe_model_name}_{timestamp}.xlsx"
        )

        logger.debug(f"Generated output path: model={safe_model_name}, timestamp={timestamp}")
        return output_path

    def _separate_artifacts(
        self, all_objects: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Separate artifacts into system interfaces and processing list"""
        system_interfaces = [
            obj for obj in all_objects if obj.get("type") == ArtifactType.SYSTEM_INTERFACE
        ]
        processing_list = [
            obj for obj in all_objects if obj.get("type") != ArtifactType.SYSTEM_INTERFACE
        ]
        return system_interfaces, processing_list

    def _process_artifacts(
        self,
        processing_list: list[dict[str, Any]],
        system_interfaces: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Process artifacts and generate test cases with enhanced progress tracking"""
        logger = get_logger()
        master_test_list = []
        issue_id_counter = 1
        current_heading = "No Heading"
        info_since_heading = []

        # Count requirements for progress tracking
        requirements_count = len(
            [
                obj
                for obj in processing_list
                if obj.get("type") == ArtifactType.SYSTEM_REQUIREMENT and obj.get("table")
            ]
        )

        logger.debug(
            f"Processing {len(processing_list)} artifacts, {requirements_count} with tables"
        )

        for i, obj in enumerate(processing_list):
            if obj.get("type") == ArtifactType.HEADING:
                current_heading = obj["text"]
                info_since_heading = []
                logger.verbose_log(f"  📍 Context set to HEADING: '{obj['id']}'")
                continue

            if obj.get("type") == ArtifactType.INFORMATION:
                info_since_heading.append(obj)
                logger.verbose_log(f"  📝 Storing INFO: '{obj['id']}'")
                continue

            if obj.get("type") == ArtifactType.SYSTEM_REQUIREMENT and obj.get("table"):
                test_cases, issue_id_counter = self._process_requirement(
                    obj,
                    current_heading,
                    info_since_heading,
                    system_interfaces,
                    i,
                    len(processing_list),
                    issue_id_counter,
                )
                master_test_list.extend(test_cases)
                info_since_heading = []  # Clear info after processing requirement

        logger.debug(f"Generated total of {len(master_test_list)} test cases")
        return master_test_list

    def _process_artifacts_with_logging(
        self,
        processing_list: list[dict[str, Any]],
        system_interfaces: list[dict[str, Any]],
        processing_logger: FileProcessingLogger,
    ) -> list[dict[str, Any]]:
        """Process artifacts and generate test cases with comprehensive logging"""
        logger = get_logger()
        master_test_list = []
        issue_id_counter = 1
        current_heading = "No Heading"
        info_since_heading = []

        # Count requirements for progress tracking
        requirements_count = len(
            [
                obj
                for obj in processing_list
                if obj.get("type") == ArtifactType.SYSTEM_REQUIREMENT and obj.get("table")
            ]
        )

        logger.debug(
            f"Processing {len(processing_list)} artifacts, {requirements_count} with tables"
        )

        for i, obj in enumerate(processing_list):
            # Update system metrics periodically
            if i % 10 == 0:
                processing_logger.update_system_metrics()

            if obj.get("type") == ArtifactType.HEADING:
                current_heading = obj["text"]
                info_since_heading = []
                logger.verbose_log(f"  📍 Context set to HEADING: '{obj['id']}'")
                continue

            if obj.get("type") == ArtifactType.INFORMATION:
                info_since_heading.append(obj)
                logger.verbose_log(f"  📝 Storing INFO: '{obj['id']}'")
                continue

            if obj.get("type") == ArtifactType.SYSTEM_REQUIREMENT and obj.get("table"):
                start_time = time.time()
                try:
                    test_cases, issue_id_counter = self._process_requirement(
                        obj,
                        current_heading,
                        info_since_heading,
                        system_interfaces,
                        i,
                        len(processing_list),
                        issue_id_counter,
                    )

                    # Record successful processing
                    processing_logger.requirements_successful += 1
                    response_time = time.time() - start_time
                    processing_logger.add_ai_response_time(response_time)

                    # Count test case types
                    positive_count = sum(
                        1 for tc in test_cases if tc.get("Components", "").find("[Positive]") != -1
                    )
                    negative_count = len(test_cases) - positive_count
                    processing_logger.increment_test_cases(
                        positive=positive_count, negative=negative_count
                    )

                    master_test_list.extend(test_cases)
                    info_since_heading = []  # Clear info after processing requirement

                except Exception as e:
                    # Record failure
                    processing_logger.add_requirement_failure(obj.get("id", "unknown"), str(e))
                    logger.error(
                        f"  ❌ Error processing requirement {obj.get('id', 'unknown')}: {e}"
                    )

        logger.debug(f"Generated total of {len(master_test_list)} test cases")
        return master_test_list

    def _process_requirement(
        self,
        requirement: dict[str, Any],
        heading: str,
        info_list: list[dict[str, Any]],
        interface_list: list[dict[str, Any]],
        index: int,
        total: int,
        issue_id_counter: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Process a single requirement and generate test cases with detailed logging"""
        logger = get_logger()
        logger.log_requirement_processing(requirement["id"], index, total)

        generated_tests = self.test_generator.generate_tests_with_context(
            requirement, heading, info_list, interface_list
        )

        if not generated_tests:
            logger.debug(f"No test cases generated for {requirement['id']}")
            return [], issue_id_counter

        formatted_tests = []
        for test in generated_tests:
            if not isinstance(test, dict):
                logger.warning(
                    f"AI returned invalid test case format for {requirement['id']}: {type(test)}"
                )
                logger.debug(f"Invalid test case content: {test}")
                continue

            # Validate test case has required fields
            required_fields = ["summary_suffix", "action", "data", "expected_result"]
            missing_fields = [field for field in required_fields if field not in test]
            if missing_fields:
                logger.warning(
                    f"Test case missing required fields {missing_fields} for {requirement['id']}"
                )
                logger.debug(f"Test case content: {test}")
                continue

            formatted_case = self.formatter.format_test_case(
                test, requirement["id"], issue_id_counter
            )
            formatted_tests.append(formatted_case)
            issue_id_counter += 1

        logger.debug(
            f"Successfully formatted {len(formatted_tests)} test cases for {requirement['id']}"
        )
        return formatted_tests, issue_id_counter


# =================================================================
# COMMAND LINE INTERFACE WITH ENHANCED LOGGING OPTIONS
# =================================================================


class CommandLineInterface:
    """Handles command line argument parsing and file discovery with logging options"""

    @staticmethod
    def parse_arguments() -> argparse.Namespace:
        """Parse command line arguments with enhanced logging options"""
        parser = argparse.ArgumentParser(
            description="Context-Aware Test Case Generator with YAML Prompt Management, XLSX Output, and Enhanced Logging",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s input.reqifz                              # Process with default settings
  %(prog)s /path/to/reqifz/files/ --model llama3.1:8b --verbose    # Verbose output
  %(prog)s input.reqifz --template driver_information_default --debug  # Debug mode
  %(prog)s input.reqifz --list-templates             # List available templates
  %(prog)s --validate-prompts --debug                # Validate with debug output

Logging Options:
  --verbose, -v         Enable verbose output with progress details
  --debug               Enable detailed debug output and logging
  --log-file FILE       Save detailed logs to specified file
  --simple              Use simple console output (legacy v002 mode)

Prompt Management:
  --template TEMPLATE        Use specific prompt template
  --list-templates          List available prompt templates
  --prompt-config FILE      Use custom prompt configuration
  --validate-prompts        Validate prompt template files
  --reload-prompts          Reload prompt templates (development)

Available Models:
  - llama3.1:8b (default)
  - deepseek-coder-v2:16b
  - Or any other Ollama model you have installed

Output Format:
  Test cases are generated in Excel (.xlsx) format for easy review and integration.
            """,
        )
        parser.add_argument(
            "input_path",
            nargs="?",
            type=Path,
            help="Path to a single .reqifz file or a folder of .reqifz files.",
        )
        parser.add_argument(
            "--model",
            default="llama3.1:8b",
            help="Ollama model to use for test generation (default: %(default)s)",
        )
        parser.add_argument(
            "--template", help="Specific prompt template to use (overrides auto-selection)"
        )
        parser.add_argument(
            "--list-templates", action="store_true", help="List available prompt templates and exit"
        )
        parser.add_argument("--prompt-config", help="Path to custom prompt configuration file")
        parser.add_argument(
            "--validate-prompts",
            action="store_true",
            help="Validate prompt template files and exit",
        )
        parser.add_argument(
            "--reload-prompts",
            action="store_true",
            help="Reload prompt templates (useful during development)",
        )
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Enable verbose output with additional progress information",
        )
        parser.add_argument(
            "--debug", action="store_true", help="Enable detailed debug output and logging"
        )
        parser.add_argument("--log-file", type=str, help="Save detailed logs to specified file")
        parser.add_argument(
            "--simple", action="store_true", help="Use simple console output (legacy v002 mode)"
        )
        return parser.parse_args()

    @staticmethod
    def discover_files(input_path: Path) -> list[Path]:
        """
        Discover REQIFZ files to process

        Args:
            input_path: Input path (file or directory)

        Returns:
            List of REQIFZ file paths to process
        """
        logger = get_logger()

        if not input_path.exists():
            raise FileNotFoundError(f"The path '{input_path}' does not exist.")

        files_to_process = []

        if input_path.is_file():
            if input_path.suffix.lower() == ".reqifz":
                files_to_process.append(input_path)
                logger.debug(f"Single file mode: {input_path.name}")
            else:
                raise ValueError(f"File '{input_path.name}' is not a .reqifz file")
        elif input_path.is_dir():
            # Use new walk() method for better performance (Python 3.13.7+)
            try:
                files_to_process = [
                    dirpath / file_path
                    for dirpath, _, file_paths in input_path.walk()
                    for file_path in file_paths
                    if file_path.suffix.lower() == ".reqifz"
                ]
                logger.debug(f"Directory mode: found {len(files_to_process)} .reqifz files")
            except AttributeError:
                # Fallback for older Python versions (shouldn't happen in 3.13.7+)
                files_to_process = list(input_path.rglob("*.reqifz"))
                logger.debug(
                    f"Directory mode (fallback): found {len(files_to_process)} .reqifz files"
                )

        if not files_to_process:
            raise ValueError("No .reqifz files found to process.")

        return sorted(files_to_process)  # Sort for consistent processing order


# =================================================================
# APPLICATION FACTORY WITH LOGGING INTEGRATION
# =================================================================


class ApplicationFactory:
    """Factory class for creating application components with logging integration"""

    @staticmethod
    def create_config_manager(config_file_path: str | None = None) -> ConfigManager:
        """
        Create configuration manager with optional custom config file

        Args:
            config_file_path: Path to custom configuration file

        Returns:
            Configured ConfigManager instance
        """
        logger = get_logger()
        config_manager = ConfigManager()

        if config_file_path and Path(config_file_path).exists():
            try:
                import yaml

                with open(config_file_path) as f:
                    custom_config = yaml.safe_load(f)
                # Update config if update_from_dict method exists
                if hasattr(config_manager, "update_from_dict"):
                    config_manager.update_from_dict(custom_config)
                logger.verbose_log(f"Loaded custom configuration from: {config_file_path}")
            except Exception as e:
                logger.warning(f"Failed to load custom config file: {e}")
                logger.info("Using default configuration.")

        return config_manager

    @staticmethod
    def create_yaml_prompt_manager(prompt_config_file: str | None = None) -> YAMLPromptManager:
        """
        Create YAML prompt manager with logging

        Args:
            prompt_config_file: Path to prompt configuration file

        Returns:
            Configured YAMLPromptManager instance
        """
        logger = get_logger()
        config_file = prompt_config_file or "prompts/config/prompt_config.yaml"

        try:
            manager = YAMLPromptManager(config_file)
            logger.debug(f"Created YAML prompt manager with config: {config_file}")
            return manager
        except Exception as e:
            logger.error(f"Failed to create YAML prompt manager: {e}")
            raise

    @staticmethod
    def create_processor(
        model_name: str,
        config_manager: ConfigManager,
        yaml_prompt_manager: YAMLPromptManager,
    ) -> REQIFZFileProcessor:
        """
        Create file processor with given model, configuration, and prompt manager

        Args:
            model_name: Name of the AI model to use
            config_manager: Configuration manager instance
            yaml_prompt_manager: YAML prompt manager instance

        Returns:
            Configured REQIFZFileProcessor instance
        """
        logger = get_logger()
        logger.debug(f"Creating processor with model: {model_name}")

        return REQIFZFileProcessor(model_name, config_manager, yaml_prompt_manager)


# =================================================================
# UTILITY FUNCTIONS
# =================================================================


def validate_model_availability(model_name: str) -> bool:
    """
    Validate that the specified model is available in Ollama

    Args:
        model_name: Name of the model to validate

    Returns:
        True if model is available, False otherwise
    """
    logger = get_logger()
    logger.debug(f"Validating model availability: {model_name}")

    try:
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if response.status_code == 200:
            try:
                data: dict[str, Any] = response.json()
            except ValueError:
                logger.debug("Could not parse Ollama API response as JSON")
                return False
            available_models = [model["name"] for model in data.get("models", [])]
            is_available = model_name in available_models
            logger.debug(f"Model {model_name} availability: {is_available}")
            if logger.debug_enabled and not is_available:
                logger.debug(f"Available models: {available_models}")
            return is_available
        logger.debug(f"Ollama API returned status code: {response.status_code}")
        return False
    except requests.exceptions.RequestException as e:
        logger.debug(f"Could not connect to Ollama API: {e}")
        return False


def handle_prompt_management_commands(args) -> int:
    """
    Handle prompt management commands with enhanced logging

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    logger = get_logger()

    try:
        # Create prompt manager
        yaml_prompt_manager = ApplicationFactory.create_yaml_prompt_manager(args.prompt_config)

        if args.list_templates:
            logger.info("📋 Available Prompt Templates:")
            templates = yaml_prompt_manager.list_templates()
            for category, template_list in templates.items():
                logger.info(f"\n[bold]{category.upper()}:[/bold]")
                for template_name in template_list:
                    info = yaml_prompt_manager.get_template_info(template_name)
                    logger.info(f"  • [cyan]{template_name}[/cyan]")
                    if info.get("description"):
                        logger.verbose_log(f"    {info['description']}")
                    if info.get("tags"):
                        logger.verbose_log(f"    Tags: {', '.join(info['tags'])}")
            return 0

        if args.validate_prompts:
            logger.info("🔍 Validating Prompt Templates...")

            # Validate test generation templates
            test_file = yaml_prompt_manager.config["file_paths"]["test_generation_prompts"]
            test_path = yaml_prompt_manager._resolve_config_path(test_file)

            if test_path.exists():
                errors = yaml_prompt_manager.validate_template_file(str(test_path))
                logger.log_template_validation(test_file, errors)
                if errors:
                    return 1
            else:
                logger.warning(f"Template file not found: {test_file}")

            # Validate error handling templates
            error_file = yaml_prompt_manager.config["file_paths"].get("error_handling_prompts", "")
            if error_file:
                error_path = yaml_prompt_manager._resolve_config_path(error_file)
                if error_path.exists():
                    errors = yaml_prompt_manager.validate_template_file(str(error_path))
                    logger.log_template_validation(error_file, errors)
                    if errors:
                        return 1
                else:
                    logger.warning(f"Error template file not found: {error_file}")

            logger.success("All prompt templates are valid!")
            return 0

        if args.reload_prompts:
            yaml_prompt_manager.reload_prompts()
            logger.success("Prompt templates reloaded successfully!")
            return 0

        return 0

    except Exception as e:
        logger.error(f"Error in prompt management: {e}")
        logger.debug(f"Full error details: {str(e)}")
        return 1


# =================================================================
# MAIN APPLICATION WITH ENHANCED LOGGING
# =================================================================


def main():
    """Main application entry point with comprehensive logging"""
    try:
        # Parse command line arguments first (before logging setup)
        args = CommandLineInterface.parse_arguments()

        # Setup logging system FIRST - handle simple mode
        if args.simple:
            # Simple mode: disable rich output for legacy behavior
            logger = setup_logger(verbose=False, debug=False, log_file=None)
        else:
            logger = setup_logger(
                verbose=args.verbose,
                debug=args.debug,
                log_file=args.log_file if hasattr(args, "log_file") else None,
            )

        # Print banner
        logger.print_banner()

        # Handle prompt management commands first
        if args.list_templates or args.validate_prompts or args.reload_prompts:
            return handle_prompt_management_commands(args)

        # Ensure input path is provided for file processing
        if not args.input_path:
            logger.error("input_path is required for file processing")
            logger.info("Use --help for usage information")
            return 1

        input_path = (
            Path(args.input_path) if not isinstance(args.input_path, Path) else args.input_path
        )

        # Validate model availability
        if not validate_model_availability(args.model):
            logger.warning(f"Model '{args.model}' may not be available in Ollama")
            logger.info("Available models can be checked with: [cyan]ollama list[/cyan]")
            logger.info("Continuing anyway...")

        # Create configuration manager
        config_manager = ApplicationFactory.create_config_manager()

        # Create YAML prompt manager
        yaml_prompt_manager = ApplicationFactory.create_yaml_prompt_manager(args.prompt_config)

        # Reload prompts if requested
        if args.reload_prompts:
            yaml_prompt_manager.reload_prompts()

        # Discover files to process
        files_to_process = CommandLineInterface.discover_files(input_path)

        # Determine template info for logging
        template_info = args.template if args.template else "auto-select"

        # Log processing start
        logger.start_file_processing(files_to_process, args.model, template_info)

        # Create processor
        processor = ApplicationFactory.create_processor(
            args.model, config_manager, yaml_prompt_manager
        )

        # If specific template requested, log it
        if args.template:
            logger.log_template_selection(args.template, auto_selected=False)

        # Process each file
        total_test_cases = 0
        successful_files = 0

        for i, reqifz_file in enumerate(files_to_process, 1):
            test_count = processor.process_file(reqifz_file, i, len(files_to_process))
            if test_count > 0:
                total_test_cases += test_count
                successful_files += 1

        # Log completion summary
        logger.log_completion_summary(successful_files, total_test_cases)

        if successful_files < len(files_to_process):
            logger.warning(
                f"Some files failed to process: {len(files_to_process) - successful_files} failures"
            )
            return 1

        return 0

    except (FileNotFoundError, ValueError) as e:
        if "_logger_instance" in globals() and _logger_instance is not None:
            get_logger().error(str(e))
        else:
            print(f"❌ Error: {e}")
        return 1
    except KeyboardInterrupt:
        if "_logger_instance" in globals() and _logger_instance is not None:
            get_logger().warning("Process interrupted by user")
        else:
            print("\n⏹️  Process interrupted by user.")
        return 1
    except Exception as e:
        if "_logger_instance" in globals() and _logger_instance is not None:
            logger = get_logger()
            logger.error(f"Unexpected error: {e}")
            if hasattr(args, "debug") and args.debug:
                import traceback

                logger.error("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    logger.debug(line)
        else:
            print(f"💥 Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
