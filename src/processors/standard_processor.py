"""
Standard processor for the AI Test Case Generator.

This module provides the standard synchronous processing workflow that orchestrates
the core components to process REQIFZ files and generate test cases.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from config import ConfigManager
from core.extractors import REQIFArtifactExtractor
from core.formatters import TestCaseFormatter
from core.generators import TestCaseGenerator
from core.ollama_client import OllamaClient
from file_processing_logger import FileProcessingLogger
from yaml_prompt_manager import YAMLPromptManager

# Type aliases
type ProcessingResult = dict[str, Any]


class REQIFZFileProcessor:
    """Standard processor for REQIFZ files using synchronous processing"""

    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = FileProcessingLogger("standard_processor")
        
        # Initialize core components
        self.extractor = REQIFArtifactExtractor(self.logger)
        self.ollama_client = OllamaClient(self.config.ollama)
        self.yaml_manager = YAMLPromptManager()
        self.generator = TestCaseGenerator(
            self.ollama_client, 
            self.yaml_manager, 
            self.logger
        )
        self.formatter = TestCaseFormatter(self.config, self.logger)

    def process_file(
        self,
        reqifz_path: Path,
        model: str = "llama3.1:8b",
        template: str = None,
        output_dir: Path = None
    ) -> ProcessingResult:
        """
        Process a single REQIFZ file and generate test cases.
        
        Args:
            reqifz_path: Path to the REQIFZ file
            model: AI model to use for generation
            template: Optional template name
            output_dir: Optional output directory (defaults to same as input)
            
        Returns:
            Processing result with statistics and file paths
        """
        start_time = time.time()
        
        self.logger.info(f"🔍 Processing: {reqifz_path.name}")
        self.logger.info(f"🤖 Model: {model}")
        
        try:
            # Step 1: Extract artifacts from REQIFZ
            self.logger.info("📂 Extracting artifacts from REQIFZ file...")
            artifacts = self.extractor.extract_reqifz_content(reqifz_path)
            
            if not artifacts:
                return {
                    "success": False,
                    "error": "No artifacts found in REQIFZ file",
                    "processing_time": time.time() - start_time
                }
            
            # Step 2: Classify artifacts by type
            classified_artifacts = self.extractor.classify_artifacts(artifacts)
            
            # Step 3: Generate test cases for System Requirements
            system_requirements = classified_artifacts.get("System Requirement", [])
            
            if not system_requirements:
                self.logger.warning("No System Requirements found for test generation")
                return {
                    "success": False,
                    "error": "No System Requirements found",
                    "processing_time": time.time() - start_time
                }
            
            self.logger.info(f"🎯 Generating test cases for {len(system_requirements)} requirements...")
            
            all_test_cases = []
            successful_requirements = 0
            
            for requirement in system_requirements:
                req_id = requirement.get("id", "UNKNOWN")
                self.logger.info(f"⚡ Processing requirement: {req_id}")
                
                test_cases = self.generator.generate_test_cases_for_requirement(
                    requirement, model, template
                )
                
                if test_cases:
                    all_test_cases.extend(test_cases)
                    successful_requirements += 1
                    self.logger.info(f"✅ Generated {len(test_cases)} test cases for {req_id}")
                else:
                    self.logger.warning(f"⚠️  No test cases generated for {req_id}")
            
            if not all_test_cases:
                return {
                    "success": False,
                    "error": "No test cases were generated",
                    "processing_time": time.time() - start_time
                }
            
            # Step 4: Format and save to Excel
            output_directory = output_dir or reqifz_path.parent
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
            model_safe = model.replace(":", "_").replace("/", "_")
            
            output_filename = f"{reqifz_path.stem}_TCD_{model_safe}_{timestamp}.xlsx"
            output_path = output_directory / output_filename
            
            self.logger.info(f"📝 Formatting {len(all_test_cases)} test cases to Excel...")
            
            metadata = {
                "model": model,
                "template": template or "auto-selected",
                "source_file": str(reqifz_path),
                "total_cases": len(all_test_cases),
                "requirements_processed": len(system_requirements),
                "successful_requirements": successful_requirements
            }
            
            success = self.formatter.format_to_excel(all_test_cases, output_path, metadata)
            
            if not success:
                return {
                    "success": False,
                    "error": "Failed to save Excel file",
                    "processing_time": time.time() - start_time
                }
            
            # Step 5: Generate processing summary
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "output_file": str(output_path),
                "total_test_cases": len(all_test_cases),
                "requirements_processed": len(system_requirements),
                "successful_requirements": successful_requirements,
                "artifacts_found": len(artifacts),
                "processing_time": processing_time,
                "model_used": model,
                "template_used": template or "auto-selected"
            }
            
            self.logger.info(f"🎉 Processing complete!")
            self.logger.info(f"📊 Generated {len(all_test_cases)} test cases in {processing_time:.2f}s")
            self.logger.info(f"📁 Saved to: {output_path.name}")
            
            return result

        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "processing_time": time.time() - start_time
            }

    def process_directory(
        self,
        input_dir: Path,
        model: str = "llama3.1:8b",
        template: str = None,
        output_dir: Path = None
    ) -> list[ProcessingResult]:
        """
        Process all REQIFZ files in a directory.
        
        Args:
            input_dir: Directory containing REQIFZ files
            model: AI model to use
            template: Optional template name
            output_dir: Optional output directory
            
        Returns:
            List of processing results
        """
        self.logger.info(f"🔍 Scanning directory: {input_dir}")
        
        # Find all REQIFZ files
        reqifz_files = list(input_dir.glob("*.reqifz"))
        
        if not reqifz_files:
            self.logger.warning("No REQIFZ files found in directory")
            return []
        
        self.logger.info(f"📁 Found {len(reqifz_files)} REQIFZ file(s)")
        
        results = []
        
        for i, reqifz_file in enumerate(reqifz_files, 1):
            self.logger.info(f"\n🔄 Processing file {i}/{len(reqifz_files)}: {reqifz_file.name}")
            
            result = self.process_file(reqifz_file, model, template, output_dir)
            results.append(result)
            
            if result["success"]:
                self.logger.info(f"✅ File {i} completed successfully")
            else:
                self.logger.error(f"❌ File {i} failed: {result.get('error', 'Unknown error')}")
        
        # Summary
        successful = sum(1 for r in results if r["success"])
        total_test_cases = sum(r.get("total_test_cases", 0) for r in results if r["success"])
        total_time = sum(r.get("processing_time", 0) for r in results)
        
        self.logger.info(f"\n🏁 Batch Processing Complete!")
        self.logger.info(f"📊 Files processed: {successful}/{len(reqifz_files)}")
        self.logger.info(f"📋 Total test cases generated: {total_test_cases}")
        self.logger.info(f"⏱️  Total processing time: {total_time:.2f}s")
        
        return results

    def validate_environment(self) -> bool:
        """Validate that the processing environment is ready"""
        try:
            # Test YAML manager
            templates = self.yaml_manager.test_prompts
            if not templates:
                self.logger.error("No prompt templates available")
                return False
            
            # Test Ollama connection (basic check)
            # Could add actual API call here if needed
            
            self.logger.info("✅ Environment validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Environment validation failed: {e}")
            return False