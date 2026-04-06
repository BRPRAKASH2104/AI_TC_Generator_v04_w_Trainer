# Installation Guide: AI Test Case Generator

**Version:** 4.0 | **Date:** October 2025 | **Audience:** System Administrators, Users

---

## 📦 System Requirements

### Hardware Requirements

| Component | Minimum | Recommended | Enterprise |
|-----------|---------|-------------|------------|
| **CPU** | 4 cores | 8 cores | 16+ cores |
| **RAM** | 8GB | 16GB | 32GB+ |
| **Disk** | 2GB | 5GB | 50GB+ SSD |
| **Network** | 10 Mbps | 50 Mbps | 1 Gbps |

### Software Prerequisites

#### Operating System Support
- **✅ Linux**: Ubuntu 20.04+, CentOS 7+, RHEL 8+
- **✅ macOS**: 12.0+ (Monterey or later)
- **✅ Windows**: 10/11 with WSL2
- **❌ Legacy OS**: Windows without WSL, macOS <12.0

#### Python Requirements
- **Version**: 3.14+ (required)
- **Architecture**: 64-bit only
- **Package Manager**: pip 20.0+ recommended

#### External Dependencies
- **Ollama**: AI service provider (0.17.4+)
- **MS Excel**: For output file viewing (optional)

---

## 🚀 Quick Installation

### 1. One-Command Setup (Recommended)

```bash
# All platforms - automated installation
curl -fsSL https://raw.githubusercontent.com/your-org/ai-tc-generator/main/install.sh | bash
```

This script will:
- Install Python 3.14+ if not present
- Install Ollama AI service
- Install AI Test Case Generator
- Download default AI model
- Validate installation

### 2. Manual Installation (Step-by-Step)

#### Step 1: Python Installation

**macOS (with Homebrew):**
```bash
# Install Python 3.14+
brew install python@3.14

# Verify installation
python3.14 --version  # Should show 3.14+
python3.14 -m pip --version  # Should work
```

**Ubuntu/Debian:**
```bash
# Add deadsnakes PPA for latest Python
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.14+
sudo apt install python3.14 python3.14-venv python3.14-pip

# Set as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.14 1
```

**Windows (WSL2):**
```bash
# Update WSL2
wsl --update
wsl --set-version Ubuntu 2

# Install Python 3.14+ in WSL Ubuntu
sudo apt update && sudo apt install python3.14 python3.14-venv python3.14-pip
```

**Enterprise/Corporate Environments:**
Consult your IT team for Python installation via approved channels.

#### Step 2: Ollama Installation

**Linux:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start service
sudo systemctl enable ollama  # Optional: auto-start
ollama serve &
```

**macOS:**
```bash
# Install via Homebrew
brew install ollama

# Start service
brew services start ollama
# OR manual: ollama serve &
```

**Windows (WSL2):**
```bash
# Install in WSL environment
curl -fsSL https://ollama.ai/install.sh | sh

# Start service
ollama serve &
```

#### Step 3: AI Test Case Generator Installation

```bash
# Install from source (recommended)
git clone https://github.com/your-org/ai-tc-generator.git
cd ai-tc-generator
pip install -e .[dev]
```

#### Step 4: AI Model Download

**Default Model (Recommended for most users):**
```bash
ollama pull llama3.1:8b
```

**Alternative Models:**
```bash
# High-quality model (larger, slower)
ollama pull deepseek-coder-v2:16b

# Balanced performance/quality
ollama pull mistral:latest

# Code-focused model
ollama pull codellama:latest
```

---

## ✅ Installation Verification

### Basic Verification

```bash
# 1. Check AI Test Case Generator
ai-tc-generator --version

# Expected: AI Test Case Generator v4.0.0

# 2. Check Ollama service
ollama list

# Expected: Shows installed models, including llama3.1:8b

# 3. Test basic functionality
ai-tc-generator --validate-prompts

# Expected: "Found X template(s)" and green checkmarks

# 4. Check service connectivity
curl http://localhost:11434/api/tags

# Expected: JSON response with model information
```

### Comprehensive Validation

```bash
#!/bin/bash
# validation_script.sh - Run after installation

echo "=== AI Test Case Generator Installation Test ==="

# Test 1: Version
echo "1. Testing version..."
if ai-tc-generator --version > /dev/null 2>&1; then
    echo "✅ Version check passed"
else
    echo "❌ Version check failed"
fi

# Test 2: Ollama connectivity
echo "2. Testing Ollama connectivity..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama connection passed"
else
    echo "❌ Ollama connection failed"
fi

# Test 3: Model availability
echo "3. Testing model availability..."
if ollama list | grep -q llama3.1:8b; then
    echo "✅ Default model available"
else
    echo "❌ Default model not found"
fi

# Test 4: Template validation
echo "4. Testing template validation..."
if ai-tc-generator --validate-prompts > /dev/null 2>&1; then
    echo "✅ Template validation passed"
else
    echo "❌ Template validation failed"
fi

echo "=== Test Complete ==="
```

---

## 🎛️ Configuration Setup

### Basic Configuration

**1. Environment Variables:**
```bash
# Create .env file in project directory
cat > .env << EOF
AI_TG_MODEL=llama3.1:8b
AI_TG_OLLAMA_HOST=127.0.0.1
AI_TG_OLLAMA_PORT=11434
AI_TG_VERBOSE=true
AI_TG_LOG_LEVEL=INFO
EOF
```

**2. YAML Configuration:**
```bash
# Create cli_config.yaml
ai-tc-generator --help | head -5
# This will show config file locations
```

### Advanced Configuration

**YAML Configuration Example:**
```yaml
# cli_config.yaml - Complete configuration
cli_defaults:
  mode: standard
  model: llama3.1:8b
  template: test_generation_v3_structured
  max_concurrent: 4
  verbose: true
  debug: false
  performance: false

ollama:
  host: 127.0.0.1
  port: 11434
  timeout: 600
  temperature: 0.0

file_processing:
  input_encoding: utf-8
  output_encoding: utf-8
  excel_engine: openpyxl
  backup_directory: backups
  reqifz_pattern: "*.reqifz"

logging:
  log_level: INFO
  log_to_file: true
  log_directory: logs
  monitor_performance: true

training:
  collect_training_data: false
  enable_raft: false

# Environment-specific overrides
environments:
  development:
    ollama:
      timeout: 120
    logging:
      log_level: DEBUG

  production:
    ollama:
      timeout: 900
    logging:
      log_level: WARNING
    training:
      enable_raft: false
```

---

## 🏥 Troubleshooting Installation

### Common Installation Issues

**1. "Python version 3.14+ required"**

```bash
# Check current version
python --version

# Install correct version
# macOS
brew install python@3.14

# Ubuntu
sudo apt install python3.14 python3.14-venv

# Verify
python3.14 --version  # Should be 3.14+
```

**2. "Permission denied" during installation**

```bash
# Use user-level installation
pip install --user -e .[dev]

# Add to PATH
export PATH=$PATH:~/.local/bin
```

**3. "Ollama command not found"**

```bash
# Check installation location
which ollama

# If missing, reinstall
curl -fsSL https://ollama.ai/install.sh | sh

# Add to PATH
export PATH=$PATH:/usr/local/bin
```

**4. "Model download fails"**

```bash
# Check network connectivity
curl -I https://registry.ollama.ai

# Try with verbose output
ollama pull llama3.1:8b --verbose

# Alternative model source
ollama pull --from http://custom-registry:5000 llama3.1:8b
```

**5. "Port 11434 already in use"**

```bash
# Check what's using the port
lsof -i :11434

# Kill conflicting process
kill -9 <PID>

# Or change Ollama port
export OLLAMA_HOST=0.0.0.0:11435
# Note: The application uses OLLAMA__BASE_URL environment variable (see src/config.py). OLLAMA_HOST may not be recognized.
ollama serve
```

### Firewall/Security Issues

**Enterprise/Corporate Environments:**

```bash
# Check outbound connectivity
curl -I https://registry.ollama.ai/v2/

# Configure proxy for Ollama
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Ollama behind corporate proxy
ollama pull llama3.1:8b
```

---

## 🚀 Deployment Options

### Local Development

```bash
# Create isolated environment
python3.14 -m venv ai-tc-generator-env
source ai-tc-generator-env/bin/activate

# Install development version
pip install -e .[dev]

# Run tests
pytest tests/
```

### Server Installation

```bash
# Install system-wide
sudo pip install ai-tc-generator

# Create dedicated user
sudo useradd -m ai-tc-user
sudo usermod -aG docker ai-tc-user

# Configure Ollama as service
sudo systemctl enable ollama
sudo systemctl start ollama
```

### Container Deployment (Docker)

**Dockerfile:**
```dockerfile
FROM python:3.14-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Install AI Test Case Generator
RUN pip install --no-cache-dir -e .[dev]

# Create non-root user
RUN useradd -m ai-user
USER ai-user

# Default command
CMD ["ai-tc-generator", "--help"]
```

**Docker Compose:**
```yaml
version: '3.8'
services:
  ai-tc-generator:
    build: .
    volumes:
      - ./input:/app/input:ro
      - ./output:/app/output
    environment:
      - OLLAMA_HOST=ollama:11434
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
```

### Cloud Deployment

**AWS/Azure/GCP Deployment Guidelines:**

```bash
# Install on EC2 instance
sudo yum update -y
sudo yum install python3.14 -y

# Install AI Test Case Generator
pip3 install -e .[dev]

# Configure Ollama
curl -fsSL https://ollama.ai/install.sh | sh
export OLLAMA_MODELS=/mnt/models

# Security group: Allow inbound on port 11434
```

---

## 🔄 Update Procedures

### Minor Updates (Bug fixes)

```bash
# Update Python package
pip install --upgrade ai-tc-generator

# Restart services
sudo systemctl restart ollama

# Verify functionality
ai-tc-generator --version
ai-tc-generator --validate-prompts
```

### Major Updates (New features)

```bash
# Backup configuration
cp cli_config.yaml cli_config.yaml.backup

# Update package
pip install --upgrade ai-tc-generator

# Update AI models (if needed)
ollama pull llama3.1:8b

# Migrate configuration
# Check release notes for breaking changes

# Test functionality
ai-tc-generator test_file.reqifz --dry-run
```

### Rollback Procedures

```bash
# Rollback to previous version
pip install ai-tc-generator==3.2.1

# Restore configuration
cp cli_config.yaml.backup cli_config.yaml

# Verify rollback
ai-tc-generator --version
```

---

## 🔍 Monitoring & Health Checks

### Basic Health Check

```bash
#!/bin/bash
# health_check.sh

# Check service availability
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama service unavailable"
    exit 1
fi

# Check model availability
if ! ollama list | grep -q llama3.1:8b; then
    echo "❌ Required model not available"
    exit 1
fi

# Check application
if ! ai-tc-generator --version > /dev/null; then
    echo "❌ AI Test Case Generator not functional"
    exit 1
fi

echo "✅ All services healthy"
```

### Performance Monitoring

```bash
# Monitor system resources during processing
ai-tc-generator large_file.reqifz --hp --performance

# Log analysis
tail -f logs/ai_tc_generator.log

# Ollama monitoring
ollama ps  # Active models
ollama logs  # Service logs
```

### Automated Monitoring (Nagios/monitoring systems)

```bash
#!/bin/bash
# nagios_check.sh - Returns codes for monitoring systems

curl -f http://localhost:11434/api/tags > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "OK - Ollama service responding"
    exit 0
else
    echo "CRITICAL - Ollama service not responding"
    exit 2
fi
```

---

## 📞 Support & Contact

### Pre-Flight Checklist

Before contacting support, verify:

- [ ] Python 3.14+ installed: `python --version`
- [ ] Package installed: `ai-tc-generator --version`
- [ ] Ollama running: `curl http://localhost:11434/api/tags`
- [ ] Models available: `ollama list`
- [ ] Templates valid: `ai-tc-generator --validate-prompts`

### Support Bundle Creation

```bash
# Create comprehensive support bundle
mkdir support_bundle_$(date +%Y%m%d_%H%M%S)
cd support_bundle*

# System information
uname -a > system_info.txt
python --version > python_version.txt
ollama --version > ollama_version.txt

# Configuration
cp ~/.config/ai_tc_generator/*.yaml config/
env | grep AI_TG > env_vars.txt

# Logs (last 100 lines)
tail -100 ~/.local/logs/ai_tc_generator.log > app_logs.txt
ollama logs > ollama_logs.txt

# Test output
ai-tc-generator --validate-prompts > template_validation.txt 2>&1
ollama list > model_list.txt

# Package info
cd ../ai-tc-generator
pip show ai-tc-generator > package_info.txt
pip list | grep -E "(ai-tc|ollama|pydantic)" > dependencies.txt

echo "Support bundle created in: $(pwd)"
```

### Support Channels

1. **Documentation First**: Check this installation guide
2. **FAQ**: Common issues in FAQ.md
3. **GitHub Issues**: Report bugs and features
4. **Email Support**: support@ai-tc-generator.org

**Required Information for Support:**
- Complete installation logs
- Support bundle (created above)
- Exact error messages
- Steps to reproduce issue
- System environment details

---

*This installation guide covers all supported deployment scenarios for the AI Test Case Generator. For additional help, see the project README.md and docs/FAQ.md.*

*Version: 4.0 | Last Updated: October 2025 | Document Reference: INST-001*
