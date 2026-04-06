# AI Test Case Generator User Manual

**Version:** 4.0 | **Date:** October 2025 | **Audience:** End Users

---

## 📖 Welcome to AI Test Case Generator

The AI Test Case Generator is an intelligent tool that automatically creates contextual test cases from automotive requirement documents (REQIF files) using advanced AI models. This user manual will guide you through installation, setup, and usage to help you generate high-quality test cases efficiently.

### 🎯 What This Tool Does

- **📋 Automated Test Case Generation**: Converts requirement specifications into complete test cases
- **🤖 AI-Powered Analysis**: Uses LLMs (like Ollama) to understand automotive domain context
- **📊 Excel Output**: Produces structured test cases ready for Jira, ALM, or spreadsheet import
- **⚡ High Performance**: Processes large requirement files in minutes instead of hours
- **🎓 Continuous Learning**: Optional training system improves AI accuracy over time

---

## 🚀 Quick Start Guide

### Prerequisites Checklist

Before you begin, ensure you have:

- [x] **Operating System**: macOS, Linux, or Windows with WSL
- [x] **Python**: Version 3.14+ (required)
- [x] **RAM**: 8GB minimum, 16GB recommended
- [x] **Disk Space**: 2GB free space
- [x] **Internet**: Required for AI model downloads
- [x] **REQIF Files**: Automotive requirement files in .reqifz format

### 3-Minute Installation

```bash
# 1. Install Python dependencies
pip install ai-tc-generator[dev]

# 2. Install and start Ollama (AI service)
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &

# 3. Download required AI model
ollama pull llama3.1:8b

# 4. Test installation
ai-tc-generator --version
ai-tc-generator --validate-prompts
```

**Expected Output:**
```
AI Test Case Generator v2.3.0
📋 Found 5 template(s)
✅ test_generation_adaptive validated
✅ test_generation_v3_structured validated
...
```

### Your First Test Case Generation

```bash
# Generate test cases from automotive requirements
ai-tc-generator my_project/requirements.reqifz --output-dir ./output
```

**What happens:**
- System analyzes the requirement file structure
- AI model understands context (headings, information, interfaces)
- Test cases are generated with complete details (preconditions, steps, expected results)
- Excel file is created: `my_project_requirements_TCD_llama3.1_8b_2025-10-06_14-30-00.xlsx`

---

## 📂 Understanding the Output

### Excel File Structure

The generated Excel file contains automotive-specific test case columns:

| Column | Description | Example |
|--------|-------------|---------|
| **Test Case ID** | Unique identifier | TC_AUTO_001 |
| **Summary** | Brief test description | Verify door lock activation under normal conditions |
| **Description** | Full requirement details | Based on REQ-Door-001: Door shall lock when vehicle speed >10km/h |
| **Preconditions** | Equipment/conditions needed | 1. Vehicle power on<br>2. Doors unlocked<br>3. Speed sensors operational |
| **Test Steps** | Step-by-step instructions | 1. Start vehicle<br>2. Accelerate to 15km/h<br>3. Monitor door lock status |
| **Expected Results** | What should happen | Door locks automatically and warning light illuminates |
| **Data** | Input variations | Speed: 5km/h, 10km/h, 15km/h, 50km/h |
| **Project** | JIRA project key | VEHC (Vehicle Control) |
| **Issue Type** | JIRA issue type | Test |
| **Test Type** | Classification | Functional |
| **Priority** | Importance level | Medium |
| **Labels** | Tags for organization | auto-generated, safety-critical |

### AI Context Enhancement

The system automatically analyzes your REQIF file structure to provide context:

**Without Context:** Basic test cases with generic instructions

**With Context:** Specific automotive-focused test cases including:
- Equipment-level requirements (CAN bus communications)
- Subsystem interactions (power management, diagnostics)
- Safety considerations (fault detection, redundancy)
- Performance requirements (timing constraints)

---

## ⚙️ Basic Configuration

### Environment Variables

Set these in your environment or `.env` file for basic setup:

```bash
# Essential settings
export AI_TG_MODEL="llama3.1:8b"
export AI_TG_OLLAMA_HOST="127.0.0.1"
export AI_TG_OLLAMA_PORT="11434"
export AI_TG_VERBOSE="true"
```

### Configuration File

For advanced configuration, create `cli_config.yaml`:

```yaml
# Basic user configuration
cli_defaults:
  mode: standard
  model: llama3.1:8b
  template: test_generation_v3_structured
  max_concurrent: 4
  verbose: true

# Output preferences
output:
  suffix: "_TCD_{model}_{timestamp}.xlsx"
  encoding: utf-8
  excel_engine: openpyxl
```

### Supported AI Models

| Model | Use Case | Requirements |
|-------|----------|--------------|
| **llama3.1:8b** | General purpose (recommended) | 8GB RAM, ~5GB space |
| **deepseek-coder-v2:16b** | Complex requirements | 16GB RAM, ~10GB space |
| **mistral:latest** | Alternative general | 8GB RAM, ~4GB space |
| **codellama:latest** | Code-focused requirements | 16GB RAM, ~8GB space |

---

## 🎛️ Basic Usage Patterns

### Processing Single Files

```bash
# Standard mode (recommended for most users)
ai-tc-generator MyProject/requirements.reqifz

# High-performance mode (3x faster for large files)
ai-tc-generator MyProject/requirements.reqifz --hp

# Custom output location
ai-tc-generator req.reqifz --output-dir ./my_test_cases/
```

### Processing Multiple Files

```bash
# Process entire directory
ai-tc-generator input/ --output-dir output/

# Process specific file types only
ai-tc-generator input/*.reqifz --output-dir output/
```

### Different AI Models

```bash
# Use different model for variety
ai-tc-generator req.reqifz --model deepseek-coder-v2:16b

# Try codellama for technical specifications
ai-tc-generator req.reqifz --model codellama:latest
```

### Custom Templates

```bash
# Use pre-built templates
ai-tc-generator req.reqifz --template test_generation_v3_structured

# Let system auto-select (default)
ai-tc-generator req.reqifz --template auto
```

---

## 📊 Understanding Results

### Success Messages

```
🚀 AI Test Case Generator v4.0
📖 Loading configuration...
🔍 Input: DoorSystems.reqifz
🤖 Model: llama3.1:8b
🏗️ Architecture: Modular Standard Processor

📊 Found 45 artifacts
🔄 Building context... (45 artifacts → 23 context-enriched requirements)
⚡ Generating test cases...

✅ Generation Complete
📊 Generated: 156 test cases from 23 requirements
⏱️ Time: 42.8 seconds
📁 Saved to: DoorSystems_TCD_llama3.1_8b_2025-10-06_14-30-00.xlsx
```

### Interpreting Metrics

| Metric | Meaning | Good Range |
|--------|---------|------------|
| **Test cases** | Total generated | 5-200+ (depends on requirements) |
| **Requirements processed** | Source requirements | 10-100+ (depends on file) |
| **Artifiacts found** | Raw XML elements | 50-1000+ (depends on REQIFZ size) |
| **Time** | Processing duration | <30s (small), <120s (large files) |
| **Success rate** | Requirements → Test cases | >80% (ignore empty/structural requirements) |

### Common Issues

**1. "No test cases generated"**
- **Cause**: Requirements without tables/table structure issues
- **Solution**: Verify REQIFZ file format or structure

**2. "AI connection timeout"**
- **Cause**: Ollama service not running or slow model
- **Solution**:
  ```bash
  ollama serve &  # Start Ollama
  ollama pull llama3.1:8b  # Ensure model downloaded
  ```

**3. "Memory errors"**
- **Cause**: Very large REQIFZ files (>1GB)
- **Solution**: Process in smaller batches or use high-performance mode

---

## 💡 Best Practices

### File Organization

```
/MyProject/
├── input/
│   ├── DoorSystem.reqifz
│   ├── WindowSystem.reqifz
│   └── ClimateSystem.reqifz
├── output/
│   ├── DoorSystem_TCD_llama3.1_8b_2025-10-06.xlsx
│   ├── WindowSystem_TCD_llama3.1_8b_2025-10-06.xlsx
│   └── ClimateSystem_TCD_llama3.1_8b_2025-10-06.xlsx
└── archive/
    └── previous_versions/
```

### Naming Conventions

```bash
# Clear project identification
ai-tc-generator systems/doors.reqifz --output-dir output/door_system/

# Version tracking
ai-tc-generator v2.3/specifications.reqifz --output-dir outputs/v2.3/

# Model comparison
ai-tc-generator req.reqifz --model llama3.1:8b --output-dir model_comparison/llama/
ai-tc-generator req.reqifz --model deepseek-coder-v2:16b --output-dir model_comparison/deepseek/
```

### Quality Verification

**1. Manual Review Process:**
1. Open generated Excel file
2. Spot-check 3-5 test cases per requirement
3. Verify conditions, steps, and expected results match requirements
4. Check automotive context is preserved (CAN bus, safety-critical, timing)

**2. AI Enhancement:**
```bash
# Run with different models for comparison
for model in llama3.1:8b deepseek-coder-v2:16b; do
    ai-tc-generator req.reqifz --model $model --output-dir comparison/${model}/
done
# Compare outputs for consistency and detail
```

### Performance Optimization

**For Large Files (>100 requirements):**
```bash
# Use high-performance mode
ai-tc-generator large_file.reqifz --hp --max-concurrent 8

# Process in batches if needed
split --bytes=500M large_file.reqifz part_
ai-tc-generator part_* --output-dir batch_output/
```

**For Memory-Constrained Systems:**
```bash
# High-performance mode with reduced concurrency
ai-tc-generator req.reqifz --hp --max-concurrent 1

# Use streaming modes when available
ai-tc-generator very_large.reqifz --mode standard  # More memory efficient
```

---

## 🔧 Troubleshooting Common Issues

### Installation Issues

**"Python version not compatible"**
```bash
# Check your Python version
python --version  # Should be 3.14+ 

# Use python3 if python is older
python3 --version
alias python=python3  # Or update your PATH
```

**"pip install fails"**
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install in user space if permission issues
pip install --user ai-tc-generator

# Alternative: use virtual environment
python -m venv ai_tc_env
source ai_tc_env/bin/activate
pip install ai-tc-generator
```

### Ollama Issues

**"Ollama not found"**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Verify running
curl http://localhost:11434/api/tags
```

**"Model not available"**
```bash
# List available models
ollama list

# Pull required model
ollama pull llama3.1:8b

# Check download progress
ollama ls
```

**"Connection refused"**
```bash
# Check if Ollama is running
ps aux | grep ollama

# Kill and restart if needed
killall ollama
ollama serve &

# Verify port is accessible
lsof -i :11434
```

### File Processing Issues

**"No artifacts found in REQIFZ file"**
- **Cause**: Corrupt or incompatible REQIFZ format
- **Solutions**:
  - Verify file is a valid .reqifz archive (not XML file)
  - Try different compression ratio if manually created
  - Check file permissions (read access)

**"Processing timeout"**
```bash
# Increase timeout for slow models
export AI_TG_TIMEOUT=900  # 15 minutes instead of default 10

# Use faster model temporarily
ai-tc-generator large_file.reqifz --model llama3.1:8b

# Process in smaller batches
ai-tc-generator batch1.reqifz --hp --max-concurrent 1
ai-tc-generator batch2.reqifz --hp --max-concurrent 1
```

### Memory Issues

**"Out of memory"**
```bash
# Use system monitoring
# Get memory usage
ps aux | grep ai-tc

# Process smaller files
split --number=3 large.reqifz part_

# Use streaming techniques (enable HP mode)
ai-tc-generator large.reqifz --hp --max-concurrent 1

# Monitor resources
top -p $(pgrep -f ai-tc)
```

### Output Issues

**"Excel file empty"**
- Check console output for error messages
- Verify write permissions on output directory
- Try different output directory

**"Excel corrupted"**
- **Cause**: Process interruption during writing
- **Recovery**: Delete corrupted file, re-run generation
- **Prevention**: Ensure stable system resources during generation

---

## 📈 Advanced Usage

### Profile-Based Configuration

Run with a named configuration profile that bundles model, mode, and options:

```bash
ai-tc-generator input/file.reqifz --profile Llama31.HP.Quality
```

| Option | Description |
|--------|-------------|
| `--profile TEXT` | Run with a named configuration profile (e.g. `Llama31.HP.Quality`). Profiles are defined in `profiles/profiles.yaml`. |

Profile format: `Model.Mode[.Modifier]`

### Custom Templates

The system supports custom YAML prompt templates for specialized requirements:

```yaml
# custom_template.yaml
test_generation:
  system_prompt: |
    You are an expert automotive test engineer specializing in [DOMAIN].
    Generate context-aware test cases considering [SPECIFIC_CONSTRAINTS].

  prompt_template: |
    Requirement: {requirement_id}
    Domain: Automotive [SUBSYSTEM]
    Context: {heading}
    Information: {info_str}

    Generate test cases with these specifications...
```

**Usage:**
```bash
# Validate custom template
ai-tc-generator --validate-prompts

# Use custom template
ai-tc-generator req.reqifz --template custom_template
```

### Batch Processing

**Directory Processing:**
```bash
# Process all REQIFZ files in directory
ai-tc-generator input/ --output-dir batch_results/

# Process specific patterns
find . -name "*.reqifz" -exec ai-tc-generator {} --output-dir results/ \;
```

**Automated Processing:**
```bash
#!/bin/bash
# batch_process.sh
for file in input/*.reqifz; do
    echo "Processing $file..."
    ai-tc-generator "$file" --output-dir output/ --hp >> batch_log.txt
done
echo "Batch processing complete"
```

### Model Comparison

```bash
#!/bin/bash
# compare_models.sh
models=("llama3.1:8b" "deepseek-coder-v2:16b" "mistral:latest")
for model in "${models[@]}"; do
    echo "Testing with $model..."
    ai-tc-generator requirements.reqifz \
        --model "$model" \
        --output-dir "comparison/$model/" \
        --performance
done
echo "Model comparison complete"
```

### Performance Monitoring

```bash
# Enable detailed performance metrics
ai-tc-generator large.reqifz --hp --performance

# Monitor AI calls and resource usage
ai-tc-generator req.reqifz --verbose --debug 2>&1 | tee generation.log

# Track memory usage
time ai-tc-generator req.reqifz --hp
```

---

## 📞 Support and Resources

### Getting Help

**1. Check Documentation First:**
- This user manual (you're reading it!)
- Troubleshooting Guide (common solutions)
- FAQ (quick answers)

**2. System Diagnostics:**
```bash
# Basic system info
uname -a
python --version
ollama --version

# Test basic functionality
ai-tc-generator --version
ai-tc-generator --validate-prompts
curl http://localhost:11434/api/tags

# Generate debug information
ai-tc-generator problem_file.reqifz --debug --verbose 2>&1 > debug.log
```

**3. Common Support Paths:**
- Search existing documentation for your specific error
- Check Ollama logs: `ollama logs`
- Verify AI model status: `ollama ls`
- Test with minimal REQIFZ file

### File Formats Supported

**.reqifz Files:**
- Automotive requirement exchanges (preferred)
- XML-based with compression
- Contains tables, specifications, relationships

**Expected Structure:**
```
├── Specification (system context)
├── headings (functional categories)
├── information artifacts (details, constraints)
├── system requirements (testable items)
├── system interfaces (system boundaries)
└── relationships (dependencies)
```

### Error Types and Solutions

| Error Type | Symptoms | Quick Fix |
|------------|----------|-----------|
| **Connection** | "Cannot connect to Ollama" | Restart Ollama service |
| **Timeout** | "Request timed out" | Increase timeout, use faster model |
| **Model Not Found** | "Model unavailable" | `ollama pull <model>` |
| **No Test Cases** | "0 test cases generated" | Check file structure, try different model |
| **Memory Error** | "Out of memory" | Use HP mode, reduce concurrency |
| **File Error** | "Cannot read REQIFZ" | Check file permissions, format |

---

## 📋 Quick Reference

### Essential Commands

```bash
# Installation
pip install ai-tc-generator

# Setup AI service
ollama serve &
ollama pull llama3.1:8b

# Generate test cases
ai-tc-generator requirements.reqifz

# High-performance mode
ai-tc-generator requirements.reqifz --hp

# Custom output
ai-tc-generator req.reqifz --output-dir ./test_cases/

# Different model
ai-tc-generator req.reqifz --model deepseek-coder-v2:16b

# Verbose output
ai-tc-generator req.reqifz --verbose
```

### File Organization Checklist

- [x] REQIFZ files in dedicated input directory
- [x] Output directory separate from inputs
- [x] Config files in standard locations
- [x] Archive old outputs (timestamp protection)
- [x] Use descriptive naming conventions

### Success Verification

- [x] Excel file created successfully
- [x] Test case count looks reasonable (>10 usually)
- [x] Processing time reasonable (<60 seconds typically)
- [x] No error messages in console output
- [x] Spot-check test cases make sense for automotive domain

---

## 🎓 Learning Resources

### Beginner Tutorials

1. **"Hello World" Example:**
   ```bash
   # Start with a simple command
   ai-tc-generator sample.reqifz
   # Check the generated Excel file for structure
   ```

2. **Exploring Templates:**
   ```bash
   ai-tc-generator --list-templates
   # Try different templates with the same file
   ```

3. **Model Comparison:**
   ```bash
   ai-tc-generator req.reqifz --model llama3.1:8b --output-dir Outputs/ModelA/
   ai-tc-generator req.reqifz --model mistral:latest --output-dir Outputs/ModelB/
   # Compare quality vs speed
   ```

### Advanced Learning

1. **Context Understanding:** Read the section on "AI Context Enhancement"
2. **Performance Tuning:** Experiment with HP mode and concurrency settings
3. **Training System:** Explore RAFT training for custom model creation
4. **CI/CD Integration:** Learn to automate test case generation

---

## 🔄 Updating and Maintenance

### Version Checking

```bash
# Check your version
ai-tc-generator --version

# Latest available (check documentation)
curl https://api.github.com/repos/your-org/ai-tc-generator/releases/latest
```

### Update Process

```bash
# Update Python package
pip install --upgrade ai-tc-generator

# Update AI models (as needed)
ollama pull llama3.1:8b  # Get latest version

# Verify installation
ai-tc-generator --validate-prompts
```

### Data Migration

The system creates new files each run (timestamp protection), so migration is typically not needed. However, for organizational changes:

```bash
# Archive old outputs
mkdir archive && mv output/batch_* archive/

# Update configuration
cp cli_config.yaml cli_config_backup.yaml
# Edit configuration file with new settings
```

---

## 📞 Need More Help?

If this manual doesn't solve your issue:

1. **📖 Check the FAQ** - Common questions and answers
2. **🔍 Search Troubleshooting Guide** - Detailed problem resolution
3. **📧 Contact Support** - Include debug logs and system information

### Creating Support Tickets

**Required Information:**
- AI Test Case Generator version: `ai-tc-generator --version`
- Python version: `python --version`
- Ollama version: `ollama --version`
- Operating System: `uname -a`
- Error messages (complete output)
- Debug log: `ai-tc-generator problem.reqifz --debug --verbose`

---

*This user manual covers the complete end-user experience for the AI Test Case Generator v4.0. For technical details, configuration options, and development information, see the complementary CLAUDE.md developer guide.*

*Version: 4.0 | Last Updated: October 2025 | Feedback: documentation@ai-tc-generator.org*
