"""
Test case generators for the AI Test Case Generator.

This module provides classes for generating test cases from requirement artifacts
using AI models, with support for both synchronous and asynchronous processing.

Both generators share construction and response post-processing through
_GeneratorCore; only the transport (sync vs async client calls) differs.
Both return structured error dicts on failure (EmptyResponse,
InvalidJSONStructure, EmptyTestCasesList, or the exception type) so the
processors can distinguish failure from success and report partial
completion instead of silently dropping requirements.
"""

import asyncio
import math  # Added for confidence calculation
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .deduplicator import TestCaseDeduplicator
from .exceptions import TestCaseValidationError
from .parsers import FastJSONResponseParser, JSONResponseParser
from .prompt_builder import PromptBuilder

if TYPE_CHECKING:
    from src.config import ConfigManager
    from src.file_processing_logger import FileProcessingLogger
    from src.yaml_prompt_manager import YAMLPromptManager

    from .ollama_client import AsyncOllamaClient, OllamaClient
from .validators import (
    TEST_CASE_RESPONSE_JSON_SCHEMA,
    SemanticValidator,
    is_canonical_test_case,
)

# Type aliases for better readability (PEP 695 style)
type TestCaseData = dict[str, Any]
type TestCaseList = list[TestCaseData]
type RequirementData = dict[str, Any]
type ProcessingResult = TestCaseList | dict[str, Any]  # Can be test cases or error info


def extract_image_paths(requirement: RequirementData) -> list[Path]:
    """
    Extract image file paths from requirement metadata.

    This is a shared helper used by both sync and async generators to avoid
    code duplication (DRY principle).

    Args:
        requirement: Requirement data containing potential image metadata

    Returns:
        List of Path objects pointing to valid image files
    """
    if not requirement.get("has_images", False):
        return []

    images = requirement.get("images", [])
    paths = []
    for img in images:
        if "saved_path" in img:
            img_path = Path(img["saved_path"])
            if img_path.exists():
                paths.append(img_path)

    return paths


def stamp_validation_results(test_cases: TestCaseList, validation_report: dict[str, Any]) -> None:
    """
    Mark each test case with its semantic-validation outcome.

    Must run BEFORE deduplication: the report's test_case_index values refer
    to the pre-dedup order, and the deduplicator's "best" strategy prefers
    test cases with validation_passed=True.

    Global issues (test_case_index <= 0, e.g. table-coverage deficiencies)
    apply to the batch, not an individual test case, and are ignored here.

    Args:
        test_cases: Test cases in the exact order they were validated
        validation_report: Report from SemanticValidator.validate_batch()
    """
    invalid_indices = {
        entry.get("test_case_index")
        for entry in validation_report.get("issues", [])
        if isinstance(entry.get("test_case_index"), int) and entry.get("test_case_index") > 0
    }
    for index, test_case in enumerate(test_cases, 1):
        test_case["validation_passed"] = index not in invalid_indices


def calculate_confidence(
    response_data: dict[str, Any], logger: FileProcessingLogger | None = None
) -> float | None:
    """
    Calculate confidence score from logprobs if available.

    Uses perplexity-based confidence: exp(mean(logprobs))
    """
    try:
        if not response_data:
            return None

        # Try to locate logprobs in response
        # Ollama structure for /api/generate with logprobs=true
        # Usually it is 'context' (IDs) but logprobs might be under a different key or currently not fully exposed in all versions
        # Documentation says `logprobs` parameter returns logprobs in response?
        # Let's check for "logprobs" key which might contain token info
        # Note: As of Ollama 0.13.3 release notes, structure isn't fully detailed, checking standard paths

        # Possible structure: {"logprobs": [{"token": "Foo", "logprob": -0.1}, ...]}
        # CAUTION: This is speculative based on common patterns.
        # If 'logprobs' is missing, return None.

        # Defensive check for different possible structures
        logprobs_data = response_data.get("logprobs")

        if not logprobs_data:
            return None

        token_logprobs = []

        if isinstance(logprobs_data, list):
            # List of objects?
            for item in logprobs_data:
                if isinstance(item, dict) and "logprob" in item:
                    token_logprobs.append(item["logprob"])
                elif isinstance(item, (int, float)):
                    # Maybe direct list of floats? Unlikely but possible
                    token_logprobs.append(item)
        elif isinstance(logprobs_data, dict) and "token_logprobs" in logprobs_data:
            # Maybe {"tokens": [...], "token_logprobs": [...]}
            token_logprobs = logprobs_data["token_logprobs"]

        if not token_logprobs:
            return None

        # Calculate mean logprob
        mean_logprob = sum(token_logprobs) / len(token_logprobs)
        return math.exp(mean_logprob)

    except Exception as e:
        if logger:
            logger.debug(
                f"Could not parse logprobs: {e}. Keys found: {list(response_data.keys()) if response_data else 'None'}"
            )
        return None


class _GeneratorCore:
    """Shared construction and post-processing for the sync/async generators.

    Wires ValidationConfig/DeduplicationConfig (thresholds, enable flags,
    keep_strategy, fields_to_compare) into the validator and deduplicator,
    and provides the validate -> stamp -> deduplicate -> enrich pipeline
    that both generators run on parsed AI responses.
    """

    __slots__ = (
        "client",
        "json_parser",
        "prompt_builder",
        "validator",
        "deduplicator",
        "logger",
        "enable_validation",
        "enable_deduplication",
        "keep_strategy",
        "fail_on_validation_error",
    )

    # Subclasses select their JSON parser implementation
    _parser_class = JSONResponseParser

    def __init__(
        self,
        client: OllamaClient | AsyncOllamaClient,
        yaml_manager: YAMLPromptManager | None = None,
        logger: FileProcessingLogger | None = None,
        validator: SemanticValidator | None = None,
        deduplicator: TestCaseDeduplicator | None = None,
        config: ConfigManager | None = None,
    ):
        validation_cfg = getattr(config, "validation", None)
        dedup_cfg = getattr(config, "deduplication", None)
        file_cfg = getattr(config, "file_processing", None)
        max_table_rows = file_cfg.max_table_rows if file_cfg else None

        self.client = client
        self.json_parser = self._parser_class()
        self.prompt_builder = PromptBuilder(yaml_manager, max_table_rows=max_table_rows)
        self.logger = logger

        self.enable_validation = (
            validation_cfg.enable_semantic_validation if validation_cfg else True
        )
        self.fail_on_validation_error = (
            validation_cfg.fail_on_validation_error if validation_cfg else False
        )
        self.enable_deduplication = dedup_cfg.enable_deduplication if dedup_cfg else True
        self.keep_strategy = dedup_cfg.keep_strategy if dedup_cfg else "best"

        self.validator = validator or SemanticValidator(
            logger=logger,
            similarity_threshold=validation_cfg.similarity_threshold if validation_cfg else 0.8,
            max_prompt_table_rows=max_table_rows,
        )
        self.deduplicator = deduplicator or TestCaseDeduplicator(
            similarity_threshold=dedup_cfg.similarity_threshold if dedup_cfg else 0.85,
            logger=logger,
            fields_to_compare=list(dedup_cfg.fields_to_compare) if dedup_cfg else None,
        )

    @staticmethod
    def _error_result(
        req_id: str, error_type: str, error_message: str, generation_time: float | None = None
    ) -> dict[str, Any]:
        """Build a structured error object with the consistent result interface.

        Shared by the sync and async generators so both report failures the
        same way (see module docstring).
        """
        error_info = {
            "error": True,
            "requirement_id": req_id,
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_cases": [],  # Consistent interface: always provide test_cases list
        }
        if generation_time is not None:
            error_info["generation_time"] = generation_time
        return error_info

    def _extract_response_parts(
        self, full_response: dict[str, Any] | str
    ) -> tuple[str, float | None]:
        """Split a client response into (response_text, confidence_score)."""
        if isinstance(full_response, dict):
            response_text = str(full_response.get("response", ""))
            confidence_score = calculate_confidence(full_response, self.logger)
        else:
            response_text = str(full_response)
            confidence_score = None
        return response_text, confidence_score

    def _postprocess_test_cases(
        self,
        test_cases: TestCaseList,
        requirement: RequirementData,
        generation_time: float,
        confidence_score: float | None,
    ) -> TestCaseList:
        """Validate, stamp, deduplicate and enrich parsed test cases.

        This is the single post-processing pipeline shared by the sync and
        async generators; test cases are mutated in place and the (possibly
        deduplicated) list is returned.
        """
        req_id = requirement.get("id", "UNKNOWN")

        # Canonical-schema gate (review 2026-07-17 finding 4): items missing
        # the five canonical fields must not reach the formatter, which would
        # otherwise render them as plausible default/N/A Excel rows.
        canonical_cases = [tc for tc in test_cases if is_canonical_test_case(tc)]
        dropped_count = len(test_cases) - len(canonical_cases)

        if dropped_count:
            message = (
                f"{dropped_count} of {len(test_cases)} test cases for {req_id} "
                f"failed canonical-schema validation"
            )
            if self.fail_on_validation_error:
                raise TestCaseValidationError(message, requirement_id=req_id)
            if self.logger:
                self.logger.warning(f"Dropped invalid test cases: {message}")
            test_cases = canonical_cases

        # Semantic validation (skippable via ValidationConfig)
        if self.enable_validation:
            validation_report = self.validator.validate_batch(test_cases, requirement)
        else:
            validation_report = {
                "total_test_cases": len(test_cases),
                "valid_count": len(test_cases),
                "invalid_count": 0,
                "issues": [],
                "table_coverage": {"is_table_based": False},
            }

        if validation_report["invalid_count"] > 0 and self.logger:
            self.logger.warning(
                f"Semantic validation: {validation_report['valid_count']}/{validation_report['total_test_cases']} passed for {req_id}"
            )
            for issue_entry in validation_report["issues"]:
                self.logger.warning(
                    f"  Test case {issue_entry['test_case_index']}: {issue_entry['summary']}"
                )
                for issue in issue_entry["issues"]:
                    self.logger.warning(f"    - {issue}")

        # Honor strict mode for semantic failures too (ValidationConfig.
        # fail_on_validation_error was previously never consulted)
        if self.fail_on_validation_error and validation_report["invalid_count"] > 0:
            raise TestCaseValidationError(
                f"{validation_report['invalid_count']} of "
                f"{validation_report['total_test_cases']} test cases for {req_id} "
                f"failed semantic validation",
                requirement_id=req_id,
            )

        # Log table coverage information
        table_coverage = validation_report.get("table_coverage", {})
        if table_coverage.get("is_table_based", False) and self.logger:
            req_rows = table_coverage.get("required_table_rows", 0)
            pos_tests = table_coverage.get("positive_test_cases", 0)
            neg_tests = table_coverage.get("negative_test_cases", 0)
            coverage_pct = table_coverage.get("coverage_percentage", 0)

            self.logger.info(
                f"Table coverage: {pos_tests}/{req_rows} rows covered ({coverage_pct:.1f}%) - "
                f"{neg_tests} negative tests"
            )

            if not table_coverage.get("adequate_coverage", True):
                self.logger.warning(
                    f"Inadequate table coverage for {req_id}: "
                    f"Expected {req_rows}+ positive tests, got {pos_tests}. "
                    f"Expected 3+ negative tests, got {neg_tests}."
                )

        # Stamp validation outcome before dedup (indices match the validator
        # report only in pre-dedup order, and the "best" keep-strategy reads
        # validation_passed)
        stamp_validation_results(test_cases, validation_report)

        # Deduplication (skippable via DeduplicationConfig)
        if self.enable_deduplication:
            test_cases, dedup_report = self.deduplicator.deduplicate(
                test_cases, keep_strategy=self.keep_strategy
            )

            if dedup_report["duplicates_removed"] > 0 and self.logger:
                self.logger.info(
                    f"Deduplication: {dedup_report['original_count']} → {dedup_report['deduplicated_count']} test cases for {req_id} "
                    f"({dedup_report['duplicates_removed']} duplicates removed)"
                )

        # Metadata enrichment
        for i, test_case in enumerate(test_cases):
            test_case["requirement_id"] = req_id
            test_case["generation_time"] = generation_time
            test_case["test_id"] = f"{req_id}_TC_{i + 1:03d}"
            if confidence_score is not None:
                test_case["confidence_score"] = confidence_score

        if self.logger:
            self.logger.info(
                f"Generated {len(test_cases)} test cases for {req_id} "
                f"({validation_report['valid_count']} passed validation)"
            )

        return test_cases

    def _split_oversized_table(self, requirement: RequirementData) -> list[RequirementData] | None:
        """Split a requirement whose table exceeds the prompt row limit.

        A single prompt truncates large tables (only the first/last rows are
        shown), so rows in the middle are never covered. Splitting the rows
        into chunks that each fit the limit lets every row be generated by a
        dedicated call (archived finding 7).

        Args:
            requirement: The requirement to inspect.

        Returns:
            One sub-requirement per row-chunk (each carrying a slice of the
            table), or None when the requirement has no table or the table
            already fits within `max_table_rows`.
        """
        table = requirement.get("table")
        if not isinstance(table, dict):
            return None
        rows = table.get("data")
        if not isinstance(rows, list) or not rows:
            return None

        max_rows = self.prompt_builder.max_table_rows
        if len(rows) <= max_rows:
            return None

        chunks: list[RequirementData] = []
        for start in range(0, len(rows), max_rows):
            chunk_rows = rows[start : start + max_rows]
            chunk_table = {**table, "data": chunk_rows, "rows": len(chunk_rows)}
            chunks.append({**requirement, "table": chunk_table})
        return chunks

    def _merge_chunk_results(
        self, req_id: str, chunk_results: list[ProcessingResult]
    ) -> ProcessingResult:
        """Merge per-chunk generation results into one requirement result.

        Flattens successful chunk test-case lists, deduplicates across chunks,
        and renumbers `test_id` (per-chunk numbering restarts and would
        otherwise collide). Returns a structured error only when every chunk
        failed; a partial failure keeps the successful chunks and logs the rest.
        """
        merged: TestCaseList = []
        failures: list[dict[str, Any]] = []
        for result in chunk_results:
            if isinstance(result, list):
                merged.extend(result)
            else:
                failures.append(result)

        if not merged:
            return self._error_result(
                req_id,
                "AllChunksFailed",
                f"all {len(chunk_results)} table chunk(s) failed to generate test cases",
            )

        if self.enable_deduplication:
            merged, _ = self.deduplicator.deduplicate(merged, keep_strategy=self.keep_strategy)

        # Renumber across the merged set; per-chunk test_ids restart at 001.
        for i, test_case in enumerate(merged):
            test_case["requirement_id"] = req_id
            test_case["test_id"] = f"{req_id}_TC_{i + 1:03d}"

        if failures and self.logger:
            self.logger.warning(
                f"{len(failures)}/{len(chunk_results)} table chunks failed for {req_id}; "
                f"kept {len(merged)} test cases from the rest"
            )
        return merged


class TestCaseGenerator(_GeneratorCore):
    """Generates test cases from requirements using AI models (synchronous)."""

    __slots__ = ()

    _parser_class = JSONResponseParser

    def __init__(
        self,
        client: OllamaClient,
        yaml_manager: YAMLPromptManager | None = None,
        logger: FileProcessingLogger | None = None,
        validator: SemanticValidator | None = None,
        deduplicator: TestCaseDeduplicator | None = None,
        config: ConfigManager | None = None,
    ):
        super().__init__(client, yaml_manager, logger, validator, deduplicator, config)
        # Narrow the inherited union type: this subclass always holds a sync
        # OllamaClient, needed so its methods' plain (non-coroutine) return
        # types type-check (the base type also admits AsyncOllamaClient).
        self.client: OllamaClient = client

    def generate_test_cases_for_requirement(
        self, requirement: RequirementData, model: str, template_name: str | None = None
    ) -> ProcessingResult:
        """
        Generate test cases for a single requirement.

        Failures return structured error objects (EmptyResponse,
        InvalidJSONStructure, EmptyTestCasesList, or the exception type)
        instead of an empty list, so the standard processor can report
        partial completion (mirrors the async generator's contract).

        Args:
            requirement: The requirement data to process
            model: AI model to use for generation
            template_name: Optional specific template to use

        Returns:
            Either a list of test cases (success) or a structured error
            object (failure).
        """
        req_id = requirement.get("id", "UNKNOWN")

        # Oversized tables: generate over row-chunks so every row is covered,
        # then merge (archived finding 7). Each chunk fits the row limit, so
        # the recursive calls take the normal single-prompt path below.
        chunks = self._split_oversized_table(requirement)
        if chunks is not None:
            if self.logger:
                self.logger.info(
                    f"Table for {req_id} exceeds {self.prompt_builder.max_table_rows} rows; "
                    f"generating over {len(chunks)} chunk(s) for full coverage"
                )
            results = [
                self.generate_test_cases_for_requirement(chunk, model, template_name)
                for chunk in chunks
            ]
            return self._merge_chunk_results(req_id, results)

        try:
            # Build prompt using PromptBuilder
            prompt = self.prompt_builder.build_prompt(requirement, template_name)

            if self.logger:
                self.logger.debug(f"Generating test cases for {req_id}")

            # Extract image paths for vision model support
            image_paths = extract_image_paths(requirement)

            # Generate AI response (use vision-capable method if images present)
            start_time = time.time()

            if image_paths:
                if self.logger:
                    self.logger.debug(f"Using vision model with {len(image_paths)} image(s)")
                full_response = self.client.generate_response_with_vision(
                    model,
                    prompt,
                    image_paths,
                    is_json=True,
                    return_full_response=True,
                    format_schema=TEST_CASE_RESPONSE_JSON_SCHEMA,
                )
            else:
                full_response = self.client.generate_completion(
                    model,
                    prompt,
                    is_json=True,
                    return_full_response=True,
                    format_schema=TEST_CASE_RESPONSE_JSON_SCHEMA,
                )

            generation_time = time.time() - start_time

            response_text, confidence_score = self._extract_response_parts(full_response)

            # Empty-response check
            if not response_text or not response_text.strip():
                if self.logger:
                    self.logger.warning(f"Empty response for {req_id}")
                return self._error_result(
                    req_id, "EmptyResponse", "AI model returned empty response", generation_time
                )

            # Parse JSON response
            test_cases_data = self.json_parser.extract_json_from_response(response_text)

            if not test_cases_data or "test_cases" not in test_cases_data:
                if self.logger:
                    self.logger.warning(f"Invalid JSON structure for {req_id}")
                return self._error_result(
                    req_id,
                    "InvalidJSONStructure",
                    "Response does not contain 'test_cases' field",
                    generation_time,
                )

            test_cases = test_cases_data["test_cases"]

            if not test_cases:
                if self.logger:
                    self.logger.warning(f"Empty test cases list for {req_id}")
                return self._error_result(
                    req_id,
                    "EmptyTestCasesList",
                    "AI returned empty test cases list",
                    generation_time,
                )

            return self._postprocess_test_cases(
                test_cases, requirement, generation_time, confidence_score
            )

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error generating test cases for {req_id}: {e}")
            return self._error_result(req_id, type(e).__name__, str(e))


class AsyncTestCaseGenerator(_GeneratorCore):
    """Asynchronous test case generator for high-performance processing."""

    __slots__ = ()

    _parser_class = FastJSONResponseParser

    def __init__(
        self,
        client: AsyncOllamaClient,
        yaml_manager: YAMLPromptManager | None = None,
        logger: FileProcessingLogger | None = None,
        validator: SemanticValidator | None = None,
        deduplicator: TestCaseDeduplicator | None = None,
        config: ConfigManager | None = None,
    ):
        super().__init__(client, yaml_manager, logger, validator, deduplicator, config)
        # Narrow the inherited union type: this subclass always holds an
        # AsyncOllamaClient, needed so awaiting self.client's async methods
        # type-checks (the base type also admits the sync OllamaClient).
        self.client: AsyncOllamaClient = client
        # No semaphore here by design: concurrency limiting is handled by
        # AsyncOllamaClient's semaphore (a second one here would halve
        # throughput - see TestNoDoubleSemaphore)

    async def generate_test_cases(
        self, requirement: RequirementData, model: str, template_name: str | None = None
    ) -> ProcessingResult:
        """
        Generate test cases for a single requirement asynchronously.

        This is a public wrapper around the internal _generate_test_cases_for_requirement_async
        method, providing a clean API for single-requirement processing (used by HP processor).

        Args:
            requirement: Requirement data containing id, type, heading, text, etc.
            model: AI model identifier for generation
            template_name: Optional template for prompt customization

        Returns:
            Either a list of test cases (success) or structured error object (failure)
        """
        return await self._generate_test_cases_for_requirement_async(
            requirement, model, template_name
        )

    async def generate_test_cases_batch(
        self, requirements: list[RequirementData], model: str, template_name: str | None = None
    ) -> list[ProcessingResult]:
        """
        Generate test cases for multiple requirements concurrently.

        Tasks are created upfront and executed with asyncio.gather()
        (return_exceptions=True so one failure doesn't cancel the batch);
        exceptions are normalized into structured error objects so all
        results share the same interface.

        Args:
            requirements: List of requirements to process
            model: AI model to use for generation
            template_name: Optional template name for prompt formatting

        Returns:
            List of processing results (successful test cases or structured error objects)
        """
        tasks = []
        for requirement in requirements:
            # Each task will be executed concurrently, subject to semaphore limiting
            task = self._generate_test_cases_for_requirement_async(
                requirement, model, template_name
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results: list[ProcessingResult] = []
        for i, result in enumerate(results):
            req_id = requirements[i].get("id", "UNKNOWN")

            if isinstance(result, BaseException):
                # Exceptions that bubbled up from asyncio.gather() — typically
                # network errors, timeouts, or unexpected failures
                error_info = self._error_result(req_id, type(result).__name__, str(result))

                if self.logger:
                    self.logger.error(f"Failed to generate test cases for {req_id}: {result}")
                    self.logger.add_requirement_failure(req_id, str(result))

                processed_results.append(error_info)
            else:
                # Successful result or structured error object from the async
                # method — both already carry the consistent interface
                processed_results.append(result)

        return processed_results

    async def _generate_test_cases_for_requirement_async(
        self, requirement: RequirementData, model: str, template_name: str | None = None
    ) -> ProcessingResult:
        """
        Generate test cases for a single requirement asynchronously.

        Unlike the sync generator, failures return structured error objects
        (EmptyResponse, EmptyTestCasesList, InvalidJSONStructure, or the
        exception type) so the HP processor can categorize them.

        Args:
            requirement: Requirement data containing id, type, heading, text, etc.
            model: AI model identifier for generation
            template_name: Optional template for prompt customization

        Returns:
            Either a list of test cases (success) or structured error object (failure)
        """
        req_id = requirement.get("id", "UNKNOWN")

        # Oversized tables: generate over row-chunks so every row is covered,
        # then merge (archived finding 7). Each chunk fits the row limit, so
        # the recursive calls take the normal single-prompt path below.
        chunks = self._split_oversized_table(requirement)
        if chunks is not None:
            if self.logger:
                self.logger.info(
                    f"Table for {req_id} exceeds {self.prompt_builder.max_table_rows} rows; "
                    f"generating over {len(chunks)} chunk(s) for full coverage"
                )
            results = [
                await self._generate_test_cases_for_requirement_async(chunk, model, template_name)
                for chunk in chunks
            ]
            return self._merge_chunk_results(req_id, results)

        # Note: Concurrency control is handled by AsyncOllamaClient's semaphore
        try:
            prompt = self.prompt_builder.build_prompt(requirement, template_name)

            if self.logger:
                self.logger.info(f"Async generating test cases for {req_id}")

            # Extract image paths for vision model support
            image_paths = extract_image_paths(requirement)

            # AI response generation (use vision-capable method if images present)
            start_time = time.time()
            if image_paths:
                if self.logger:
                    self.logger.debug(
                        f"Using vision model with {len(image_paths)} image(s) for {req_id}"
                    )
                full_response = await self.client.generate_response_with_vision(
                    model,
                    prompt,
                    image_paths,
                    is_json=True,
                    return_full_response=True,
                    format_schema=TEST_CASE_RESPONSE_JSON_SCHEMA,
                )
            else:
                full_response = await self.client.generate_completion(
                    model,
                    prompt,
                    is_json=True,
                    return_full_response=True,
                    format_schema=TEST_CASE_RESPONSE_JSON_SCHEMA,
                )
            generation_time = time.time() - start_time

            response_text, confidence_score = self._extract_response_parts(full_response)

            # Record timing metrics for performance analysis and optimization
            if self.logger:
                self.logger.add_ai_response_time(generation_time)

            # Empty-response check
            if not response_text or not response_text.strip():
                if self.logger:
                    self.logger.warning(f"Empty response for {req_id}")
                    self.logger.add_requirement_failure(req_id, "Empty AI response")
                return self._error_result(
                    req_id, "EmptyResponse", "AI model returned empty response", generation_time
                )

            # JSON parsing and structure validation
            test_cases_data = self.json_parser.extract_json_from_response(response_text)

            if not test_cases_data or "test_cases" not in test_cases_data:
                if self.logger:
                    self.logger.warning(f"Invalid JSON structure for {req_id}")
                    self.logger.add_requirement_failure(req_id, "Invalid JSON structure")
                return self._error_result(
                    req_id,
                    "InvalidJSONStructure",
                    "Response does not contain 'test_cases' field",
                    generation_time,
                )

            test_cases = test_cases_data["test_cases"]

            # Validate that we actually got test cases, not just an empty array
            if not test_cases:
                if self.logger:
                    self.logger.warning(f"Empty test cases list for {req_id}")
                    self.logger.add_requirement_failure(req_id, "Empty test cases list")
                return self._error_result(
                    req_id,
                    "EmptyTestCasesList",
                    "AI returned empty test cases list",
                    generation_time,
                )

            # Shared pipeline: validate -> stamp -> deduplicate -> enrich
            return self._postprocess_test_cases(
                test_cases, requirement, generation_time, confidence_score
            )

        except Exception as e:
            if self.logger:
                self.logger.error(f"Exception generating test cases for {req_id}: {e}")
                self.logger.add_requirement_failure(req_id, str(e))
            return self._error_result(req_id, type(e).__name__, str(e))
