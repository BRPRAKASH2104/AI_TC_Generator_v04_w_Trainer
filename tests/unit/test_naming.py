#!/usr/bin/env python3
"""Test the updated log file naming pattern"""

import sys
from pathlib import Path

# Add src to path (go up two levels from test file to project root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from file_processing_logger import FileProcessingLogger

def test_naming_patterns():
    """Test different naming scenarios"""
    
    print("🧪 Testing updated log file naming patterns...")
    
    # Test 1: Standard version naming
    print("\n1️⃣ Testing Standard version (v002) naming:")
    logger1 = FileProcessingLogger(
        reqifz_file="TFDCX32348_DIAG.reqifz",
        input_path="/test/TFDCX32348_DIAG.reqifz",
        output_file="/test/TFDCX32348_DIAG_TCD_llama3_1_8b_2025-09-06_15-30-45.xlsx",
        version="v002_Standard",
        ai_model="llama3.1:8b"
    )
    
    logger1.end_processing(success=True)
    log_path1 = logger1.save_log("/tmp")
    expected1 = "TFDCX32348_DIAG_TCD_llama3_1_8b_2025-09-06_15-30-45.json"
    actual1 = Path(log_path1).name if log_path1 else "None"
    
    print(f"   Excel file: TFDCX32348_DIAG_TCD_llama3_1_8b_2025-09-06_15-30-45.xlsx")
    print(f"   Expected:   {expected1}")
    print(f"   Actual:     {actual1}")
    print(f"   Match: {'✅' if expected1 == actual1 else '❌'}")
    
    # Test 2: Enhanced logging version naming  
    print("\n2️⃣ Testing Enhanced Logging version (v002_w_Logging_WIP) naming:")
    logger2 = FileProcessingLogger(
        reqifz_file="door_control.reqifz",
        input_path="/test/door_control.reqifz", 
        output_file="/test/door_control_TCD_deepseek_coder_v2_16b_2025-09-06_16-45-22.xlsx",
        version="v002_w_Logging_WIP",
        ai_model="deepseek-coder-v2:16b"
    )
    
    logger2.end_processing(success=True)
    log_path2 = logger2.save_log("/tmp")
    expected2 = "door_control_TCD_deepseek_coder_v2_16b_2025-09-06_16-45-22.json"
    actual2 = Path(log_path2).name if log_path2 else "None"
    
    print(f"   Excel file: door_control_TCD_deepseek_coder_v2_16b_2025-09-06_16-45-22.xlsx")
    print(f"   Expected:   {expected2}")
    print(f"   Actual:     {actual2}")
    print(f"   Match: {'✅' if expected2 == actual2 else '❌'}")
    
    # Test 3: High-Performance version naming
    print("\n3️⃣ Testing High-Performance version (v003_HighPerformance) naming:")
    logger3 = FileProcessingLogger(
        reqifz_file="window_control.reqifz",
        input_path="/test/window_control.reqifz",
        output_file="/test/window_control_TCD_HP_llama3_1_8b_2025-09-06_20-15-33.xlsx",
        version="v003_HighPerformance", 
        ai_model="llama3.1:8b"
    )
    
    logger3.end_processing(success=True)
    log_path3 = logger3.save_log("/tmp")
    expected3 = "window_control_TCD_HP_llama3_1_8b_2025-09-06_20-15-33.json"
    actual3 = Path(log_path3).name if log_path3 else "None"
    
    print(f"   Excel file: window_control_TCD_HP_llama3_1_8b_2025-09-06_20-15-33.xlsx")
    print(f"   Expected:   {expected3}")
    print(f"   Actual:     {actual3}")
    print(f"   Match: {'✅' if expected3 == actual3 else '❌'}")
    
    # Test 4: Fallback when no output file specified
    print("\n4️⃣ Testing fallback naming (no output file specified):")
    logger4 = FileProcessingLogger(
        reqifz_file="test_fallback.reqifz",
        input_path="/test/test_fallback.reqifz",
        output_file="",  # Empty output file
        version="test_version",
        ai_model="llama3.1:8b"
    )
    
    logger4.end_processing(success=True)
    log_path4 = logger4.save_log("/tmp")
    actual4 = Path(log_path4).name if log_path4 else "None"
    contains_processing_log = "processing_log" in actual4
    
    print(f"   Excel file: (not specified)")
    print(f"   Expected:   test_fallback_processing_log_YYYY-MM-DD_HH-MM-SS.json")
    print(f"   Actual:     {actual4}")
    print(f"   Uses fallback pattern: {'✅' if contains_processing_log else '❌'}")
    
    # Summary
    all_match = (
        expected1 == actual1 and 
        expected2 == actual2 and 
        expected3 == actual3 and
        contains_processing_log
    )
    
    print(f"\n📋 Summary:")
    print(f"   Standard version:      {'✅' if expected1 == actual1 else '❌'}")
    print(f"   Enhanced version:      {'✅' if expected2 == actual2 else '❌'}")
    print(f"   High-Performance:      {'✅' if expected3 == actual3 else '❌'}")
    print(f"   Fallback pattern:      {'✅' if contains_processing_log else '❌'}")
    print(f"\n{'🎉 All naming patterns work correctly!' if all_match else '❌ Some naming patterns failed'}")
    
    return all_match

if __name__ == "__main__":
    success = test_naming_patterns()
    print(f"\n{'✅ Naming test passed' if success else '❌ Naming test failed'}")