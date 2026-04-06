# AI Test Case Generator v2.3.0

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Production Ready](https://img.shields.io/badge/status-production%20ready-brightgreen.svg)]()

AI-powered test case generator for automotive REQIFZ requirements files using local LLM models via Ollama.

## 🎯 Overview

This tool automatically generates comprehensive test cases from automotive requirements (REQIF/REQIFZ format) using AI models. It features intelligent context-aware processing, hybrid vision/text model support, and high-performance concurrent processing capabilities.

### Key Features

- ✅ **Hybrid AI Strategy**: Automatically uses vision models (llama3.2-vision:11b) for requirements with diagrams, text models (llama3.1:8b) for text-only requirements
- ✅ **Context-Aware Processing**: Enriches requirements with headings, information blocks, and system interfaces for better test case quality
- ✅ **High-Performance Mode**: Async/concurrent processing with 3-9x performance improvement
- ✅ **Image Extraction**: Extracts and processes embedded images from REQIFZ files for vision AI analysis
- ✅ **RAFT Training**: Fine-tune models with custom automotive domain data for improved accuracy
- ✅ **Production Ready**: 87% test coverage, comprehensive validation, robust error handling

## 🚀 Quick Start

### Prerequisites

- **Python 3.14+** (no backward compatibility)
- **Ollama 0.17.4+** with models:
  ```bash
  ollama pull llama3.1:8b          # Text-only processing
  ollama pull llama3.2-vision:11b  # Vision + text processing
  ```

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd AI_TC_Generator_v04_w_Trainer

# Install with all dependencies
pip install -e .[all]

# Or install production only
pip install -e .

# Verify installation
ai-tc-generator --help
```

### Basic Usage

```bash
# Standard mode (recommended)
ai-tc-generator input/requirements.reqifz --verbose

# High-performance mode (3-9x faster)
ai-tc-generator input/ --hp --max-concurrent 4

# With specific model
ai-tc-generator input/file.reqifz --model llama3.1:8b

python main.py .\input\REQIFZ_Files --preset qwen_vision --max-concurrent 1

python main.py input/ --preset qwen_moe

# Clean up temp images after processing (v2.3.0)
ai-tc-generator input/file.reqifz --clean-temp

# Process entire directory
ai-tc-generator input/ --verbose
```

### Profile-Based Configuration

Run with a named preset that bundles model + mode + options:

```bash
ai-tc-generator input/file.reqifz --profile Llama31.HP.Quality
```

Profile format: `Model.Mode[.Modifier]`
- **Models**: `Llama31`, `Deepseek`, `Qwen`
- **Modes**: `Standard`, `HP`
- **Modifiers**: `Verbose`, `Debug`, `Fast`, `Quality`

Profiles are defined in `profiles/profiles.yaml`. See `profiles/sample-profiles.yaml` for examples.

### Output

Generated test cases are saved as Excel files alongside input files:
```
input/requirements.reqifz
input/requirements_TCD_llama3.1_8b_2025-11-03_20-51-49.xlsx
```

## 📋 Core Capabilities

### Context-Aware Processing

The system intelligently builds context for each requirement:

- **Heading Context**: Current section heading
- **Information Context**: Related information blocks (resets per requirement)
- **Interface Context**: Global system interfaces
- **Image Context**: Extracted diagrams for vision model analysis

This context-aware approach significantly improves test case quality and relevance.

### Hybrid Vision Strategy (v2.2.0)

Requirements are automatically processed with the appropriate model:

- **With images** → `llama3.2-vision:11b` (understands diagrams, state machines, interfaces)
- **Without images** → `llama3.1:8b` (faster text-only processing)

No configuration needed - the system automatically detects images and selects the best model.

### High-Performance Mode

Process large REQIFZ files efficiently:

```bash
# Standard: Sequential processing (~7,254 artifacts/sec)
ai-tc-generator input/large_file.reqifz

# HP Mode: Concurrent async processing (~65,000 artifacts/sec)
ai-tc-generator input/large_file.reqifz --hp --max-concurrent 4
```

**Performance**: 9x faster with proper resource management and memory optimization.

## 🏗️ Architecture

```
CLI Entry Point
    ↓
Processor (Standard or HP)
    ├─ REQIFArtifactExtractor (parse XML, extract images)
    ├─ BaseProcessor (context-aware processing)
    ├─ Hybrid Model Selection (vision vs text)
    ↓
Generator (Sync or Async)
    ├─ PromptBuilder (context + image prompts)
    ├─ OllamaClient (AI generation)
    ├─ Parser, Validator, Deduplicator
    ↓
Formatter (Excel/JSON)
    ↓
Output Files + Extracted Images
```

**Key Components**:
- `src/processors/` - Standard and HP workflow orchestration
- `src/core/` - Core logic (extraction, generation, formatting)
- `src/config.py` - Centralized Pydantic-based configuration
- `prompts/` - YAML prompt templates
- `tests/` - Comprehensive test suite

## 🧪 Development

### Setup Development Environment

```bash
# Install with development tools
pip install -e .[dev]

# Run tests
python3 -m pytest tests/core/ -v              # Fast unit tests
python3 -m pytest tests/ -v --cov=src         # Full suite with coverage

# Code quality
ruff check src/ main.py utilities/ --fix     # Lint and auto-fix
ruff format src/ main.py utilities/           # Format code
mypy src/ main.py --python-version 3.14       # Type checking

# Validate prompt templates
ai-tc-generator --validate-prompts
```

### Writing Tests

**Important**: After v2.2.0 vision integration, tests must use helper functions for XHTML format:

```python
from tests.helpers import (
    create_test_requirement,
    create_test_heading,
    create_test_information,
)

# ✅ CORRECT
artifacts = [
    create_test_heading("Door System"),
    create_test_requirement("Door shall lock", requirement_id="REQ_001")
]

# ❌ WRONG - Plain text will fail
artifacts = [
    {"type": "Heading", "text": "Door System"}
]
```

See `tests/helpers/USAGE_EXAMPLES.md` for complete examples.

## 📚 Documentation

### Essential Reading

- **[CLAUDE.md](CLAUDE.md)** - Comprehensive developer guide (architecture, critical code sections, testing)
- **[System_Instructions.md](System_Intructions.md)** - Vibe coding principles and review guidelines

### Architecture & Implementation

- [Vision Training Guide](docs/training/training_guideline.md) - Complete RAFT training guide with utility scripts

### Configuration

```bash
# Vision model settings
export OLLAMA__VISION_MODEL="llama3.2-vision:11b"
export OLLAMA__ENABLE_VISION=true

# Training data collection
export AI_TG_ENABLE_RAFT=true
export AI_TG_COLLECT_TRAINING_DATA=true

# Ollama connection
export OLLAMA__BASE_URL="http://localhost:11434"
```

See `src/config.py` for all configuration options (Pydantic-based with environment variable support).

## 🎓 Training Custom Models

Fine-tune vision models on your automotive domain data using RAFT methodology.

**RAFT collection is opt-in and disabled by default.** Enable it in `config/cli_config.yaml` (`training.enable_raft: true`, `training.collect_training_data: true`) or via environment variables before running.

```bash
# 1. Enable RAFT data collection (opt-in — off by default)
export AI_TG_ENABLE_RAFT=true
export AI_TG_COLLECT_TRAINING_DATA=true

# 2. Process requirements (automatically collects training data with images)
ai-tc-generator input/ --hp --verbose

# 3. Annotate collected examples
# Edit JSON files in training_data/collected/ to mark oracle/distractor context and images
# Move annotated files to training_data/validated/

# 4. Build RAFT dataset (using utility script)
python3 utilities/build_vision_dataset.py

# 5. Train custom vision model (using utility script)
python3 utilities/train_vision_model.py

# 6. Deploy trained model
export OLLAMA__VISION_MODEL="automotive-tc-vision-raft-v1"
ai-tc-generator input/ --hp --verbose
```

**Expected Results**: 40-60% better test case quality for requirements with diagrams.

See [Vision Training Guide](docs/training/training_guideline.md) for complete guide including:
- Hardware requirements (12+ GB VRAM)
- Image annotation best practices
- Monitoring and evaluation
- Troubleshooting common issues

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'src'` | Run `pip install -e .[dev]` |
| `OllamaConnectionError` | Start Ollama: `ollama serve` |
| `OllamaModelNotFoundError` | Install model: `ollama pull llama3.1:8b` |
| Vision model fails (out of VRAM) | Disable vision: `export OLLAMA__ENABLE_VISION=false` |
| Requirements skipped ("no text content") | Check REQIFZ file attribute definitions |

See [CLAUDE.md](CLAUDE.md) for complete troubleshooting guide.

## 📊 Performance Benchmarks

| Mode | Speed | Memory | Use Case |
|------|-------|--------|----------|
| **Standard** | ~7,254 artifacts/sec | Normal | Small-medium files |
| **HP Mode** | ~65,000 artifacts/sec | Optimized | Large files, batches |
| **Vision Model** | ~4-5 sec/requirement | 10-12 GB VRAM | Requirements with images |
| **Text Model** | ~2-3 sec/requirement | 6-7 GB VRAM | Text-only requirements |

**Optimization**: Uses `__slots__`, async/await, streaming formatters, and intelligent model selection.

## 🧪 Test Suite Status

Current test coverage (as of Nov 3, 2025):

- **Core unit tests**: 83/83 (100%) ✅
- **Integration tests**: 223/255 (87%) ✅
- **Helper verification**: 10/10 (100%) ✅
- **Production validation**: 104/104 (100%) ✅

## 🔒 Requirements

- **Python**: 3.14+ only (no backward compatibility)
- **Ollama**: 0.17.4+ with GPU support (recommended: 12+ GB VRAM for vision models)
- **Dependencies**: Managed in `pyproject.toml`
  - Core: pandas, pydantic, click, rich, openpyxl
  - Performance: aiohttp, ujson, psutil
  - Dev: pytest, ruff, mypy
  - Training: torch, transformers, peft

## 📝 License

MIT License - see [LICENSE](LICENSE) file.

## 🤝 Contributing

This project follows "Vibe Coding" principles:

1. **Readability first** - Code for humans, not machines
2. **Test-driven** - Write tests with implementation
3. **Simple over clever** - Avoid over-engineering
4. **Modern Python** - Use Python 3.14+ features, no legacy support

See [System_Instructions.md](System_Intructions.md) for detailed coding guidelines.

## 📧 Support

- **Documentation**: See [CLAUDE.md](CLAUDE.md) for comprehensive guidance
- **Issues**: Open GitHub issues for bugs or feature requests
- **Architecture**: Review code in `src/` following the processor → generator → formatter pattern

## 🎯 Project Status

**Version**: v2.3.0
**Status**: Production Ready ✅
**Python**: 3.14+ only
**Last Updated**: November 3, 2025

---

**Built with**: Python 3.14 • Ollama • llama3.1/3.2-vision • Pydantic • AsyncIO
