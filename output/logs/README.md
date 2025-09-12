# Logs Output Directory

Processing log files (.json) are stored here when using organized output structure.

## Log File Contents

Each JSON log file contains comprehensive processing metrics:

### File Information
- Source REQIFZ file path
- Output Excel file path
- Processing timestamps

### Processing Metadata
- AI model used (e.g., llama3.1:8b)
- Template used for generation
- Python version
- Ollama version

### Performance Metrics
- Total processing time
- Requirements processed vs successful
- Test cases generated
- Peak CPU and memory usage
- AI response times
- Processing rates (requirements/second)

### Detailed Analysis
- Artifact breakdown by type (Heading, System Requirement, etc.)
- Failure details for unsuccessful requirements
- Test case statistics (positive vs negative tests)
- Generation success rates

## Example Log Structure

```json
{
  "file_info": {
    "reqifz_file": "input/automotive_door_window_system.reqifz",
    "output_file": "output/excel/automotive_door_window_TCD_HP_llama31_8b_14-30-15.xlsx"
  },
  "processing_metadata": {
    "ai_model": "llama3.1:8b",
    "template_used": "driver_information_default",
    "python_version": "3.13.7"
  },
  "performance_metrics": {
    "total_duration_seconds": 45.234,
    "requirements_per_second": 2.3,
    "peak_cpu_usage_percent": 85.2,
    "peak_memory_mb": 512.8
  },
  "test_case_generation": {
    "total_generated": 24,
    "positive_tests": 16,
    "negative_tests": 8,
    "generation_success_rate": 92.5
  }
}
```

## Usage

Logs are automatically generated alongside Excel files and provide valuable insights for:
- Performance monitoring
- Quality analysis
- Processing optimization
- Audit trails