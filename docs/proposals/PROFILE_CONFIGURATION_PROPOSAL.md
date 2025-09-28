# Configuration-Driven CLI Proposal

## Overview

This document outlines a comprehensive proposal to externalize CLI switches via YAML profiles while maintaining the powerful existing architecture of the AI Test Case Generator.

## Current Pain Points

- **17 CLI flags** with complex combinations
- Repetitive parameter entry for common workflows
- No easy way to share team configurations
- Difficult to manage environment-specific settings

## Proposed Solution: Profile-Based Configuration System

**Core Concept:** Replace verbose CLI commands with simple, named profiles that encapsulate common workflows.

### Current vs. Proposed Commands

**BEFORE (Complex):**
```bash
# Current verbose commands
ai-tc-generator input/file.reqifz --hp --model deepseek-coder-v2:16b --max-concurrent 4 --performance --template advanced_v3 --verbose --timeout 600

ai-tc-generator input/ --hp --model llama3.1:8b --max-concurrent 2 --verbose --template basic_v2 --debug
```

**AFTER (Simplified):**
```bash
# New profile-based commands
ai-tc-generator input/file.reqifz --profile Deepseek.HP.Verbose

ai-tc-generator input/ --profile Llama31.HP.Debug

# Even shorter with alias
ai-tc-gen input/file.reqifz -p Deepseek.HP.Verbose
ai-tc-gen input/ -p Llama31.HP.Debug
```

## Configuration Architecture

### Profile Naming Convention

**Final Format:** `Model.Mode[.Modifier]`

**Examples:**
- `Llama31.Standard` → Llama3.1 model, standard mode
- `Deepseek.HP.Verbose` → DeepSeek model, high-performance mode, verbose output
- `Qwen.HP` → Qwen model, high-performance mode

### Parameter Position Meanings

**Position 1 - Model:**
- `Llama31` = llama3.1:8b
- `Deepseek` = deepseek-coder-v2:16b
- `Qwen` = qwen2.5-coder:14b

**Position 2 - Mode:**
- `Standard` = Standard processing mode
- `HP` = High-Performance mode

**Position 3 - Modifier (Optional):**
- `Verbose` = Enable verbose output
- `Debug` = Enable debug mode
- `Fast` = Optimized for speed
- `Quality` = Optimized for quality

## Enhanced CLI Interface

### Profile Management Commands

```bash
# Profile management
ai-tc-generator --list-profiles                    # Show available profiles
ai-tc-generator --show-profile Deepseek.HP.Verbose # Show profile details
ai-tc-generator --validate-profiles                # Validate all profiles

# Environment switching
ai-tc-generator input/file.reqifz --profile Deepseek.HP --env production
ai-tc-generator input/file.reqifz -p Llama31.Fast -e ci-pipeline

# Override specific settings while using profile
ai-tc-generator input/file.reqifz -p Deepseek.HP --max-concurrent 8
ai-tc-generator input/file.reqifz -p Llama31.Standard --verbose

# Backward compatibility - existing flags still work
ai-tc-generator input/file.reqifz --hp --verbose   # Still supported
```

## Configuration File Structure

### Single YAML File Configuration

```yaml
# profiles.yaml
profiles:
  Llama31.Standard:
    description: "Llama3.1 standard processing"
    model: "llama3.1:8b"
    mode: "standard"
    template: "default-v2"
    max_concurrent: 0
    timeout: 300
    verbose: false
    debug: false

  Deepseek.HP.Verbose:
    description: "DeepSeek high-performance with verbose output"
    model: "deepseek-coder-v2:16b"
    mode: "high-performance"
    template: "default-v2"
    max_concurrent: 6
    timeout: 600
    performance: true
    verbose: true

environments:
  local-development:
    description: "Local development environment"
    ollama:
      host: "127.0.0.1"
      port: 11434
      timeout: 300

  production:
    description: "Production environment"
    ollama:
      host: "prod-ollama.company.com"
      port: 11434
      timeout: 900
      concurrent_requests: 2

model_configurations:
  "llama3.1:8b":
    description: "Fast general-purpose model"
    keep_alive: "15m"
    num_ctx: 4096
    num_predict: 2048
    temperature: 0.0
```

### Configuration File Discovery

**Priority Order (Highest to Lowest):**
1. **CLI flags** (immediate overrides)
2. **Environment variables** (`AI_TG_PROFILE`, `AI_TG_ENV`)
3. **Project profiles** (`./profiles.yaml` in project root)
4. **User profiles** (`~/.config/ai-tc-generator/profiles.yaml`)
5. **System profiles** (`/etc/ai-tc-generator/profiles.yaml`)
6. **Built-in defaults**

**Discovery Pattern:**
```bash
# Profile file locations checked in order:
./profiles.yaml                                    # Project root
./.ai-tc-profiles.yaml                             # Project hidden
./config/profiles.yaml                             # Project config
~/.config/ai-tc-generator/profiles.yaml            # User config
~/.ai-tc/profiles.yaml                             # User legacy
/etc/ai-tc-generator/profiles.yaml                 # System-wide
```

## Usage Examples & Workflow Benefits

### Team Collaboration Scenarios

**Scenario 1: New Developer Onboarding**
```bash
# Instead of memorizing complex flags:
ai-tc-generator --help-flags  # Shows 17+ options, overwhelming

# Simply use team standard:
ai-tc-generator input/my_first_file.reqifz --profile Llama31.Development

# Or discover available profiles:
ai-tc-generator --list-profiles
```

**Scenario 2: CI/CD Pipeline**
```bash
# Before: Complex pipeline configuration
ai-tc-generator input/ --hp --model llama3.1:8b --max-concurrent 8 --performance --timeout 300 --verbose false

# After: Clean pipeline configuration
ai-tc-generator input/ --profile Llama31.Fast --env ci-pipeline
```

**Scenario 3: Different Processing Requirements**
```bash
# Speed-focused processing
ai-tc-generator input/quick_test/ --profile Llama31.Fast

# Quality-focused processing
ai-tc-generator input/production/ --profile Deepseek.Quality

# Automotive-specific processing
ai-tc-generator input/ecu_reqs/ --profile Deepseek.Automotive --env production
```

## Profile Categories

### Standard Profiles

**Llama3.1 Model Profiles:**
- `Llama31.Standard` - Basic processing
- `Llama31.HP` - High-performance processing
- `Llama31.HP.Verbose` - HP with verbose output
- `Llama31.Fast` - Speed-optimized processing
- `Llama31.Development` - Development workflow

**DeepSeek Model Profiles:**
- `Deepseek.Standard` - Basic processing
- `Deepseek.HP` - High-performance processing
- `Deepseek.HP.Verbose` - HP with verbose output
- `Deepseek.Quality` - Quality-optimized processing
- `Deepseek.Telltale` - Telltale-specific template
- `Deepseek.Automotive` - Automotive-specific processing

**Qwen Model Profiles:**
- `Qwen.Standard` - Basic processing
- `Qwen.HP` - High-performance processing
- `Qwen.HP.Verbose` - HP with verbose output

### Specialized Profiles

- `Deepseek.Validation` - Comprehensive validation testing
- `Llama31.Development` - Development workflow optimization
- `Deepseek.Automotive` - Automotive requirements processing

## Implementation Benefits

### For Users
- **90% reduction** in command complexity for common tasks
- **Shareable configurations** across team members
- **Environment-specific** settings without manual changes
- **Reduced errors** from typos in long command lines
- **Faster onboarding** for new team members

### For DevOps
- **Standardized configurations** across environments
- **Version-controlled** team settings
- **Easier CI/CD** pipeline configuration
- **Reduced documentation** maintenance
- **Consistent** processing parameters across projects

### For Organizations
- **Knowledge sharing** through profile repositories
- **Compliance enforcement** via approved profiles
- **Audit trails** for configuration changes
- **Scalable** configuration management
- **Domain-specific** optimization (automotive, aerospace, etc.)

## Migration & Backward Compatibility

### Gradual Migration Path
1. **Phase 1**: Complete redesign with profiles alongside existing CLI flags
2. **Phase 2**: Encourage profile adoption via documentation
3. **Phase 3**: Default common configurations to profiles
4. **Phase 4**: (Optional) Deprecate verbose flags for common use cases

### Backward Compatibility
- All existing CLI flags continue to work
- Profiles override defaults but CLI flags override profiles
- Existing scripts and automation remain functional
- Clear migration documentation and examples

## Implementation Requirements

### CLI Integration
- Add `--profile` and `-p` flags to main.py
- Add profile management commands (`--list-profiles`, `--show-profile`, etc.)
- Maintain backward compatibility with existing flags

### Configuration Management
- Update ConfigManager to load and apply profiles
- Implement configuration file discovery hierarchy
- Add profile validation and error handling

### User Experience
- Profile listing and discovery commands
- Clear error messages for missing profiles
- Documentation and usage examples

## Files Created

1. **`profiles.yaml`** - Clean implementation with consistent naming
2. **`sample-profiles-edited.yaml`** - User-edited version showing preferences
3. **`sample-profiles.yaml`** - Original comprehensive example

## Next Steps

When ready to continue implementation:

1. **CLI Integration** - Add `--profile` flag to main.py
2. **Profile Loading** - Update ConfigManager to load and apply profiles
3. **Validation** - Add profile validation and listing commands
4. **Testing** - Create test cases for profile functionality
5. **Documentation** - Update help text and examples

## Decision Points Made

- **Configuration Format**: YAML (chosen over TOML/INI)
- **File Structure**: Single file (chosen over multiple files)
- **Naming Convention**: `Model.Mode[.Modifier]` (chosen over hierarchical)
- **Migration Strategy**: Complete redesign (chosen over gradual introduction)
- **Smart Features**: Excluded auto-selection and intelligent defaults

This proposal provides a foundation for dramatically simplifying the CLI while maintaining all existing functionality and adding powerful configuration management capabilities.