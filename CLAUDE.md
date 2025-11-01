# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Instruction

Always read, understand and follow the guidelines from System_Instruction.md.

## 📋 Quick Reference

**Project**: AI-powered test case generator for automotive REQIFZ requirements
**Version**: v2.2.0 | **Python**: 3.14+ (no backward compatibility) | **Ollama**: v0.12.5+
**Vision Support**: ✅ Hybrid llama3.2-vision:11b + llama3.1:8b strategy

**Essential Commands**:
```bash
# Development setup
pip install -e .[dev]              # Install with dev dependencies
pip install -e .                   # Production install only

# Running the application
ai-tc-generator input/file.reqifz --verbose           # Standard mode (hybrid vision/text)
ai-tc-generator input/ --hp --max-concurrent 4        # HP mode (3-9x faster, hybrid)
python3 main.py input/file.reqifz --model llama3.2-vision:11b --verbose  # Force vision model
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

**Architecture Pattern**: `CLI → Processor → Generator → PromptBuilder → Ollama (hybrid vision/text) → Excel`

**Hybrid Vision Strategy** (v2.2.0):
- Requirements with images → `llama3.2-vision:11b` (vision understanding)
- Requirements without images → `llama3.1:8b` (faster text-only)
- Automatic per-requirement model selection via `ConfigManager.get_model_for_requirement()`

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
- Augments artifacts with image references for future OCR/vision AI

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

## 🔧 Recent Fixes & Known Issues

### ✅ Fixed (v2.2.0 - Nov 1, 2025)

1. **Vision Model Support - Hybrid Strategy**: Implemented intelligent model selection
   - Added `generate_response_with_vision()` to both sync and async Ollama clients
   - Generators automatically extract image paths and use vision methods when images present
   - `ConfigManager.get_model_for_requirement()` selects appropriate model per requirement
   - `PromptBuilder.format_image_context()` provides vision-specific guidance
   - Processors (standard and HP) apply hybrid strategy per requirement
   - Configuration: `vision_model`, `enable_vision`, `vision_context_window` settings
   - **Impact**: Requirements with diagrams use llama3.2-vision:11b, text-only use llama3.1:8b
   - **Files Modified**: 9 files, ~424 lines added
   - **Zero Breaking Changes**: Fully backward compatible

### ✅ Fixed (v2.1.1 - Nov 1, 2025)

1. **Image Extraction Integration**: Fully integrated image extraction into processing pipeline
   - Updated `REQIFArtifactExtractor` and `HighPerformanceREQIFArtifactExtractor` to extract images
   - Added config parameter to extractors for image extraction settings
   - Processors now pass config to extractors (standard_processor.py:90, hp_processor.py:117)
   - Extracts external images and base64-embedded images from REQIFZ files
   - Saves images to `extracted_images/` directory with metadata
   - Configurable via `config.image_extraction.enable_image_extraction`

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
| **Vision Model Not Found** | `OllamaModelNotFoundError` for vision | Install: `ollama pull llama3.2-vision:11b` |
| **Out of VRAM** | Vision model fails | Reduce concurrency or disable vision: `export OLLAMA__ENABLE_VISION=false` |

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

### Benchmarks (v2.2.0)
- **Standard mode**: ~7,254 artifacts/second
- **HP mode**: ~65,000 artifacts/second (9x faster)
- **Memory**: 0.008 MB per artifact (with `__slots__`)
- **Ollama context**: 16K tokens (text), 32K-128K tokens (vision)
- **Response length**: 4K tokens (2K → 4K with v0.12.5)

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

- `VISION_MODEL_IMPLEMENTATION_SUMMARY.md` - Vision model hybrid strategy (Nov 1, 2025)
- `LLAMA32_VISION_MIGRATION_PLAN.md` - Comprehensive vision migration guide
- `IMAGE_TO_AI_GAP_ANALYSIS.md` - Image extraction to vision model analysis
- `ENHANCEMENT_SUMMARY.md` - Recent fixes and improvements (Oct 31, 2025)
- `TEST_REPORT.md` - End-to-end test verification
- `UPGRADE_COMPLETE.md` - Python 3.14 + Ollama 0.12.5 upgrade summary
- `System_Intructions.md` - Vibe coding principles and review guidelines
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

**Last Updated**: 2025-11-01 | **Python**: 3.14+ only | **Status**: Production-Ready ✅
