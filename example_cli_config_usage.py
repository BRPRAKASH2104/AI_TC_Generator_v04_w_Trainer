#!/usr/bin/env python3
"""
Practical Example: CLI Configuration System Usage
File: example_cli_config_usage.py

This example demonstrates how the CLI configuration system works with:
1. Configuration file loading
2. Preset usage
3. Environment variables
4. Command-line overrides
5. Configuration hierarchy
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import ConfigManager


def demonstrate_configuration_loading():
    """Demonstrate how configuration files are loaded and merged"""
    print("🔧 CLI Configuration System Demonstration")
    print("=" * 60)
    
    # Initialize ConfigManager
    config_manager = ConfigManager()
    
    # Load CLI configuration from our example file
    config_manager.load_cli_config("config/cli_config.yaml")
    
    print("\n📋 AVAILABLE PRESETS:")
    for preset_name, preset_config in config_manager.cli.presets.items():
        print(f"  • {preset_name}: {preset_config}")
    
    print("\n🌍 AVAILABLE ENVIRONMENTS:")
    for env_name, env_config in config_manager.cli.environments.items():
        print(f"  • {env_name}: {env_config}")
    
    return config_manager


def demonstrate_preset_usage(config_manager):
    """Show how presets work"""
    print("\n" + "=" * 60)
    print("🎛️  PRESET CONFIGURATION EXAMPLES")
    print("=" * 60)
    
    presets_to_demo = ["development", "production", "testing", "turbo", "accurate"]
    
    for preset_name in presets_to_demo:
        print(f"\n📦 Using preset: '{preset_name}'")
        print("-" * 30)
        
        preset_config = config_manager.get_preset_config(preset_name)
        if preset_config:
            for key, value in preset_config.items():
                print(f"  {key}: {value}")
        else:
            print("  (Preset not found)")


def demonstrate_environment_variables(config_manager):
    """Show how environment variables override settings"""
    print("\n" + "=" * 60)
    print("🌐 ENVIRONMENT VARIABLE OVERRIDES")
    print("=" * 60)
    
    print("\n📍 Current environment variables (AI_TG_* prefix):")
    env_vars = {k: v for k, v in os.environ.items() if k.startswith("AI_TG_")}
    if env_vars:
        for env_var, value in env_vars.items():
            print(f"  {env_var} = {value}")
    else:
        print("  (No AI_TG_* environment variables set)")
    
    # Demonstrate setting environment variables programmatically
    print("\n🧪 Setting test environment variables:")
    test_env_vars = {
        "AI_TG_MODE": "hp",
        "AI_TG_MODEL": "deepseek-coder-v2:16b", 
        "AI_TG_MAX_CONCURRENT": "6",
        "AI_TG_VERBOSE": "true",
        "AI_TG_PERFORMANCE": "true"
    }
    
    for var, value in test_env_vars.items():
        os.environ[var] = value
        print(f"  Set {var} = {value}")
    
    # Show effective configuration with environment variables
    print("\n📊 Effective configuration with environment variables:")
    config_manager.show_effective_config()
    
    # Clean up environment variables
    for var in test_env_vars:
        del os.environ[var]


def demonstrate_configuration_hierarchy(config_manager):
    """Show how configuration hierarchy works (precedence order)"""
    print("\n" + "=" * 60)
    print("⚡ CONFIGURATION HIERARCHY DEMONSTRATION")
    print("=" * 60)
    
    print("\n🏗️  Configuration Precedence (highest to lowest):")
    print("  1. Command-line arguments")
    print("  2. Environment variables (AI_TG_*)")
    print("  3. User config file (~/.config/ai_tc_generator/config.yaml)")
    print("  4. Project config file (config/cli_config.yaml)")
    print("  5. Default values")
    
    scenarios = [
        {
            "name": "Defaults only",
            "env_vars": {},
            "cli_args": {},
            "description": "Using only default configuration"
        },
        {
            "name": "With preset",
            "env_vars": {},
            "cli_args": {"preset": "production"},
            "description": "Using production preset configuration"
        },
        {
            "name": "Environment overrides",
            "env_vars": {"AI_TG_MODE": "hp", "AI_TG_VERBOSE": "true"},
            "cli_args": {},
            "description": "Environment variables override defaults"
        },
        {
            "name": "CLI overrides all",
            "env_vars": {"AI_TG_MODE": "hp", "AI_TG_VERBOSE": "true"},
            "cli_args": {"mode": "standard", "verbose": False, "debug": True},
            "description": "CLI args have highest priority"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print(f"   {scenario['description']}")
        print("-" * 40)
        
        # Set environment variables
        for env_var, value in scenario["env_vars"].items():
            os.environ[env_var] = value
        
        # Apply preset if specified
        cli_overrides = scenario["cli_args"].copy()
        if "preset" in cli_overrides:
            preset_name = cli_overrides.pop("preset")
            preset_config = config_manager.get_preset_config(preset_name)
            cli_overrides.update(preset_config)
        
        # Show effective configuration
        effective_config = config_manager.apply_cli_overrides(**cli_overrides)
        
        for key, value in effective_config.items():
            print(f"  {key}: {value}")
        
        # Clean up environment variables
        for env_var in scenario["env_vars"]:
            if env_var in os.environ:
                del os.environ[env_var]


def demonstrate_practical_usage_examples():
    """Show practical command-line usage examples"""
    print("\n" + "=" * 60)
    print("💡 PRACTICAL USAGE EXAMPLES")
    print("=" * 60)
    
    examples = [
        {
            "before": "python main.py input/file.reqifz --hp --model deepseek-coder-v2:16b --max-concurrent 8 --performance --verbose",
            "after": "python main.py input/file.reqifz --preset production",
            "description": "Long command becomes simple with presets"
        },
        {
            "before": "python main.py input/file.reqifz --model llama3.1:8b --verbose --debug --max-concurrent 2",
            "after": "python main.py input/file.reqifz --preset development",
            "description": "Development settings in one preset"
        },
        {
            "before": "python main.py input/file.reqifz --hp --max-concurrent 12 --performance",
            "after": "python main.py input/file.reqifz --preset turbo",
            "description": "Maximum speed configuration"
        },
        {
            "before": "# Set environment variables for CI/CD\nexport AI_TG_MODE=standard\nexport AI_TG_VERBOSE=false",
            "after": "python main.py input/file.reqifz --env ci_cd",
            "description": "CI/CD environment configuration"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['description']}")
        print(f"   Before: {example['before']}")
        print(f"   After:  {example['after']}")


def main():
    """Main demonstration function"""
    try:
        # Demonstrate configuration loading
        config_manager = demonstrate_configuration_loading()
        
        # Show preset usage
        demonstrate_preset_usage(config_manager)
        
        # Show environment variable handling
        demonstrate_environment_variables(config_manager)
        
        # Show configuration hierarchy
        demonstrate_configuration_hierarchy(config_manager)
        
        # Show practical examples
        demonstrate_practical_usage_examples()
        
        print("\n" + "=" * 60)
        print("✅ CLI Configuration System Demonstration Complete!")
        print("=" * 60)
        
        print("\n🔧 To use this system:")
        print("  1. Copy config/cli_config.yaml to your project")
        print("  2. Modify presets and environments as needed")  
        print("  3. Use --preset or --env flags with main.py")
        print("  4. Set AI_TG_* environment variables as needed")
        print("  5. CLI arguments always have highest priority")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()