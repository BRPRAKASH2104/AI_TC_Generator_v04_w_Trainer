#!/usr/bin/env python3
"""
AI Test Case Generator - Truly Modular Implementation

This is the unified entry point that orchestrates the modular components:
- Core components (extractors, generators, formatters, clients, parsers) 
- Processors (standard and high-performance workflows)
- Clean separation of concerns and maintainable architecture

Modern Python 3.13.7+ with full expert review recommendations implemented.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

# Add src to path for imports (only when running directly, not when installed as package)
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import processors (high-level orchestrators)
from processors.hp_processor import HighPerformanceREQIFZFileProcessor
from processors.standard_processor import REQIFZFileProcessor

# Import utilities
from config import ConfigManager
from yaml_prompt_manager import YAMLPromptManager
from app_logger import get_app_logger, shutdown_app_logger

# Version and metadata
__version__ = "1.4.0"
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
        f"[dim]Modular Architecture • Python 3.13.7+[/dim]",
        border_style="cyan"
    )
    console.print(panel)


@click.command()
@click.argument('input_path', required=False, type=click.Path(exists=True))
@click.option('--hp', '--high-performance', is_flag=True,
              help='Enable high-performance mode with async processing')
@click.option('--training', is_flag=True,
              help='Enable training mode (requires ML dependencies)')
@click.option('--model', default="llama3.1:8b",
              help='AI model to use for generation')
@click.option('--template', type=str, default=None,
              help='Specific prompt template to use')
@click.option('--output-dir', type=click.Path(), default=None,
              help='Output directory for generated files')
@click.option('--config', type=click.Path(exists=True), default=None,
              help='Configuration file path')
@click.option('--validate-prompts', is_flag=True,
              help='Validate all prompt templates and exit')
@click.option('--list-templates', is_flag=True,
              help='List available prompt templates and exit')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
@click.option('--debug', is_flag=True,
              help='Enable debug mode with detailed logging')
@click.option('--performance', is_flag=True,
              help='Show detailed performance metrics (HP mode only)')
@click.option('--max-concurrent', type=int, default=None,
              help='Maximum concurrent requirements (HP mode)')
@click.version_option(version=__version__)
def main(
    input_path: str | None,
    hp: bool,
    training: bool,
    model: str,
    template: str | None,
    output_dir: str | None,
    config: str | None,
    validate_prompts: bool,
    list_templates: bool,
    verbose: bool,
    debug: bool,
    performance: bool,
    max_concurrent: int | None,
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
        console.print("[yellow]Install: pip install torch transformers peft datasets wandb[/yellow]")
        console.print("[blue]ℹ️  Training logic would be implemented here[/blue]")
        return
    
    # Initialize configuration with CLI overrides applied
    base_config = ConfigManager()

    # Apply CLI overrides to create effective configuration
    effective_config = base_config.apply_cli_overrides(
        model=model,
        template=template,
        max_concurrent=max_concurrent,
        verbose=verbose,
        debug=debug,
        performance=performance,
        config=config
    )

    # Initialize centralized application logger with effective config
    app_logger = get_app_logger(effective_config)
    app_logger.info(f"AI Test Case Generator v{__version__} starting",
                   version=__version__, architecture=__architecture__)

    if config:
        console.print(f"📝 Loading config from: {config}")
        app_logger.info(f"Loading custom configuration", config_file=config)

    if verbose:
        effective_config.show_effective_config()
        app_logger.info("Verbose mode enabled")

    # Determine processing mode and show banner
    if hp:
        mode = "hp"
        show_banner(mode)
        app_logger.info("Starting high-performance processing mode",
                       mode=mode, input_path=input_path)
        _run_hp_mode(input_path, output_dir, effective_config)
    else:
        mode = "standard"
        show_banner(mode)
        app_logger.info("Starting standard processing mode",
                       mode=mode, input_path=input_path)
        _run_standard_mode(input_path, output_dir, effective_config)


def _run_standard_mode(
    input_path: str,
    output_dir: str | None,
    config: ConfigManager
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
            result = {"success": any(r["success"] for r in results)}

        # Log processing completion
        app_logger.log_file_processing_complete(
            str(input_file),
            result["success"],
            result.get("total_test_cases", 0),
            result.get("processing_time", 0.0),
            mode="standard"
        )

        # Display results
        if result["success"]:
            console.print("\n🎉 [green]Processing completed successfully![/green]")
            if "total_test_cases" in result:
                console.print(f"📊 Generated: {result['total_test_cases']} test cases")
                console.print(f"⏱️  Time: {result['processing_time']:.2f}s")
        else:
            error_msg = result.get('error', 'Unknown error')
            app_logger.error(f"Processing failed: {error_msg}", mode="standard")
            console.print(f"\n❌ [red]Processing failed: {error_msg}[/red]")
            sys.exit(1)

    except Exception as e:
        app_logger.error(f"Error in standard mode: {e}", mode="standard", exception=str(e))
        console.print(f"[red]💥 Error in standard mode: {e}[/red]")
        sys.exit(1)


def _run_hp_mode(
    input_path: str,
    output_dir: str | None,
    config: ConfigManager
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
            result = {"success": any(r["success"] for r in results)}

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
            max_concurrent=max_concurrent,
            **performance_data
        )

        # Display results with performance metrics
        if result["success"]:
            console.print("\n🏆 [green]High-Performance Processing Complete![/green]")
            if "total_test_cases" in result:
                console.print(f"📊 Generated: {result['total_test_cases']} test cases")
                console.print(f"⏱️  Time: {result['processing_time']:.2f}s")

                if "performance_metrics" in result and show_performance:
                    metrics = result["performance_metrics"]
                    console.print(f"⚡ Rate: {metrics.get('test_cases_per_second', 0):.1f} test cases/sec")
                    console.print(f"🎯 Efficiency: {metrics.get('parallel_efficiency', 0):.1f}%")
                    console.print(f"🤖 AI Calls: {metrics.get('ai_calls_made', 0)}")
        else:
            error_msg = result.get('error', 'Unknown error')
            app_logger.error(f"HP Processing failed: {error_msg}", mode="high-performance")
            console.print(f"\n❌ [red]HP Processing failed: {error_msg}[/red]")
            sys.exit(1)

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
        
        for template_name in manager.test_prompts:
            try:
                template = manager.get_test_prompt(template_name)
                if template and template.get("prompt"):
                    console.print(f"✅ {template_name}")
                else:
                    console.print(f"❌ {template_name} - Invalid structure")
            except Exception as e:
                console.print(f"❌ {template_name} - Error: {e}")
        
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