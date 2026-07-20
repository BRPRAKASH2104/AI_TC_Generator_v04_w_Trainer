#!/usr/bin/env python3
"""
AI Test Case Generator - Truly Modular Implementation

This is the unified entry point that orchestrates the modular components:
- Core components (extractors, generators, formatters, clients, parsers)
- Processors (standard and high-performance workflows)
- Clean separation of concerns and maintainable architecture

Modern Python 3.14+ (no backward compatibility).
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

# Add project root to path so src package can be imported
sys.path.insert(0, str(Path(__file__).parent))

import click
from rich.console import Console
from rich.panel import Panel

# Import processors (high-level orchestrators)
from src.app_logger import get_app_logger, shutdown_app_logger

# Import utilities
from src.config import ConfigManager
from src.core.image_extractor import RequirementImageExtractor
from src.core.validators import template_schema_issues
from src.processors.hp_processor import HighPerformanceREQIFZFileProcessor
from src.processors.standard_processor import REQIFZFileProcessor
from src.yaml_prompt_manager import YAMLPromptManager

# Version and metadata (matches pyproject.toml)
__version__ = "2.3.0"
__architecture__ = "Modular"

console = Console()


def show_banner(mode: str = "standard") -> None:
    """Display application banner with mode information"""
    mode_info = {
        "standard": "Standard Processing Mode",
        "hp": "High-Performance Mode (4-8x faster)",
        "training": "Training-Enhanced Mode",
        "validate": "Template Validation Mode",
    }

    title = f"🚀 AI Test Case Generator v{__version__}"
    subtitle = mode_info.get(mode, "Standard Processing Mode")

    panel = Panel.fit(
        f"[bold cyan]{title}[/bold cyan]\n"
        f"[dim]{subtitle}[/dim]\n"
        f"[dim]Modular Architecture • Python 3.14+[/dim]",
        border_style="cyan",
    )
    console.print(panel)


def _apply_preset(
    base_config: ConfigManager, preset_name: str
) -> tuple[ConfigManager, dict[str, set[str]]]:
    """Merge a named preset into the base configuration.

    Args:
        base_config: Configuration loaded from defaults and cli_config.yaml.
        preset_name: Name of the preset under `presets:` in cli_config.yaml.

    Returns:
        Tuple of (merged config, preset-applied keys per section). The keys
        are handed to apply_cli_overrides() so preset values are protected
        from model-specific defaults exactly like explicit overrides
        (review 2026-07-17 finding 5).
    """
    preset_config = base_config.get_preset_config(preset_name)
    if not preset_config:
        return base_config, {}

    # Mapping definitions (flat preset key -> nested config path)
    key_mapping = {
        "model": ["ollama", "synthesizer_model"],
        "mode": ["cli", "mode"],
        "verbose": ["cli", "verbose"],
        "debug": ["cli", "debug"],
        "performance": ["cli", "performance"],
        "max_concurrent": ["ollama", "concurrent_requests"],
    }

    def set_nested(d: dict[str, Any], path: list[str], value: Any) -> None:
        for key in path[:-1]:
            d = d.setdefault(key, {})
        d[path[-1]] = value

    nested_update: dict[str, Any] = {}
    preset_keys: dict[str, set[str]] = {}

    for key, value in preset_config.items():
        if key in key_mapping:
            section, field = key_mapping[key]
            temp_dict: dict[str, Any] = {}
            set_nested(temp_dict, key_mapping[key], value)
            ConfigManager._deep_merge_dict(nested_update, temp_dict)
            preset_keys.setdefault(section, set()).add(field)
        else:
            # Already-nested keys like 'ollama' are merged as-is
            temp_dict = {key: value}
            ConfigManager._deep_merge_dict(nested_update, temp_dict)
            if isinstance(value, dict):
                preset_keys.setdefault(key, set()).update(value.keys())

    current_data = base_config.model_dump()
    ConfigManager._deep_merge_dict(current_data, nested_update)
    # Re-validate to ensure type safety and apply changes
    return ConfigManager.model_validate(current_data), preset_keys


def _resolve_processing_mode(hp: bool, config: ConfigManager) -> str:
    """Resolve the processing mode: --hp forces HP, else the effective
    config (which includes preset `mode`) decides (review 2026-07-17 §5)."""
    return "hp" if hp or config.cli.mode == "hp" else "standard"


def _aggregate_directory_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-file processing results for directory runs.

    The run is successful only when every file succeeded; any mix of
    successes and failures is a partial completion (review 2026-07-17 §1).

    Args:
        results: Per-file result dictionaries from process_directory().

    Returns:
        Aggregated result with success/partial flags, failed file names,
        collected failed requirements, and summed statistics.
    """
    if not results:
        return {
            "success": False,
            "partial": False,
            "failed_files": [],
            "failed_requirements": [],
            "error": "No REQIFZ files found to process",
            "total_test_cases": 0,
            "processing_time": 0.0,
        }

    failed = [r for r in results if not r.get("success")]
    succeeded = [r for r in results if r.get("success")]

    aggregated: dict[str, Any] = {
        "success": not failed,
        "partial": bool(succeeded) and (bool(failed) or any(r.get("partial") for r in succeeded)),
        "failed_files": [r.get("input_file", "unknown") for r in failed],
        "failed_requirements": [
            entry for r in results for entry in r.get("failed_requirements", [])
        ],
        "total_test_cases": sum(r.get("total_test_cases", 0) for r in results),
        "processing_time": sum(r.get("processing_time", 0.0) for r in results),
    }

    if failed:
        aggregated["error"] = f"{len(failed)} of {len(results)} files failed"

    return aggregated


def _resolve_exit_code(result: dict[str, Any]) -> int:
    """Map a processing result to the process exit code.

    Contract: 0 = everything completed, 2 = partial completion (some output
    was produced but not all requested inputs completed), 1 = total failure.
    """
    if result.get("partial"):
        return 2
    return 0 if result.get("success") else 1


def _print_partial_details(result: dict[str, Any]) -> None:
    """Print the failed files/requirements behind a partial completion."""
    failed_files = result.get("failed_files") or []
    if failed_files:
        console.print(f"❗ {len(failed_files)} file(s) failed:")
        for file_name in failed_files:
            console.print(f"   • {file_name}")

    failed_requirements = result.get("failed_requirements") or []
    if failed_requirements:
        console.print(f"❗ {len(failed_requirements)} requirement(s) produced no test cases:")
        for entry in failed_requirements:
            console.print(
                f"   • {entry.get('requirement_id', 'UNKNOWN')}: "
                f"{entry.get('error_type', 'Unknown')} - {entry.get('error_message', '')}"
            )


@click.command()
@click.argument("input_path", required=False, type=click.Path(exists=True))
@click.option(
    "--hp",
    "--high-performance",
    is_flag=True,
    help="Enable high-performance mode with async processing",
)
@click.option("--training", is_flag=True, help="Enable training mode (requires ML dependencies)")
@click.option(
    "--model",
    default=None,
    help="AI model to use for generation (default: config synthesizer_model, llama3.1:8b)",
)
@click.option("--template", type=str, default=None, help="Specific prompt template to use")
@click.option(
    "--preset", type=str, default=None, help="Use a named configuration preset (e.g., qwen_vision)"
)
@click.option(
    "--output-dir", type=click.Path(), default=None, help="Output directory for generated files"
)
@click.option(
    "--config", type=click.Path(exists=True), default=None, help="Configuration file path"
)
@click.option("--validate-prompts", is_flag=True, help="Validate all prompt templates and exit")
@click.option("--list-templates", is_flag=True, help="List available prompt templates and exit")
@click.option("--verbose", "-v", is_flag=True, default=None, help="Enable verbose output")
@click.option("--debug", is_flag=True, default=None, help="Enable debug mode with detailed logging")
@click.option(
    "--performance",
    is_flag=True,
    default=None,
    help="Show detailed performance metrics (HP mode only)",
)
@click.option(
    "--max-concurrent", type=int, default=None, help="Maximum concurrent requirements (HP mode)"
)
@click.option(
    "--num-ctx",
    type=int,
    default=None,
    help="Context window size (e.g., 2048, 4096)",
)
@click.option(
    "--clean-temp",
    is_flag=True,
    help="Clean up temporary extracted images after processing",
)
@click.version_option(version=__version__)
def main(
    input_path: str | None,
    hp: bool,
    training: bool,
    model: str,
    template: str | None,
    preset: str | None,
    output_dir: str | None,
    config: str | None,
    validate_prompts: bool,
    list_templates: bool,
    verbose: bool | None,
    debug: bool | None,
    performance: bool | None,
    max_concurrent: int | None,
    num_ctx: int | None,
    clean_temp: bool,
) -> None:
    """
    AI Test Case Generator - Modular Architecture

    Process REQIFZ files to generate contextual test cases using Ollama AI models.
    Built with clean, modular components for maintainability and extensibility.
    """

    # Handle utility modes
    if validate_prompts:
        show_banner("validate")
        _validate_templates()
        return

    if list_templates:
        show_banner("validate")
        _list_templates()
        return

    # Require input for processing modes
    if not input_path:
        console.print("[red]❌ Error: Input path required for processing modes[/red]")
        console.print("Use --validate-prompts or --list-templates for utility modes")
        sys.exit(1)

    # Handle training mode
    if training:
        show_banner("training")
        console.print("[yellow]⚠️  Training mode requires additional ML dependencies[/yellow]")
        console.print(
            "[yellow]Install: pip install torch transformers peft datasets wandb[/yellow]"
        )
        console.print("[blue]ℹ️  Training logic would be implemented here[/blue]")
        return

    # Initialize configuration
    base_config = ConfigManager()

    # Load CLI defaults and presets from config file
    # This must be done BEFORE accessing presets
    base_config.load_cli_config()

    # 1. Load Preset if specified (This merges preset values into base config)
    preset_keys: dict[str, set[str]] = {}
    if preset:
        base_config, preset_keys = _apply_preset(base_config, preset)
        if preset_keys:
            console.print(f"🔧 Applied preset: [cyan]{preset}[/cyan]")

    # 2. Apply CLI overrides (These invoke logic to create *effective* config)
    effective_config = base_config.apply_cli_overrides(
        # None when --model was not passed, so presets/config keep their model;
        # an explicit --model (even the default name) always wins. The boolean
        # flags are tri-state (None when omitted) for the same reason.
        model=model,
        template=template,
        max_concurrent=max_concurrent,
        num_ctx=num_ctx,
        verbose=verbose,
        debug=debug,
        performance=performance,
        config=config,
        preset_overrides=preset_keys,
    )

    # Initialize centralized application logger with effective config
    app_logger = get_app_logger(effective_config)
    app_logger.info(
        f"AI Test Case Generator v{__version__} starting",
        version=__version__,
        architecture=__architecture__,
    )

    if config:
        console.print(f"📝 Loading config from: {config}")
        app_logger.info("Loading custom configuration", config_file=config)

    if effective_config.cli.verbose:
        effective_config.show_effective_config()
        app_logger.info("Verbose mode enabled")

    # Determine processing mode from the effective config (--hp overrides)
    mode = _resolve_processing_mode(hp, effective_config)
    show_banner(mode)
    if mode == "hp":
        app_logger.info(
            "Starting high-performance processing mode", mode=mode, input_path=input_path
        )
        _run_hp_mode(input_path, output_dir, effective_config, clean_temp)
    else:
        app_logger.info("Starting standard processing mode", mode=mode, input_path=input_path)
        _run_standard_mode(input_path, output_dir, effective_config, clean_temp)


def _run_standard_mode(
    input_path: str, output_dir: str | None, config: ConfigManager, clean_temp: bool
) -> None:
    """Execute standard processing using modular components"""
    app_logger = get_app_logger()

    try:
        # Initialize standard processor with modular components
        processor = REQIFZFileProcessor(config)

        input_file = Path(input_path)
        output_directory = Path(output_dir) if output_dir else None

        # Extract configuration values from the effective config
        model = config.ollama.synthesizer_model
        template = config.cli.template

        app_logger.log_file_processing_start(str(input_file), model, "standard")

        console.print(f"🔍 Input: [cyan]{input_file.name}[/cyan]")
        console.print(f"🤖 Model: [cyan]{model}[/cyan]")
        console.print("🏗️  Architecture: [cyan]Modular Standard Processor[/cyan]")

        # Process single file or directory
        if input_file.is_file():
            result = processor.process_file(input_file, model, template, output_directory)
        else:
            results = processor.process_directory(input_file, model, template, output_directory)
            result = _aggregate_directory_results(results)

        # Log processing completion
        app_logger.log_file_processing_complete(
            str(input_file),
            result["success"],
            result.get("total_test_cases", 0),
            result.get("processing_time", 0.0),
            mode="standard",
        )

        exit_code = _resolve_exit_code(result)

        # Display results
        if result["success"]:
            if exit_code == 0:
                console.print("\n🎉 [green]Processing completed successfully![/green]")
            else:
                console.print("\n⚠️  [yellow]Processing completed partially[/yellow]")
                _print_partial_details(result)
            if "total_test_cases" in result:
                console.print(f"📊 Generated: {result['total_test_cases']} test cases")
                console.print(f"⏱️  Time: {result['processing_time']:.2f}s")
        else:
            error_msg = result.get("error", "Unknown error")
            app_logger.error(f"Processing failed: {error_msg}", mode="standard")
            console.print(f"\n❌ [red]Processing failed: {error_msg}[/red]")
            _print_partial_details(result)
            sys.exit(exit_code)

        # Clean up temporary extracted images if requested
        if clean_temp:
            extractor = RequirementImageExtractor(
                output_dir=Path(config.image_extraction.output_dir),
                save_images=False,
                validate_images=False,
            )
            count = extractor.cleanup_extracted_images()
            if count > 0:
                console.print(f"🧹 Cleaned up {count} temporary image(s)")
                app_logger.info(f"Cleaned up {count} temporary images", mode="standard")

        if exit_code != 0:
            sys.exit(exit_code)

    except Exception as e:
        app_logger.error(f"Error in standard mode: {e}", mode="standard", exception=str(e))
        console.print(f"[red]💥 Error in standard mode: {e}[/red]")
        sys.exit(1)

    finally:
        # Release the HTTP connection pool held by the sync Ollama client
        if "processor" in locals():
            processor.ollama_client.close()


def _run_hp_mode(
    input_path: str, output_dir: str | None, config: ConfigManager, clean_temp: bool
) -> None:
    """Execute high-performance processing using async modular components"""
    app_logger = get_app_logger()

    try:
        # Extract configuration values from the effective config
        model = config.ollama.synthesizer_model
        template = config.cli.template
        max_concurrent = config.ollama.concurrent_requests
        show_performance = config.cli.performance

        # Initialize HP processor with modular components
        processor = HighPerformanceREQIFZFileProcessor(config, max_concurrent)

        input_file = Path(input_path)
        output_directory = Path(output_dir) if output_dir else None

        app_logger.log_file_processing_start(str(input_file), model, "high-performance")

        console.print(f"🚀 Input: [cyan]{input_file.name}[/cyan]")
        console.print(f"🤖 Model: [cyan]{model}[/cyan]")
        console.print(f"⚡ Concurrency: [cyan]{processor.max_concurrent_requirements}[/cyan]")
        console.print("🏗️  Architecture: [cyan]Modular HP Async Processor[/cyan]")

        # Run async processing
        if input_file.is_file():
            result = asyncio.run(
                processor.process_file(input_file, model, template, output_directory)
            )
        else:
            results = asyncio.run(
                processor.process_directory(input_file, model, template, output_directory)
            )
            result = _aggregate_directory_results(results)

        # Log processing completion with performance metrics
        performance_data = {}
        if "performance_metrics" in result:
            performance_data = result["performance_metrics"]

        app_logger.log_file_processing_complete(
            str(input_file),
            result["success"],
            result.get("total_test_cases", 0),
            result.get("processing_time", 0.0),
            mode="high-performance",
            **performance_data,
        )

        exit_code = _resolve_exit_code(result)

        # Display results with performance metrics
        if result["success"]:
            if exit_code == 0:
                console.print("\n🏆 [green]High-Performance Processing Complete![/green]")
            else:
                console.print(
                    "\n⚠️  [yellow]High-Performance Processing completed partially[/yellow]"
                )
                _print_partial_details(result)
            if "total_test_cases" in result:
                console.print(f"📊 Generated: {result['total_test_cases']} test cases")
                console.print(f"⏱️  Time: {result['processing_time']:.2f}s")

                if "performance_metrics" in result and show_performance:
                    metrics = result["performance_metrics"]
                    console.print(
                        f"⚡ Rate: {metrics.get('test_cases_per_second', 0):.1f} test cases/sec"
                    )
                    console.print(f"🎯 Efficiency: {metrics.get('parallel_efficiency', 0):.1f}%")
                    console.print(f"🤖 AI Calls: {metrics.get('ai_calls_made', 0)}")
        else:
            error_msg = result.get("error", "Unknown error")
            app_logger.error(f"HP Processing failed: {error_msg}", mode="high-performance")
            console.print(f"\n❌ [red]HP Processing failed: {error_msg}[/red]")
            _print_partial_details(result)
            sys.exit(exit_code)

        # Clean up temporary extracted images if requested
        if clean_temp:
            extractor = RequirementImageExtractor(
                output_dir=Path(config.image_extraction.output_dir),
                save_images=False,
                validate_images=False,
            )
            count = extractor.cleanup_extracted_images()
            if count > 0:
                console.print(f"🧹 Cleaned up {count} temporary image(s)")
                app_logger.info(f"Cleaned up {count} temporary images", mode="high-performance")

        if exit_code != 0:
            sys.exit(exit_code)

    except Exception as e:
        app_logger.error(f"Error in HP mode: {e}", mode="high-performance", exception=str(e))
        console.print(f"[red]💥 Error in HP mode: {e}[/red]")
        sys.exit(1)


def _validate_templates() -> None:
    """Validate prompt templates using modular components"""
    try:
        manager = YAMLPromptManager()
        console.print("🔍 Validating Prompt Templates...")

        template_count = len(manager.test_prompts)
        console.print(f"📋 Found {template_count} template(s)")

        schema_failures = 0
        for template_name in manager.test_prompts:
            try:
                # Render with placeholder values for required variables —
                # validation checks the template itself, not caller input
                template_info = manager.get_template_info(template_name)
                vars_spec = template_info.get("variables", {})
                required = (
                    vars_spec if isinstance(vars_spec, list) else vars_spec.get("required", [])
                )
                placeholder_vars = {var: f"<{var}>" for var in required}

                template = manager.get_test_prompt(template_name, **placeholder_vars)
                if not (template and isinstance(template, str) and len(template.strip()) > 0):
                    console.print(f"❌ {template_name} - Invalid or empty template")
                    schema_failures += 1
                    continue

                # Semantic check: the template must instruct the canonical
                # output schema and not any retired field directives.
                issues = template_schema_issues(template)
                if issues:
                    schema_failures += 1
                    console.print(f"❌ {template_name} - schema mismatch:")
                    for issue in issues:
                        console.print(f"     - {issue}")
                else:
                    console.print(f"✅ {template_name}")
            except Exception as e:
                console.print(f"❌ {template_name} - Error: {e}")
                schema_failures += 1

        if schema_failures:
            console.print(
                f"\n[red]❌ Template validation failed: {schema_failures} template(s) "
                f"with issues[/red]"
            )
            sys.exit(1)

        console.print("\n✅ Template validation complete!")

    except Exception as e:
        console.print(f"[red]❌ Validation failed: {e}[/red]")
        sys.exit(1)


def _list_templates() -> None:
    """List available templates using modular components"""
    try:
        manager = YAMLPromptManager()
        console.print("📋 Available Prompt Templates:")

        if not manager.test_prompts:
            console.print("  [yellow]No templates found[/yellow]")
            return

        for template_name, template_data in manager.test_prompts.items():
            description = template_data.get("description", "No description available")
            console.print(f"  • [cyan]{template_name}[/cyan]")
            console.print(f"    {description}")

        console.print(f"\n✅ Total: {len(manager.test_prompts)} template(s)")

    except Exception as e:
        console.print(f"[red]❌ Failed to list templates: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        app_logger = get_app_logger()
        app_logger.warning("Process interrupted by user", event_type="user_interrupt")
        app_logger.log_application_metrics()
        shutdown_app_logger()
        console.print("\n⏹️  Process interrupted by user.")
        sys.exit(0)
    except Exception as e:
        app_logger = get_app_logger()
        app_logger.critical(f"Unexpected error: {e}", exception=str(e), event_type="critical_error")
        app_logger.log_application_metrics()
        shutdown_app_logger()
        console.print(f"[red]💥 Unexpected error: {e}[/red]")
        sys.exit(1)
    finally:
        # Ensure proper cleanup of logger
        try:
            app_logger = get_app_logger()
            app_logger.log_application_metrics()
            shutdown_app_logger()
        except Exception:
            pass  # Silently handle cleanup errors
