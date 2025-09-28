# CLI Configuration Management Proposal

## Current CLI Switches Analysis

### **Current CLI Switches (14 total)**

From `main.py`, the following switches are available:

**Input/Output Control:**
- `input_path` (argument): Input REQIFZ file or directory path
- `--output-dir`: Output directory for generated files
- `--config`: Configuration file path

**Processing Mode Control:**
- `--hp`, `--high-performance`: Enable high-performance async processing
- `--training`: Enable training mode (requires ML dependencies)

**AI Model Configuration:**
- `--model`: AI model to use (default: "llama3.1:8b")
- `--template`: Specific prompt template to use
- `--max-concurrent`: Maximum concurrent requirements (HP mode)

**Utility Operations:**
- `--validate-prompts`: Validate all prompt templates and exit
- `--list-templates`: List available prompt templates and exit
- `--version`: Show version information

**Output Control:**
- `--verbose`, `-v`: Enable verbose output
- `--debug`: Enable debug mode with detailed logging
- `--performance`: Show detailed performance metrics (HP mode only)

---

## Proposed External Configuration Strategy

### **Phase 1: Enhanced Configuration File Support**

#### **1.1 CLI Configuration File (cli_config.yaml)**

Create a dedicated CLI configuration file that can override all command-line defaults:

```yaml
# cli_config.yaml - CLI Defaults and Presets
cli_defaults:
  # Processing settings
  mode: "standard"  # standard|hp|training
  model: "llama3.1:8b"
  template: null
  max_concurrent: 4
  
  # Input/Output settings
  input_directory: "input/"
  output_directory: null  # null = same as input directory
  
  # Logging and output
  verbose: false
  debug: false
  performance: false

# Named presets for common configurations
presets:
  development:
    mode: "standard"
    model: "llama3.1:8b"
    verbose: true
    debug: true
    
  production:
    mode: "hp"
    model: "deepseek-coder-v2:16b"
    max_concurrent: 8
    performance: true
    verbose: false
    
  testing:
    mode: "standard"
    model: "llama3.1:8b"
    verbose: true
    max_concurrent: 2

# Environment-specific overrides
environments:
  local:
    max_concurrent: 2
    verbose: true
    
  ci_cd:
    mode: "standard"
    verbose: false
    debug: false
    
  production:
    mode: "hp"
    max_concurrent: 8
    performance: false  # Don't clutter production logs
```

#### **1.2 Enhanced ConfigManager Integration**

Extend the existing `src/config.py` to include CLI configuration management:

```python
class CLIConfig(BaseModel):
    """Configuration for CLI defaults and behavior"""
    
    # Processing mode defaults
    default_mode: str = Field("standard", pattern="^(standard|hp|training)$")
    default_model: str = Field("llama3.1:8b")
    default_template: str | None = Field(None)
    default_max_concurrent: int = Field(4, ge=1, le=16)
    
    # I/O defaults
    default_input_directory: Path = Field(Path("input/"))
    default_output_directory: Path | None = Field(None)
    
    # Logging defaults
    default_verbose: bool = Field(False)
    default_debug: bool = Field(False)
    default_performance: bool = Field(False)
    
    # Preset configurations
    presets: dict[str, dict[str, Any]] = Field(default_factory=dict)
    environments: dict[str, dict[str, Any]] = Field(default_factory=dict)

class ConfigManager:
    def __init__(self, cli_config_path: Path | None = None):
        self.cli_config = self.load_cli_config(cli_config_path)
        # ... existing config loading
    
    def load_cli_config(self, config_path: Path | None = None) -> CLIConfig:
        \"\"\"Load CLI configuration with fallback to defaults\"\"\"
        if config_path and config_path.exists():
            with open(config_path) as f:
                config_data = yaml.safe_load(f)
            return CLIConfig(**config_data.get('cli_defaults', {}))
        return CLIConfig()
    
    def get_preset_config(self, preset_name: str) -> dict[str, Any]:
        \"\"\"Get named preset configuration\"\"\"
        return self.cli_config.presets.get(preset_name, {})
    
    def get_environment_config(self, env_name: str) -> dict[str, Any]:
        \"\"\"Get environment-specific configuration\"\"\"
        return self.cli_config.environments.get(env_name, {})
```

### **Phase 2: Advanced Configuration Features**

#### **2.1 Configuration Hierarchy**

Implement a configuration precedence system:

1. **Command-line arguments** (highest priority)
2. **Environment variables** (e.g., `AI_TG_MODEL=deepseek-coder-v2:16b`)
3. **User config file** (`~/.config/ai_tc_generator/config.yaml`)
4. **Project config file** (`./cli_config.yaml`)
5. **Default values** (lowest priority)

#### **2.2 Environment Variable Support**

Add environment variable support for all CLI options:

```bash
# Environment variables with AI_TG_ prefix
export AI_TG_MODE=hp
export AI_TG_MODEL=deepseek-coder-v2:16b
export AI_TG_MAX_CONCURRENT=8
export AI_TG_VERBOSE=true
export AI_TG_DEBUG=false
export AI_TG_PERFORMANCE=true

# Run with environment variables
python main.py input/file.reqifz
```

#### **2.3 Profile-Based Configuration**

Add support for configuration profiles:

```bash
# Use predefined profiles
python main.py input/file.reqifz --profile development
python main.py input/file.reqifz --profile production
python main.py input/file.reqifz --profile testing

# Environment-based profiles
python main.py input/file.reqifz --env local
python main.py input/file.reqifz --env ci_cd
```

### **Phase 3: Advanced Configuration Management**

#### **3.1 Interactive Configuration**

Add interactive configuration setup:

```bash
# Interactive configuration wizard
python main.py --configure

# Validate current configuration
python main.py --validate-config

# Show effective configuration
python main.py --show-config
```

#### **3.2 Configuration Templates**

Provide configuration templates for common use cases:

```bash
# Generate configuration templates
python main.py --init-config development
python main.py --init-config production
python main.py --init-config ci_cd
```

---

## Implementation Plan

### **Phase 1: Basic Config File Support (Priority: High)**

**Files to Create:**
- `config/cli_config.yaml` - Default CLI configuration
- `config/cli_config_schema.yaml` - JSON Schema for validation

**Files to Modify:**
- `src/config.py` - Add CLIConfig class and configuration loading
- `main.py` - Integrate configuration loading with Click options

**Implementation Steps:**
1. Create `CLIConfig` Pydantic model in `src/config.py`
2. Add configuration file loading logic
3. Update `main.py` to use configuration defaults
4. Create example configuration files

**Benefits:**
- Reduce command-line verbosity
- Standardize team configurations
- Easy switching between development/production settings

### **Phase 2: Environment Variables & Profiles (Priority: Medium)**

**Files to Create:**
- `src/config_profiles.py` - Profile management system
- `config/profiles/` - Directory for profile configurations

**Files to Modify:**
- `src/config.py` - Add environment variable support
- `main.py` - Add `--profile` and `--env` options

**Implementation Steps:**
1. Add environment variable detection using `os.environ`
2. Implement profile loading system
3. Create configuration hierarchy resolution
4. Add profile validation and error handling

**Benefits:**
- CI/CD integration support
- Environment-specific optimizations
- Team collaboration improvements

### **Phase 3: Advanced Features (Priority: Low)**

**Files to Create:**
- `src/config_wizard.py` - Interactive configuration setup
- `config/templates/` - Configuration templates

**Files to Modify:**
- `main.py` - Add configuration management commands

**Implementation Steps:**
1. Create interactive configuration wizard
2. Implement configuration validation tools
3. Add template generation system
4. Create configuration migration tools

**Benefits:**
- User-friendly setup experience
- Configuration validation and debugging
- Easy onboarding for new users

---

## Configuration File Examples

### **Basic CLI Configuration**

```yaml
# cli_config.yaml
cli_defaults:
  mode: "hp"
  model: "llama3.1:8b"
  max_concurrent: 4
  verbose: true
  input_directory: "input/"

presets:
  fast:
    mode: "hp"
    model: "llama3.1:8b"
    max_concurrent: 8
    performance: true
    
  accurate:
    mode: "standard"
    model: "deepseek-coder-v2:16b"
    verbose: true
    debug: true
```

### **Advanced Configuration with Environments**

```yaml
# cli_config.yaml
cli_defaults:
  mode: "standard"
  model: "llama3.1:8b"
  verbose: false

environments:
  development:
    verbose: true
    debug: true
    max_concurrent: 2
    
  staging:
    mode: "hp"
    max_concurrent: 4
    performance: true
    
  production:
    mode: "hp" 
    model: "deepseek-coder-v2:16b"
    max_concurrent: 8
    verbose: false
    debug: false

model_configs:
  "llama3.1:8b":
    timeout: 300
    temperature: 0.0
    max_concurrent: 4
    
  "deepseek-coder-v2:16b":
    timeout: 600
    temperature: 0.0
    max_concurrent: 2
```

---

## Usage Examples

### **Current Usage (Before)**
```bash
python main.py input/file.reqifz --hp --model deepseek-coder-v2:16b --max-concurrent 8 --performance --verbose
```

### **Proposed Usage (After)**

**With Configuration File:**
```bash
# Simple usage with config file defaults
python main.py input/file.reqifz

# Using presets
python main.py input/file.reqifz --profile production

# Override specific settings
python main.py input/file.reqifz --profile production --verbose
```

**With Environment Variables:**
```bash
export AI_TG_MODE=hp
export AI_TG_MODEL=deepseek-coder-v2:16b
python main.py input/file.reqifz
```

**Configuration Management:**
```bash
# Setup configuration interactively
python main.py --configure

# Show current effective configuration
python main.py --show-config

# Validate configuration
python main.py --validate-config
```

---

## Benefits of External Configuration

### **For Developers**
- **Reduced Typing**: Long command lines become simple commands
- **Consistency**: Standardized settings across team members
- **Flexibility**: Easy switching between different configurations
- **Documentation**: Configuration files serve as documentation

### **For DevOps/CI/CD**
- **Environment Variables**: Easy integration with deployment systems
- **Profiles**: Different settings for dev/staging/production
- **Validation**: Configuration validation prevents deployment errors
- **Repeatability**: Consistent builds and deployments

### **For End Users**
- **Simplicity**: Reduced learning curve for new users
- **Presets**: Common configurations readily available
- **Customization**: Easy to create personal preferences
- **Portability**: Configuration files can be shared and version controlled

---

## Technical Implementation Details

### **Configuration Loading Order**
1. Load default configuration from code
2. Load project configuration file (`cli_config.yaml`)
3. Load user configuration file (`~/.config/ai_tc_generator/config.yaml`)
4. Load environment variables (`AI_TG_*`)
5. Apply command-line arguments (highest priority)

### **Error Handling**
- Graceful fallback to defaults if configuration files are invalid
- Clear error messages for configuration problems
- Configuration validation before processing
- Support for partial configurations

### **Backward Compatibility**
- All existing command-line arguments continue to work
- Configuration is purely additive - no breaking changes
- Default behavior remains unchanged without configuration files

This proposal provides a comprehensive strategy for managing CLI switches through external configuration while maintaining full backward compatibility and adding powerful new features for different use cases.