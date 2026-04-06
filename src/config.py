#!/usr/bin/env python3
"""
Configuration Management for AI Test Case Generator
File: config.py

This module provides configuration classes for the AI Test Case Generator,
including settings for Ollama API, static test case parameters, and file processing.
Updated to use Pydantic for robust validation and settings management.
"""

import contextlib
import os
import sys
from pathlib import Path
from typing import Any, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

# Redundant function removed - using class method in ConfigManager instead


class OllamaConfig(BaseModel):
    """Configuration for Ollama API connection and settings (Python 3.14 + Ollama 0.12.5)"""

    # Connection settings
    host: str = Field("127.0.0.1", description="Ollama host")
    port: int = Field(11434, ge=1, le=65535, description="Ollama port")
    timeout: int = Field(600, gt=0, description="API timeout in seconds")

    # Security settings - using environment variables for sensitive data
    api_key: str | None = Field(
        None, description="API key for authentication (use AI_TG_API_KEY env var)"
    )
    auth_token: str | None = Field(
        None, description="Auth token for API access (use AI_TG_AUTH_TOKEN env var)"
    )

    # Model settings
    temperature: float = Field(0.0, ge=0.0, le=2.0, description="Model temperature")
    max_retries: int = Field(3, ge=0, description="Maximum number of API retries")
    concurrent_requests: int = Field(4, ge=1, description="Number of concurrent requests")

    # Advanced sampling parameters for improved determinism
    tfs_z: float = Field(
        0.9, ge=0.0, le=1.0, description="Tail-free sampling parameter (reduces hallucinations)"
    )
    typical_p: float = Field(
        0.9, ge=0.0, le=1.0, description="Typical sampling parameter (improves coherence)"
    )
    repeat_last_n: int = Field(
        128, ge=0, description="Number of previous tokens to consider for repetition penalty"
    )

    # GPU/Hardware-specific concurrency settings (Ollama 0.12.5 optimized)
    gpu_concurrency_limit: int = Field(
        2, ge=1, description="Concurrent requests for GPU inference (0.12.5 improved)"
    )
    cpu_concurrency_limit: int = Field(
        4, ge=1, description="Concurrent requests for CPU-only inference"
    )

    # Ollama 0.12.5 optimization parameters
    keep_alive: str = Field(
        "30m", description="Keep model loaded in memory (0.12.5 improved scheduling)"
    )
    num_ctx: int = Field(16384, gt=0, description="Context window size (0.12.5 supports 16K+)")
    num_predict: int = Field(4096, gt=0, description="Response length limit (0.12.5 increased max)")

    # Ollama 0.12.5 memory management
    enable_gpu_offload: bool = Field(True, description="Enable GPU memory offloading (0.12.5)")
    max_vram_usage: float = Field(0.95, ge=0.1, le=1.0, description="Max VRAM utilization (0.12.5)")

    # Model preferences
    synthesizer_model: str = Field("llama3.1:8b", description="Model for synthesizing test cases")
    decomposer_model: str = Field(
        "deepseek-coder-v2:16b", description="Model for decomposing requirements"
    )

    # Vision model support (Ollama 0.12.5+ with multimodal models)
    vision_model: str = Field(
        "llama3.2-vision:11b",
        description="Vision-capable model for requirements with diagrams (e.g., llama3.2-vision:11b)",
    )
    enable_vision: bool = Field(
        True, description="Enable vision model for requirements with images (hybrid strategy)"
    )
    vision_context_window: int = Field(
        32768,
        gt=0,
        description="Context window for vision model (llama3.2-vision supports 32K-128K)",
    )

    # Logprobs for confidence scoring (Ollama 0.13.3+)
    enable_logprobs: bool = Field(
        True, description="Enable logprobs generation for confidence scoring"
    )
    top_logprobs: int = Field(
        1, ge=1, le=10, description="Number of top logprobs to return (default 1)"
    )

    @model_validator(mode="after")
    def audit_config(self) -> Self:
        """Post-initialization validation and audit logging"""
        with contextlib.suppress(RuntimeError, OSError):
            sys.audit(
                "ollama.config.init", self.host, self.port
            )  # Audit hook may not be available in all environments
        return self

    @property
    def api_url(self) -> str:
        """Get the complete API URL for Ollama"""
        return f"http://{self.host}:{self.port}/api/generate"

    @property
    def version_url(self) -> str:
        """Get the URL for version endpoint (Ollama 0.12.5+)"""
        return f"http://{self.host}:{self.port}/api/version"

    @property
    def show_url(self) -> str:
        """Get the URL for model information endpoint (Ollama)"""
        return f"http://{self.host}:{self.port}/api/show"


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


class ValidationConfig(BaseModel):
    """Configuration for semantic validation"""

    enable_semantic_validation: bool = Field(
        True, description="Enable semantic validation of test cases"
    )
    signal_name_validation: bool = Field(
        True, description="Validate signal names against interface dictionary"
    )
    similarity_threshold: float = Field(
        0.8, ge=0.0, le=1.0, description="Fuzzy match threshold for signal names"
    )
    fail_on_validation_error: bool = Field(
        False, description="Fail generation if validation fails (vs. warn only)"
    )


class DeduplicationConfig(BaseModel):
    """Configuration for test case deduplication"""

    enable_deduplication: bool = Field(True, description="Enable test case deduplication")
    similarity_threshold: float = Field(
        0.85,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for considering test cases as duplicates",
    )
    keep_strategy: str = Field(
        "best", description="Strategy for keeping duplicates: 'first', 'last', or 'best'"
    )
    fields_to_compare: list[str] = Field(
        default_factory=lambda: ["action", "data", "expected_result"],
        description="Fields to compare for similarity detection",
    )


class RelationshipConfig(BaseModel):
    """Configuration for requirement relationship parsing"""

    enable_relationship_parsing: bool = Field(
        True, description="Enable parsing of SPEC-RELATION elements"
    )
    augment_requirements: bool = Field(
        True, description="Augment requirements with parent/child/hierarchy metadata"
    )
    build_dependency_graph: bool = Field(
        False, description="Build dependency graph from relationships"
    )
    max_hierarchy_depth: int = Field(
        10, ge=1, le=100, description="Maximum hierarchy depth (prevents infinite loops)"
    )


class ImageExtractionConfig(BaseModel):
    """Configuration for image extraction from REQIFZ files"""

    enable_image_extraction: bool = Field(
        True, description="Enable extraction of images from REQIFZ files"
    )
    save_images: bool = Field(True, description="Save extracted images to disk")
    output_dir: str = Field("TEMP/images", description="Directory for saving extracted images")
    validate_images: bool = Field(
        True, description="Validate images using PIL/Pillow (requires Pillow)"
    )
    augment_artifacts: bool = Field(
        True, description="Augment artifacts with image reference metadata"
    )


class FileProcessingConfig(BaseModel):
    """Configuration for file processing and I/O operations"""

    # Input/Output settings
    input_encoding: str = "utf-8"
    output_encoding: str = "utf-8"

    # REQIF processing
    reqif_namespaces: dict[str, str] = {
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


class SecretsConfig(BaseModel):
    """Configuration for secrets and sensitive data management"""

    # API credentials - loaded from environment variables
    ollama_api_key: str | None = Field(None, description="Ollama API key")
    external_api_key: str | None = Field(None, description="External AI service API key")
    database_password: str | None = Field(None, description="Database password")
    encryption_key: str | None = Field(None, description="Encryption key for sensitive data")

    # Cloud service credentials
    aws_access_key_id: str | None = Field(None, description="AWS access key ID")
    aws_secret_access_key: str | None = Field(None, description="AWS secret access key")
    azure_client_id: str | None = Field(None, description="Azure client ID")
    azure_client_secret: str | None = Field(None, description="Azure client secret")

    # Webhook and integration secrets
    webhook_secret: str | None = Field(None, description="Webhook validation secret")
    github_token: str | None = Field(None, description="GitHub personal access token")
    slack_token: str | None = Field(None, description="Slack bot token")

    # Security settings
    enable_encryption: bool = Field(False, description="Enable encryption for sensitive data")
    secrets_expiry_hours: int = Field(
        24, ge=1, le=168, description="Hours after which secrets should be refreshed"
    )

    def model_post_init(self, __context) -> None:
        """Load secrets from environment variables after initialization"""
        # Mapping of field names to environment variable names
        env_mapping = {
            "ollama_api_key": "AI_TG_OLLAMA_API_KEY",
            "external_api_key": "AI_TG_EXTERNAL_API_KEY",
            "database_password": "AI_TG_DATABASE_PASSWORD",
            "encryption_key": "AI_TG_ENCRYPTION_KEY",
            "aws_access_key_id": "AWS_ACCESS_KEY_ID",
            "aws_secret_access_key": "AWS_SECRET_ACCESS_KEY",
            "azure_client_id": "AZURE_CLIENT_ID",
            "azure_client_secret": "AZURE_CLIENT_SECRET",
            "webhook_secret": "AI_TG_WEBHOOK_SECRET",
            "github_token": "AI_TG_GITHUB_TOKEN",
            "slack_token": "AI_TG_SLACK_TOKEN",
        }

        # Load values from environment variables
        for field_name, env_var in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value:
                setattr(self, field_name, env_value)

    def get_masked_summary(self) -> dict[str, str]:
        """Get a summary of secrets with masked values for logging"""
        summary = {}
        for field_name, value in self.model_dump().items():
            if field_name.endswith("_hours") or field_name.startswith("enable_"):
                summary[field_name] = str(value)
            elif value is not None:
                # Mask sensitive values
                if len(str(value)) > 8:
                    summary[field_name] = f"{str(value)[:4]}***{str(value)[-2:]}"
                else:
                    summary[field_name] = "***"
            else:
                summary[field_name] = "not_set"
        return summary

    def validate_required_secrets(self, required_secrets: list[str]) -> tuple[bool, list[str]]:
        """
        Validate that required secrets are present

        Args:
            required_secrets: List of required secret field names

        Returns:
            Tuple of (all_present, missing_secrets)
        """
        missing_secrets = []
        for secret_name in required_secrets:
            if not getattr(self, secret_name, None):
                missing_secrets.append(secret_name)

        return len(missing_secrets) == 0, missing_secrets


class TrainingConfig(BaseModel):
    """Configuration for training and model customization"""

    # Training data collection
    collect_training_data: bool = False
    training_data_dir: str = "training_data"
    auto_approve_threshold: float = Field(0.9, ge=0.0, le=1.0)
    min_examples_for_training: int = Field(50, ge=1)

    # RAFT-specific settings
    enable_raft: bool = Field(False, description="Enable RAFT data collection")
    raft_collect_context: bool = Field(True, description="Collect retrieved context for RAFT")
    raft_min_oracle_docs: int = Field(1, ge=1, description="Minimum oracle documents per example")
    raft_min_distractor_docs: int = Field(1, ge=0, description="Minimum distractor documents")
    raft_context_window: int = Field(5, ge=1, description="Max context items to include")
    raft_min_quality: int = Field(
        3, ge=1, le=5, description="Minimum quality rating for RAFT dataset"
    )

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
            "system": "<|system|>\n{content}\n",
            "user": "<|user|>\n{content}\n",
            "assistant": "<|assistant|>\n{content}\n",
        },
        description="Templates for formatting conversation roles during training",
    )


class LoggingConfig(BaseModel):
    """Configuration for logging and monitoring"""

    # Log levels and settings
    log_level: str = "INFO"
    log_to_file: bool = False
    log_directory: str = "TEMP/logs"

    # Performance monitoring
    monitor_performance: bool = True
    log_api_calls: bool = False
    log_template_usage: bool = True


class CLIConfig(BaseModel):
    """Configuration for CLI defaults and behavior"""

    model_config = ConfigDict(protected_namespaces=())

    # Processing mode defaults
    mode: str = Field(
        "standard", pattern="^(standard|hp|training)$", description="Default processing mode"
    )
    model: str = Field("llama3.1:8b", description="Default AI model")
    template: str | None = Field(None, description="Default template name")
    max_concurrent: int = Field(4, ge=1, le=16, description="Default max concurrent requests")

    # I/O defaults
    input_directory: Path = Field(Path("input/"), description="Default input directory")
    output_directory: Path | None = Field(
        None, description="Default output directory (None = same as input)"
    )

    # Logging defaults
    verbose: bool = Field(False, description="Default verbose mode")
    debug: bool = Field(False, description="Default debug mode")
    performance: bool = Field(False, description="Default performance metrics")

    # Configuration collections
    presets: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Named configuration presets"
    )
    environments: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Environment-specific configs"
    )
    model_configs: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Model-specific settings"
    )


class ConfigManager(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        yaml_file="src/example_config.yaml" if Path("src/example_config.yaml").exists() else None,
        case_sensitive=False,
    )

    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    static_test: StaticTestConfig = Field(default_factory=StaticTestConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    deduplication: DeduplicationConfig = Field(default_factory=DeduplicationConfig)
    relationships: RelationshipConfig = Field(default_factory=RelationshipConfig)
    image_extraction: ImageExtractionConfig = Field(default_factory=ImageExtractionConfig)
    file_processing: FileProcessingConfig = Field(default_factory=FileProcessingConfig)
    secrets: SecretsConfig = Field(default_factory=SecretsConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)

    @classmethod
    def settings_customise_sources(
        cls,
        _settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            YamlConfigSettingsSource(cls, cls.model_config.get("yaml_file")),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

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

    def get_model_for_requirement(self, requirement: dict) -> str:
        """
        Select appropriate model based on requirement characteristics (hybrid strategy).

        This method implements intelligent model selection:
        - Vision model (llama3.2-vision) for requirements with diagrams/images
        - Text model (llama3.1) for text-only requirements (faster)

        Args:
            requirement: Requirement data containing metadata

        Returns:
            Model name to use for generation
        """
        # Use vision model only if vision enabled AND valid saved images exist
        if self.ollama.enable_vision:
            images = requirement.get("images", [])
            if images and any(img.get("saved_path") for img in images):
                return self.ollama.vision_model

        # Fallback to standard synthesizer model for text-only
        return self.ollama.synthesizer_model

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

        print("\n🔐 SECRETS MANAGEMENT:")
        secrets_summary = self.secrets.get_masked_summary()
        for key, value in secrets_summary.items():
            if not key.endswith("_hours") and not key.startswith("enable_"):
                print(f"  • {key.replace('_', ' ').title()}: {value}")
        print(f"  • Encryption Enabled: {self.secrets.enable_encryption}")
        print(f"  • Secrets Expiry: {self.secrets.secrets_expiry_hours}h")

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
                    with open(config_path, encoding="utf-8") as f:
                        config_data = yaml.safe_load(f)

                    # Update CLI configuration
                    if "cli_defaults" in config_data:
                        cli_data = config_data["cli_defaults"]
                        # Merge with existing CLI config through Pydantic validation
                        current = self.cli.model_dump()
                        for key, value in cli_data.items():
                            if key in current:
                                current[key] = value
                        self.cli = self.cli.__class__.model_validate(current)

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

    def apply_cli_overrides(self, **kwargs) -> ConfigManager:
        """
        Apply CLI configuration with environment variables and overrides.

        This method creates a new ConfigManager instance with the overrides applied,
        providing a single source of truth for configuration throughout the application.

        Args:
            **kwargs: CLI arguments to override (model, template, max_concurrent, num_ctx, etc.)

        Returns:
            New ConfigManager instance with overrides applied
        """
        # Application of overrides
        # We need to track which keys were explicitly populated via environment variables
        # so they aren't incorrectly overwritten by model-specific defaults later.
        config_dict = self.model_dump()
        env_overrides = {"cli": set(), "ollama": set(), "logging": set(), "secrets": set()}

        # Apply environment variables (AI_TG_* prefix)
        env_mapping = {
            "AI_TG_MODEL": ("ollama", "synthesizer_model"),
            "AI_TG_TEMPLATE": ("cli", "template"),
            "AI_TG_MAX_CONCURRENT": ("ollama", "concurrent_requests"),
            "AI_TG_NUM_CTX": ("ollama", "num_ctx"),
            "AI_TG_VERBOSE": ("cli", "verbose"),
            "AI_TG_DEBUG": ("cli", "debug"),
            "AI_TG_PERFORMANCE": ("cli", "performance"),
            "AI_TG_LOG_LEVEL": ("logging", "log_level"),
            "AI_TG_TIMEOUT": ("ollama", "timeout"),
            "AI_TG_TEMPERATURE": ("ollama", "temperature"),
            "AI_TG_OLLAMA_HOST": ("ollama", "host"),
            "AI_TG_OLLAMA_PORT": ("ollama", "port"),
            "AI_TG_ENCRYPTION": ("secrets", "enable_encryption"),
        }

        for env_var, (section, key) in env_mapping.items():
            if env_value := os.getenv(env_var):
                if key in ["verbose", "debug", "performance"]:
                    config_dict[section][key] = env_value.lower() in ("true", "1", "yes", "on")
                    env_overrides[section].add(key)
                elif key in ["max_concurrent", "concurrent_requests", "timeout", "num_ctx"]:
                    try:
                        config_dict[section][key] = int(env_value)
                        env_overrides[section].add(key)
                    except ValueError:
                        print(f"⚠️  Invalid {env_var} value: {env_value}")
                elif key == "temperature":
                    try:
                        config_dict[section][key] = float(env_value)
                        env_overrides[section].add(key)
                    except ValueError:
                        print(f"⚠️  Invalid {env_var} value: {env_value}")
                else:
                    config_dict[section][key] = env_value
                    env_overrides[section].add(key)

        # Apply direct kwargs (highest priority)
        cli_overrides = {}
        ollama_overrides = {}

        # Map CLI arguments to configuration sections
        if "model" in kwargs and kwargs["model"] is not None:
            ollama_overrides["synthesizer_model"] = kwargs["model"]
        if "template" in kwargs and kwargs["template"] is not None:
            cli_overrides["template"] = kwargs["template"]
        if "max_concurrent" in kwargs and kwargs["max_concurrent"] is not None:
            ollama_overrides["concurrent_requests"] = kwargs["max_concurrent"]
        if "num_ctx" in kwargs and kwargs["num_ctx"] is not None:
            ollama_overrides["num_ctx"] = kwargs["num_ctx"]
        if "verbose" in kwargs and kwargs["verbose"] is not None:
            cli_overrides["verbose"] = kwargs["verbose"]
        if "debug" in kwargs and kwargs["debug"] is not None:
            cli_overrides["debug"] = kwargs["debug"]
        if "performance" in kwargs and kwargs["performance"] is not None:
            cli_overrides["performance"] = kwargs["performance"]
        if "config" in kwargs and kwargs["config"] is not None:
            # Load additional config file if specified
            try:
                additional_config = yaml.safe_load(Path(kwargs["config"]).read_text())
                # Deep merge additional config
                self._deep_merge_dict(config_dict, additional_config)
            except Exception as e:
                print(f"⚠️  Warning: Could not load config file {kwargs['config']}: {e}")

        if cli_overrides:
            self._deep_merge_dict(config_dict["cli"], cli_overrides)
        if ollama_overrides:
            self._deep_merge_dict(config_dict["ollama"], ollama_overrides)

        # -------------------------------------------------------------------------
        # Critical Fix: Auto-apply model-specific settings (timeout, temperature, etc.)
        # -------------------------------------------------------------------------
        # Determine the effective model to use for lookup
        # Priority: 1. CLI Override -> 2. Environment Var -> 3. Current Config (Preset/Default)
        effective_model = ollama_overrides.get("synthesizer_model") or config_dict["ollama"].get(
            "synthesizer_model"
        )

        # Check if we have specific config for this model
        # Access model_configs from the current instance's CLI config
        model_configs = self.cli.model_configs

        if effective_model and effective_model in model_configs:
            m_config = model_configs[effective_model]

            # Apply timeout if not explicitly overridden by CLI/Env
            # (We check if 'timeout' was in the overrides dicts passed to this method or env vars)
            # Actually, simplest safe way: apply defaults from model_config IF they are unset/default
            # OR just overwrite, assuming model_config is the specific intent for that model.
            # BUT CLI args should always win.

            # Helper to update if NOT in overrides AND not in env_overrides
            def update_if_not_overridden(section, key, value, override_dict, env_tracker):
                if key not in override_dict and key not in env_tracker.get(section, set()):
                    config_dict[section][key] = value

            if "timeout" in m_config:
                update_if_not_overridden("ollama", "timeout", m_config["timeout"], ollama_overrides, env_overrides)

            if "temperature" in m_config:
                update_if_not_overridden("ollama", "temperature", m_config["temperature"], ollama_overrides, env_overrides)

            if "recommended_concurrent" in m_config:
                update_if_not_overridden("ollama", "concurrent_requests", m_config["recommended_concurrent"], ollama_overrides, env_overrides)

            if "num_ctx" in m_config:
                update_if_not_overridden("ollama", "num_ctx", m_config["num_ctx"], ollama_overrides, env_overrides)

            # Log this internal application if debugging
            # print(f"ℹ️  Applied specific settings for model: {effective_model}")

        # Create new ConfigManager instance with updated configuration
        return ConfigManager.model_validate(config_dict)

    @staticmethod
    def _deep_merge_dict(base_dict: dict[str, Any], update_dict: dict[str, Any]) -> None:
        """Deep merge update_dict into base_dict"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                ConfigManager._deep_merge_dict(base_dict[key], value)
            else:
                base_dict[key] = value

    def show_effective_config(self, **overrides) -> None:
        """Display the effective configuration with all overrides applied"""
        effective_config = self.apply_cli_overrides(**overrides)

        print("\n🔧 EFFECTIVE CLI CONFIGURATION")
        print("=" * 40)
        print(f"  Mode: {effective_config.cli.mode}")
        print(f"  Model: {effective_config.ollama.synthesizer_model}")
        print(f"  Template: {effective_config.cli.template or 'auto-select'}")
        print(f"  Max Concurrent: {effective_config.ollama.concurrent_requests}")
        print(f"  Verbose: {effective_config.cli.verbose}")
        print(f"  Debug: {effective_config.cli.debug}")
        print(f"  Performance: {effective_config.cli.performance}")
        print(f"  Timeout: {effective_config.ollama.timeout}s")
        print(f"  Temperature: {effective_config.ollama.temperature}")
        print("=" * 40)

    def validate_secrets_for_mode(self, mode: str) -> tuple[bool, list[str]]:
        """
        Validate that required secrets are available for a specific operational mode

        Args:
            mode: Operational mode (e.g., 'cloud', 'external_api', 'training')

        Returns:
            Tuple of (all_present, missing_secrets)
        """
        required_secrets_by_mode = {
            "cloud": ["aws_access_key_id", "aws_secret_access_key"],
            "azure": ["azure_client_id", "azure_client_secret"],
            "external_api": ["external_api_key"],
            "training": ["encryption_key"],
            "webhooks": ["webhook_secret"],
            "integrations": ["github_token", "slack_token"],
        }

        required = required_secrets_by_mode.get(mode, [])
        return self.secrets.validate_required_secrets(required)

    def get_secrets_status(self) -> dict[str, Any]:
        """Get comprehensive secrets status for monitoring and debugging"""
        secrets_summary = self.secrets.get_masked_summary()

        # Count configured vs unconfigured secrets
        configured_count = sum(
            1
            for v in secrets_summary.values()
            if v not in ["not_set", "False"] and not v.startswith("enable_")
        )
        total_secrets = len(
            [k for k in secrets_summary if not k.endswith("_hours") and not k.startswith("enable_")]
        )

        return {
            "secrets_configured": configured_count,
            "total_secrets_available": total_secrets,
            "encryption_enabled": self.secrets.enable_encryption,
            "secrets_expiry_hours": self.secrets.secrets_expiry_hours,
            "secrets_summary": secrets_summary,
            "configuration_health": "healthy" if configured_count > 0 else "minimal",
        }


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
