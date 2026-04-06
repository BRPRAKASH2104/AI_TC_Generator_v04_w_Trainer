# Frequently Asked Questions (FAQ) - AI Test Case Generator

**Version:** 4.0 | **Last Updated:** October 2025 | **Audience:** All Users

**Table of Contents:**
- [Installation & Setup](#installation--setup)
- [Usage & Operation](#usage--operation)
- [Performance & Technical](#performance--technical)
- [Models & AI](#models--ai)
- [File Processing](#file-processing)
- [Troubleshooting](#troubleshooting)
- [Configuration](#configuration)
- [Licensing & Support](#licensing--support)

---

## 🎛️ Installation & Setup

### Can I install this on Windows?

**Yes, but with limitations.** The preferred approach is Windows Subsystem for Linux (WSL2):

```bash
# Install WSL2
wsl --install -d Ubuntu

# Then follow Linux installation instructions
sudo apt update && sudo apt install python3.14 python3.14-venv python3.14-pip
```

**Why WSL2?**
- Native Windows has limited Python 3.14+ support
- WSL2 provides full Linux compatibility
- Access to all Linux tools (apt, systemctl, etc.)
- Better performance for AI workloads

**Alternative:** Use Docker on Windows 10/11 Pro/Enterprise.

### What if I get "Python version not compatible"?

**Problem:** Messages like "Python 3.14+ required but found 3.11.6"

**Solutions:**

1. **Ubuntu/Debian:**
   ```bash
   # Add deadsnakes PPA
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt update
   sudo apt install python3.14 python3.14-venv

   # Set as default
   sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.14 1
   ```

2. **macOS:**
   ```bash
   brew install python@3.14
   export PATH="/opt/homebrew/opt/python@3.14/bin:$PATH"
   ```

3. **Check version:**
   ```bash
   python --version  # Should show 3.14+
   ```

### How do I know if Ollama is running?

```bash
# Quick tests
curl -s http://localhost:11434/api/tags && echo "✅ Ollama responding"

ollama list  # Should show downloaded models

ps aux | grep ollama  # Should show running process
```

### Can I use system-installed Python instead of pip installs?

**No, not recommended.** The system requires specific Python, NumPy, and CUDA versions that may conflict with system packages.

**Best practice:** Always use virtual environments:

```bash
python3.14 -m venv ~/ai-tc-env
source ~/ai-tc-env/bin/activate
pip install -e .[dev]
```

---

## 🎯 Usage & Operation

### How do I process multiple REQIFZ files?

**Option 1: Specify directory**
```bash
ai-tc-generator input/ --output-dir output/
# Processes all *.reqifz files in input directory
```

**Option 2: Use wildcards**
```bash
ai-tc-generator input/*.reqifz --output-dir output/
```

**Option 3: Batch script**
```bash
#!/bin/bash
for file in requirements/*.reqifz; do
    echo "Processing $file..."
    ai-tc-generator "$file" --output-dir output/
done
```

### Why do I get "No test cases generated"?

**Common causes:**

1. **Empty requirements table**
   - Check REQIFZ file structure
   - Some REQIFZ files only contain system specifications

2. **AI model timeout**
   - Try different model: `--model mistral:latest`
   - Check Ollama service: `ollama list`

3. **File corruption**
   - Verify file with: `file requirements.reqifz`
   - Try alternative compression tools

4. **Empty system requirements**
   ```bash
   ai-tc-generator file.reqifz --verbose  # Shows processing details
   ```

### How many test cases should I expect?

**Typical ratios:**
- Simple requirements: 3-5 test cases each
- Complex requirements: 8-15 test cases each
- System interfaces: 2-3 verification tests each

**Example:** 50 requirements with contexts = 200-400 test cases

### Can I stop processing mid-way?

**Yes, safely:**
- Use Ctrl+C to interrupt
- Files save atomically (no corruption)
- Resume with new command (different timestamp)

---

## ⚡ Performance & Technical

### Why does high-performance mode need more RAM?

**HP mode benefits:**
- Concurrent processing (4+ requirements simultaneously)
- Requires GPU/CPU resources for parallel processing
- Memory scales with `--max-concurrent` setting

**Memory usage:** ~2-4x standard mode due to concurrent AI model loading

### What affects processing speed?

**Fastest to slowest:**

1. **Local GPU** (NVIDIA RTX 30/40 series) - ~7,000 artifacts/sec
2. **Local CPU** (8-16 cores) - ~3,000 artifacts/sec
3. **Remote AI services** - Variable, depends on network

**Parameters affecting speed:**
```bash
# Fastest settings
ai-tc-generator req.reqifz --hp --max-concurrent 8 --model llama3.1:8b

# Slowest setting
ai-tc-generator req.reqifz --model deepseek-coder-v2:16b  # +300% slower
```

### How much disk space do I need?

**Minimum per model:**
- llama3.1:8b: 4.9 GB
- deepseek-coder-v2:16b: 10.3 GB
- codellama:latest: 8.1 GB

**Working space:** +5GB for temp files and outputs

### Can I run on a Raspberry Pi or small device?

**Limited support:**
- Requires 8GB RAM minimum
- Must use lightweight models (llama3.1:8b barely fits)
- Performance: ~50 artifacts/second
- HP mode: Not recommended (<2GB RAM limit)

**Recommendation:** Minimum system requirements = Core i7, 16GB RAM, SSD

---

## 🤖 Models & AI

### Which model should I choose?

| Model | Speed | Quality | RAM | Use Case |
|-------|-------|---------|-----|----------|
| **llama3.1:8b** | ⚡ Fast | ⭐⭐⭐⭐ | 8GB | **General (recommended)** |
| **mistral:latest** | ⚡ Fast | ⭐⭐⭐ | 4GB | Simple requirements |
| **deepseek-coder-v2:16b** | 🐌 Slow | ⭐⭐⭐⭐⭐ | 16GB | Complex technical specs |
| **codellama:latest** | 🐌 Slow | ⭐⭐⭐⭐ | 16GB | Code-focused requirements |

**Recommendation:**
- Start with `llama3.1:8b` (balanced performance/quality)
- Use `mistral:latest` for speed-focused workflows
- Reserve advanced models for critical automotive specs

### How do I know if my model is compatible?

**Compatible models:**
```bash
# Test model loading
ollama pull <model_name>
ollama run <model_name> "Hello"  # Should respond

# Test with AI Test Case Generator
ai-tc-generator small_test.reqifz --model <model_name> --verbose
```

**Incompatible characteristics:**
- Chat-oriented models (not instruction-tuned)
- Very old models (<2023)
- Specialized domain models (medical, legal) without automotive knowledge

### Can I use OpenAI or external AI services?

**Not currently supported.** The system is designed specifically for Ollama local AI models due to:
- Privacy requirements (automotive requirements often sensitive)
- Network reliability for large file processing
- Cost predictability (no per-token billing)

**Alternative:** Consider contributing a provider interface for external services.

---

## 📄 File Processing

### What is REQIFZ format?

**REQIFZ** (Requirements Interchange Format Zipped) is the automotive standard for requirement exchange:
- XML-based specification format
- Compressed (ZIP) for efficient storage
- Contains tables, specifications, and metadata
- Standard for automotive OEMs and suppliers

**File structure:**
```
requirements.reqifz/
├── META-INF/
│   └── container.xml     # ZIP descriptor
├── content.reqifz/       # Actual content
│   ├── specifications    # System specifications
│   ├── specifications/requirements  # Technical requirements
│   └── tool-extensions   # Tool-specific metadata
```

### Can I process normal XML files?

**Limited support:**
```bash
# Convert XML to REQIFZ first, or:
# Use third-party tools to import into ReqIF-compatible format

# NOT supported:
ai-tc-generator requirements.xml  # ❌ Will fail
```

**Workaround:** Use OpenOffice/LibreOffice to save XML as ODT, then convert.

### What if my REQIFZ file is very large?

**Strategies:**

1. **Split large files:**
   ```bash
   # Extract specific requirements using ReqIF tools
   reqif-tool extract --requirements "Engine_Specs" large_file.reqifz

   # Process smaller chunks
   ai-tc-generator batch1.reqifz --hp
   ai-tc-generator batch2.reqifz --hp
   ```

2. **Optimize processing:**
   ```bash
   # Reduce memory usage
   ai-tc-generator large.reqifz --max-concurrent 2

   # Use diagnostic mode
   ai-tc-generator large.reqifz --debug --performance
   ```

---

## 🔧 Troubleshooting

### "connection refused" errors

**Ollama not running:**
```bash
# Check status
ps aux | grep ollama

# Start service
ollama serve &

# Alternative (macOS)
brew services start ollama
```

**Port conflicts:**
```bash
# Check port usage
lsof -i :11434

# Change port
export OLLAMA_HOST=127.0.0.1:11435
```

### Memory allocation errors

**Increase system memory:**
```bash
# Check available RAM
free -h

# Close other applications
# Use --max-concurrent 1 in HP mode

# For large files, consider:
ai-tc-generator large.reqifz --mode standard  # More memory efficient
```

### Template validation errors

**Missing templates:**
```bash
# Check templates
ai-tc-generator --list-templates

# Reinstall or update
pip install --upgrade ai-tc-generator
```

**Corrupt templates:**
```bash
# Reset templates
rm -rf ~/.config/ai_tc_generator/templates/
ai-tc-generator --validate-prompts  # Regenerates defaults
```

### Excel file corruption

**Prevention:**
```bash
# Ensure write permissions
chmod 755 output_directory/

# Use absolute paths
ai-tc-generator /full/path/to/input.reqifz --output-dir /full/path/to/output/
```

**Recovery:**
Delete corrupted file and rerun command (includes timestamp protection)

---

## ⚙️ Configuration

### Where are configuration files stored?

**Location priority (highest to lowest):**

1. **CLI arguments**: `--model llama3.1:8b --timeout 300`
2. **Environment variables**: `export AI_TG_MODEL=llama3.1:8b`
3. **YAML config file**: `cli_config.yaml`
4. **Defaults**: Built-in fallback values

**File locations:**
- User: `~/.config/ai_tc_generator/cli_config.yaml`
- Project: `./cli_config.yaml`
- System: `/etc/ai_tc_generator/config.yaml`

### How do I configure for multiple projects?

**Project-specific configuration:**
```bash
# Create project config
cat > automotive_project.yaml << EOF
cli_defaults:
  model: deepseek-coder-v2:16b  # Technical automotive specs
  template: test_generation_v3_structured
  max_concurrent: 6
  verbose: true

file_processing:
  output_encoding: utf-8
  excel_engine: openpyxl

training:
  enable_raft: false  # Disable for production
EOF

# Use with command
ai-tc-generator --config automotive_project.yaml requirements.reqifz
```

### What are the best settings for production?

**Production configuration:**
```yaml
cli_defaults:
  mode: hp              # High performance
  model: llama3.1:8b    # Balanced quality/speed
  max_concurrent: 4     # Scale with available RAM
  verbose: false        # Silent for automation

ollama:
  timeout: 900          # 15min for large batches
  keep_alive: "30m"     # Keep model loaded

logging:
  log_level: WARNING    # Warn only
  log_to_file: true
  monitor_performance: false

training:
  collect_training_data: false  # No training in production
  enable_raft: false            # Use only validated models
```

---

## 📄 Licensing & Support

### Is this open source?

**Yes, MIT licensed.** Commercial and non-commercial use permitted with attribution.

**License conditions:**
- Include original copyright notice
- Include MIT license text
- No warranty or liability from authors

### Do you provide commercial support?

**Support levels:**

- **Community**: GitHub issues, documentation
- **Basic Commercial**: Email support, 48-hour response
- **Enterprise**: 24/7 support, custom deployments, training

**Contact:** support@ai-tc-generator.org

### How do I get help quickly?

**Immediate help sources:**
1. This FAQ (you're reading it!)
2. User Manual troubleshooting sections
3. Installation Guide specific errors
4. Command help: `ai-tc-generator --help`

**For issues:**
1. Check `ai-tc-generator --verbose --debug` output
2. See "Support bundle creation" in installation guide
3. Create minimal reproducer with small file
4. Include: Python version, Ollama version, OS details

### Can I contribute improvements?

**Welcome contributions:**
- Bug fixes, feature additions, documentation
- Follow existing code style
- Include tests for new features
- Use GitHub pull requests

**Getting started:**
```bash
git clone https://github.com/your-org/ai-tc-generator.git
cd ai-tc-generator
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
pytest tests/  # Ensure tests pass
```

---

*Still have questions? Check the User Manual or Technical Documentation for detailed explanations. For immediate help with errors, include the full command output with `--debug` flag.*

*For support requests: support@ai-tc-generator.org | Documentation Version: FAQ-001-v4.0*
