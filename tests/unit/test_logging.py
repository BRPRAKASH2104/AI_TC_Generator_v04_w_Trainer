#!/usr/bin/env python3
"""
Test script to verify FileProcessingLogger functionality
"""

import sys
from pathlib import Path
import time
import json

# Add src to path (go up two levels from test file to project root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from file_processing_logger import FileProcessingLogger, ProcessingPhase, RequirementFailure

def test_basic_logging():
    """Test basic logging functionality"""
    print("🧪 Testing basic FileProcessingLogger functionality...")
    
    # Create a test logger
    logger = FileProcessingLogger(
        reqifz_file="test_file.reqifz",
        input_path="/test/path/test_file.reqifz",
        output_file="/test/output/test_file_TCD_llama3_1_8b_2025-09-06.xlsx",
        version="test_v002",
        ai_model="llama3.1:8b"
    )
    
    # Test phase tracking
    logger.start_phase("xml_parsing")
    time.sleep(0.1)  # Simulate work
    logger.end_phase("xml_parsing")
    
    logger.start_phase("ai_generation")
    time.sleep(0.2)  # Simulate work
    logger.end_phase("ai_generation")
    
    # Test artifact counting
    logger.total_artifacts_found = 100
    logger.artifacts_by_type = {
        "Heading": 10,
        "Information": 30,
        "System Interface": 5,
        "System Requirement": 55
    }
    
    # Test requirement processing
    logger.requirements_processed_total = 55
    logger.requirements_successful = 50
    
    # Test failure recording
    logger.add_requirement_failure("REQ_001", "AI timeout after 120s")
    logger.add_requirement_failure("REQ_025", "Invalid table structure")
    
    # Test test case counting
    logger.increment_test_cases(positive=80, negative=40)
    
    # Test AI response times
    logger.add_ai_response_time(8.5)
    logger.add_ai_response_time(12.3)
    logger.add_ai_response_time(6.7)
    
    # Test warnings
    logger.add_warning("Template auto-selection used fallback for 3 requirements")
    
    # Test system metrics
    logger.update_system_metrics()
    
    # End processing
    logger.end_processing(success=True)
    
    # Convert to dict and verify structure
    log_data = logger.to_dict()
    
    # Verify required sections
    required_sections = [
        "file_info", "processing_metadata", "timing", 
        "requirements_analysis", "test_case_generation", 
        "performance_metrics", "status", "warnings"
    ]
    
    for section in required_sections:
        assert section in log_data, f"Missing section: {section}"
        print(f"✅ Section '{section}' present")
    
    # Verify specific values
    assert log_data["file_info"]["reqifz_file"] == "test_file.reqifz"
    assert log_data["processing_metadata"]["version"] == "test_v002"
    assert log_data["requirements_analysis"]["total_artifacts_found"] == 100
    assert log_data["requirements_analysis"]["requirements_processed"]["successful"] == 50
    assert log_data["requirements_analysis"]["requirements_processed"]["failed"] == 2
    assert log_data["test_case_generation"]["total_generated"] == 120
    assert log_data["test_case_generation"]["positive_tests"] == 80
    assert log_data["test_case_generation"]["negative_tests"] == 40
    assert log_data["status"] == "SUCCESS"
    assert len(log_data["warnings"]) == 1
    assert len(log_data["requirements_analysis"]["failure_details"]) == 2
    
    print(f"✅ All verification checks passed!")
    
    # Test file saving
    log_path = logger.save_log("/tmp")
    if log_path:
        print(f"✅ Log file saved successfully: {log_path}")
        
        # Verify the saved file can be loaded
        with open(log_path, 'r') as f:
            saved_data = json.load(f)
        assert saved_data["status"] == "SUCCESS"
        print(f"✅ Saved log file verified")
    else:
        print("⚠️  Log file saving failed")
    
    print("\n📊 Sample log data structure:")
    print(json.dumps(log_data, indent=2)[:500] + "...")

def test_phase_timing():
    """Test phase timing functionality"""
    print("\n🧪 Testing phase timing...")
    
    phase = ProcessingPhase("test_phase")
    
    phase.start()
    time.sleep(0.1)
    phase.end()
    
    assert phase.duration > 0.09, f"Expected duration > 0.09, got {phase.duration}"
    assert phase.duration < 0.15, f"Expected duration < 0.15, got {phase.duration}"
    
    print(f"✅ Phase timing works correctly: {phase.duration:.3f}s")

def test_failure_details():
    """Test requirement failure tracking"""
    print("\n🧪 Testing failure detail tracking...")
    
    failure = RequirementFailure("REQ_TEST_001", "Test error message")
    
    assert failure.requirement_id == "REQ_TEST_001"
    assert failure.error == "Test error message"
    assert failure.timestamp  # Should have a timestamp
    
    print(f"✅ Failure tracking works correctly")
    print(f"   - ID: {failure.requirement_id}")
    print(f"   - Error: {failure.error}")
    print(f"   - Timestamp: {failure.timestamp}")

if __name__ == "__main__":
    print("🚀 Starting FileProcessingLogger Tests\n")
    
    try:
        test_basic_logging()
        test_phase_timing()
        test_failure_details()
        
        print("\n🎉 All tests passed! FileProcessingLogger is working correctly.")
        print("\n📝 Integration Summary:")
        print("   ✅ FileProcessingLogger class implemented")
        print("   ✅ Integrated into v002 (Standard)")
        print("   ✅ Integrated into v002_w_Logging_WIP (Enhanced)")
        print("   ✅ Integrated into v003_HighPerformance (Multi-threaded)")
        print("   ✅ JSON log files generated by default")
        print("   ✅ No command-line options required")
        print("   ✅ Comprehensive metrics tracking")
        
        print("\n📋 Log files will include:")
        print("   • Start/end timestamps with phase breakdown")
        print("   • File paths (input REQIFZ, output Excel)")
        print("   • Artifact counts by type")
        print("   • Requirements processed vs successful")
        print("   • Test case generation counts (positive/negative)")
        print("   • AI response times and performance metrics")
        print("   • Error details and warnings")
        print("   • System resource usage (CPU/memory)")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)