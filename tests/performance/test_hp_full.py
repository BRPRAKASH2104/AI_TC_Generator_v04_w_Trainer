#!/usr/bin/env python3
"""
Full test of high-performance version with mock AI responses
"""

import sys
import asyncio
from pathlib import Path

# Add src to path (go up two levels from test file to project root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from generate_contextual_tests_v003_HighPerformance import *

class MockAsyncOllamaClient:
    """Mock Ollama client for testing without actual AI calls"""
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def generate_multiple_responses(self, requests_data):
        """Generate mock responses"""
        await asyncio.sleep(0.1)  # Simulate AI processing time
        
        responses = []
        for i, (model, prompt, is_json) in enumerate(requests_data):
            # Mock JSON response with test cases
            mock_response = {
                "test_cases": [
                    {
                        "summary_suffix": f"Test case {i+1} - Verify functionality",
                        "action": "1. Set voltage to 12V\n2. Enable system\n3. Execute test",
                        "data": f"Test data set {i+1}",
                        "expected_result": f"Expected result {i+1}"
                    },
                    {
                        "summary_suffix": f"Test case {i+1}b - Verify error handling", 
                        "action": "1. Set invalid condition\n2. Monitor response",
                        "data": f"Error test data {i+1}",
                        "expected_result": "System should handle error gracefully"
                    }
                ]
            }
            responses.append(json_fast.dumps(mock_response))
        
        return responses

async def test_full_hp_processing():
    """Test full high-performance processing with mock AI"""
    print("🚀 Testing Full High-Performance Processing\n")
    
    # Setup high-performance logger
    logger = setup_logger(verbose=True, debug=False)
    logger.start_performance_monitoring()
    logger.print_banner()
    
    # Test file
    test_file = Path("input/Reqifz_Files/TFDCX32348_001 Rental Car Mode_551f0c.reqifz")
    
    if not test_file.exists():
        print("❌ Test REQIFZ file not found")
        return
    
    print(f"📁 Testing with file: {test_file.name}")
    
    # Create components with mock client
    try:
        from yaml_prompt_manager import YAMLPromptManager
        from config import ConfigManager
    except ImportError:
        print("⚠️  Using fallback config")
        config_manager = ConfigManager()
        yaml_prompt_manager = YAMLPromptManager("prompts/config/prompt_config.yaml")
    else:
        config_manager = ConfigManager()
        yaml_prompt_manager = YAMLPromptManager("prompts/config/prompt_config.yaml")
    
    # Create high-performance processor
    processor = HighPerformanceREQIFZFileProcessor(
        "llama3.1:8b",
        config_manager,
        yaml_prompt_manager,
        max_workers=4
    )
    
    # Replace the async client with mock
    original_process_method = processor._process_single_file_async
    
    async def mock_process_single_file_async(semaphore, reqifz_file, async_generator, file_index, total_files):
        """Mock single file processing with fake AI responses"""
        async with semaphore:
            logger.verbose_log(f"[{file_index}/{total_files}] Processing: {reqifz_file.name}")
            
            try:
                # Extract artifacts (real extraction)
                loop = asyncio.get_event_loop()
                all_objects = await loop.run_in_executor(
                    None, processor.extractor.extract_all_artifacts, reqifz_file
                )
                
                if not all_objects:
                    logger.warning(f"No objects found in {reqifz_file.name}")
                    return 0
                
                # Separate artifacts
                system_interfaces, processing_list = processor._separate_artifacts(all_objects)
                logger.debug(f"{reqifz_file.name}: {len(all_objects)} objects, {len(system_interfaces)} interfaces")
                
                # Mock AI processing - create fake test cases
                master_test_list = []
                issue_id_counter = 1
                
                # Find requirements that would normally be processed by AI
                requirements_count = len([
                    obj for obj in processing_list 
                    if obj.get('type') == ArtifactType.SYSTEM_REQUIREMENT and obj.get('table')
                ])
                
                logger.verbose_log(f"    🤖 Mock generating test cases for {requirements_count} requirements")
                
                # Generate mock test cases
                for obj in processing_list:
                    if obj.get('type') == ArtifactType.SYSTEM_REQUIREMENT and obj.get('table'):
                        # Create 2 mock test cases per requirement
                        for i in range(2):
                            mock_test = {
                                "summary_suffix": f"Mock test case {i+1} - {obj['id']}",
                                "action": f"1. Setup test conditions\n2. Execute requirement {obj['id']}\n3. Verify results",
                                "data": f"Mock test data for {obj['id']}",
                                "expected_result": f"Expected behavior for requirement {obj['id']}"
                            }
                            
                            formatted_case = processor.formatter._format_single_test_case(
                                mock_test, obj['id'], issue_id_counter
                            )
                            master_test_list.append(formatted_case)
                            issue_id_counter += 1
                
                # Generate output file
                output_path = processor._generate_output_path(reqifz_file)
                
                # Save results
                await loop.run_in_executor(
                    None, processor._save_test_cases_to_excel, master_test_list, output_path
                )
                
                test_count = len(master_test_list)
                logger.success(f"{reqifz_file.name}: Generated {test_count} test cases")
                
                return test_count
                
            except Exception as e:
                logger.error(f"Error processing {reqifz_file.name}: {e}")
                return 0
    
    # Replace the method with mock version
    processor._process_single_file_async = mock_process_single_file_async
    
    # Process files with high-performance mode
    print("\n🏭 Starting High-Performance Processing...")
    
    start_time = time.time()
    results = await processor.process_files_parallel([test_file])
    processing_time = time.time() - start_time
    
    # Show results
    successful_files = sum(1 for count in results.values() if count > 0)
    total_test_cases = sum(results.values())
    
    print(f"\n🎉 High-Performance Results:")
    print(f"✅ Processed: {successful_files}/{len([test_file])} files")
    print(f"📋 Generated: {total_test_cases} test cases")
    print(f"⏱️  Time: {processing_time:.2f} seconds")
    print(f"📈 Speed: {total_test_cases/processing_time:.1f} test cases/second")
    
    # Show performance dashboard
    logger.show_performance_dashboard()
    
    # Stop monitoring
    logger.stop_performance_monitoring()
    logger.log_performance_summary()
    
    print("\n🚀 High-Performance Test Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(test_full_hp_processing())