# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📋 Quick Reference

**Project**: AI-powered test case generator for automotive REQIFZ requirements
**Version**: v2.1.0 | **Python**: 3.14.0+ | **Ollama**: v0.12.5+

**Essential Commands**:
```bash
pip install -e .[dev]              # Install with dev dependencies
python tests/run_tests.py          # Run complete test suite
ai-tc-generator input/ --hp        # Process files in HP mode (3-5x faster)
ruff check src/ main.py --fix      # Lint and auto-fix
```

**Critical Files**:
- `src/processors/base_processor.py:62-126` - Context-aware processing (DO NOT MODIFY)
- `src/core/extractors.py:151-172,191,235` - REQIFZ extraction with attribute mapping (RECENT FIX)
- `src/core/prompt_builder.py` - Stateless prompt construction
- `src/core/generators.py` - Test case generation (sync + async)
- `src/core/exceptions.py` - Structured error handling
- `prompts/templates/test_generation_adaptive.yaml` - Adaptive prompt (table + text-only)

**Architecture Pattern**: `CLI → Processor → Generator → PromptBuilder → Ollama → Excel`

---

## ⚠️ System Instructions
You are an expert Python developer and software architect. This repository implements an AI-powered test case generator for system requirements in REQIFZ files, using the Ollama API for LLM interactions.

You are an agent – keep going until the user's query is completely resolved before ending your turn.

If you are not sure about code or file content pertaining to the user's request, open them. Do not hallucinate. Use your tools; don't guess.

You MUST plan thoroughly before every tool call and reflect extensively on the outcome.


## ⚠️ CRITICAL: Context-Aware Processing Architecture

**This system REQUIRES context-aware artifact processing to generate high-quality test cases.**

### Core Architecture Pattern (DO NOT BREAK)

The heart of this system is in `BaseProcessor._build_augmented_requirements()` which ALL processors inherit. This method implements context-aware processing:

```python
# BaseProcessor._build_augmented_requirements() - src/processors/base_processor.py:62-126
current_heading = "No Heading"
info_since_heading = []

for obj in artifacts:
    if obj.get("type") == "Heading":
        current_heading = obj.get("text", "No Heading")
        info_since_heading = []  # Reset on new heading
    elif obj.get("type") == "Information":
        info_since_heading.append(obj)
    elif obj.get("type") == "System Requirement" and obj.get("table"):
        augmented_requirement = obj.copy()
        augmented_requirement.update({
            "heading": current_heading,
            "info_list": info_since_heading.copy(),
            "interface_list": system_interfaces
        })
        augmented_requirements.append(augmented_requirement)
        info_since_heading = []  # CRITICAL: Reset after each requirement
```

**Why This Matters:**
- AI generates better test cases with context (heading, info, interfaces)
- Information context resets after each requirement (no carryover)
- Both standard and HP processors share this exact logic via inheritance

**DO NOT:**
- Filter artifacts before context iteration: `[obj for obj in artifacts if obj.get("type") == "System Requirement"]`
- Duplicate context logic in processors (use BaseProcessor inheritance)
- Remove context fields from PromptBuilder template variables
- Modify extractor without building attribute definition mappings (see v2.0 fix below)

## 🏗️ Architecture Overview

### High-Level Structure

```
main.py (CLI) → Processor (standard/hp) → Generator → PromptBuilder → Ollama API
                     ↓
                BaseProcessor (shared context logic)
                     ↓
          Extract → Augment with context → Generate → Format to Excel
```

### Directory Structure (Critical Paths Only)

```
src/
├── core/                    # Core business logic
│   ├── extractors.py       # REQIFZ parsing
│   ├── generators.py       # TestCaseGenerator + AsyncTestCaseGenerator
│   ├── prompt_builder.py   # Stateless prompt construction
│   ├── ollama_client.py    # Ollama API clients (sync + async)
│   ├── exceptions.py       # Structured error handling
│   └── formatters.py       # Excel/JSON output
├── processors/             # Workflow orchestration
│   ├── base_processor.py   # CRITICAL: Context-aware processing (DO NOT MODIFY)
│   ├── standard_processor.py
│   └── hp_processor.py
├── training/               # RAFT training (optional, v1.6.0)
├── config.py              # Pydantic configuration
├── yaml_prompt_manager.py # YAML template management
└── app_logger.py          # Centralized logging

prompts/templates/         # YAML prompt templates
tests/                     # Test suite (109/130 passing)
utilities/                 # Helper scripts
```

### Key Components

**REQIFArtifactExtractor** (`src/core/extractors.py`):
- **PURPOSE**: Extracts artifacts from REQIFZ files with proper attribute name resolution
- **CRITICAL FIX (v2.0)**: Attribute definition mapping prevents extraction failures
- **KEY METHODS**:
  - `extract_reqifz_content(reqifz_file_path)` - Main entry point
  - `_build_attribute_definition_mapping(root, namespaces)` - Maps attribute identifiers to LONG-NAME values (CRITICAL)
  - `_extract_spec_object(spec_obj, ..., attr_def_map)` - Extracts single artifact with proper attribute resolution
- **COMMON ISSUE**: Without attribute mapping, extractor uses identifiers like `_json2reqif_XXX` instead of "ReqIF.Text", causing requirements to be skipped
- **VALIDATION**: Check extraction success rate - should be >95% for valid REQIFZ files

**BaseProcessor** (`src/processors/base_processor.py`):
- **PURPOSE**: Eliminates code duplication between standard and HP processors
- **KEY METHOD**: `_build_augmented_requirements()` - implements v03 context-aware processing
- **SHARED METHODS**: Logger init, artifact extraction, context building, output path generation, metadata creation
- **INHERITANCE**: Both `REQIFZFileProcessor` and `HighPerformanceREQIFZFileProcessor` inherit from this

**PromptBuilder** (`src/core/prompt_builder.py`):
- **PURPOSE**: Stateless, reusable prompt construction decoupled from generators
- **KEY METHODS**:
  - `build_prompt(requirement, template_name)` - Main entry point
  - `format_info_list(info_list)` - Formats information context
  - `format_interfaces(interface_list)` - Formats interface context
- **TEMPLATE VARIABLES**: Includes `info_str`, `interface_str`, `heading` (required for context)
- **USED BY**: Both `TestCaseGenerator` and `AsyncTestCaseGenerator`

**Processors** (`src/processors/`):
- `standard_processor.py`: Sequential processing, uses `TestCaseGenerator`
- `hp_processor.py`: Async processing with batching, uses `AsyncTestCaseGenerator`
- Both inherit context logic from `BaseProcessor` (0% code duplication)

**Generators** (`src/core/generators.py`):
- `TestCaseGenerator`: Synchronous test case generation
- `AsyncTestCaseGenerator`: Concurrent async generation with semaphore control
- Both use shared `PromptBuilder` instance (no awkward coupling)
- **IMPORTANT**: Only `AsyncOllamaClient` has semaphore (removed from AsyncTestCaseGenerator in v1.5.0)

**Exception System** (`src/core/exceptions.py`):
- **PURPOSE**: Structured error handling with actionable context (replaces silent failures)
- **BASE CLASSES**: `AITestCaseGeneratorError`, `OllamaError`
- **SPECIFIC EXCEPTIONS**:
  - `OllamaConnectionError` - stores host, port (connection failures)
  - `OllamaTimeoutError` - stores timeout value (timeout failures)
  - `OllamaModelNotFoundError` - stores model name (missing model)
  - `OllamaResponseError` - stores response details (invalid API responses)
  - `REQIFParsingError` - stores file_path (parsing errors)
- **USED BY**: `OllamaClient`, `AsyncOllamaClient`, processors for structured error handling

### Data Flow

```
1. REQIFZ File → Extractor
2. ALL Artifacts (Heading, Information, System Interface, System Requirement)
3. BaseProcessor._build_augmented_requirements()
   - Iterate through ALL artifacts
   - Track heading context
   - Collect info context
   - Augment each System Requirement with full context
   - Reset info after each requirement
4. Generator receives augmented requirement
5. PromptBuilder formats context into prompt
6. Ollama API generates test cases
7. Formatter creates Excel output with metadata
```

### Import Structure (CRITICAL)

All imports within `src/` MUST use absolute imports from module root:

```python
# ✅ CORRECT
from config import ConfigManager
from core.extractors import REQIFArtifactExtractor
from processors.base_processor import BaseProcessor
from core.prompt_builder import PromptBuilder

# ❌ WRONG (breaks tests)
from ..config import ConfigManager
from ..core.extractors import REQIFArtifactExtractor
```

**Reason**: Tests add `src/` to sys.path, requiring absolute imports.

## 🚀 Common Commands

### Development Setup

```bash
# Install with dev dependencies
pip install -e .[dev]

# Verify installation
python3 -c "import src; print(f'v{src.__version__}')"

# Check Ollama service
ollama list
curl -s http://localhost:11434/api/tags
```

### Running the Application

```bash
# Process single file (installed CLI)
ai-tc-generator input/your_file.reqifz --verbose

# High-performance mode (3-5x faster with v1.5.0 optimizations)
ai-tc-generator input/directory/ --hp --max-concurrent 4

# Development mode (not installed)
python main.py input/your_file.reqifz --debug

# With custom model
ai-tc-generator input/ --model deepseek-coder-v2:16b --verbose
```

### Testing

```bash
# Run complete test suite (recommended)
python tests/run_tests.py

# Run specific test file
python -m pytest tests/core/test_parsers.py -v

# Run with coverage
python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Run only refactoring tests
python -m pytest tests/test_refactoring.py -v

# Run integration tests
python -m pytest tests/test_integration_refactored.py -v

# Run critical improvements tests (v1.5.0)
python -m pytest tests/test_critical_improvements.py -v

# Run RAFT tests (v1.6.0)
python -m pytest tests/training/ -v

# Run Python 3.14 + Ollama 0.12.5 tests (v2.1.0)
python -m pytest tests/test_python314_ollama0125.py -v
```

### Code Quality

```bash
# Check code style
ruff check src/ main.py utilities/

# Auto-fix issues
ruff check src/ main.py --fix

# Format code
ruff format src/ main.py utilities/

# Type checking
mypy src/ main.py --python-version 3.14

# Validate YAML templates
ai-tc-generator --validate-prompts
```

### Ollama Setup

```bash
# Install required models
ollama pull llama3.1:8b
ollama pull deepseek-coder-v2:16b

# Start Ollama service (if not running)
ollama serve

# Check service status
ollama list
```

## 🧪 Development Guidelines

### Before Making Changes

1. **Context-Aware Processing**: Never bypass BaseProcessor's context logic
2. **Test Coverage**: Run `python tests/run_tests.py` before committing
3. **Import Style**: Use absolute imports from `src` root (not relative)
4. **Code Quality**: Run `ruff check src/ main.py --fix` before commits

### When Modifying Core Components

**Processors** (`src/processors/`):
- Context logic lives in `BaseProcessor` only (do not duplicate)
- Both processors must inherit from `BaseProcessor`
- Standard processor uses synchronous generator, HP uses async generator
- **CRITICAL (v1.5.0)**: HP processor must process ALL requirements concurrently (not sequential batches)
  ```python
  # ✅ CORRECT (v1.5.0)
  batch_results = await generator.generate_test_cases_batch(
      augmented_requirements,  # ALL requirements at once
      model, template
  )

  # ❌ WRONG (old pattern - do not use)
  for i in range(0, len(augmented_requirements), batch_size):
      batch = augmented_requirements[i:i + batch_size]
      batch_results = await generator.generate_test_cases_batch(batch, ...)
  ```

**Generators** (`src/core/generators.py`):
- Both generators must use shared `PromptBuilder` instance
- Do not create TestCaseGenerator inside AsyncTestCaseGenerator
- Maintain stateless design with `__slots__`
- **CRITICAL (v1.5.0)**: Only `AsyncOllamaClient` has semaphore - do NOT add semaphore to `AsyncTestCaseGenerator`

**Exception Handling** (`src/core/exceptions.py`):
- Always use custom exceptions instead of returning empty strings
- Include context in exceptions: host/port for connection errors, timeout for timeout errors, model for model errors
- Processors must catch and handle specific exception types for actionable error messages
- Example pattern:
  ```python
  except OllamaConnectionError as e:
      self.logger.error(f"Cannot connect to Ollama at {e.host}:{e.port}")
      return error_result_with_fix_instructions
  ```

**PromptBuilder** (`src/core/prompt_builder.py`):
- Keep stateless (only yaml_manager attribute)
- Context formatting methods must be static
- Template variables must include: `info_str`, `interface_str`, `heading`

**YAML Templates** (`prompts/templates/`):
- Run `ai-tc-generator --validate-prompts` after changes
- Templates expect context variables: `heading`, `info_str`, `interface_str`
- Test with real REQIFZ files after template changes

### Python 3.14+ Features Used

- **PEP 695 Type Aliases**: `type JSONObj[T] = dict[str, T]`
- **PEP 649**: Deferred annotation evaluation (default, no `from __future__ import annotations` needed)
- **PEP 737**: Enhanced type parameters
- **Pattern Matching**: `match`/`case` for XML processing
- **__slots__**: Memory optimization (20-30% reduction)
- **Async/Await**: Concurrent processing in HP mode with improved TaskGroup

## 📊 Current System Status

**Version**: v2.1.0 (Production/Stable) | **Python**: 3.14.0+ | **Ollama**: v0.12.5+

**Test Status**:
- 109/130 tests passing (84% success rate)
- 18/18 critical improvement tests passing (100% - v1.5.0 features)
- 16/16 Python 3.14 + Ollama 0.12.5 tests passing (100% - v2.1.0 features)
- 100% coverage on critical paths (context-aware processing, BaseProcessor, PromptBuilder)
- Known issues: 21 legacy integration tests need updating to expect custom exceptions

**Architecture Status**:
- ✅ BaseProcessor refactoring: Complete (0% code duplication)
- ✅ PromptBuilder decoupling: Complete (no awkward coupling)
- ✅ Context-aware processing: Verified 100% intact
- ✅ Custom exception system: Complete
- ✅ Double semaphore removed: Complete
- ✅ Concurrent batch processing: Complete
- ✅ RAFT training system: Complete (v1.6.0, optional, non-invasive)
- ✅ Python 3.14 compatibility: Complete (v2.1.0, no future imports)
- ✅ Ollama 0.12.5 integration: Complete (v2.1.0, 16K context, GPU offload)
- ✅ Import structure: All absolute imports from `src` root
- ✅ Dependency management: Single source (pyproject.toml)

**Performance Benchmarks** (v2.1.0):
- Standard mode: ~7,254 artifacts/second
- HP mode: ~54,624 → **~65,000 artifacts/second (estimated +19%)**
- Processing rate improvement: 24 req/sec (3x from baseline)
- Memory efficiency: 0.010 → ~0.008 MB per artifact (estimated -20%)
- Error debugging: 10x faster with structured exceptions + response_body field
- Context capacity: 8K → 16K tokens (+100%)
- Response length: 2K → 4K tokens (+100%)
- GPU concurrency: 1 → 2 requests (+100%)

## 🔍 Verification Commands

```bash
# Verify context formatting methods work
python3 -c "
from src.core.prompt_builder import PromptBuilder
builder = PromptBuilder()
info = [{'text': 'Test info'}]
interfaces = [{'id': 'IF_001', 'text': 'Signal'}]
print('Info:', builder.format_info_list(info))
print('Interface:', builder.format_interfaces(interfaces))
"

# Test complete workflow
ai-tc-generator input/automotive_door_window_system.reqifz --verbose

# Verify BaseProcessor inheritance
python3 -c "
from processors.standard_processor import REQIFZFileProcessor
from processors.hp_processor import HighPerformanceREQIFZFileProcessor
from processors.base_processor import BaseProcessor
print('Standard inherits BaseProcessor:', issubclass(REQIFZFileProcessor, BaseProcessor))
print('HP inherits BaseProcessor:', issubclass(HighPerformanceREQIFZFileProcessor, BaseProcessor))
"

# Verify v1.5.0 improvements
python3 -c "
from src.core.generators import AsyncTestCaseGenerator
print('AsyncTestCaseGenerator slots:', AsyncTestCaseGenerator.__slots__)
print('Has semaphore:', 'semaphore' in AsyncTestCaseGenerator.__slots__)
# Should print: Has semaphore: False
"

# Run critical improvements tests
python -m pytest tests/test_critical_improvements.py -v
# Should show: 18/18 tests PASSED

# Run Python 3.14 + Ollama 0.12.5 verification tests
python -m pytest tests/test_python314_ollama0125.py -v
# Should show: 16/16 tests PASSED
```

## 🐛 Common Issues and Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| **Import Errors** | `ModuleNotFoundError: No module named 'src'` | Run `pip install -e .[dev]` in project root |
| **Context Loss** | Test cases lack relevant context | Check processors use `BaseProcessor._build_augmented_requirements()` - never filter artifacts before context iteration |
| **Template Issues** | YAML parsing errors | Run `ai-tc-generator --validate-prompts` |
| **Ollama Connection** | `OllamaConnectionError` | Start service: `ollama serve`, verify: `ollama list` |
| **Missing Model** | `OllamaModelNotFoundError: model 'X' not found` | Install: `ollama pull <model>` |
| **Timeout** | `OllamaTimeoutError: request timed out after Xs` | Use faster model or increase timeout in config |
| **Test Failures** | Import errors in tests | Ensure all imports are absolute from `src` root (not relative `..`) |
| **Performance** | Slow processing | Use `--hp` mode for 3-5x speedup (large files) |
| **RAFT Not Working** | Examples not collected | Set `AI_TG_ENABLE_RAFT=true` or enable in config |
| **Requirements Skipped** | "no text content" warnings, 0 requirements extracted | Extractor missing attribute mapping - check `_build_attribute_definition_mapping()` exists and is called |
| **Table vs Text Mismatch** | Poor test quality, prompt expects table but none exists | Use adaptive prompt template (`adaptive_default`) that handles both scenarios |

## 🎓 RAFT Training (Retrieval Augmented Fine-Tuning)

**Status**: Implemented (v1.6.0) - Optional, disabled by default

### Overview

RAFT enables custom model training by teaching the AI to distinguish relevant context from noise when generating test cases.

### Architecture

**Key Modules**:
- `src/training/raft_collector.py`: Collects training examples with context
- `src/training/raft_dataset_builder.py`: Builds RAFT datasets for Ollama fine-tuning
- `utilities/annotate_raft.py`: Interactive annotation tool for marking oracle/distractor context

**Integration** (Non-Invasive):
- BaseProcessor conditionally initializes RAFT collector
- Processors optionally save examples AFTER core logic completes
- Zero impact when disabled (default: `enable_raft: false`)

### Enabling RAFT

```bash
# Via environment variable
export AI_TG_ENABLE_RAFT=true

# Or in config
# config.training.enable_raft = True
```

### Workflow

```bash
# 1. Enable collection and process files
ai-tc-generator input/ --verbose  # Examples saved to training_data/collected/

# 2. Annotate examples (mark oracle vs distractor context)
python utilities/annotate_raft.py

# 3. Build RAFT dataset
python -c "from training.raft_dataset_builder import RAFTDatasetBuilder; builder = RAFTDatasetBuilder(); builder.save_dataset(builder.build_dataset())"

# 4. Train custom model with Ollama
cd training_data/raft_dataset/
ollama create automotive-tc-raft-v1 --file Modelfile --training-data raft_training_dataset.jsonl

# 5. Use trained model
ai-tc-generator input/ --model automotive-tc-raft-v1 --hp
```

### Critical Guarantees

- ✅ Core logic 100% unchanged (verified via line-by-line inspection)
- ✅ Context-aware processing intact
- ✅ No side effects on test case generation
- ✅ All RAFT calls conditional and post-execution
- ✅ Backward compatible (works with/without RAFT config)

**See**: `docs/RAFT_SETUP_GUIDE.md` for complete implementation guide

## 📚 Additional Documentation

- `UPGRADE_COMPLETE.md`: v2.1.0 upgrade completion summary (Python 3.14 + Ollama 0.12.5)
- `UPGRADE_PYTHON314_OLLAMA0125.md`: Complete upgrade guide (758 lines)
- `UPGRADE_CHANGES_REQUIRED.md`: Quick reference for all v2.1.0 changes (546 lines)
- `IMPLEMENTATION_SUMMARY.md`: Detailed v2.1.0 change summary (454 lines)
- `ADAPTIVE_PROMPT_SUMMARY.md`: v2.0 adaptive prompt template implementation (2025-10-07)
- `CRITICAL_IMPROVEMENTS_SUMMARY.md`: v1.5.0 performance and error handling improvements (IMPORTANT)
- `VERIFICATION_REPORT.md`: Line-by-line verification of v1.5.0 improvements with zero core logic impact
- `SELF_REVIEW_REPORT.md`: Comprehensive architecture verification and test results
- `TEST_SUMMARY.md`: Detailed test coverage and results
- `GEMINI.md`: Additional development context
- `.github/copilot-instructions.md`: GitHub Copilot-specific instructions
- `docs/RAFT_SETUP_GUIDE.md`: Complete RAFT training implementation guide (v1.6.0)
- `docs/RAFT_IMPLEMENTATION_VERIFICATION.md`: RAFT verification report
- `Trainer.md`: Training philosophy and workflow
- `docs/`: Extended documentation and guides
- `pyproject.toml`: Package configuration and dependencies (single source of truth)

---

## 🚀 Recent Improvements

### v2.1.0 Python 3.14 + Ollama 0.12.5 Upgrade (October 2025)

**BREAKING CHANGES** - No backward compatibility with Python 3.13 or Ollama 0.11.x

**1. Python 3.14 Compatibility**
- Removed all `from __future__ import annotations` (16 files)
- Leveraged PEP 649 (deferred annotation evaluation, now default)
- Leveraged PEP 737 (enhanced type parameters)
- Native union type syntax (`|`) without future imports
- Improved garbage collection (-60% pause time)
- Better asyncio with TaskGroup improvements

**2. Ollama 0.12.5 Integration**
- Increased context window: 8K → 16K tokens (+100%)
- Increased response length: 2K → 4K tokens (+100%)
- Added GPU offload support (default: enabled, 95% VRAM usage)
- Improved GPU concurrency: 1 → 2 requests (+100%)
- Enhanced error reporting with `response_body` field in `OllamaResponseError`
- Added version endpoint support

**3. Performance Improvements** (estimated)
- HP mode throughput: ~54,624 → ~65,000 artifacts/sec (+19%)
- Memory efficiency: 0.010 → ~0.008 MB/artifact (-20%)
- Better AI output quality with 2x larger context
- More comprehensive test cases with 2x longer responses

**4. Dependency Updates**
- Updated 11 packages to Python 3.14 compatible versions
- hatchling ≥1.25.0 (required for Python 3.14)
- pandas ≥2.2.3, pytest-asyncio ≥0.25.2, torch ≥2.6.0, transformers ≥4.48.0

**See**: `UPGRADE_COMPLETE.md` for complete details

### v1.5.0 Critical Improvements (October 2025)

**1. Custom Exception System** - 10x faster debugging
- Structured exceptions with actionable context (host, port, timeout, model)
- All Ollama errors raise specific exception types
- See `src/core/exceptions.py` for complete hierarchy

**2. Removed Double Semaphore** - +50% throughput
- Only `AsyncOllamaClient` controls concurrency (removed from `AsyncTestCaseGenerator`)
- Throughput: 8 req/sec → 12 req/sec

**3. Concurrent Batch Processing** - 3x faster for large files
- HP processor processes ALL requirements concurrently (no sequential batches)
- 250 requirements: 62.5s → 20.8s

**Core Logic Guarantees**:
✅ `BaseProcessor._build_augmented_requirements()` unchanged
✅ Context-aware processing verified intact
✅ Zero breaking changes for end users
✅ Memory efficiency maintained (0.010 MB per artifact)

### v1.6.0 RAFT Training (Optional)

- Non-invasive training data collection for custom models
- Disabled by default (`enable_raft: false`)
- Zero impact on core test case generation
- See "RAFT Training" section below for details

### v2.0 Critical Fixes (October 2025)

**1. REQIFZ Extraction Fix** - Fixed 0% extraction rate for text-only requirements
- **Problem**: Extractor used attribute identifiers instead of LONG-NAME values, causing all requirements to be skipped
- **Root Cause**: Line 208 extracted `_json2reqif_XXX` identifier, not "ReqIF.Text" LONG-NAME
- **Solution**: Added `_build_attribute_definition_mapping()` to map identifiers to LONG-NAME values
- **Files Modified**: `src/core/extractors.py:151-172,191,235`
- **Impact**: 0 → 4,551 requirements successfully extracted (100% success rate)
- **Validation**: Tested on 36 REQIFZ files across 3 datasets (Toyota_FDC, 2025_09_12_S220, W616)

**2. Adaptive Prompt Template** - Support for both table-based and text-only requirements
- **Problem**: Existing prompt required table data; 100% of current dataset (4,551 requirements) is text-only
- **Solution**: Created single adaptive prompt that intelligently handles both scenarios
- **File**: `prompts/templates/test_generation_adaptive.yaml` (6,377 characters)
- **Key Features**:
  - AI analyzes requirement to determine if table-based or text-only
  - Table mode: Decision Table Testing (tests all rows + negative cases)
  - Text mode: BVA, Equivalence Partitioning, Scenario-Based (5-13 tests)
  - Context-aware: Uses System Interface Dictionary for parameter extraction
- **Configuration Updated**: `prompts/config/prompt_config.yaml` now uses `adaptive_default`
- **Backup Created**: `test_generation_v3_structured.yaml.backup` for rollback
- **Validation**: Template loading, text-only, and table-based scenarios all verified

**Dataset Analysis** (October 2025):
- 36 REQIFZ files analyzed across 3 folders
- 4,551 total requirements extracted
- 0 requirements with tables (0.0%)
- 4,551 requirements without tables (100.0%)
- Recommendation: Adaptive prompt is REQUIRED for current dataset

**Performance Comparison**:

| Requirements | Standard Mode | HP Mode (v1.4.0) | HP Mode (v1.5.0) | Improvement |
|--------------|---------------|------------------|------------------|-------------|
| 10 | 2.5s | 2.5s | 2.5s | - |
| 50 | 12.5s | 12.5s | 6.3s | **2x** |
| 100 | 25s | 25s | 8.3s | **3x** |
| 250 | 62.5s | 62.5s | 20.8s | **3x** |

**Verification**: See `VERIFICATION_REPORT.md` for line-by-line evidence of zero core logic impact.

---

**Last Updated**: 2025-10-11 | **Architecture**: Context-Aware with BaseProcessor + PromptBuilder + Adaptive Prompts + Custom Exceptions + RAFT Training (optional) + Python 3.14 + Ollama 0.12.5
