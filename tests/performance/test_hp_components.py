#!/usr/bin/env python3
"""
Test script for high-performance components without Ollama dependency
"""

import sys
import time
import asyncio
from pathlib import Path

# Add src to path (go up two levels from test file to project root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from generate_contextual_tests_v003_HighPerformance import (
    HighPerformanceLogger,
    PerformanceMonitor,
    ParallelXMLParser,
    HighPerformanceREQIFArtifactExtractor,
    setup_logger
)

async def test_components():
    """Test high-performance components"""
    print("🧪 Testing High-Performance Components\n")
    
    # Test 1: Logger and Performance Monitor
    print("1️⃣ Testing Logger and Performance Monitor...")
    logger = setup_logger(verbose=True, debug=True)
    logger.start_performance_monitoring()
    
    logger.print_banner()
    logger.success("Logger test successful!")
    
    # Let it collect some metrics
    await asyncio.sleep(2)
    
    # Test 2: Performance Monitor
    print("\n2️⃣ Testing Performance Monitor...")
    metrics = logger.performance_monitor.get_current_metrics()
    print(f"✅ CPU cores detected: {metrics.cpu_usage and len(metrics.cpu_usage) or 'Unknown'}")
    
    logger.performance_monitor.record_file_processed()
    logger.performance_monitor.record_test_cases(5)
    logger.performance_monitor.record_ai_call()
    
    # Test 3: XML Parser (if we have a test file)
    print("\n3️⃣ Testing XML Parser...")
    test_file = Path("input/Reqifz_Files/TFDCX32348_001 Rental Car Mode_551f0c.reqifz")
    
    if test_file.exists():
        print(f"✅ Found test file: {test_file.name}")
        
        extractor = HighPerformanceREQIFArtifactExtractor()
        print("📊 Starting XML extraction test...")
        
        start_time = time.time()
        artifacts = extractor.extract_all_artifacts(test_file)
        extraction_time = time.time() - start_time
        
        print(f"✅ Extracted {len(artifacts)} artifacts in {extraction_time:.2f} seconds")
        print(f"📈 Processing speed: {len(artifacts)/extraction_time:.1f} artifacts/second")
        
        # Show artifact types
        artifact_types = {}
        for artifact in artifacts:
            artifact_type = artifact.get('type', 'Unknown')
            artifact_types[artifact_type] = artifact_types.get(artifact_type, 0) + 1
        
        print("📋 Artifact types found:")
        for atype, count in artifact_types.items():
            print(f"   • {atype}: {count}")
            
    else:
        print("⚠️  No test REQIFZ file found - skipping XML test")
    
    # Test 4: Performance Dashboard
    print("\n4️⃣ Testing Performance Dashboard...")
    logger.show_performance_dashboard()
    
    # Stop monitoring
    logger.stop_performance_monitoring()
    logger.log_performance_summary()
    
    print("\n🎉 All component tests completed!")

if __name__ == "__main__":
    asyncio.run(test_components())