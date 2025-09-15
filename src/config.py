#!/usr/bin/env python3
"""
Configuration Management for AI Test Case Generator
File: config.py

This module provides configuration classes for the AI Test Case Generator,
including settings for Ollama API, static test case parameters, and file processing.
Updated to use Pydantic for robust validation and settings management.
"""

import os
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, HttpUrl, model_validator
from pydantic_settings import SettingsError
from pydantic_settings import BaseSettings, SettingsConfigDict

# Redundant function removed - using class method in ConfigManager instead



class OllamaConfig(BaseModel):
    """Configuration for Ollama API connection and settings"""

    # Connection settings
    host: str = Field("127.0.0.1", description="Ollama host")
    port: int = Field(11434, ge=1, le=65535, description="Ollama port")
    timeout: int = Field(600, gt=0, description="API timeout in seconds")

    # Model settings
    temperature: float = Field(0.0, ge=0.0, le=2.0, description="Model temperature")
    max_retries: int = Field(3, ge=0, description="Maximum number of API retries")
    concurrent_requests: int = Field(4, ge=1, description="Number of concurrent requests")

    # GPU/Hardware-specific concurrency settings
    gpu_concurrency_limit: int = Field(1, ge=1, description="Concurrent requests for GPU-accelerated inference")
    cpu_concurrency_limit: int = Field(4, ge=1, description="Concurrent requests for CPU-only inference")

    # Ollama v0.11.10+ optimization parameters
    keep_alive: str = Field("30m", description="Keep model loaded in memory")
    num_ctx: int = Field(8192, gt=0, description="Context window size")
    num_predict: int = Field(2048, gt=0, description="Response length limit")

    # Model preferences
    synthesizer_model: str = Field("llama3.1:8b", description="Model for synthesizing test cases")
    decomposer_model: str = Field("deepseek-coder-v2:16b", description="Model for decomposing requirements")

    @model_validator(mode="after")
    def audit_config(self) -> "OllamaConfig":
        """Post-initialization validation and audit logging"""
        try:
            sys.audit("ollama.config.init", self.host, self.port)
        except (RuntimeError, OSError):
            # Audit hook may not be available in all environments
            pass
        return self

    @property
    def api_url(self) -> str:
        """Get the complete API URL for Ollama"""
        return f"http://{self.host}:{self.port}/api/generate"

    @property
    def tags_url(self) -> str:
        """Get the URL for listing available models"""
        return f"http://{self.host}:{self.port}/api/tags"


class StaticTestConfig(BaseModel):
    """Static configuration for test case generation and formatting"""

    # Test case preconditions
    voltage_precondition: str = "1. Voltage= 12V\n2. Bat-ON"

    # JIRA/Test management fields
    test_type: str = "PROVEtech"
    issue_type: str = "Test"
    project_key: str = "TCTOIC"
    assignee: str = "ENGG"
    planned_execution: str = "Manual"
    test_case_type: str = "Feature Functional"
    components: str = "SW_DI_FV"
    labels: str = "AI Generated TCs"

    # Test case formatting options
    use_issue_id_prefix: bool = True
    summary_max_length: int = Field(200, gt=0)
    description_template: str = "Generated test case for requirement {requirement_id}"


class FileProcessingConfig(BaseModel):
    """Configuration for file processing and I/O operations"""

    # Input/Output settings
    input_encoding: str = "utf-8"
    output_encoding: str = "utf-8"

    # REQIF processing
    reqif_namespaces: dict[str, HttpUrl] = {
        "reqif": "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd",
        "html": "http://www.w3.org/1999/xhtml",
    }

    # File patterns and locations
    reqifz_pattern: str = "*.reqifz"
    output_suffix: str = "_TCD_{model}_{timestamp}.xlsx"
    backup_directory: str = "backups"

    # Processing options
    validate_xml: bool = True
    skip_empty_tables: bool = True
    max_table_rows: int = Field(100, ge=0)

    # Excel-specific settings
    excel_engine: str = "openpyxl"
    excel_index: bool = False


class TrainingConfig(BaseModel):
    """Configuration for training and model customization"""

    # Training data collection
    collect_training_data: bool = False
    training_data_dir: str = "training_data"
    auto_approve_threshold: float = Field(0.9, ge=0.0, le=1.0)
    min_examples_for_training: int = Field(50, ge=1)

    # Custom model settings
    enable_custom_models: bool = False
    custom_model_prefix: str = "automotive-test-"
    retraining_schedule: str = "weekly"

    # LoRA fine-tuning parameters
    lora_r: int = Field(16, gt=0)
    lora_alpha: int = Field(32, gt=0)
    learning_rate: float = Field(2e-4, gt=0)
    num_train_epochs: int = Field(3, ge=1)

    # Conversation formatting templates (configurable for different model architectures)
    conversation_format: dict[str, str] = Field(
        default={
            'system': '<|system|>\n{content}\n',
            'user': '<|user|>\n{content}\n',
            'assistant': '<|assistant|>\n{content}\n'
        },
        description="Templates for formatting conversation roles during training"
    )


class LoggingConfig(BaseModel):
    """Configuration for logging and monitoring"""

    # Log levels and settings
    log_level: str = "INFO"
    log_to_file: bool = False
    log_directory: str = "logs"

    # Performance monitoring
    monitor_performance: bool = True
    log_api_calls: bool = False
    log_template_usage: bool = True


class CLIConfig(BaseModel):
    """Configuration for CLI defaults and behavior"""

    # Processing mode defaults
    mode: str = Field("standard", pattern="^(standard|hp|training)$", description="Default processing mode")
    model: str = Field("llama3.1:8b", description="Default AI model")
    template: str | None = Field(None, description="Default template name")
    max_concurrent: int = Field(4, ge=1, le=16, description="Default max concurrent requests")

    # I/O defaults
    input_directory: Path = Field(Path("input/"), description="Default input directory")
    output_directory: Path | None = Field(None, description="Default output directory (None = same as input)")

    # Logging defaults
    verbose: bool = Field(False, description="Default verbose mode")
    debug: bool = Field(False, description="Default debug mode")
    performance: bool = Field(False, description="Default performance metrics")

    # Configuration collections
    presets: dict[str, dict[str, Any]] = Field(default_factory=dict, description="Named configuration presets")
    environments: dict[str, dict[str, Any]] = Field(default_factory=dict, description="Environment-specific configs")
    model_configs: dict[str, dict[str, Any]] = Field(default_factory=dict, description="Model-specific settings")


class ConfigManager(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        yaml_file="example_config.yaml",
        case_sensitive=False,
    )

    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    static_test: StaticTestConfig = Field(default_factory=StaticTestConfig)
    file_processing: FileProcessingConfig = Field(default_factory=FileProcessingConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            cls.yaml_config_settings_source,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

    @classmethod
    def yaml_config_settings_source(cls, **kwargs) -> dict[str, Any]:
        """
        A simple settings source that loads variables from a YAML file
        at the project's root.

        Here we happen to know that returning an empty dictionary is an acceptable
        behavior when the YAML file does not exist.
        """
        encoding = cls.model_config.get('yaml_file_encoding')
        yaml_file = cls.model_config.get('yaml_file')
        if not yaml_file:
            return {}
        try:
            return yaml.safe_load(Path(yaml_file).read_text(encoding=encoding))
        except FileNotFoundError:
            return {}
        except Exception as e:
            raise SettingsError(f'Error loading YAML file "{yaml_file}": {e}') from e


    def save_to_file(self, config_file: str) -> None:
        """
        Save current configuration to YAML file

        Args:
            config_file: Path where to save configuration
        """
        try:
            config_path = Path(config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.model_dump(), f, default_flow_style=False, indent=2)

            print(f"✅ Configuration saved to: {config_file}")

        except Exception as e:
            print(f"Error saving configuration: {e}")

    def print_summary(self) -> None:
        """Print a summary of current configuration"""
        print("\n" + "=" * 50)
        print("CONFIGURATION SUMMARY")
        print("=" * 50)

        print("\n🔗 OLLAMA CONNECTION:")
        print(f"  • Host: {self.ollama.host}:{self.ollama.port}")
        print(f"  • API URL: {self.ollama.api_url}")
        print(f"  • Timeout: {self.ollama.timeout}s")
        print(f"  • Temperature: {self.ollama.temperature}")
        print(
            f"  • Default Models: {self.ollama.synthesizer_model}, {self.ollama.decomposer_model}"
        )

        print("\n📋 TEST CASE SETTINGS:")
        print(f"  • Test Type: {self.static_test.test_type}")
        print(f"  • Project Key: {self.static_test.project_key}")
        print(f"  • Assignee: {self.static_test.assignee}")
        print(f"  • Execution: {self.static_test.planned_execution}")

        print("\n📁 FILE PROCESSING:")
        print(f"  • Input Encoding: {self.file_processing.input_encoding}")
        print("  • Output Format: Excel (.xlsx)")
        print(f"  • Excel Engine: {self.file_processing.excel_engine}")
        print(f"  • Validate XML: {self.file_processing.validate_xml}")
        print(f"  • Max Table Rows: {self.file_processing.max_table_rows}")

        print("\n📊 LOGGING:")
        print(f"  • Log Level: {self.logging.log_level}")
        print(f"  • Log to File: {self.logging.log_to_file}")
        print(f"  • Monitor Performance: {self.logging.monitor_performance}")

        print("=" * 50)

    def load_cli_config(self, cli_config_path: Path | str | None = None) -> None:
        """Load CLI configuration from file and merge with current settings"""
        config_paths = [
            cli_config_path,  # Explicitly provided path
            Path("config/cli_config.yaml"),  # Project config
            Path.home() / ".config" / "ai_tc_generator" / "config.yaml",  # User config
        ]
        
        for config_path in config_paths:
            if config_path and Path(config_path).exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config_data = yaml.safe_load(f)
                    
                    # Update CLI configuration
                    if "cli_defaults" in config_data:
                        cli_data = config_data["cli_defaults"]
                        # Merge with existing CLI config
                        for key, value in cli_data.items():
                            if hasattr(self.cli, key):
                                setattr(self.cli, key, value)
                    
                    # Load presets, environments, and model configs
                    if "presets" in config_data:
                        self.cli.presets.update(config_data["presets"])
                    if "environments" in config_data:
                        self.cli.environments.update(config_data["environments"])
                    if "model_configs" in config_data:
                        self.cli.model_configs.update(config_data["model_configs"])
                        
                    print(f"✅ Loaded CLI config from: {config_path}")
                    return
                    
                except Exception as e:
                    print(f"⚠️  Warning: Could not load CLI config from {config_path}: {e}")
                    continue
        
        print("ℹ️  Using default CLI configuration (no config file found)")

    def get_preset_config(self, preset_name: str) -> dict[str, Any]:
        """Get named preset configuration"""
        if preset_name in self.cli.presets:
            return self.cli.presets[preset_name].copy()
        else:
            available = list(self.cli.presets.keys())
            print(f"❌ Preset '{preset_name}' not found. Available presets: {available}")
            return {}

    def get_environment_config(self, env_name: str) -> dict[str, Any]:
        """Get environment-specific configuration"""
        if env_name in self.cli.environments:
            return self.cli.environments[env_name].copy()
        else:
            available = list(self.cli.environments.keys())
            print(f"❌ Environment '{env_name}' not found. Available environments: {available}")
            return {}

    def apply_cli_overrides(self, **kwargs) -> dict[str, Any]:
        """Apply CLI configuration with environment variables and overrides"""
        # Start with CLI defaults
        effective_config = {
            "mode": self.cli.mode,
            "model": self.cli.model,
            "template": self.cli.template,
            "max_concurrent": self.cli.max_concurrent,
            "verbose": self.cli.verbose,
            "debug": self.cli.debug,
            "performance": self.cli.performance,
        }
        
        # Apply environment variables (AI_TG_* prefix)
        env_mapping = {
            "AI_TG_MODE": "mode",
            "AI_TG_MODEL": "model", 
            "AI_TG_TEMPLATE": "template",
            "AI_TG_MAX_CONCURRENT": "max_concurrent",
            "AI_TG_VERBOSE": "verbose",
            "AI_TG_DEBUG": "debug",
            "AI_TG_PERFORMANCE": "performance",
        }
        
        for env_var, config_key in env_mapping.items():
            if env_value := os.getenv(env_var):
                if config_key in ["verbose", "debug", "performance"]:
                    effective_config[config_key] = env_value.lower() in ("true", "1", "yes", "on")
                elif config_key == "max_concurrent":
                    try:
                        effective_config[config_key] = int(env_value)
                    except ValueError:
                        print(f"⚠️  Invalid {env_var} value: {env_value}")
                else:
                    effective_config[config_key] = env_value
        
        # Apply direct kwargs (highest priority)
        effective_config.update({k: v for k, v in kwargs.items() if v is not None})
        
        return effective_config

    def show_effective_config(self, **overrides) -> None:
        """Display the effective configuration with all overrides applied"""
        config = self.apply_cli_overrides(**overrides)
        
        print("\n🔧 EFFECTIVE CLI CONFIGURATION")
        print("=" * 40)
        print(f"  Mode: {config['mode']}")
        print(f"  Model: {config['model']}")
        print(f"  Template: {config['template'] or 'auto-select'}")
        print(f"  Max Concurrent: {config['max_concurrent']}")
        print(f"  Verbose: {config['verbose']}")
        print(f"  Debug: {config['debug']}")
        print(f"  Performance: {config['performance']}")
        print("=" * 40)


# Global configuration instance
default_config = ConfigManager()


if __name__ == "__main__":
    # Demo configuration usage
    print("🔧 AI Test Case Generator - Pydantic Configuration Demo")

    try:
        # Create default configuration
        # Pydantic automatically loads from env vars and files
        config = ConfigManager()

        # Print summary
        config.print_summary()

        # Save example configuration
        config.save_to_file("example_config.yaml")

        # Example of accessing a nested value
        print(f"\nTesting a nested value: {config.ollama.timeout}s")

    except Exception as e:
        print(f"❌ An error occurred during configuration demo: {e}")
