# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Instruction

Always read, understand and follow the guidelines from `System_Intructions.md` - this defines the "Vibe Coding" philosophy, review checklists, and documentation standards for this project.

## 📋 Quick Reference

**Project**: AI-powered test case generator for automotive REQIFZ requirements
**Version**: v2.2.0
**Status**: Production-Ready
**Python**: 3.14 or higher (no backward compatibility)
**Ollama**: v0.12.9+
**Vision Support**: ✅ Hybrid llama3.2-vision:11b + llama3.1:8b strategy
**Training**: ✅ RAFT training with vision support (v2.2.0+)

**Essential Commands**:
```bash
# Development setup
pip install -e .[dev]              # Install with dev dependencies (includes ruff, pytest, mypy)
pip install -e .[training]         # Add training dependencies (torch, transformers, peft)
pip install -e .[all]              # Everything (dev + training)

# Running the application
ai-tc-generator input/file.reqifz --verbose           # Standard mode (hybrid vision/text)
ai-tc-generator input/ --hp --max-concurrent 4        # HP mode (3-9x faster)
python3 main.py input/file.reqifz --debug             # Development mode with debug logging

# Testing (per System_Instructions.md: testing is non-negotiable)
python3 -m pytest tests/core/ -v                      # Core unit tests (fast)
python3 -m pytest tests/ -v -m "not integration"      # All except integration tests
python3 -m pytest tests/ -v --cov=src                 # With coverage report

# Code quality (must pass before committing)
ruff check src/ main.py utilities/ --fix             # Lint and auto-fix
ruff format src/ main.py utilities/                   # Format code
mypy src/ main.py --python-version 3.14               # Type checking

# Validation
ai-tc-generator --validate-prompts                    # Validate YAML templates after editing

# Quick verification (useful after installation)
ai-tc-generator --version                             # Check installed version
ai-tc-gen --help                                      # Test short alias (ai-tc-gen)
ollama list                                            # Verify Ollama models installed
```

**Architecture Pattern**: `CLI → Processor → Generator → PromptBuilder → Ollama (hybrid vision/text) → Excel`

**Hybrid Vision Strategy** (v2.2.0):
- Requirements **with images** → `llama3.2-vision:11b` (vision understanding of diagrams)
- Requirements **without images** → `llama3.1:8b` (faster text-only processing)
- Automatic per-requirement model selection via `ConfigManager.get_model_for_requirement()`

---

## ⚠️ CRITICAL: Context-Aware Processing Architecture

**DO NOT BREAK THIS - It's the heart of the system.**

The system REQUIRES context-aware artifact processing in `BaseProcessor._build_augmented_requirements()` (src/processors/base_processor.py:62-126) which ALL processors inherit:

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
- Information context resets after each requirement (no carryover between requirements)
- Both standard and HP processors share this logic via `BaseProcessor` inheritance

**DO NOT:**
- Filter artifacts before iteration: `[obj for obj in artifacts if obj.get("type") == "System Requirement"]` ❌
- Duplicate context logic in processors (use inheritance) ❌
- Remove context fields from `PromptBuilder` templates ❌

---

## 🏗️ Architecture Overview

### Processing Flow
```
main.py (CLI entry)
  ↓
Processor (standard or HP)
  ├─ BaseProcessor (shared context logic)
  ├─ REQIFArtifactExtractor (parse REQIFZ XML)
  │   ├─ Extract text artifacts from REQIF XML
  │   ├─ RequirementImageExtractor (extract & save images) [v2.1.1]
  │   └─ Augment artifacts with image metadata
  ├─ _build_augmented_requirements() (add context)
  ├─ Hybrid model selection (ConfigManager.get_model_for_requirement) [v2.2.0]
  ↓
Generator (TestCaseGenerator or AsyncTestCaseGenerator)
  ├─ _extract_image_paths() - Extract images from requirement [v2.2.0]
  ├─ PromptBuilder (format prompts with context + image context) [v2.2.0]
  ├─ OllamaClient/AsyncOllamaClient (AI generation)
  │   ├─ generate_response() - Text-only (llama3.1:8b)
  │   └─ generate_response_with_vision() - Vision model (llama3.2-vision:11b) [v2.2.0]
  ├─ FastJSONResponseParser (parse AI responses)
  ├─ SemanticValidator (validate test cases)
  ├─ TestCaseDeduplicator (remove duplicates)
  ↓
Formatter (TestCaseFormatter or StreamingTestCaseFormatter)
  ↓
Excel/JSON Output + Extracted Images
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
- **NEW (v2.1.1)**: Integrated image extraction via `RequirementImageExtractor`
  - Extracts external images and base64-embedded images from REQIFZ
  - Augments artifacts with image metadata (format, size, hashes)
  - Configurable via `config.image_extraction` settings

**RequirementImageExtractor** (`src/core/image_extractor.py`):
- Extracts images from REQIFZ files (external files and embedded base64)
- Supports PNG, JPEG, GIF, BMP, SVG, TIFF, WEBP
- Validates images using PIL/Pillow (optional)
- Saves images to `extracted_images/` directory
- Augments artifacts with image references for vision AI

**PromptBuilder** (`src/core/prompt_builder.py`):
- Stateless prompt construction
- Template variables: `heading`, `info_str`, `interface_str`, `requirement_text`, `image_context` [v2.2.0]
- `format_image_context()` - Provides vision model guidance for diagram analysis [v2.2.0]
- Used by both sync and async generators

**OllamaClient & AsyncOllamaClient** (`src/core/ollama_client.py`):
- **NEW (v2.2.0)**: Vision model support
  - `generate_response_with_vision()` - Sends images as base64 to vision models
  - Supports multiple images per requirement
  - Graceful fallback if images fail to load
  - Backward compatible (existing code unchanged)

**Formatters** (`src/core/formatters.py`):
- `TestCaseFormatter`: Standard Excel export (16 columns)
- `StreamingTestCaseFormatter`: Memory-efficient streaming (HP mode)
- **CRITICAL (v2.1.0)**: Excel columns must match `_prepare_test_cases_for_excel` output:
  - Column 13: "Feature Group"
  - Column 16: "LinkTest" (not "Tests")
  - Total: 16 columns

---

## 🎯 Architectural Decisions

**Why BaseProcessor exists:**
- **DRY Principle**: Context logic shared between standard and HP modes
- Both processors need identical context-building (heading, info, interfaces)
- Changes to context logic automatically apply to both modes
- Zero code duplication = easier maintenance and fewer bugs

**Why hybrid vision strategy:**
- Vision models are **slower** (4-5s vs 2-3s per requirement)
- Vision models use **more VRAM** (10-12GB vs 6-7GB)
- Auto-selection optimizes: use vision only when images present
- **Result**: Best of both worlds (speed + accuracy)

**Why async in HP mode only:**
- **Standard mode** is simpler, easier to debug, more predictable
- **HP mode** trades complexity for 3-9x performance improvement
- Users choose based on their needs (correctness/simplicity vs speed)
- Async adds cognitive overhead - only worth it for large-scale processing

**Why Pydantic for config:**
- Type validation at runtime (catches config errors early)
- Environment variable support built-in (12-factor app pattern)
- Auto-documentation of config schema
- IDE autocomplete for config fields

---

## 🔧 Recent Fixes & Known Issues

### ✅ Fixed (v2.2.0 - Nov 3, 2025)

1. **Test Helper Functions for XHTML Format**: Created comprehensive test infrastructure
   - New `tests/helpers/` package with 8 helper functions
   - `create_test_artifact()`, `create_test_requirement()`, `create_test_heading()`, etc.
   - Automatically generate XHTML-formatted test data matching production output
   - 10 verification tests ensure helpers produce correct format
   - Updated 11 integration tests to use helpers (223/255 tests passing, 87%)
   - **Documentation**: `tests/helpers/USAGE_EXAMPLES.md`
   - **Impact**: All new tests must use helpers to match v2.2.0 XHTML format

### ✅ Fixed (v2.2.0 - Nov 2, 2025)

2. **Vision Training Infrastructure**: Extended RAFT training to support vision models
   - `RAFTDataCollector` now captures images with base64 encoding
   - `RAFTDatasetBuilder` builds hybrid vision/text datasets
   - `VisionRAFTTrainer` - complete training pipeline for llama3.2-vision
   - `QualityScorer` includes image quality and relevance metrics
   - **Files Modified**: 5 files, ~810 lines added
   - **Zero Breaking Changes**: Fully backward compatible

### ✅ Fixed (v2.2.0 - Nov 1, 2025)

3. **Vision Model Support - Hybrid Strategy**: Implemented intelligent model selection
   - Added `generate_response_with_vision()` to both sync and async Ollama clients
   - Generators automatically extract image paths and use vision methods when images present
   - `ConfigManager.get_model_for_requirement()` selects appropriate model per requirement
   - `PromptBuilder.format_image_context()` provides vision-specific guidance
   - Processors (standard and HP) apply hybrid strategy per requirement
   - Configuration: `vision_model`, `enable_vision`, `vision_context_window` settings
   - **Impact**: Requirements with diagrams use llama3.2-vision:11b, text-only use llama3.1:8b
   - **Files Modified**: 9 files, ~424 lines added

### ✅ Fixed (v2.1.1 - Nov 1, 2025)

4. **Image Extraction Integration**: Fully integrated image extraction into processing pipeline
   - Updated `REQIFArtifactExtractor` and `HighPerformanceREQIFArtifactExtractor` to extract images
   - Added config parameter to extractors for image extraction settings
   - Processors now pass config to extractors (standard_processor.py:90, hp_processor.py:117)
   - Extracts external images and base64-embedded images from REQIFZ files
   - Saves images to `extracted_images/` directory with metadata
   - Configurable via `config.image_extraction.enable_image_extraction`

### ⚠️ Known Issues

1. **HP Mode Extraction** (pre-existing):
   - HP mode may show "no text content" for some requirements
   - Standard mode works fine on same files
   - Under investigation (not related to v2.1.0+ fixes)

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

# Run single test
python3 -m pytest tests/test_refactoring.py::TestBaseProcessor::test_build_augmented_requirements_with_context -v
```

### Test Markers
```bash
-m "unit"          # Fast unit tests with mocks
-m "integration"   # Integration tests (require Ollama)
-m "slow"          # Tests taking >5 seconds
-m "async_test"    # Async/await tests
```

### Writing Tests with XHTML Format (v2.2.0+)

**CRITICAL**: After vision integration, all text fields use XHTML format. Tests must use helper functions.

```python
# Import helpers
from tests.helpers import (
    create_test_heading,
    create_test_information,
    create_test_requirement,
    create_test_interface,
    create_test_artifact_with_images,
)

# ❌ WRONG - Plain text (will fail)
artifacts = [
    {"type": "Heading", "text": "Door System"},
    {"type": "System Requirement", "id": "REQ_001", "text": "Door shall lock"}
]

# ✅ CORRECT - Use helpers for XHTML format
artifacts = [
    create_test_heading("Door System", heading_id="H_001"),
    create_test_requirement("Door shall lock", requirement_id="REQ_001")
]

# ❌ WRONG - Exact match assertion
assert artifact["heading"] == "Door System"

# ✅ CORRECT - Check within XHTML
assert "Door System" in artifact["heading"]
```

**Helper Functions** (in `tests/helpers/`):
- `create_test_artifact()` - General purpose artifact
- `create_test_requirement()` - System Requirements
- `create_test_heading()` - Headings
- `create_test_information()` - Information blocks
- `create_test_interface()` - System Interfaces
- `create_test_artifact_with_images()` - Requirements with `<object>` tags
- `create_augmented_requirement()` - Full context-enriched requirement

**Documentation**: See `tests/helpers/USAGE_EXAMPLES.md` for complete examples.

### CI/CD
GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push:
1. Lint & format check (ruff)
2. Type checking (mypy - continue-on-error)
3. Unit tests with coverage
4. Security scan (bandit)
5. Dependency check (pip-audit)
6. Build & package validation
7. YAML prompt validation

### Test Suite Status (as of Nov 3, 2025)
- **Core unit tests**: 83/83 passing (100%) ✅
- **Integration tests**: 223/255 passing (87%) ✅
- **Helper verification**: 10/10 passing (100%) ✅
- **Production validation**: 104/104 custom tests passing (100%) ✅

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
| **Vision Model Not Found** | `OllamaModelNotFoundError` for vision | Install: `ollama pull llama3.2-vision:11b` |
| **Out of VRAM** | Vision model fails | Reduce concurrency or disable vision: `export OLLAMA__ENABLE_VISION=false` |

---

## 🔍 Debugging Workflow

**Common debugging pattern:**

1. **Check logs first** (structured JSON logs):
   ```bash
   tail -f output/logs/*.json | jq '.'  # Live log monitoring (if jq installed)
   tail -f output/logs/*.json            # Without jq
   ```

2. **Enable debug mode** for verbose output:
   ```bash
   python3 main.py input/file.reqifz --debug
   ```

3. **Test single requirement** (modify extractor temporarily):
   ```python
   # In src/core/extractors.py, add after artifact extraction:
   artifacts = artifacts[:5]  # Test with first 5 artifacts only
   ```

4. **Validate Ollama connection**:
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags

   # Test model generation
   curl http://localhost:11434/api/generate -d '{
     "model": "llama3.1:8b",
     "prompt": "test",
     "stream": false
   }'
   ```

5. **Isolate the problem**:
   - Extractor issue? Check `extracted_images/` directory
   - Generator issue? Look at Ollama logs
   - Formatter issue? Check Excel output structure
   - Context issue? Add logging in `BaseProcessor._build_augmented_requirements()`

6. **Compare with working example**:
   ```bash
   # Process a known-good file first
   ai-tc-generator input/sample_working.reqifz --verbose
   # Then process the problematic file
   ai-tc-generator input/problematic.reqifz --debug
   ```

**Debugging Tips:**
- Use `--verbose` for progress info, `--debug` for detailed logs
- Check `output/logs/` for structured error information
- HP mode failures: Try standard mode first to isolate concurrency issues
- Vision model issues: Disable vision to test text-only path

---

## 🔍 Critical Files & Line Numbers

**DO NOT MODIFY WITHOUT UNDERSTANDING:**
- `src/processors/base_processor.py:62-126` - Context-aware processing core
- `src/core/extractors.py:151-172,191,235` - Attribute definition mapping (v2.0 fix)
- `src/core/formatters.py:363-447` - Streaming Excel formatter (16 columns)
- `src/core/ollama_client.py:146-266,578-689` - Vision model support (v2.2.0)
- `src/core/generators.py:41-62,85-98,200-221,351-367` - Image path extraction & vision logic (v2.2.0)
- `src/config.py:79-92,475-498` - Vision model config & hybrid selection (v2.2.0)
- `main.py:278-285` - HP mode logging (no duplicate parameters)

**Safe to Modify:**
- `src/core/prompt_builder.py` - Prompt formatting (keep stateless)
- `prompts/templates/*.yaml` - Prompt templates (validate after changes with `--validate-prompts`)
- `src/config.py` - Configuration (Pydantic-based, follow existing patterns)
- `tests/` - Test files (required for all new features per System_Instructions.md)
- `tests/helpers/test_artifact_builder.py` - Test helper functions (update if XHTML format changes)

---

## ⚠️ When NOT to Modify Core Logic

**Before modifying these areas, understand the full system impact:**

**Context-Aware Processing** (`BaseProcessor._build_augmented_requirements()`):
- ❌ Do NOT filter artifacts before iteration
- ❌ Do NOT duplicate this logic in processors
- ❌ Do NOT change the reset behavior for `info_since_heading`
- ✅ DO make changes here (not in individual processors) if context logic needs updating

**Attribute Definition Mapping** (extractor lines 151-172, 191, 235):
- ❌ Do NOT remove or bypass the mapping logic
- ❌ Do NOT assume attribute names without mapping
- ✅ DO add new attribute types to the mapping if needed

**Excel Formatter Structure** (16 columns, specific names):
- ❌ Do NOT change column count without updating formatters
- ❌ Do NOT rename columns without updating both formatters
- ✅ DO update both `TestCaseFormatter` and `StreamingTestCaseFormatter` together

**Hybrid Vision Model Selection**:
- ❌ Do NOT bypass `ConfigManager.get_model_for_requirement()`
- ❌ Do NOT hardcode model selection in processors
- ✅ DO modify selection logic in `ConfigManager` only

**When in doubt:**
1. Search for usages: `rg "function_name" src/`
2. Run full test suite: `python3 -m pytest tests/ -v`
3. Test with real REQIFZ files before committing
4. Ask in code review if the change affects core logic

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

**Python Version**: 3.14 or higher (no backward compatibility per System_Instructions.md)

---

## 🚀 Performance

### Benchmarks (v2.2.0)
- **Standard mode**: ~7,254 artifacts/second
- **HP mode**: ~65,000 artifacts/second (9x faster)
- **Memory**: 0.008 MB per artifact (with `__slots__`)
- **Ollama context**: 16K tokens (text), 32K-128K tokens (vision)
- **Response length**: 4K tokens (2K → 4K with Ollama v0.12.5)

### Vision Model Performance (v2.2.0)
- **llama3.1:8b (text)**: ~2-3 sec/requirement, 6-7 GB VRAM
- **llama3.2-vision:11b**: ~4-5 sec/requirement, 10-12 GB VRAM
- **Hybrid strategy**: ~10-15 min for 70 files (vs 5-10 min text-only)
  - 42 files with images → vision model
  - 28 files without images → text model (faster)

### Optimization Notes
- HP mode uses `asyncio.TaskGroup` (Python 3.14+)
- Only `AsyncOllamaClient` has semaphore (not `AsyncTestCaseGenerator`)
- All classes use `__slots__` for 20-30% memory savings
- GPU concurrency: 2 parallel requests (Ollama 0.12.5)

---

## 📚 Documentation

### Architecture & Design
- `VISION_MODEL_IMPLEMENTATION_SUMMARY.md` - Vision model hybrid strategy (Nov 1, 2025)
- `VISION_TRAINING_IMPLEMENTATION_SUMMARY.md` - Vision training infrastructure (Nov 2, 2025)
- `LLAMA32_VISION_MIGRATION_PLAN.md` - Comprehensive vision migration guide
- `IMAGE_TO_AI_GAP_ANALYSIS.md` - Image extraction to vision model analysis
- `ENHANCEMENT_SUMMARY.md` - Recent fixes and improvements (Oct 31, 2025)
- `TEST_REPORT.md` - End-to-end test verification
- `UPGRADE_COMPLETE.md` - Python 3.14 + Ollama 0.12.5 upgrade summary

### Test Infrastructure & Validation
- `TEST_FIX_COMPLETE_SUMMARY.md` - Test helper implementation summary (Nov 3, 2025)
- `OPTIONAL_TASKS_SUMMARY.md` - Performance & training test analysis (Nov 3, 2025)
- `tests/helpers/USAGE_EXAMPLES.md` - Test helper function usage guide
- `tests/helpers/test_artifact_builder.py` - XHTML test artifact builders

### Development Guidelines
- `System_Intructions.md` - **MUST READ**: Vibe coding principles, review guidelines, documentation standards
- `.github/copilot-instructions.md` - Copilot-specific guidance (aligned with System_Instructions.md)
- `docs/reviews/` - Comprehensive code review archive

### Training Documentation
- `docs/training/training_guideline.md` - **Complete vision model training guide** (consolidated v2.0, Nov 2025)
  - Includes RAFT methodology, image annotation, dataset preparation
  - Step-by-step workflow with utility scripts
  - Hardware requirements, best practices, troubleshooting
- `docs/training/TRAINING_GUIDE.md` - RAFT training for text models
- `docs/training/RAFT_TECHNICAL.md` - RAFT implementation details
- `docs/training/MODEL_TRAINING_GUIDE.md` - Model training and fine-tuning
- `utilities/build_vision_dataset.py` - Script to build vision RAFT dataset
- `utilities/train_vision_model.py` - Script to train custom vision models

---

## 🚀 Quick Start for New Contributors

**First time working on this codebase?**

### Step 1: Read Documentation (in this order)
1. **`System_Intructions.md`** - Coding philosophy and "Vibe Coding" principles
2. **This file (CLAUDE.md)** - Architecture, commands, and critical patterns
3. **`README.md`** - User-facing documentation and features

### Step 2: Set Up Environment
```bash
# Clone and install
git clone <repository-url>
cd AI_TC_Generator_v04_w_Trainer
pip install -e .[dev]

# Verify installation
ai-tc-generator --version
python3 -m pytest tests/core/ -v    # Should pass 83/83 tests

# Install Ollama models
ollama pull llama3.1:8b
ollama pull llama3.2-vision:11b
```

### Step 3: Understand the Flow
Make a small change to see how data flows through the system:

```python
# Add a log statement in src/processors/base_processor.py:
# Around line 75 (inside _build_augmented_requirements)
print(f"DEBUG: Processing requirement {obj.get('id')} with heading: {current_heading}")
```

Run it:
```bash
python3 main.py input/sample.reqifz --debug
```

Observe how context (heading, info, interfaces) flows through each requirement.

### Step 4: Make Your First Change
Try something simple first:
- Add a new validation rule in `src/core/validators.py`
- Write a test for it in `tests/core/test_validators.py`
- Run tests: `python3 -m pytest tests/core/test_validators.py -v`
- Check code quality: `ruff check src/core/validators.py --fix`

### Step 5: Before Your First Commit
```bash
# Run full test suite
python3 -m pytest tests/ -v

# Check code quality
ruff check src/ main.py utilities/ --fix
ruff format src/ main.py utilities/

# Type checking
mypy src/ main.py --python-version 3.14

# If you modified prompts
ai-tc-generator --validate-prompts
```

### Key Concepts to Understand
1. **Context-Aware Processing**: See "CRITICAL: Context-Aware Processing Architecture" section
2. **Hybrid Vision Strategy**: Requirements with images use vision model, others use text model
3. **BaseProcessor Inheritance**: Standard and HP processors share core logic
4. **Test Helpers**: Use `tests/helpers/` functions for XHTML-formatted test data

### Common First Contributions
- Add new prompt templates in `prompts/templates/`
- Improve error messages in `src/core/exceptions.py`
- Add new validators in `src/core/validators.py`
- Enhance documentation in `docs/`
- Write tests for uncovered code paths

**Need help?** Check the "Common Issues & Solutions" and "Debugging Workflow" sections below.

---

## 🎯 Development Workflow

1. **Make changes** to code (follow System_Instructions.md principles)
2. **Write tests** alongside implementation (per System_Instructions.md: testing is non-negotiable)
3. **Run tests**: `python3 -m pytest tests/core/ -v`
4. **Check quality**: `ruff check src/ main.py --fix` and `ruff format ...`
5. **Type check**: `mypy src/ main.py --python-version 3.14`
6. **Verify E2E**: Test with real REQIFZ file
7. **Check Excel output**: Verify 16 columns if formatter changed
8. **Validate prompts**: If templates modified: `ai-tc-generator --validate-prompts`
9. **Update docs**: Per System_Instructions.md, documentation must be kept in sync
10. **Commit** with descriptive message

---

## 🔍 Vision Model Configuration (v2.2.0)

### Enable/Disable Vision

```bash
# Default: Vision enabled (hybrid strategy)
# Requirements with images use llama3.2-vision:11b automatically

# Disable vision (always use text model)
export OLLAMA__ENABLE_VISION=false

# Change vision model
export OLLAMA__VISION_MODEL="llama3.2-vision:90b"

# Adjust vision context window
export OLLAMA__VISION_CONTEXT_WINDOW=65536
```

### Hybrid Strategy Details

**Automatic Model Selection** (per requirement):
```python
# In ConfigManager.get_model_for_requirement():
if requirement.has_images and config.ollama.enable_vision:
    return config.ollama.vision_model  # llama3.2-vision:11b
else:
    return config.ollama.synthesizer_model  # llama3.1:8b
```

**Processors automatically apply hybrid strategy**:
- Standard processor: `standard_processor.py:126-140`
- HP processor: `hp_processor.py:167-178`

**Logs indicate model selection**:
```
⚡ Processing REQ_123 (heading: ACC) - Using llama3.2-vision:11b (has 8 images)
⚡ Processing REQ_124 (heading: Diagnostics)  # Uses llama3.1:8b (no images)
```

### Vision Model Requirements

**Hardware**:
- Minimum: 12 GB VRAM (single request)
- Recommended: 24 GB VRAM (HP mode with 4 concurrent)
- CPU fallback: Possible but 10-20x slower

**Model Installation**:
```bash
# Install vision model
ollama pull llama3.2-vision:11b

# Verify
ollama list | grep llama3.2-vision
```

---

## 🎓 Vision Model Training (v2.2.0+)

### RAFT Training with Images

The training infrastructure now supports **vision model fine-tuning** using RAFT methodology with images:

**Key Features**:
- **Image Capture**: Automatically collects images during RAFT data collection
- **Image Annotation**: Expert annotation of oracle/distractor images
- **Hybrid Datasets**: Mix text-only and vision examples
- **Quality Metrics**: Automated image quality and relevance scoring
- **Vision Training Pipeline**: Complete pipeline for training custom vision models

### Quick Training Workflow

```bash
# 1. Enable RAFT collection (images captured automatically)
export AI_TG_ENABLE_RAFT=true
export AI_TG_COLLECT_TRAINING_DATA=true

# 2. Process requirements to collect data
ai-tc-generator input/ --hp --verbose

# 3. Check collection stats (includes image metrics)
python3 -c "
from src.training.raft_collector import RAFTDataCollector
stats = RAFTDataCollector('training_data/collected').get_collection_stats()
print(f'Collected: {stats[\"total_collected\"]} examples')
print(f'With images: {stats[\"with_images\"]} ({stats[\"total_images\"]} images)')
"

# 4. Annotate examples (text context + images)
# Edit JSON files in training_data/collected/
# Mark oracle/distractor for both context and images

# 5. Build vision RAFT dataset
python3 -c "
from src.training.raft_dataset_builder import RAFTDatasetBuilder
builder = RAFTDatasetBuilder(
    validated_dir='training_data/validated',
    output_dir='training_data/raft_dataset'
)
examples = builder.build_dataset(min_quality=3)
builder.save_dataset(examples, 'vision_raft_dataset')
"

# 6. Train vision model
python3 -c "
from src.training.vision_raft_trainer import create_vision_training_pipeline
trainer = create_vision_training_pipeline(
    dataset_path='training_data/raft_dataset/vision_raft_dataset.jsonl',
    base_model='llama3.2-vision:11b',
    output_model='automotive-tc-vision-raft-v1'
)
result = trainer.train()
print(f'Training completed: {result[\"success\"]}')
"

# 7. Deploy trained model
export OLLAMA__VISION_MODEL="automotive-tc-vision-raft-v1"
```

### Training Data Format

Vision RAFT examples include base64-encoded images:

```json
{
  "requirement_id": "REQ_001",
  "requirement_text": "System shall process ACC signals...",
  "images": [
    {
      "id": "IMG_0",
      "base64": "iVBORw0KGgo...",
      "image_type": "state_machine",
      "relevance": "oracle",
      "description": "ACC state machine with 4 states"
    }
  ],
  "has_images": true,
  "context_annotation": {
    "oracle_context": ["HEADING", "IF_001", "IMG_0"],
    "distractor_context": ["INFO_2", "IMG_1"]
  }
}
```

### Image Quality Metrics (v2.2.0)

Automated quality assessment includes vision metrics:

```python
from src.training.quality_scorer import QualityScorer

scorer = QualityScorer()
assessment = scorer.assess_example_quality(example)

print(f"Overall score: {assessment.metrics.overall_score:.2f}")
print(f"Image quality: {assessment.metrics.image_quality_score:.2f}")
print(f"Image relevance: {assessment.metrics.image_relevance_score:.2f}")
```

### Training Documentation

- **Vision Training Guide**: `docs/training/training_guideline.md` (complete consolidated guide)
  - Comprehensive RAFT training for vision models
  - Includes utility scripts: `utilities/build_vision_dataset.py`, `utilities/train_vision_model.py`
  - Hardware requirements, monitoring, evaluation, troubleshooting
- **RAFT Technical**: `docs/training/RAFT_TECHNICAL.md` (implementation details)
- **Training Guide**: `docs/training/TRAINING_GUIDE.md` (text model training)

---

**Last Updated**: 2025-11-07 | **Python**: 3.14 or higher | **Status**: Production-Ready ✅
