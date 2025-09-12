# AI Test Case Generator v1.4.0

Modern, unified AI-powered test case generator for automotive REQIFZ files using Ollama models.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Basic usage - Standard mode
python main.py input.reqifz

# High-performance mode (4-8x faster)
python main.py input.reqifz --hp --performance

# Validate templates
python main.py --validate-prompts
```

## 📋 Available Modes

- **Standard**: `python main.py input.reqifz`
- **High-Performance**: `python main.py input.reqifz --hp`
- **Training**: `python main.py input.reqifz --training` (requires ML deps)
- **Validation**: `python main.py --validate-prompts`

## 📚 Documentation

See `CLAUDE.md` for comprehensive documentation, configuration, and usage examples.

## 🎯 Requirements

- Python 3.13.7+
- Ollama v0.11.10+ with models: llama3.1:8b, deepseek-coder-v2:16b

## 🏗️ Architecture

- **Unified CLI**: Single entrypoint (`main.py`) for all modes
- **Modular Core**: Components in `src/core/` for reusability
- **Modern Python**: PEP 695 type aliases, pattern matching, `__slots__`
- **Performance Optimized**: Async processing, configurable concurrency

---
🤖 Generated with Claude Code