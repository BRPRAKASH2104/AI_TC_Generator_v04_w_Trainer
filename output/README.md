# Output Directory

This directory organizes all generated files from the AI Test Case Generator.

## Directory Structure

```
output/
├── excel/          # Generated Excel test case files (.xlsx)
├── logs/           # Processing log files (.json)
├── reports/        # Analysis and summary reports
└── README.md       # This file
```

## Default Output Behavior

**Without --output-dir flag:**
- Files are saved in the **same directory as input files**
- Example: `input/file.reqifz` → `input/file_TCD_model_timestamp.xlsx`

**With --output-dir flag:**
```bash
# Save all outputs to organized structure
python3 main.py input/file.reqifz --output-dir output/excel/

# Save to custom location
python3 main.py input/file.reqifz --output-dir /path/to/custom/location/
```

## File Naming Patterns

### Excel Files
- **Standard mode:** `{filename}_TCD_{model}_{timestamp}.xlsx`
- **High-performance mode:** `{filename}_TCD_HP_{model}_{timestamp}.xlsx`

### Log Files  
- **Processing logs:** `{filename}_TCD_{model}_{timestamp}.json`
- Contains detailed metrics, timing, and processing statistics

## Usage Examples

```bash
# Default - saves to input directory
python3 main.py input/automotive_door_window_system.reqifz

# Organized - saves to output/excel/
python3 main.py input/automotive_door_window_system.reqifz --output-dir output/excel/

# Process directory with organized output
python3 main.py input/ --output-dir output/excel/

# High-performance with organized output
python3 main.py input/file.reqifz --hp --output-dir output/excel/ --performance
```

## File Organization Tips

1. **Daily Processing:** Create date-based subdirectories
   ```bash
   python3 main.py input/file.reqifz --output-dir output/excel/2025-09-12/
   ```

2. **Project-based:** Organize by project
   ```bash
   python3 main.py input/project1/ --output-dir output/excel/project1/
   python3 main.py input/project2/ --output-dir output/excel/project2/
   ```

3. **Model Comparison:** Separate by AI model
   ```bash  
   python3 main.py input/file.reqifz --model llama3.1:8b --output-dir output/excel/llama31/
   python3 main.py input/file.reqifz --model deepseek-coder-v2:16b --output-dir output/excel/deepseek/
   ```