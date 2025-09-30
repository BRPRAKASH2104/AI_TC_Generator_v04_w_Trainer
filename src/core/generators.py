"""
Test case generators for the AI Test Case Generator.

This module provides classes for generating test cases from requirement artifacts
using AI models, with support for both synchronous and asynchronous processing.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from core.ollama_client import AsyncOllamaClient, OllamaClient
from core.parsers import FastJSONResponseParser, JSONResponseParser

# Type aliases for better readability (PEP 695 style)
type TestCaseData = dict[str, Any]
type TestCaseList = list[TestCaseData]
type RequirementData = dict[str, Any]
type ProcessingResult = TestCaseList | dict[str, Any]  # Can be test cases or error info


class TestCaseGenerator:
    """Generates test cases from requirements using AI models"""

    __slots__ = ("client", "json_parser", "yaml_manager", "logger")

    def __init__(self, client: OllamaClient, yaml_manager=None, logger=None):
        self.client = client
        self.json_parser = JSONResponseParser()
        self.yaml_manager = yaml_manager
        self.logger = logger

    def generate_test_cases_for_requirement(
        self,
        requirement: RequirementData,
        model: str,
        template_name: str = None
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
            # Get prompt template
            if self.yaml_manager:
                prompt = self._build_prompt_from_template(requirement, template_name)
            else:
                prompt = self._build_default_prompt(requirement)

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
                
                # Add metadata to each test case
                for i, test_case in enumerate(test_cases):
                    test_case["requirement_id"] = requirement.get("id", "UNKNOWN")
                    test_case["generation_time"] = generation_time
                    test_case["test_id"] = f"{requirement.get('id', 'UNKNOWN')}_TC_{i+1:03d}"
                
                if self.logger:
                    self.logger.info(f"Generated {len(test_cases)} test cases for {requirement.get('id', 'UNKNOWN')}")
                
                return test_cases
            else:
                if self.logger:
                    self.logger.warning(f"No test cases generated for {requirement.get('id', 'UNKNOWN')}")
                return []

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error generating test cases for {requirement.get('id', 'UNKNOWN')}: {e}")
            return []

    def _build_prompt_from_template(self, requirement: RequirementData, template_name: str = None) -> str:
        """Build prompt using YAML template manager"""
        try:
            # Prepare template variables with context information
            variables = {
                "requirement_id": requirement.get("id", "UNKNOWN"),
                "heading": requirement.get("heading", ""),
                "requirement_text": requirement.get("text", ""),
                "table_str": self._format_table_for_prompt(requirement.get("table")),
                "row_count": requirement.get("table", {}).get("rows", 0) if requirement.get("table") else 0,
                "voltage_precondition": "1. Voltage= 12V\n2. Bat-ON",  # Default automotive precondition
                # Context-aware fields (v03 restoration)
                "info_str": self._format_info_for_prompt(requirement.get("info_list", [])),
                "interface_str": self._format_interfaces_for_prompt(requirement.get("interface_list", []))
            }

            # Use template manager to get formatted prompt
            if template_name:
                return self.yaml_manager.get_test_prompt(template_name, **variables)
            else:
                return self.yaml_manager.get_test_prompt(**variables)

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error building template prompt: {e}, using default")
            return self._build_default_prompt(requirement)

    def _build_default_prompt(self, requirement: RequirementData) -> str:
        """Build a default prompt when template system is not available"""
        req_id = requirement.get("id", "UNKNOWN")
        heading = requirement.get("heading", "")
        text = requirement.get("text", "")
        
        prompt = f"""Generate comprehensive test cases for the following automotive requirement:

Requirement ID: {req_id}
Heading: {heading}
Description: {text}

Please generate test cases in JSON format with the following structure:
{{
    "test_cases": [
        {{
            "summary": "Brief test case description",
            "action": "Detailed test steps",
            "data": "Test data and inputs",
            "expected_result": "Expected outcome"
        }}
    ]
}}

Focus on:
- Boundary value testing
- Positive and negative scenarios
- Automotive-specific conditions (voltage levels, temperature ranges)
- Safety and security considerations

Ensure each test case is detailed and executable."""

        return prompt

    def _format_table_for_prompt(self, table_data: dict[str, Any] | None) -> str:
        """Format table data for inclusion in prompts"""
        if not table_data or "data" not in table_data:
            return "No table data available"

        try:
            rows = table_data["data"]
            if not rows:
                return "Empty table"

            # Get headers from first row
            headers = list(rows[0].keys()) if rows else []

            # Format as simple table
            formatted = "Table Data:\n"
            formatted += " | ".join(headers) + "\n"
            formatted += "-" * (len(" | ".join(headers))) + "\n"

            for row in rows[:10]:  # Limit to first 10 rows
                values = [str(row.get(header, "")) for header in headers]
                formatted += " | ".join(values) + "\n"

            if len(rows) > 10:
                formatted += f"... ({len(rows) - 10} more rows)\n"

            return formatted

        except Exception as e:
            return f"Error formatting table: {e}"

    def _format_info_for_prompt(self, info_list: list[dict[str, Any]]) -> str:
        """
        Format information list for inclusion in prompt (v03 restoration)

        Args:
            info_list: List of information artifacts collected since last heading

        Returns:
            Formatted string for prompt template
        """
        if not info_list:
            return "None"

        return "\n".join([f"- {info.get('text', '')}" for info in info_list])

    def _format_interfaces_for_prompt(self, interface_list: list[dict[str, Any]]) -> str:
        """
        Format system interface list for inclusion in prompt (v03 restoration)

        Args:
            interface_list: List of system interface artifacts (global context)

        Returns:
            Formatted string for prompt template
        """
        if not interface_list:
            return "None"

        return "\n".join([f"- {interface.get('id', 'UNKNOWN')}: {interface.get('text', '')}"
                         for interface in interface_list])


class AsyncTestCaseGenerator:
    """Asynchronous test case generator for high-performance processing"""

    __slots__ = ("client", "json_parser", "yaml_manager", "logger", "semaphore")

    def __init__(self, client: AsyncOllamaClient, yaml_manager=None, logger=None, max_concurrent: int = 4):
        self.client = client
        self.json_parser = FastJSONResponseParser()
        self.yaml_manager = yaml_manager
        self.logger = logger
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def generate_test_cases_batch(
        self,
        requirements: list[RequirementData],
        model: str,
        template_name: str = None
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
                    "test_cases": []  # Consistent interface: always provide test_cases list
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
        self,
        requirement: RequirementData,
        model: str,
        template_name: str = None
    ) -> ProcessingResult:
        """
        Generate test cases for a single requirement asynchronously with comprehensive error handling.

        This method implements a sophisticated async processing pipeline:
        1. Semaphore-controlled concurrency to prevent API overload
        2. Prompt generation with template system integration
        3. Async AI API communication with timing metrics
        4. Multi-layered response validation and error categorization
        5. Structured error objects that maintain consistent interfaces

        Args:
            requirement: Requirement data containing id, type, heading, text, etc.
            model: AI model identifier for generation
            template_name: Optional template for prompt customization

        Returns:
            Either a list of test cases (success) or structured error object (failure)
            Both maintain the same interface with test_cases field for consistency
        """
        req_id = requirement.get('id', 'UNKNOWN')

        # Semaphore controls concurrent API requests to prevent overwhelming the AI service
        # This is critical for maintaining stable performance under high load
        async with self.semaphore:
            try:
                # Phase 1: Prompt Construction
                # We reuse the synchronous prompt building logic to maintain consistency
                # between sync and async processing paths
                sync_generator = TestCaseGenerator(None, self.yaml_manager, self.logger)

                if self.yaml_manager:
                    # Use template system for structured, customizable prompts
                    prompt = sync_generator._build_prompt_from_template(requirement, template_name)
                else:
                    # Fallback to default prompt if template system unavailable
                    prompt = sync_generator._build_default_prompt(requirement)

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
                        "test_cases": []  # Maintain consistent interface
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
                            "error_type": "NoTestCases",
                            "error_message": "AI response contained empty test_cases array",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "generation_time": generation_time,
                            "test_cases": []
                        }

                        if self.logger:
                            self.logger.warning(f"Empty test cases array for {req_id}")
                            self.logger.add_requirement_failure(req_id, "Empty test cases array")

                        return error_info

                    # Phase 5: Test Case Enrichment and Metadata Addition
                    # Add traceability and metadata to each generated test case
                    for i, test_case in enumerate(test_cases):
                        # Ensure traceability back to source requirement
                        test_case["requirement_id"] = req_id
                        test_case["generation_time"] = generation_time

                        # Generate unique test case ID with consistent format
                        test_case["test_id"] = f"{req_id}_TC_{i+1:03d}"

                        # Track which model and template were used for debugging
                        test_case["model_used"] = model
                        test_case["template_used"] = template_name or "default"

                    if self.logger:
                        self.logger.info(f"✅ Generated {len(test_cases)} test cases for {req_id}")

                    return test_cases
                else:
                    # Phase 6: JSON Parsing Failure Handling
                    # Handle cases where JSON parsing failed or structure is invalid
                    error_info = {
                        "error": True,
                        "requirement_id": req_id,
                        "error_type": "InvalidJSONResponse",
                        "error_message": "Could not parse test_cases from AI response",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "generation_time": generation_time,
                        # Include truncated raw response for debugging (avoid logging sensitive data)
                        "raw_response": response[:200] + "..." if len(response) > 200 else response,
                        "test_cases": []
                    }

                    if self.logger:
                        self.logger.warning(f"Invalid JSON response for {req_id}: {response[:100]}...")
                        self.logger.add_requirement_failure(req_id, "Invalid JSON response format")

                    return error_info

            except asyncio.TimeoutError as e:
                # Handle timeout errors specifically - these are common in async processing
                # and should be handled gracefully without crashing the entire batch
                error_info = {
                    "error": True,
                    "requirement_id": req_id,
                    "error_type": "TimeoutError",
                    "error_message": f"AI request timed out: {str(e)}",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "test_cases": []
                }

                if self.logger:
                    self.logger.error(f"⏱️  Timeout error for {req_id}: {e}")
                    self.logger.add_requirement_failure(req_id, f"Timeout: {str(e)}")

                return error_info

            except Exception as e:
                # Catch-all for any other unexpected errors during processing
                # This ensures the async batch processing continues even if individual
                # requirements fail due to network issues, API errors, etc.
                error_info = {
                    "error": True,
                    "requirement_id": req_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "test_cases": []
                }

                if self.logger:
                    self.logger.error(f"💥 Unexpected error for {req_id}: {e}")
                    self.logger.add_requirement_failure(req_id, str(e))

                return error_info