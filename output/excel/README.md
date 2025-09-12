# Excel Output Directory

Generated Excel test case files (.xlsx) are stored here when using `--output-dir output/excel/`.

## File Contents

Each Excel file contains:
- **Test Cases Sheet:** Generated test cases with automotive-specific formatting
- **Metadata Sheet:** Processing information, model used, generation timestamps

## Columns in Test Cases

| Column | Description |
|--------|-------------|
| Issue ID | Unique test case identifier |
| Summary | Brief test case description |
| Description | Detailed test steps and context |
| Issue Type | Test (automotive standard) |
| Status | To Do (default) |
| Project Key | TCTOIC (configurable) |
| Assignee | ENGG (configurable) |
| Test Case Type | Feature Functional |
| Planned Execution | Manual |
| Components | SW_DI_FV (configurable) |
| Labels | AI Generated TCs |
| Action | Test execution steps |
| Data | Test data requirements |
| Expected Result | Expected test outcomes |
| Precondition | Voltage/system preconditions |
| Test Type | PROVEtech |

## Organization Examples

```
excel/
├── 2025-09-12/                          # Daily organization
│   ├── automotive_door_window_TCD_HP_llama31_8b_14-30-15.xlsx
│   └── requirements_v2_TCD_deepseek_15-45-30.xlsx
├── project1/                            # Project-based
│   ├── specs_v1_TCD_llama31_8b_09-15-22.xlsx
│   └── specs_v2_TCD_llama31_8b_10-22-45.xlsx
└── comparative_analysis/                 # Model comparison
    ├── llama31/
    └── deepseek/
```