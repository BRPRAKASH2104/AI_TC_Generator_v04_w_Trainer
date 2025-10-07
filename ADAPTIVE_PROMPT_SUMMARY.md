# Adaptive Prompt Template - Implementation Summary

**Date**: 2025-10-07
**Version**: 2.0
**Status**: ✅ Implemented and Validated

---

## 📊 Problem Analysis

### Dataset Analysis Results:
- **Total Requirements Analyzed**: 4,551 across 36 REQIFZ files
- **Requirements WITH tables**: 0 (0.0%)
- **Requirements WITHOUT tables**: 4,551 (100.0%)

### Critical Finding:
The existing `test_generation_v3_structured.yaml` prompt was **100% incompatible** with the current dataset because:
- It required `table_str` and `row_count` as mandatory variables
- All instructions assumed structured decision tables
- Text-only requirements would generate poor quality test cases

---

## ✅ Solution Implemented: Adaptive Prompt Template

### Option Selected: **Option 1 - Single Adaptive Prompt**

**File**: `prompts/templates/test_generation_adaptive.yaml`

### Key Features:

1. **Intelligent Analysis Step**
   - AI examines the requirement to determine if it's table-based or text-only
   - Adapts testing strategy based on available data

2. **Dual-Mode Instructions**
   - **Table-Based Mode**: When `table_str` contains data and `row_count > 0`
     - Uses Decision Table Testing as primary technique
     - Tests all table rows (positive coverage)
     - Adds boundary and negative tests

   - **Text-Only Mode**: When no table is provided
     - Analyzes requirement text for parameters
     - Uses appropriate techniques: BVA, Equivalence Partitioning, Scenario-Based
     - Extracts parameters from System Interface Dictionary
     - Generates 5-13 comprehensive test cases

3. **Context-Aware Testing**
   - Utilizes System Interface Dictionary for parameter definitions
   - References Additional Information Notes for special conditions
   - Considers Feature Heading for broader context

4. **Automotive-Specific Guidance**
   - Voltage conditions (normal, low, high)
   - Ignition states (Off, ACC, ON)
   - Communication failures (CAN timeout, invalid frames)
   - Safety implications (fail-safe behavior, degraded modes)

---

## 🔧 Configuration Changes

### Files Modified:

1. **`prompts/config/prompt_config.yaml`**
   - Changed: `test_generation_prompts: "prompts/templates/test_generation_adaptive.yaml"`
   - Changed: `template_selection: "adaptive_default"`
   - Updated model configurations to use `adaptive_default`

2. **`prompts/templates/test_generation_adaptive.yaml`** ✨ NEW
   - Created adaptive prompt template (6,377 characters)
   - Supports both table-based and text-only requirements

3. **`prompts/templates/test_generation_v3_structured.yaml.backup`** 📦
   - Backed up original template for reference

---

## ✅ Validation Results

### Template Loading Tests:

```
✅ Prompt template loaded successfully
✅ Prompt length: 6,377 characters (text-only)
✅ Prompt length: 6,685 characters (with table)
```

### Adaptive Features Verified:

```
✅ Contains text-only guidance: "IF NO TABLE PROVIDED"
✅ Contains table-based guidance: "IF LOGIC TABLE IS PROVIDED"
✅ Contains adaptive analysis: "STEP 1: ANALYZE THE REQUIREMENT"
✅ Row count correctly embedded in prompts
✅ Table data correctly embedded in prompts
✅ System interfaces correctly included
```

### Test Scenarios:

1. **Text-Only Requirement** (Toyota CXPI example)
   - ✅ Prompt generated successfully
   - ✅ Contains text-based testing instructions
   - ✅ Guides AI to extract parameters from text

2. **Table-Based Requirement** (Simulated door lock logic)
   - ✅ Prompt generated successfully
   - ✅ Contains table-specific instructions
   - ✅ Correctly references row count (4 rows)

---

## 📋 Template Structure

### Required Variables:
- `heading`: Feature heading (context)
- `requirement_id`: Unique requirement identifier
- `requirement_text`: Main requirement description

### Optional Variables (with defaults):
- `table_str`: HTML table data (default: empty string)
- `row_count`: Number of table rows (default: 0)
- `info_str`: Additional information notes (default: "None")
- `interface_str`: System interface dictionary (default: "None")
- `voltage_precondition`: Test preconditions (default: "1. Voltage= 12V\n2. Bat-ON")

---

## 🎯 How It Works

### For Text-Only Requirements (Current Dataset):

```yaml
Input:
  requirement_text: "CXPI Processing Cycle = 10 msec"
  table_str: ""
  row_count: 0

AI Behavior:
  1. Recognizes no table data is present
  2. Analyzes requirement text: "CXPI Processing Cycle = 10 msec"
  3. Identifies: timing parameter (10 msec)
  4. Applies techniques: BVA (boundary testing), Equivalence Partitioning
  5. Generates positive tests: typical, min valid, max valid
  6. Generates negative tests: below min, above max, invalid values
```

### For Table-Based Requirements (Future Use):

```yaml
Input:
  requirement_text: "Door lock control logic"
  table_str: "Speed | DoorState | LockCommand..."
  row_count: 4

AI Behavior:
  1. Recognizes table data with 4 rows
  2. Applies Decision Table Testing as primary technique
  3. Creates 4 positive tests (one per table row)
  4. Adds negative tests for boundary violations
  5. Tests invalid input combinations not in table
```

---

## 🚀 Benefits

1. **Immediate Compatibility**: Works TODAY with 100% text-only dataset
2. **Future-Ready**: Ready for table-based requirements when they arrive
3. **Zero Code Changes**: No modifications needed in processors or generators
4. **Single Template**: Easier maintenance than multiple templates
5. **Intelligent Adaptation**: AI naturally adapts to available data

---

## 📝 Usage

### Current Behavior:
```bash
# Automatically uses adaptive template
python main.py input/Toyota_FDC --verbose
python main.py input/2025_09_12_S220 --hp
```

### Manual Template Selection (if needed):
```bash
# Use adaptive template explicitly
python main.py input/ --template adaptive_default
```

---

## 🔍 Quality Assurance

### Test Coverage Requirements:

**For Text-Only Requirements**:
- Generate 5-13 total test cases
- Mix of positive (3-8) and negative (2-5) tests
- Cover boundary values, equivalence classes, error conditions

**For Table-Based Requirements**:
- Generate 1 test per table row (positive coverage)
- Add 3-5 negative tests
- Cover invalid inputs, boundary violations, conflicting combinations

### JSON Output Structure (Unchanged):
```json
{
  "test_cases": [
    {
      "summary_suffix": "Descriptive test title",
      "action": "1. Voltage= 12V\n2. Bat-ON",
      "data": "1) Test step one\n2) Test step two",
      "expected_result": "Verify observable outcome",
      "test_type": "positive"
    }
  ]
}
```

---

## 🎓 Next Steps

1. ✅ **Completed**: Adaptive prompt template created
2. ✅ **Completed**: Configuration updated
3. ✅ **Completed**: Validation tests passed
4. ⏭️ **Next**: Run full processing on Toyota_FDC dataset to verify quality
5. ⏭️ **Next**: Monitor test case quality and iterate if needed

---

## 📚 Files Reference

- **New Template**: `prompts/templates/test_generation_adaptive.yaml`
- **Configuration**: `prompts/config/prompt_config.yaml`
- **Backup**: `prompts/templates/test_generation_v3_structured.yaml.backup`
- **This Summary**: `ADAPTIVE_PROMPT_SUMMARY.md`

---

## 🔄 Rollback Instructions (if needed)

If you need to revert to the old table-focused prompt:

```bash
# 1. Restore configuration
sed -i '' 's/test_generation_adaptive.yaml/test_generation_v3_structured.yaml/' prompts/config/prompt_config.yaml
sed -i '' 's/adaptive_default/driver_information_default/' prompts/config/prompt_config.yaml

# 2. Or use backup
cp prompts/templates/test_generation_v3_structured.yaml.backup prompts/templates/test_generation_v3_structured.yaml
```

---

**Status**: ✅ Ready for production use with text-only requirements
**Future**: ✅ Ready for table-based requirements when they arrive
**Maintenance**: ✅ Single template, easy to update
