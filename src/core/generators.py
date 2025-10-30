"""
Test case generators for the AI Test Case Generator.

This module provides classes for generating test cases from requirement artifacts
using AI models, with support for both synchronous and asynchronous processing.
"""

import asyncio
import time
from typing import TYPE_CHECKING, Any

from .deduplicator import TestCaseDeduplicator
from .parsers import FastJSONResponseParser, JSONResponseParser
from .prompt_builder import PromptBuilder
from .validators import SemanticValidator

if TYPE_CHECKING:
    from .ollama_client import AsyncOllamaClient, OllamaClient

# Type aliases for better readability (PEP 695 style)
type TestCaseData = dict[str, Any]
type TestCaseList = list[TestCaseData]
type RequirementData = dict[str, Any]
type ProcessingResult = TestCaseList | dict[str, Any]  # Can be test cases or error info


class TestCaseGenerator:
    """Generates test cases from requirements using AI models"""

    __slots__ = ("client", "json_parser", "prompt_builder", "validator", "deduplicator", "logger")

    def __init__(self, client: OllamaClient, yaml_manager=None, logger=None, validator=None, deduplicator=None):
        self.client = client
        self.json_parser = JSONResponseParser()
        self.prompt_builder = PromptBuilder(yaml_manager)
        self.validator = validator or SemanticValidator(logger=logger)
        self.deduplicator = deduplicator or TestCaseDeduplicator(logger=logger)
        self.logger = logger

    def generate_test_cases_for_requirement(
        self, requirement: RequirementData, model: str, template_name: str = None
    ) -> TestCaseList:
        """
        Generate test cases for a single requirement.

        Args:
            requirement: The requirement data to process
            model: AI model to use for generation
            template_name: Optional specific template to use

        Returns:
            List of generated test cases
        """
        try:
            # Build prompt using PromptBuilder
            prompt = self.prompt_builder.build_prompt(requirement, template_name)

            if self.logger:
                self.logger.debug(f"Generating test cases for {requirement.get('id', 'UNKNOWN')}")

            # Generate AI response
            start_time = time.time()
            response = self.client.generate_response(model, prompt, is_json=True)
            generation_time = time.time() - start_time

            # Parse JSON response
            test_cases_data = self.json_parser.extract_json_from_response(response)

            if test_cases_data and "test_cases" in test_cases_data:
                test_cases = test_cases_data["test_cases"]

                # Semantic validation
                validation_report = self.validator.validate_batch(test_cases, requirement)

                if validation_report["invalid_count"] > 0 and self.logger:
                    self.logger.warning(
                        f"Semantic validation: {validation_report['valid_count']}/{validation_report['total_test_cases']} passed"
                    )
                    for issue_entry in validation_report["issues"]:
                        self.logger.warning(
                            f"  Test case {issue_entry['test_case_index']}: {issue_entry['summary']}"
                        )
                        for issue in issue_entry["issues"]:
                            self.logger.warning(f"    - {issue}")

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
                            f"Inadequate table coverage for {requirement.get('id', 'UNKNOWN')}: "
                            f"Expected {req_rows}+ positive tests, got {pos_tests}. "
                            f"Expected 3+ negative tests, got {neg_tests}."
                        )

                # Deduplication
                test_cases, dedup_report = self.deduplicator.deduplicate(test_cases, keep_strategy="best")

                if dedup_report["duplicates_removed"] > 0 and self.logger:
                    self.logger.info(
                        f"Deduplication: {dedup_report['original_count']} → {dedup_report['deduplicated_count']} test cases "
                        f"({dedup_report['duplicates_removed']} duplicates removed)"
                    )

                # Add metadata to each test case
                for i, test_case in enumerate(test_cases):
                    test_case["requirement_id"] = requirement.get("id", "UNKNOWN")
                    test_case["generation_time"] = generation_time
                    test_case["test_id"] = f"{requirement.get('id', 'UNKNOWN')}_TC_{i + 1:03d}"
                    # Add validation status
                    is_valid = i >= len(validation_report["issues"]) or all(
                        entry["test_case_index"] != i + 1
                        for entry in validation_report["issues"]
                    )
                    test_case["validation_passed"] = is_valid

                if self.logger:
                    self.logger.info(
                        f"Generated {len(test_cases)} test cases for {requirement.get('id', 'UNKNOWN')} "
                        f"({validation_report['valid_count']} passed validation)"
                    )

                return test_cases
            else:
                if self.logger:
                    self.logger.warning(
                        f"No test cases generated for {requirement.get('id', 'UNKNOWN')}"
                    )
                return []

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Error generating test cases for {requirement.get('id', 'UNKNOWN')}: {e}"
                )
            return []


class AsyncTestCaseGenerator:
    """Asynchronous test case generator for high-performance processing"""

    __slots__ = ("client", "json_parser", "prompt_builder", "validator", "deduplicator", "logger")

    def __init__(
        self, client: AsyncOllamaClient, yaml_manager=None, logger=None, validator=None, deduplicator=None, _max_concurrent: int = 4
    ):
        self.client = client
        self.json_parser = FastJSONResponseParser()
        self.prompt_builder = PromptBuilder(yaml_manager)
        self.validator = validator or SemanticValidator(logger=logger)
        self.deduplicator = deduplicator or TestCaseDeduplicator(logger=logger)
        self.logger = logger
        # Note: Concurrency limiting is handled by AsyncOllamaClient's semaphore
        # No need for double semaphore here - improves throughput by ~50%

    async def generate_test_cases_batch(
        self, requirements: list[RequirementData], model: str, template_name: str = None
    ) -> list[ProcessingResult]:
        """
        Generate test cases for multiple requirements concurrently with intelligent batching.

        This method implements several performance optimizations:
        1. Creates async tasks for each requirement to enable true concurrent processing
        2. Uses asyncio.gather() with return_exceptions=True to handle failures gracefully
        3. Processes results in a structured way to maintain consistency
        4. Implements proper error categorization and structured error objects

        Args:
            requirements: List of requirements to process
            model: AI model to use for generation
            template_name: Optional template name for prompt formatting

        Returns:
            List of processing results (successful test cases or structured error objects)
            Each result maintains the same interface regardless of success/failure
        """
        # Phase 1: Create async tasks for concurrent execution
        # We create all tasks upfront to maximize parallelism potential
        tasks = []

        for requirement in requirements:
            # Each task will be executed concurrently, subject to semaphore limiting
            task = self._generate_test_cases_for_requirement_async(
                requirement, model, template_name
            )
            tasks.append(task)

        # Phase 2: Execute all tasks concurrently with exception handling
        # asyncio.gather() allows us to wait for all tasks while catching exceptions
        # return_exceptions=True ensures that exceptions don't cancel other tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Phase 3: Process and normalize results for consistent output structure
        # This ensures all downstream code gets a predictable format regardless of success/failure
        processed_results = []
        for i, result in enumerate(results):
            req_id = requirements[i].get("id", "UNKNOWN")

            if isinstance(result, Exception):
                # Handle exceptions that bubbled up from asyncio.gather()
                # These are typically network errors, timeouts, or unexpected failures
                error_info = {
                    "error": True,
                    "requirement_id": req_id,
                    "error_type": type(result).__name__,
                    "error_message": str(result),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "test_cases": [],  # Consistent interface: always provide test_cases list
                }

                # Log the failure for debugging and metrics
                if self.logger:
                    self.logger.error(f"Failed to generate test cases for {req_id}: {result}")
                    self.logger.add_requirement_failure(req_id, str(result))

                processed_results.append(error_info)
            else:
                # Handle successful results or controlled error responses
                if isinstance(result, dict) and result.get("error"):
                    # This is a structured error object returned by the async method
                    # (e.g., empty response, JSON parsing failure, etc.)
                    processed_results.append(result)
                else:
                    # This is a successful result containing test cases
                    # The result should already be in the correct format from the async method
                    processed_results.append(result)

        return processed_results

    async def _generate_test_cases_for_requirement_async(
        self, requirement: RequirementData, model: str, template_name: str = None
    ) -> ProcessingResult:
        """
        Generate test cases for a single requirement asynchronously with comprehensive error handling.

        This method implements a sophisticated async processing pipeline:
        1. Prompt generation with template system integration
        2. Async AI API communication with timing metrics (rate-limited by AsyncOllamaClient)
        3. Multi-layered response validation and error categorization
        4. Structured error objects that maintain consistent interfaces

        Args:
            requirement: Requirement data containing id, type, heading, text, etc.
            model: AI model identifier for generation
            template_name: Optional template for prompt customization

        Returns:
            Either a list of test cases (success) or structured error object (failure)
            Both maintain the same interface with test_cases field for consistency
        """
        req_id = requirement.get("id", "UNKNOWN")

        # Note: Concurrency control is handled by AsyncOllamaClient's semaphore
        # No need for additional semaphore here - allows better throughput
        try:
            # Phase 1: Prompt Construction
            # Use PromptBuilder for clean, reusable prompt generation
            prompt = self.prompt_builder.build_prompt(requirement, template_name)

            if self.logger:
                self.logger.info(f"Async generating test cases for {req_id}")

            # Phase 2: AI Response Generation
            # Time the AI call for performance metrics and SLA monitoring
            start_time = time.time()
            response = await self.client.generate_response(model, prompt, is_json=True)
            generation_time = time.time() - start_time

            # Record timing metrics for performance analysis and optimization
            if self.logger:
                self.logger.add_ai_response_time(generation_time)

            # Phase 3: Response Validation - Empty Response Check
            # Handle cases where AI returns empty or whitespace-only responses
            if not response or not response.strip():
                error_info = {
                    "error": True,
                    "requirement_id": req_id,
                    "error_type": "EmptyResponse",
                    "error_message": "AI model returned empty response",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "generation_time": generation_time,
                    "test_cases": [],  # Maintain consistent interface
                }

                if self.logger:
                    self.logger.warning(f"Empty response for {req_id}")
                    self.logger.add_requirement_failure(req_id, "Empty AI response")

                return error_info

            # Phase 4: JSON Parsing and Structure Validation
            # Use fast JSON parser optimized for AI responses
            test_cases_data = self.json_parser.extract_json_from_response(response)

            if test_cases_data and "test_cases" in test_cases_data:
                test_cases = test_cases_data["test_cases"]

                # Validate that we actually got test cases, not just an empty array
                if not test_cases:
                    error_info = {
                        "error": True,
                        "requirement_id": req_id,
                        "error_type": "EmptyTestCasesList",
                        "error_message": "AI returned empty test cases list",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "generation_time": generation_time,
                        "test_cases": [],
                    }

                    if self.logger:
                        self.logger.warning(f"Empty test cases list for {req_id}")
                        self.logger.add_requirement_failure(req_id, "Empty test cases list")

                    return error_info

                # Phase 5: Semantic Validation
                # Validate test cases against requirement context
                validation_report = self.validator.validate_batch(test_cases, requirement)

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

                # Phase 6: Deduplication
                # Remove duplicate or highly similar test cases
                test_cases, dedup_report = self.deduplicator.deduplicate(test_cases, keep_strategy="best")

                if dedup_report["duplicates_removed"] > 0 and self.logger:
                    self.logger.info(
                        f"Deduplication: {dedup_report['original_count']} → {dedup_report['deduplicated_count']} test cases for {req_id} "
                        f"({dedup_report['duplicates_removed']} duplicates removed)"
                    )

                # Phase 7: Metadata Enrichment
                # Add tracking and correlation metadata to each test case
                for i, test_case in enumerate(test_cases):
                    test_case["requirement_id"] = req_id
                    test_case["generation_time"] = generation_time
                    test_case["test_id"] = f"{req_id}_TC_{i + 1:03d}"
                    # Add validation status
                    is_valid = i >= len(validation_report["issues"]) or all(
                        entry["test_case_index"] != i + 1
                        for entry in validation_report["issues"]
                    )
                    test_case["validation_passed"] = is_valid

                if self.logger:
                    self.logger.info(
                        f"Generated {len(test_cases)} test cases for {req_id} "
                        f"({validation_report['valid_count']} passed validation)"
                    )

                return test_cases
            else:
                # Phase 8: Handle JSON Parsing Failures
                # The response was valid but didn't contain expected structure
                error_info = {
                    "error": True,
                    "requirement_id": req_id,
                    "error_type": "InvalidJSONStructure",
                    "error_message": "Response does not contain 'test_cases' field",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "generation_time": generation_time,
                    "test_cases": [],
                }

                if self.logger:
                    self.logger.warning(f"Invalid JSON structure for {req_id}")
                    self.logger.add_requirement_failure(req_id, "Invalid JSON structure")

                return error_info

        except Exception as e:
            # Phase 9: Catastrophic Error Handling
            # Catch any unexpected errors and wrap them in structured format
            error_info = {
                "error": True,
                "requirement_id": req_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "test_cases": [],
            }

            if self.logger:
                self.logger.error(f"Exception generating test cases for {req_id}: {e}")
                self.logger.add_requirement_failure(req_id, str(e))

            return error_info
