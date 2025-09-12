# 🚀 Installation Guide

## Quick Start (Recommended)

```bash
# 1. Install core dependencies (required for all versions)
pip install -r requirements.txt

# 2. For basic usage - you're ready!
python src/generate_contextual_tests_v002.py --validate-prompts
```

## Optional Features

```bash  
# Install optional dependencies for additional features
pip install -r requirements-optional.txt
```

**What optional dependencies enable:**
- **High-Performance Version**: aiohttp, asyncio-throttle, psutil
- **Training System**: torch, transformers, peft, datasets, wandb
- **Development Tools**: pytest, mypy, ruff, pip-audit

## Installation Options

### Option 1: Minimal (Core Only)
```bash
pip install -r requirements.txt
```
**Includes:** pandas, requests, PyYAML, click, rich, openpyxl, pydantic, lxml, ujson
**Enables:** Standard version (unified), basic functionality

### Option 2: Full Installation  
```bash
pip install -r requirements.txt
pip install -r requirements-optional.txt
```
**Enables:** All features including training and high-performance versions

### Option 3: Selective Installation
```bash
pip install -r requirements.txt

# Only high-performance features
pip install aiohttp asyncio-throttle psutil

# Only ML training features  
pip install torch transformers peft datasets wandb

# Only development tools
pip install pytest mypy ruff pip-audit
```


## System Requirements

- **Python**: 3.13.7+ (required)
- **OS**: macOS, Linux, Windows
- **Memory**: 4GB+ RAM recommended for training features
- **Disk**: 2GB+ free space for ML models

## Verification

```bash
# Test core installation
python src/generate_contextual_tests_v002.py --validate-prompts

# Test all features (if optional deps installed)
python utilities/version_check.py --strict
python -m py_compile src/*.py
```