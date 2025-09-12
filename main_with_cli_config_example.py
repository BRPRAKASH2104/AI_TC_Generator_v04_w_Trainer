#!/usr/bin/env python3
"""
Example: main.py with CLI Configuration Support
File: main_with_cli_config_example.py

This shows how main.py would be modified to support external CLI configuration
with presets, environment variables, and configuration hierarchy.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import processors (high-level orchestrators)
from processors.hp_processor import HighPerformanceREQIFZFileProcessor
from processors.standard_processor import REQIFZFileProcessor

# Import utilities
from config import ConfigManager
from yaml_prompt_manager import YAMLPromptManager

# Version and metadata
__version__ = "1.5.0"  # Updated for CLI config support
__architecture__ = "Modular with CLI Configuration"

console = Console()


def show_banner(mode: str = "standard", config_source: str = "defaults") -> None:
    """Display application banner with mode and configuration information"""
    mode_info = {
        "standard": "Standard Processing Mode",
        "hp": "High-Performance Mode (4-8x faster)", 
        "training": "Training-Enhanced Mode",
        "validate": "Template Validation Mode",
    }
    
    title = f"🚀 AI Test Case Generator v{__version__}"
    subtitle = mode_info.get(mode, "Standard Processing Mode")
    config_info = f"Configuration: {config_source}"
    
    panel = Panel.fit(
        f"[bold cyan]{title}[/bold cyan]\n"
        f"[dim]{subtitle}[/dim]\n"
        f"[dim]{config_info}[/dim]\n"
        f"[dim]Modular Architecture • Python 3.13.7+[/dim]",
        border_style="cyan"
    )
    console.print(panel)


@click.command()
@click.argument('input_path', required=False, type=click.Path(exists=True))
# Configuration options
@click.option('--preset', type=str, default=None,
              help='Use named configuration preset (development, production, testing, turbo, accurate)')
@click.option('--env', type=str, default=None,
              help='Use environment-specific configuration (local, ci_cd, staging, production)')
@click.option('--config-file', type=click.Path(exists=True), default=None,
              help='Custom CLI configuration file path')
@click.option('--show-config', is_flag=True,
              help='Show effective configuration and exit')
# Processing mode options (can override config file/preset settings)
@click.option('--hp', '--high-performance', is_flag=True,
              help='Enable high-performance mode with async processing')
@click.option('--training', is_flag=True,
              help='Enable training mode (requires ML dependencies)')
@click.option('--model', type=str, default=None,
              help='AI model to use for generation')
@click.option('--template', type=str, default=None,
              help='Specific prompt template to use')
@click.option('--output-dir', type=click.Path(), default=None,
              help='Output directory for generated files')
@click.option('--max-concurrent', type=int, default=None,
              help='Maximum concurrent requirements (HP mode)')
# Utility operations
@click.option('--validate-prompts', is_flag=True,
              help='Validate all prompt templates and exit')
@click.option('--list-templates', is_flag=True,
              help='List available prompt templates and exit')
@click.option('--list-presets', is_flag=True,
              help='List available configuration presets and exit')
@click.option('--list-environments', is_flag=True,
              help='List available environment configurations and exit')
# Output control options (can override config file/preset settings)
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
@click.option('--debug', is_flag=True,
              help='Enable debug mode with detailed logging')
@click.option('--performance', is_flag=True,
              help='Show detailed performance metrics (HP mode only)')
@click.version_option(version=__version__)
def main(
    input_path: str | None,
    preset: str | None,
    env: str | None,
    config_file: str | None,
    show_config: bool,
    hp: bool,
    training: bool,
    model: str | None,
    template: str | None,
    output_dir: str | None,
    max_concurrent: int | None,
    validate_prompts: bool,
    list_templates: bool,
    list_presets: bool,
    list_environments: bool,
    verbose: bool,
    debug: bool,
    performance: bool,
) -> None:
    """
    AI Test Case Generator - Modular Architecture with CLI Configuration
    
    Process REQIFZ files to generate contextual test cases using Ollama AI models.
    Built with clean, modular components and flexible configuration management.
    """
    
    # Initialize configuration manager
    config_manager = ConfigManager()
    config_manager.load_cli_config(config_file)
    config_source = "config file" if config_file or Path("config/cli_config.yaml").exists() else "defaults"
    
    # Handle configuration display
    if show_config:
        show_banner("validate", config_source)
        config_manager.show_effective_config(
            mode="hp" if hp else ("training" if training else None),
            model=model,
            template=template,
            max_concurrent=max_concurrent,
            verbose=verbose,
            debug=debug,
            performance=performance
        )
        return
    
    # Handle preset and environment listing
    if list_presets:
        show_banner("validate", config_source)
        console.print("📋 Available Configuration Presets:")
        for preset_name, preset_config in config_manager.cli.presets.items():
            console.print(f"  • [cyan]{preset_name}[/cyan]: {preset_config}")
        return
    
    if list_environments:
        show_banner("validate", config_source)
        console.print("🌍 Available Environment Configurations:")
        for env_name, env_config in config_manager.cli.environments.items():
            console.print(f"  • [cyan]{env_name}[/cyan]: {env_config}")
        return
    
    # Apply configuration hierarchy: preset -> environment -> CLI args
    effective_config = {}
    
    # Start with CLI defaults from config file
    effective_config.update(config_manager.apply_cli_overrides())
    
    # Apply preset configuration
    if preset:
        preset_config = config_manager.get_preset_config(preset)
        if preset_config:
            effective_config.update(preset_config)
            config_source = f"preset '{preset}'"
        else:
            console.print(f"[red]❌ Unknown preset: {preset}[/red]")
            return
    
    # Apply environment configuration
    if env:
        env_config = config_manager.get_environment_config(env)
        if env_config:
            effective_config.update(env_config)
            config_source = f"environment '{env}'"
        else:
            console.print(f"[red]❌ Unknown environment: {env}[/red]")
            return
    
    # Apply CLI argument overrides (highest priority)
    cli_overrides = {}
    if hp:
        cli_overrides["mode"] = "hp"
    if training:
        cli_overrides["mode"] = "training"
    if model:
        cli_overrides["model"] = model
    if template:
        cli_overrides["template"] = template
    if max_concurrent:
        cli_overrides["max_concurrent"] = max_concurrent
    if verbose:
        cli_overrides["verbose"] = True
    if debug:
        cli_overrides["debug"] = True
    if performance:
        cli_overrides["performance"] = True
    
    effective_config.update(cli_overrides)
    
    # Extract final configuration values
    final_mode = effective_config.get("mode", "standard")
    final_model = effective_config.get("model", "llama3.1:8b")
    final_template = effective_config.get("template")
    final_max_concurrent = effective_config.get("max_concurrent", 4)
    final_verbose = effective_config.get("verbose", False)
    final_debug = effective_config.get("debug", False)
    final_performance = effective_config.get("performance", False)
    
    # Handle utility modes
    if validate_prompts:
        show_banner("validate", config_source)
        _validate_templates()
        return
        
    if list_templates:
        show_banner("validate", config_source)
        _list_templates()
        return
    
    # Require input for processing modes
    if not input_path:
        console.print("[red]❌ Error: Input path required for processing modes[/red]")
        console.print("Use --validate-prompts, --list-templates, --list-presets, or --show-config for utility modes")
        sys.exit(1)
    
    # Handle training mode
    if final_mode == "training":
        show_banner("training", config_source)
        console.print("[yellow]⚠️  Training mode requires additional ML dependencies[/yellow]")
        console.print("[yellow]Install: pip install torch transformers peft datasets wandb[/yellow]")
        console.print("[blue]ℹ️  Training logic would be implemented here[/blue]")
        return
    
    # Show configuration summary
    if final_verbose or final_debug:
        console.print("\n🔧 Using Configuration:")
        console.print(f"  Source: {config_source}")
        console.print(f"  Mode: {final_mode}")
        console.print(f"  Model: {final_model}")
        console.print(f"  Template: {final_template or 'auto-select'}")
        console.print(f"  Max Concurrent: {final_max_concurrent}")
        console.print(f"  Verbose: {final_verbose}")
        console.print(f"  Debug: {final_debug}")
        console.print(f"  Performance: {final_performance}")
    
    # Determine processing mode and show banner
    if final_mode == "hp":
        show_banner("hp", config_source)
        _run_hp_mode(input_path, final_model, final_template, output_dir, config_manager, 
                     final_performance, final_max_concurrent)
    else:
        show_banner("standard", config_source)
        _run_standard_mode(input_path, final_model, final_template, output_dir, config_manager)


def _run_standard_mode(
    input_path: str,
    model: str,
    template: str | None,
    output_dir: str | None,
    config: ConfigManager
) -> None:
    """Execute standard processing using modular components"""
    try:
        processor = REQIFZFileProcessor(config)
        
        if not processor.validate_environment():
            console.print("[red]❌ Environment validation failed[/red]")
            sys.exit(1)
        
        input_file = Path(input_path)
        output_directory = Path(output_dir) if output_dir else None
        
        console.print(f"🔍 Input: [cyan]{input_file.name}[/cyan]")
        console.print(f"🤖 Model: [cyan]{model}[/cyan]")
        console.print(f"🏗️  Architecture: [cyan]Modular Standard Processor[/cyan]")
        
        if input_file.is_file():
            result = processor.process_file(input_file, model, template, output_directory)
        else:
            results = processor.process_directory(input_file, model, template, output_directory)
            result = {"success": any(r["success"] for r in results)}
        
        if result["success"]:
            console.print("\n🎉 [green]Processing completed successfully![/green]")
            if "total_test_cases" in result:
                console.print(f"📊 Generated: {result['total_test_cases']} test cases")
                console.print(f"⏱️  Time: {result['processing_time']:.2f}s")
        else:
            console.print(f"\n❌ [red]Processing failed: {result.get('error', 'Unknown error')}[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]💥 Error in standard mode: {e}[/red]")
        sys.exit(1)


def _run_hp_mode(
    input_path: str,
    model: str,
    template: str | None,
    output_dir: str | None,
    config: ConfigManager,
    show_performance: bool,
    max_concurrent: int | None
) -> None:
    """Execute high-performance processing using async modular components"""
    try:
        processor = HighPerformanceREQIFZFileProcessor(config, max_concurrent)
        
        input_file = Path(input_path)
        output_directory = Path(output_dir) if output_dir else None
        
        console.print(f"🚀 Input: [cyan]{input_file.name}[/cyan]")
        console.print(f"🤖 Model: [cyan]{model}[/cyan]")
        console.print(f"⚡ Concurrency: [cyan]{processor.max_concurrent_requirements}[/cyan]")
        console.print(f"🏗️  Architecture: [cyan]Modular HP Async Processor[/cyan]")
        
        if input_file.is_file():
            result = asyncio.run(
                processor.process_file(input_file, model, template, output_directory)
            )
        else:
            results = asyncio.run(
                processor.process_directory(input_file, model, template, output_directory)
            )
            result = {"success": any(r["success"] for r in results)}
        
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
            console.print(f"\n❌ [red]HP Processing failed: {result.get('error', 'Unknown error')}[/red]")
            sys.exit(1)

    except Exception as e:
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
        console.print("\n⏹️  Process interrupted by user.")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]💥 Unexpected error: {e}[/red]")
        sys.exit(1)