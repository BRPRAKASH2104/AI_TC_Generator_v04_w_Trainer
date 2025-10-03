# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

## 🏗️ Architecture Overview

### High-Level Structure

```
main.py (CLI) → Processor (standard/hp) → Generator → PromptBuilder → Ollama API
                     ↓
                BaseProcessor (shared context logic)
                     ↓
          Extract → Augment with context → Generate → Format to Excel
```

### Key Components

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

# High-performance mode (2.5x faster)
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
mypy src/ main.py --python-version 3.13

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

**Generators** (`src/core/generators.py`):
- Both generators must use shared `PromptBuilder` instance
- Do not create TestCaseGenerator inside AsyncTestCaseGenerator
- Maintain stateless design with `__slots__`

**PromptBuilder** (`src/core/prompt_builder.py`):
- Keep stateless (only yaml_manager attribute)
- Context formatting methods must be static
- Template variables must include: `info_str`, `interface_str`, `heading`

**YAML Templates** (`prompts/templates/`):
- Run `ai-tc-generator --validate-prompts` after changes
- Templates expect context variables: `heading`, `info_str`, `interface_str`
- Test with real REQIFZ files after template changes

### Python 3.13+ Features Used

- **PEP 695 Type Aliases**: `type JSONObj[T] = dict[str, T]`
- **Pattern Matching**: `match`/`case` for XML processing
- **__slots__**: Memory optimization (20-30% reduction)
- **Async/Await**: Concurrent processing in HP mode

## 📊 Current System Status

**Version**: v1.4.0 | **Python**: 3.13.7+ | **Ollama**: v0.11.10+

**Test Status**:
- 140/164 tests passing (85% success rate)
- 100% coverage on critical paths (context-aware processing, BaseProcessor, PromptBuilder)
- Known issues: 2 HP async test mocking issues, 22 legacy integration tests need updating

**Architecture Status**:
- ✅ BaseProcessor refactoring: Complete (0% code duplication)
- ✅ PromptBuilder decoupling: Complete (no awkward coupling)
- ✅ Context-aware processing: Verified working correctly
- ✅ Import structure: All absolute imports
- ✅ Dependency management: Single source (pyproject.toml)

**Performance**:
- Standard mode: ~7,254 artifacts/second
- HP mode: ~18,208 artifacts/second (2.5x faster)
- Memory efficiency: 0.010 MB per artifact

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
```

## 🐛 Common Issues and Solutions

**Import Errors**: Ensure `pip install -e .[dev]` was run in the project root

**Context Loss**: Check that processors use `BaseProcessor._build_augmented_requirements()` and do not filter artifacts prematurely

**Template Issues**: Run `ai-tc-generator --validate-prompts` to check YAML syntax

**Ollama Connection**: Verify service with `ollama list` and ensure models are pulled

**Test Failures**: Check that all imports are absolute (not relative) from `src` root

**Performance Issues**: Use `--hp` mode for 2.5x speedup on multi-requirement files

## 📚 Additional Documentation

- `SELF_REVIEW_REPORT.md`: Comprehensive architecture verification and test results
- `TEST_SUMMARY.md`: Detailed test coverage and results
- `GEMINI.md`: Additional development context
- `.github/copilot-instructions.md`: GitHub Copilot-specific instructions
- `docs/`: Extended documentation and guides
- `pyproject.toml`: Package configuration and dependencies (single source of truth)

---

**Last Updated**: 2025-10-01 | **Architecture**: Context-Aware with BaseProcessor + PromptBuilder
