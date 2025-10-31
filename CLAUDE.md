# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📋 Quick Reference

**Project**: AI-powered test case generator for automotive REQIFZ requirements
**Version**: v2.1.0 | **Python**: 3.14+ (no backward compatibility) | **Ollama**: v0.12.5+

**Essential Commands**:
```bash
# Development setup
pip install -e .[dev]              # Install with dev dependencies
pip install -e .                   # Production install only

# Running the application
ai-tc-generator input/file.reqifz --verbose           # Standard mode
ai-tc-generator input/ --hp --max-concurrent 4        # HP mode (3-9x faster)
python3 main.py input/file.reqifz --debug             # Development mode

# Testing
python3 -m pytest tests/core/ -v                      # Core unit tests (fast)
python3 -m pytest tests/ -v -m "not integration"      # All tests except integration
python3 -m pytest tests/ -v --cov=src                 # With coverage

# Code quality
ruff check src/ main.py utilities/ --fix             # Lint and auto-fix
ruff format src/ main.py utilities/                   # Format code
mypy src/ main.py --python-version 3.14               # Type checking

# Validation
ai-tc-generator --validate-prompts                    # Validate YAML templates
```

**Architecture Pattern**: `CLI → Processor → Generator → PromptBuilder → Ollama → Excel`

---

## ⚠️ CRITICAL: Context-Aware Processing Architecture

**DO NOT BREAK THIS - It's the heart of the system.**

The system REQUIRES context-aware artifact processing in `BaseProcessor._build_augmented_requirements()` (lines 62-126) which ALL processors inherit:

```python
current_heading = "No Heading"
info_since_heading = []

for obj in artifacts:
    if obj.get("type") == "Heading":
        current_heading = obj.get("text", "No Heading")
        info_since_heading = []  # Reset on new heading
    elif obj.get("type") == "Information":
        info_since_heading.append(obj)
    elif obj.get("type") == "System Requirement":
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
- Both standard and HP processors share this logic via `BaseProcessor`

**DO NOT:**
- Filter artifacts before iteration: `[obj for obj in artifacts if obj.get("type") == "System Requirement"]`
- Duplicate context logic in processors (use inheritance)
- Remove context fields from `PromptBuilder` templates

---

## 🏗️ Architecture Overview

### Processing Flow
```
main.py (CLI entry)
  ↓
Processor (standard or HP)
  ├─ BaseProcessor (shared context logic)
  ├─ REQIFArtifactExtractor (parse REQIFZ)
  ├─ _build_augmented_requirements() (add context)
  ↓
Generator (TestCaseGenerator or AsyncTestCaseGenerator)
  ├─ PromptBuilder (format prompts with context)
  ├─ OllamaClient/AsyncOllamaClient (AI generation)
  ├─ FastJSONResponseParser (parse AI responses)
  ├─ SemanticValidator (validate test cases)
  ├─ TestCaseDeduplicator (remove duplicates)
  ↓
Formatter (TestCaseFormatter or StreamingTestCaseFormatter)
  ↓
Excel/JSON Output
```

### Key Components

**BaseProcessor** (`src/processors/base_processor.py`):
- Shared logic for both standard and HP processors
- `_build_augmented_requirements()` - context-aware processing (DO NOT MODIFY)
- Eliminates code duplication between processors

**Processors** (`src/processors/`):
- `standard_processor.py`: Sequential processing with `TestCaseGenerator`
- `hp_processor.py`: Concurrent async processing with `AsyncTestCaseGenerator`
- Both inherit from `BaseProcessor` (zero duplication)

**Generators** (`src/core/generators.py`):
- `TestCaseGenerator`: Synchronous generation
- `AsyncTestCaseGenerator`: Concurrent generation with semaphore control
  - **IMPORTANT**: Has `generate_test_cases()` method for HP processor single-requirement calls
  - Has `generate_test_cases_batch()` for batch processing
- Both use shared `PromptBuilder` instance

**REQIFArtifactExtractor** (`src/core/extractors.py`):
- **CRITICAL FIX (v2.0)**: Lines 151-172, 191, 235 implement attribute definition mapping
- Without mapping, uses identifiers like `_json2reqif_XXX` instead of "ReqIF.Text"
- `_build_attribute_definition_mapping()` prevents extraction failures
- Extraction success rate should be >95%

**PromptBuilder** (`src/core/prompt_builder.py`):
- Stateless prompt construction
- Template variables: `heading`, `info_str`, `interface_str`, `requirement_text`
- Used by both sync and async generators

**Formatters** (`src/core/formatters.py`):
- `TestCaseFormatter`: Standard Excel export (16 columns)
- `StreamingTestCaseFormatter`: Memory-efficient streaming (HP mode)
- **CRITICAL (v2.1.0)**: Excel columns must match `_prepare_test_cases_for_excel` output:
  - Column 13: "Feature Group"
  - Column 16: "LinkTest" (not "Tests")
  - Total: 16 columns

---

## 🔧 Recent Fixes & Known Issues

### ✅ Fixed (v2.1.0 - Oct 31, 2025)

1. **HP Processor API**: Added `generate_test_cases()` to `AsyncTestCaseGenerator`
2. **Excel Formatter**: Fixed column names ("Feature Group", "LinkTest") - 16 columns total
3. **CLI Entry Point**: Removed duplicate `src/main.py`, unified to root `main.py`
4. **Dependencies**: `pyproject.toml` is single source of truth (requirements.txt deprecated)
5. **Code Quality**: Fixed 33 ruff errors → 0 errors
6. **HP Mode Logging**: Removed duplicate `max_concurrent` parameter in `main.py:284`

### ⚠️ Known Issues

1. **HP Mode Extraction** (pre-existing):
   - HP mode may show "no text content" for some requirements
   - Standard mode works fine on same files
   - Under investigation (not related to v2.1.0 fixes)

---

## 🧪 Testing

### Running Tests
```bash
# Fast unit tests (recommended for quick verification)
python3 -m pytest tests/core/ -v

# All tests except slow integration tests
python3 -m pytest tests/ -v -m "not integration and not slow"

# Specific test file
python3 -m pytest tests/core/test_generators.py -v

# With coverage
python3 -m pytest tests/ -v --cov=src --cov-report=term-missing
```

### Test Markers
```bash
-m "unit"          # Fast unit tests with mocks
-m "integration"   # Integration tests (require Ollama)
-m "slow"          # Tests taking >5 seconds
-m "async_test"    # Async/await tests
```

### CI/CD
GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push:
1. Lint & format check (ruff)
2. Type checking (mypy - continue-on-error)
3. Unit tests with coverage
4. Security scan (bandit)
5. Dependency check (pip-audit)
6. Build & package validation
7. YAML prompt validation

---

## 🐛 Common Issues & Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| **Import Errors** | `ModuleNotFoundError: No module named 'src'` | Run `pip install -e .[dev]` |
| **Context Loss** | Test cases lack context | Verify processors use `BaseProcessor._build_augmented_requirements()` |
| **Ollama Connection** | `OllamaConnectionError` | Start: `ollama serve`, verify: `ollama list` |
| **Missing Model** | `OllamaModelNotFoundError` | Install: `ollama pull llama3.1:8b` |
| **Requirements Skipped** | "no text content" warnings | Check attribute mapping in extractor lines 151-172 |
| **Excel Export Crash** | `KeyError` in HP mode | Verify 16 columns with "Feature Group", "LinkTest" |
| **HP Mode AttributeError** | `generate_test_cases` not found | Verify `AsyncTestCaseGenerator` has the method (v2.1.0 fix) |

---

## 🔍 Critical Files & Line Numbers

**DO NOT MODIFY WITHOUT UNDERSTANDING:**
- `src/processors/base_processor.py:62-126` - Context-aware processing core
- `src/core/extractors.py:151-172,191,235` - Attribute definition mapping (v2.0 fix)
- `src/core/formatters.py:363-447` - Streaming Excel formatter (16 columns)
- `main.py:278-285` - HP mode logging (no duplicate parameters)

**Safe to Modify:**
- `src/core/prompt_builder.py` - Prompt formatting (keep stateless)
- `prompts/templates/*.yaml` - Prompt templates (validate after changes)
- `src/config.py` - Configuration (Pydantic-based)
- `tests/` - Test files

---

## 📦 Dependency Management

**Single Source of Truth**: `pyproject.toml`

```bash
# Install production dependencies
pip install -e .

# Install with dev tools (ruff, pytest, mypy)
pip install -e .[dev]

# Install with training features (torch, transformers)
pip install -e .[training]

# Install everything
pip install -e .[all]
```

**Note**: `requirements.txt` is deprecated - use `pyproject.toml`

---

## 🚀 Performance

### Benchmarks (v2.1.0)
- **Standard mode**: ~7,254 artifacts/second
- **HP mode**: ~65,000 artifacts/second (9x faster)
- **Memory**: 0.008 MB per artifact (with `__slots__`)
- **Ollama context**: 16K tokens (8K → 16K with v0.12.5)
- **Response length**: 4K tokens (2K → 4K with v0.12.5)

### Optimization Notes
- HP mode uses `asyncio.TaskGroup` (Python 3.14+)
- Only `AsyncOllamaClient` has semaphore (not `AsyncTestCaseGenerator`)
- All classes use `__slots__` for 20-30% memory savings
- GPU concurrency: 2 parallel requests (Ollama 0.12.5)

---

## 📚 Documentation

- `ENHANCEMENT_SUMMARY.md` - Recent fixes and improvements (Oct 31, 2025)
- `TEST_REPORT.md` - End-to-end test verification
- `UPGRADE_COMPLETE.md` - Python 3.14 + Ollama 0.12.5 upgrade summary
- `docs/reviews/` - Comprehensive code review archive
- `.github/copilot-instructions.md` - Copilot-specific guidance

---

## 🎯 Development Workflow

1. **Make changes** to code
2. **Run tests**: `python3 -m pytest tests/core/ -v`
3. **Check quality**: `ruff check src/ main.py --fix`
4. **Verify E2E**: Test with real REQIFZ file
5. **Check Excel output**: Verify 16 columns if formatter changed
6. **Commit** with descriptive message

---

**Last Updated**: 2025-10-31 | **Python**: 3.14+ only | **Status**: Production-Ready ✅
