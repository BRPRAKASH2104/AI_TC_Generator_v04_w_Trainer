# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ **CURRENT SYSTEM STATUS**

**Last Updated**: 2025-09-30 | **Python**: 3.13.7+ | **Ollama**: v0.11.10+ | **Test Suite**: 62 PASSING, 14 FAILING | **Package**: v1.4.0 | **Architecture**: ✅ CONTEXT-AWARE RESTORED

## 🎯 **CRITICAL: Context-Aware Processing (v03 Logic Restored)**

**This system requires context-aware artifact processing to generate high-quality test cases.**

### Why Context Matters

The AI model generates better test cases when given rich contextual information:
- **Heading context**: Which feature section the requirement belongs to
- **Information artifacts**: Explanatory notes collected since the last heading
- **System interfaces**: Global dictionary of inputs/outputs/signals

### Architecture Pattern (DO NOT BREAK)

Both `standard_processor.py` and `hp_processor.py` **MUST** iterate through ALL artifacts (not just System Requirements) to build context:

```python
# ✅ CORRECT: Context-aware iteration
current_heading = "No Heading"
info_since_heading = []

for obj in artifacts:
    if obj.get("type") == "Heading":
        current_heading = obj.get("text", "No Heading")
        info_since_heading = []
    elif obj.get("type") == "Information":
        info_since_heading.append(obj)
    elif obj.get("type") == "System Requirement" and obj.get("table"):
        # Augment requirement with context BEFORE passing to generator
        augmented_requirement = obj.copy()
        augmented_requirement.update({
            "heading": current_heading,
            "info_list": info_since_heading.copy(),
            "interface_list": system_interfaces
        })
        # Generate test cases with enriched context
        test_cases = generator.generate_test_cases_for_requirement(
            augmented_requirement, model, template
        )
        info_since_heading = []  # Reset after each requirement
```

```python
# ❌ WRONG: Premature filtering loses context
system_requirements = [obj for obj in artifacts if obj.get("type") == "System Requirement"]
for requirement in system_requirements:
    # This loses heading and information context!
    test_cases = generator.generate_test_cases_for_requirement(requirement, model, template)
```

### Generator Context Formatting

`generators.py` includes helper methods that **MUST** be used in `_build_prompt_from_template()`:

```python
# Required template variables (lines 104-107 in generators.py)
variables = {
    "requirement_id": requirement.get("id", "UNKNOWN"),
    "heading": requirement.get("heading", ""),
    "table_str": self._format_table_for_prompt(requirement.get("table")),
    "row_count": requirement.get("table", {}).get("rows", 0),
    "voltage_precondition": "1. Voltage= 12V\n2. Bat-ON",
    # Context-aware fields (REQUIRED):
    "info_str": self._format_info_for_prompt(requirement.get("info_list", [])),
    "interface_str": self._format_interfaces_for_prompt(requirement.get("interface_list", []))
}
```

Helper methods (lines 184-213 in generators.py):
- `_format_info_for_prompt(info_list)` → Returns bullet-point formatted string or "None"
- `_format_interfaces_for_prompt(interface_list)` → Returns "ID: Description" formatted string or "None"

### YAML Template Expectations

The prompt template in `prompts/templates/test_generation_v3_structured.yaml` expects these variables:
- `heading` (required)
- `info_str` (optional, default: "None")
- `interface_str` (optional, default: "None")

## 📚 Documentation Quick Navigation

| Section | What You'll Find |
|---------|------------------|
| **[🚀 Quick Start Guide](#-quick-start-guide)** | Installation options and first steps |
| **[📋 CLI Command Reference](#-cli-command-reference)** | Complete command-line interface guide |
| **[🧪 Development & Testing](#-development--testing-guide)** | Development setup and testing commands |
| **[🤖 AI Model Setup](#-ai-model-setup-ollama)** | Ollama installation and configuration |
| **[🏗️ Architecture](#-architecture-overview)** | Modular system design and data flow |

### ⚡ Most Common Commands

**For New Users:**
```bash
# 1. Install
pip install -e .[dev]

# 2. Process files
ai-tc-generator input/your_file.reqifz --verbose

# 3. Fast processing
ai-tc-generator input/directory/ --hp
```

**For Developers:**
```bash
# 1. Run tests
python tests/run_tests.py

# 2. Check code quality
ruff check src/ main.py --fix

# 3. Development mode
python main.py input/file.reqifz --debug
```

## 🚀 Quick Start Guide

### Installation Options

**Option 1: Development Setup (RECOMMENDED for contributors)**
```bash
pip install -e .[dev]          # Editable install with all development tools
```

**Option 2: Production Setup (when available on PyPI)**
```bash
pip install ai-tc-generator    # Standard installation
```

**Option 3: Specialized Installations**
```bash
pip install -e .[security]     # + Security scanning tools
pip install -e .[training]     # + ML training dependencies
pip install -e .[all]          # All optional dependencies
```

## 📋 CLI Command Reference

### Basic Usage Commands

| Command | Description | Example |
|---------|-------------|---------|
| `ai-tc-generator <file>` | Process single REQIFZ file | `ai-tc-generator input/door_system.reqifz` |
| `ai-tc-generator <directory>` | Process all REQIFZ files in directory | `ai-tc-generator input/` |
| `ai-tc-gen <file>` | Short alias for ai-tc-generator | `ai-tc-gen input/door_system.reqifz` |

### Information & Help Commands

| Command | Description |
|---------|-------------|
| `ai-tc-generator --help` | Show all available options |
| `ai-tc-generator --version` | Show version information |
| `ai-tc-generator --list-templates` | List available prompt templates |
| `ai-tc-generator --validate-prompts` | Validate YAML template syntax |

### Processing Mode Options

| Flag | Description | Usage Example |
|------|-------------|---------------|
| `--hp` | High-performance mode (2.5x faster) | `ai-tc-generator input/ --hp` |
| `--verbose` | Detailed logging output | `ai-tc-generator input/ --verbose` |
| `--debug` | Debug mode with extra details | `ai-tc-generator input/ --debug` |
| `--performance` | Show performance metrics | `ai-tc-generator input/ --hp --performance` |

### AI Model Configuration

| Option | Description | Example |
|--------|-------------|---------|
| `--model <name>` | Specify AI model to use | `--model deepseek-coder-v2:16b` |
| `--template <name>` | Use specific prompt template | `--template advanced_v3` |
| `--max-concurrent <num>` | Set concurrent workers (HP mode) | `--max-concurrent 4` |
| `--timeout <seconds>` | Set AI request timeout | `--timeout 300` |

### Common Usage Examples

**Basic Processing:**
```bash
# Process single file with default settings
ai-tc-generator input/automotive_door_window_system.reqifz

# Process directory with verbose output
ai-tc-generator input/2025_09_12_S220 --verbose
```

**High-Performance Processing:**
```bash
# Fast processing with performance metrics
ai-tc-generator input/ --hp --performance

# High-performance with custom workers
ai-tc-generator input/ --hp --max-concurrent 4
```

**Advanced Options:**
```bash
# Custom model with verbose output
ai-tc-generator input/ --model deepseek-coder-v2:16b --verbose

# Debug mode with custom template
ai-tc-generator input/door_system.reqifz --debug --template advanced_v3
```

**Template Management:**
```bash
# Validate prompt templates
ai-tc-generator --validate-prompts

# List available templates
ai-tc-generator --list-templates
```

## 🛠️ Development Mode (Direct Execution)

**When package is not installed, use direct execution:**

| Command | Description |
|---------|-------------|
| `python main.py <file>` | Basic processing |
| `python main.py <file> --hp` | High-performance mode |
| `python main.py --validate-prompts` | Validate templates |
| `python main.py --list-templates` | List templates |

**Development Examples:**
```bash
# Standard processing
python main.py input/automotive_door_window_system.reqifz

# High-performance with metrics
python main.py input/ --hp --performance --verbose

# Advanced configuration
python main.py input/ --model deepseek-coder-v2:16b --max-concurrent 4 --debug
```

## 🧪 Development & Testing Guide

### Environment Setup

| Task | Command | Purpose |
|------|---------|---------|
| **Check Python Version** | `python3 utilities/version_check.py --strict` | Verify Python 3.13.7+ |
| **Install Dev Environment** | `pip install -e .[dev]` | Install with all dev tools |
| **Verify Installation** | `python3 -c "import src; print(f'v{src.__version__}')"` | Check package import |
| **Syntax Check** | `python3 -m py_compile src/*.py main.py` | Validate syntax |

### Code Quality & Linting

| Task | Command | Description |
|------|---------|-------------|
| **Check Code Style** | `ruff check src/ main.py utilities/` | Fast linting |
| **Auto-format Code** | `ruff format src/ main.py utilities/` | Format code |
| **Fix Issues** | `ruff check src/ main.py --fix` | Auto-fix problems |
| **Type Checking** | `mypy src/ main.py --python-version 3.13` | Static type analysis |

### Testing Commands

**Quick Testing:**
```bash
python tests/run_tests.py                    # Run complete test suite (recommended)
python tests/run_tests.py tests/core/test_specific.py  # Run specific test file
```

**Detailed Testing:**
```bash
# Full test suite with coverage
python -m pytest tests/ -v --cov=src

# Test specific components
python -m pytest tests/core/ -v                           # Core components
python -m pytest tests/integration/ -v                    # Integration tests
python -m pytest tests/core/test_parsers.py -v           # JSON/HTML parsers
python -m pytest tests/core/test_generators.py -v        # Test generation
python -m pytest tests/integration/test_end_to_end.py -v # Full workflows
```

### Build & Distribution

| Task | Command | Purpose |
|------|---------|---------|
| **Build Package** | `python -m build` | Create wheel and source dist |
| **Validate Package** | `twine check dist/*` | Check package metadata |
| **Generate Test Data** | `python3 utilities/create_mock_reqifz.py` | Create test REQIFZ file |

### Quick Validation Checks

```bash
# Verify everything is working
python3 -c "import src; print(f'✅ v{src.__version__} ready')"

# Test with sample data
ai-tc-generator input/automotive_door_window_system.reqifz --verbose
```

## 🤖 AI Model Setup (Ollama)

### Required Models Installation

| Model | Command | Purpose |
|-------|---------|---------|
| **LLaMA 3.1 8B** | `ollama pull llama3.1:8b` | Default model for test generation |
| **DeepSeek Coder** | `ollama pull deepseek-coder-v2:16b` | Advanced coding-focused model |

### Service Management

| Task | Command | Description |
|------|---------|-------------|
| **Check Version** | `ollama --version` | Verify Ollama v0.11.10+ installed |
| **Start Service** | `ollama serve` | Start Ollama service |
| **List Models** | `ollama list` | Show installed models |
| **Check API** | `curl http://localhost:11434/api/tags` | Test API connectivity |

### Troubleshooting

**If models aren't working:**
```bash
# 1. Check service is running
ollama list

# 2. Test basic connectivity
curl http://localhost:11434/api/tags

# 3. If service isn't running
ollama serve

# 4. Re-pull models if needed
ollama pull llama3.1:8b
ollama pull deepseek-coder-v2:16b
```

**Advanced API Test:**
```bash
# Test full API functionality
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Test connectivity",
  "stream": false,
  "keep_alive": "30m",
  "options": {"num_ctx": 8192, "num_predict": 2048, "temperature": 0.0}
}'
```

## 🏗️ Architecture Overview

### Modular System Design

```
├── main.py                         # CLI entry point (Click-based)
├── src/
│   ├── core/                       # Reusable business logic components
│   │   ├── extractors.py          # REQIFZ XML parsing (automotive REQIF format)
│   │   ├── parsers.py             # JSON/HTML parsing with error recovery
│   │   ├── generators.py          # AI test case generation (sync + async)
│   │   ├── formatters.py          # Excel/JSON output formatting
│   │   └── ollama_client.py       # Ollama API integration
│   ├── processors/                 # Workflow orchestration
│   │   ├── standard_processor.py  # Sequential context-aware processing
│   │   └── hp_processor.py        # Async context-aware processing
│   ├── config.py                  # Pydantic configuration management
│   ├── app_logger.py              # Structured logging with JSON output
│   └── yaml_prompt_manager.py     # YAML template management
├── tests/                         # Test suite (62 passing, 14 failing)
│   ├── conftest.py               # Shared fixtures
│   ├── run_tests.py              # Test runner
│   ├── core/                     # Unit tests
│   └── integration/              # Integration tests
├── prompts/                      # AI prompt templates (YAML)
└── utilities/                    # Development tools
```

### Data Flow: Context-Aware Processing

```
REQIFZ File → Extractor → ALL Artifacts (ordered list)
                              ↓
                     Context-Aware Iteration
                              ↓
           ┌──────────────────┼──────────────────┐
           ↓                  ↓                  ↓
       Heading          Information       System Requirement
    (set context)     (collect info)      (augment + generate)
           ↓                  ↓                  ↓
    current_heading  → info_since_heading → requirement + context
                                                  ↓
                                         Generator with rich prompt
                                                  ↓
                                         AI model generates tests
                                                  ↓
                                         Excel output with metadata
```

### Key Architecture Principles

1. **Context Preservation**: Processors iterate through ALL artifacts to build contextual state
2. **Requirement Augmentation**: Each System Requirement is enriched with heading, info_list, interface_list
3. **Separation of Concerns**: Core components are stateless; processors manage workflow state
4. **Dual-Mode Processing**: Standard (sequential) and HP (async) share same context logic
5. **Template-Driven Prompts**: YAML templates expect context variables (heading, info_str, interface_str)

### Component Responsibilities

**Extractors** (`src/core/extractors.py`):
- Parse REQIFZ (zipped REQIF XML) files
- Extract ALL artifact types: Heading, Information, System Interface, System Requirement
- Classify artifacts but DO NOT filter prematurely
- Support automotive REQIF format with XHTML namespaces

**Generators** (`src/core/generators.py`):
- Build AI prompts from YAML templates with context variables
- Format context: `_format_info_for_prompt()`, `_format_interfaces_for_prompt()`
- Generate test cases via Ollama API (sync and async)
- Handle structured error responses

**Processors** (`src/processors/`):
- **Standard**: Sequential context-aware processing (lines 112-155)
- **HP**: Async context-aware processing with batching (lines 112-144)
- Both maintain: `current_heading`, `info_since_heading`, `system_interfaces`
- Augment requirements before passing to generators

**Formatters** (`src/core/formatters.py`):
- Convert test cases to Excel format with metadata
- Streaming formatters for memory efficiency in HP mode

### Import Structure

**Critical**: All imports within `src/` use absolute imports from module root:
```python
# ✅ CORRECT
from config import ConfigManager
from core.extractors import REQIFArtifactExtractor
from processors.standard_processor import REQIFZFileProcessor

# ❌ WRONG (breaks tests)
from ..config import ConfigManager
from ..core.extractors import REQIFArtifactExtractor
```

Reason: Tests add `src/` to sys.path, requiring absolute imports from src root.

### Configuration System

**Pydantic-Based Configuration** (`src/config.py`):
```python
ConfigManager()
  ├── ollama: OllamaConfig        # AI model settings
  ├── static_test: StaticTestConfig  # Excel formatting
  └── file_processing: FileProcessingConfig  # I/O settings
```

**YAML Prompt System** (`prompts/`):
```
prompts/
├── templates/test_generation_v3_structured.yaml  # Main template
├── config/prompt_config.yaml                     # Template config
└── tools/template_validator.py                   # Validation
```

### Performance Characteristics

- **Standard Mode**: ~7,254 artifacts/second, single-threaded
- **HP Mode**: ~18,208 artifacts/second, 2-4 workers optimal (2.5x speedup)
- **Memory Efficiency**: 0.010 MB per artifact
- **JSON Parsing**: Linear scalability up to 50K test cases
- **End-to-End**: <1 second for typical automotive REQIFZ files

## ⚡ Quick Start for New Developers

### 5-Minute Setup

```bash
# 1. Verify Python 3.13.7+
python3 --version

# 2. Install in development mode
pip install -e .[dev]

# 3. Verify package installation
python3 -c "import src; print(f'Version: {src.__version__}')"

# 4. Check Ollama (must be v0.11.10+)
ollama --version
curl -s http://localhost:11434/api/tags

# 5. Create test data and run
python3 utilities/create_mock_reqifz.py
ai-tc-generator input/automotive_door_window_system.reqifz --verbose

# 6. Run test suite
python tests/run_tests.py
```

### Development Guidelines

- **Context-Aware Processing**: Never filter artifacts before context iteration (see top of this file)
- **Test Before Commit**: Run `python tests/run_tests.py` (currently 62/76 passing)
- **Code Quality**: Use `ruff check src/ main.py --fix` before commits
- **Import Style**: Use absolute imports from src root (not relative imports)
- **Template Changes**: Run `--validate-prompts` after modifying YAML files
- **Performance Testing**: Use `--hp --performance` to verify optimizations
- **Debug Logging**: Check JSON log files for detailed processing traces

### Python 3.13.7+ Modern Features

**Language Features Used:**
- **PEP 695 Type Aliases**: `type JSONObj[T] = dict[str, T]`
- **Pattern Matching**: `match`/`case` for XML processing
- **__slots__**: 20-30% memory reduction on core classes
- **Async/Await**: Concurrent processing in HP mode

### Known Issues (2025-09-30)

**Test Failures (14 failing, 62 passing = 82% success rate):**
- Network error simulation tests (4 failures - mock configuration issues)
- Integration workflow tests (10 failures - end-to-end scenarios)
- Core logic tests: ✅ ALL PASSING

**Status:**
- ✅ Context-aware processing: **RESTORED and WORKING**
- ✅ Context formatting methods: **IMPLEMENTED**
- ✅ Import paths: **FIXED**
- ✅ Test coverage: 61% (up from 25%)
- ⚠️ Integration tests: Need mock refinement
- ⚠️ Network tests: Need connection simulation fixes

**Priority:**
- Core functionality (context-aware processing): ✅ **COMPLETE**
- Integration test mocking: ⚠️ Needs attention
- Network error simulation: ⚠️ Needs fixes

### Common Issues and Solutions

**Import Errors**: Use `pip install -e .[dev]` for proper package setup
**Ollama Connection**: Verify service with `ollama list` and ensure models are available
**Template Issues**: Run `ai-tc-generator --validate-prompts` to check YAML syntax
**Performance**: Use `--hp` mode for 2.5x speedup
**REQIFZ Parsing**: Ensure automotive REQIF format with proper XHTML namespaces
**Context Loss**: Check that processors iterate ALL artifacts (not just System Requirements)

### Verification Commands

```bash
# Test context formatting methods
python3 -c "
from src.core.generators import TestCaseGenerator
gen = TestCaseGenerator(None, None, None)
info = [{'text': 'Test info'}]
print('Info:', gen._format_info_for_prompt(info))
interfaces = [{'id': 'IF_001', 'text': 'Signal'}]
print('Interface:', gen._format_interfaces_for_prompt(interfaces))
"

# Verify package
python3 -c "import src; print(f'✅ v{src.__version__} ready')"

# Test with sample data
ai-tc-generator input/automotive_door_window_system.reqifz --verbose
```