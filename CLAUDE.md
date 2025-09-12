# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ✅ **SYSTEM STATUS**

**Last Updated**: 2025-09-12 | **Python**: 3.13.7+ | **Architecture**: Modular | **Status**: ✅ FULLY FUNCTIONAL

## Core Application Commands

### **Main Interface (Unified Entrypoint)**

```bash
# Basic processing - Standard mode
python3 main.py input/file.reqifz

# High-performance mode (4-8x faster)
python3 main.py input/file.reqifz --hp --performance

# Process entire input directory
python3 main.py input/ --output-dir output/excel/

# Organized output with specific model
python3 main.py input/file.reqifz --model deepseek-coder-v2:16b --output-dir output/excel/

# Template validation and management
python3 main.py --validate-prompts
python3 main.py --list-templates

# Debug and verbose modes
python3 main.py input/file.reqifz --verbose --debug
```

### **Development and Testing**

```bash
# Environment validation (ESSENTIAL - run first)
python3 utilities/version_check.py --strict

# Install dependencies
pip install -r requirements.txt                    # Core dependencies
pip install -r requirements-optional.txt          # Optional: ML, performance, dev tools

# Code quality and validation
python3 -m py_compile main.py src/*.py src/core/*.py src/processors/*.py  # Compile check
ruff check src/ --fix                             # Linting with auto-fix
ruff format src/                                   # Code formatting
mypy src/ --python-version 3.13                   # Type checking

# Test data generation
python3 utilities/create_mock_reqifz.py           # Creates test REQIFZ in input/
```

### **Ollama Model Management**

```bash
# Required AI models (validated)
ollama pull llama3.1:8b
ollama pull deepseek-coder-v2:16b

# Service verification
ollama --version                                   # Must be v0.11.10+
ollama list                                        # Show available models
curl -s http://localhost:11434/api/tags           # API connectivity test
```

## High-Level Architecture

### **Modular Structure (Post-Refactoring)**

The system follows a clean modular architecture with separated concerns:

```
main.py                 # Unified CLI entrypoint and mode orchestration
├── src/
│   ├── config.py              # Pydantic configuration management
│   ├── yaml_prompt_manager.py # AI prompt template system
│   ├── file_processing_logger.py # Comprehensive JSON logging
│   ├── core/                  # Business logic components
│   │   ├── extractors.py      # REQIFZ XML parsing and artifact classification
│   │   ├── generators.py      # AI test case generation (sync/async)
│   │   ├── formatters.py      # Excel output with automotive formatting
│   │   ├── ollama_client.py   # AI API client (sync/async)
│   │   └── parsers.py         # AI response parsing (JSON/HTML)
│   └── processors/            # Workflow orchestrators
│       ├── standard_processor.py    # Synchronous processing workflow
│       └── hp_processor.py          # Async high-performance workflow
```

### **Key Design Patterns**

1. **Modular Components**: Each core module has single responsibility
2. **Workflow Processors**: High-level orchestrators compose core components
3. **Dual Processing Modes**: Sync (standard) and async (high-performance)
4. **Configuration-Driven**: Pydantic settings with YAML prompt system
5. **Comprehensive Logging**: JSON metrics for performance monitoring

### **Processing Pipeline**

```
REQIFZ Input → XML Extraction → Artifact Classification → AI Generation → Excel Output
     ↓              ↓                    ↓                     ↓              ↓
File Discovery → REQIFArtifact → Pattern Matching → YAML Prompt → Test Case → XLSX + JSON
              Extractor        (System Requirements)  Manager    Generator   Logs
```

### **AI Integration Architecture**

- **Template System**: YAML-based prompts with variable substitution
- **Model Support**: llama3.1:8b, deepseek-coder-v2:16b (extensible)
- **Dual Clients**: Sync OllamaClient and async AsyncOllamaClient
- **Response Parsing**: Multiple JSON extraction strategies + HTML table parsing
- **Error Handling**: Graceful degradation with comprehensive error logging

### **Output Management**

Files are saved using flexible output patterns:
- **Default**: Same directory as input file
- **Organized**: `--output-dir output/excel/` for structured output
- **Naming**: `{filename}_TCD[_HP]_{model}_{timestamp}.xlsx`
- **Logging**: Matching JSON files with comprehensive metrics

## File Organization

### **Input Management**
```
input/                  # Organized REQIFZ file storage
├── automotive_door_window_system.reqifz  # Generated test data
└── README.md          # Usage documentation
```

### **Output Structure**
```
output/
├── excel/             # Generated test case files (.xlsx)
├── logs/              # Processing analytics (.json)
├── reports/           # Future analysis reports
└── README.md          # Output documentation
```

### **Configuration and Templates**
```
prompts/
├── config/prompt_config.yaml           # Prompt system configuration
├── templates/test_generation_v3_structured.yaml  # AI prompt templates
├── tools/validation_and_tools.py       # Template validation utilities
└── prompt_documentation.md             # Template system documentation
```

## Key Differences from Legacy System

**Removed**: All legacy `generate_contextual_tests_*.py` files (4,200+ lines of monolithic code)  
**Added**: Clean modular architecture with separated concerns  
**Improved**: Single unified entrypoint instead of multiple scripts  
**Enhanced**: Dual processing modes (sync/async) with shared components  

## Important Development Notes

- **Main Entry**: Use `python3 main.py` - all other entry points removed
- **Component Architecture**: Import from `src.core.*` and `src.processors.*`
- **Template System**: YAML prompts in `prompts/templates/` with `prompt_config.yaml`
- **Test Data**: Use `utilities/create_mock_reqifz.py` for test file generation
- **Performance**: HP mode provides 4-8x speedup with async processing
- **Output**: Supports both same-directory (default) and organized output structures

## Dependencies and Requirements

- **Python**: 3.13.7+ (enforced by utilities/version_check.py)
- **Core**: pandas, requests, PyYAML, click, rich, openpyxl, pydantic
- **Optional**: torch, transformers (ML), lxml, orjson (performance), pytest, mypy (dev)
- **External**: Ollama v0.11.10+ with llama3.1:8b and/or deepseek-coder-v2:16b models