"""
Interactive RAFT Annotation Interface

This module provides an interactive interface for human experts to annotate
context relevance in RAFT training examples.
"""

from __future__ import annotations
import json
try:
    import readline
except ImportError:
    # Readline not available on Windows
    pass
from pathlib import Path
from typing import Any, List, Dict, Set
from logging import Logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

type RAFTExample = dict[str, Any]


class RAFTAnnotator:
    """Interactive annotation interface for RAFT training examples"""

    def __init__(self, collected_dir: str | Path = "training_data/collected",
                 validated_dir: str | Path = "training_data/validated",
                 rejected_dir: str | Path = "training_data/rejected",
                 logger: Logger | None = None):
        """
        Initialize RAFT annotator.

        Args:
            collected_dir: Directory with collected examples
            validated_dir: Directory for validated examples
            rejected_dir: Directory for rejected examples
            logger: Optional logger
        """
        self.collected_dir = Path(collected_dir)
        self.validated_dir = Path(validated_dir)
        self.rejected_dir = Path(rejected_dir)
        self.logger = logger
        self.console = Console()

        # Create directories if they don't exist
        self.validated_dir.mkdir(parents=True, exist_ok=True)
        self.rejected_dir.mkdir(parents=True, exist_ok=True)

    def annotate_examples(self, batch_size: int = 5, resume_annotation: bool = True):
        """
        Start interactive annotation session.

        Args:
            batch_size: Number of examples to annotate per session
            resume_annotation: Allow resuming incomplete annotations
        """
        self.console.print(Panel.fit(
            "[bold blue]🚀 RAFT Interactive Annotation[/bold blue]\n"
            "[yellow]Rate context relevance for AI training data[/yellow]\n"
            "[dim]Use this tool to create high-quality training examples[/dim]",
            title="Welcome"
        ))

        unannotated_files = self._get_unannotated_files()

        if not unannotated_files:
            self.console.print("[green]✅ No unannotated examples found![/green]")
            return

        self.console.print(f"[blue]Found {len(unannotated_files)} unannotated examples[/blue]")

        annotated_count = 0
        skipped_count = 0

        # Process examples
        for example_path in unannotated_files[:batch_size]:
            try:
                # Load example
                with open(example_path, encoding="utf-8") as f:
                    example = json.load(f)

                # Skip if already annotated
                if resume_annotation and self._is_annotated(example):
                    continue

                # Annotate example
                if self._annotate_single_example(example, example_path):
                    annotated_count += 1
                else:
                    skipped_count += 1

                # Progress update
                total_processed = annotated_count + skipped_count
                self.console.print(f"[blue]Progress: {total_processed}/{min(batch_size, len(unannotated_files))}[/blue]")

            except Exception as e:
                self.console.print(f"[red]Error processing {example_path.name}: {e}[/red]")
                if self.logger:
                    self.logger.error(f"Annotation error for {example_path}: {e}")

        # Summary
        self.console.print(Panel.fit(
            f"[green]✅ Annotation session completed![/green]\n"
            f"[blue]Annotated: {annotated_count}[/blue]\n"
            f"[yellow]Skipped: {skipped_count}[/yellow]\n"
            f"[cyan]Quality focus areas identified[/cyan]",
            title="Session Summary"
        ))

    def _annotate_single_example(self, example: RAFTExample, file_path: Path) -> bool:
        """
        Annotate a single RAFT example with user interaction.

        Returns:
            True if annotation completed, False if skipped
        """
        req_id = example['requirement_id']
        req_text = example['requirement_text']

        # Display requirement
        self.console.print(Panel.fit(
            f"[bold white]{req_text}[/bold white]",
            title=f"📋 Requirement {req_id}",
            border_style="blue"
        ))

        # Display retrieved context
        ctx = example["retrieved_context"]
        context_items = self._build_context_items_list(ctx)

        # Interactive annotation
        while True:
            try:
                # Show context table
                self._display_context_table(context_items)

                # User input: annotate relevant context
                oracle_ids = self._get_user_oracle_selection(context_items)

                if oracle_ids is None:  # Skip example
                    self._move_to_rejected(file_path)
                    return False

                # Get quality rating and notes
                quality_rating, notes = self._get_quality_rating_and_notes()

                # Calculate distractor context (not in oracle)
                all_context_ids = {item['id'] for item in context_items}
                distractor_ids = list(all_context_ids - set(oracle_ids))

                # Update annotation
                example['context_annotation'] = {
                    'oracle_context': oracle_ids,
                    'distractor_context': distractor_ids,
                    'quality_rating': quality_rating,
                    'annotation_notes': notes,
                    'annotated_timestamp': json.dumps(None)  # Will be filled on save
                }

                example['validation_status'] = 'validated'
                example['annotation_timestamp'] = json.dumps(None)

                # Save validated example
                self._save_validated_example(example, file_path)
                return True

            except KeyboardInterrupt:
                if Confirm.ask("[yellow]Save partial annotation?[/yellow]"):
                    self._save_validated_example(example, file_path)
                    return True
                else:
                    return False
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                continue

    def _build_context_items_list(self, ctx: dict) -> list[dict[str, Any]]:
        """Build numbered list of context items for annotation"""
        items = []

        # Heading
        if ctx.get('heading', {}).get('text'):
            items.append({
                'id': 'HEADING',
                'type': 'heading',
                'text': ctx['heading']['text'],
                'display_text': f"[bold cyan]Header:[/bold cyan] {ctx['heading']['text']}"
            })

        # Info artifacts
        for info in ctx.get('info_artifacts', []):
            items.append({
                'id': info['id'],
                'type': 'info',
                'text': info['text'],
                'display_text': f"[green]Info {info['id']}:[/green] {info['text'][:100]}..."
            })

        # Interfaces
        for iface in ctx.get('interfaces', []):
            items.append({
                'id': iface['id'],
                'type': 'interface',
                'text': iface['text'],
                'display_text': f"[magenta]Interface {iface['id']}:[/magenta] {iface['text'][:100]}..."
            })

        return items

    def _display_context_table(self, context_items: list[dict[str, Any]]):
        """Display context items in a table for user review"""
        table = Table(title="📚 Retrieved Context Items")
        table.add_column("#", style="dim", width=3)
        table.add_column("Type", style="cyan", width=10)
        table.add_column("Context ID", style="yellow", width=10)
        table.add_column("Content", style="white")

        for i, item in enumerate(context_items, 1):
            # Truncate long content for display
            content = item['text']
            if len(content) > 150:
                content = content[:147] + "..."

            table.add_row(
                str(i),
                item['type'].title(),
                item['id'],
                content
            )

        self.console.print(table)

    def _get_user_oracle_selection(self, context_items: list[dict[str, Any]]) -> list[str] | None:
        """Get user's selection of relevant (oracle) context items"""
        if not context_items:
            return []

        while True:
            # Instructions
            self.console.print(Panel.fit(
                "[bold green]🎯 Annotation Instructions:[/bold green]\n"
                "• Enter context item numbers (comma-separated) that are RELEVANT for generating test cases\n"
                "• Example: 1,3,5 (means items 1, 3, and 5 are relevant)\n"
                "• Enter 'all' for all items relevant\n"
                "• Enter 'none' for no items relevant\n"
                "• Enter 'skip' to skip this example\n"
                "• Enter 'help' for more details",
                border_style="green"
            ))

            response = Prompt.ask("[bold cyan]Relevant context item numbers[/bold cyan]").strip().lower()

            if response == 'skip':
                return None
            elif response == 'help':
                self._show_annotation_help()
                continue
            elif response == 'all':
                return [item['id'] for item in context_items]
            elif response == 'none':
                return []
            else:
                # Parse number selections
                try:
                    indices = []
                    for part in response.split(','):
                        part = part.strip()
                        if part:
                            idx = int(part) - 1  # Convert to 0-based
                            if 0 <= idx < len(context_items):
                                indices.append(idx)
                            else:
                                raise ValueError(f"Invalid item number: {idx + 1}")

                    selected_ids = [context_items[i]['id'] for i in indices]

                    # Confirm selection
                    selected_items = [context_items[i] for i in indices]
                    self.console.print("[green]Selected relevant context:[/green]")
                    for item in selected_items:
                        self.console.print(f"  • {item['id']}: {item['text'][:50]}...")

                    # Confirm with user
                    if not Confirm.ask("[yellow]Confirm this selection?[/yellow]", default=True):
                        continue

                    return selected_ids

                except ValueError as e:
                    self.console.print(f"[red]Invalid input: {e}[/red]")
                    continue

    def _get_quality_rating_and_notes(self) -> tuple[int, str]:
        """Get quality rating and annotation notes from user"""
        # Quality rating
        while True:
            try:
                rating = IntPrompt.ask("[bold magenta]Quality rating (1-5, where 5 is excellent)[/bold magenta]",
                                     choices=[1, 2, 3, 4, 5])
                break
            except ValueError:
                self.console.print("[red]Please enter a number between 1-5[/red]")
                continue

        # Optional notes
        notes = Prompt.ask("[bold cyan]Optional notes about this annotation[/bold cyan]", default="")

        return rating, notes

    def _show_annotation_help(self):
        """Display detailed annotation help"""
        help_text = """
        [bold cyan]RAFT Annotation Help[/bold cyan]

        The goal is to teach AI models which context is relevant for test case generation.

        [bold green]Oracle Context:[/bold green] Information that is clearly relevant and should be used for generating test cases.

        [bold red]Distractor Context:[/bold red] Information that might seem useful but is not relevant for this specific requirement.

        [bold yellow]Examples:[/bold yellow]
        • Heading: Often relevant for domain context
        • Interface definitions: Relevant if requirement involves that interface
        • General information: May be distractor if not specific to requirement

        [bold blue]Quality Rating Scale:[/bold blue]
        • 5: Excellent - perfect relevant/irrelevant separation
        • 4: Good - mostly correct separations
        • 3: Acceptable - some unclear distinctions
        • 2: Poor - many questionable separations
        • 1: Very Poor - mostly incorrect separations
        """
        self.console.print(Panel(help_text, border_style="blue"))

    def _save_validated_example(self, example: RAFTExample, original_path: Path):
        """Save validated example to validated directory"""
        import datetime
        from pathlib import Path

        # Update timestamp
        example['annotation_timestamp'] = datetime.datetime.now().isoformat()

        # Create new filename
        stem = original_path.stem
        validated_path = self.validated_dir / f"{stem}_annotated.json"

        # Save validated example
        with open(validated_path, 'w', encoding='utf-8') as f:
            json.dump(example, f, indent=2, ensure_ascii=False)

        # Optionally remove from collected (or move to processed subdir)
        # For now, keep originals for audit trail

        self.console.print(f"✅ Saved validated example: {validated_path.name}")

    def _move_to_rejected(self, file_path: Path):
        """Move skipped example to rejected directory"""
        # Create rejected filename
        rejected_path = self.rejected_dir / file_path.name

        # Copy to rejected
        import shutil
        shutil.copy2(file_path, rejected_path)

    def _get_unannotated_files(self) -> list[Path]:
        """Get list of files that need annotation"""
        if not self.collected_dir.exists():
            return []

        # Get all JSON files in collected directory
        json_files = list(self.collected_dir.glob("raft_*.json"))

        unannotated = []
        for file_path in json_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)

                # Check if annotation is complete
                if not self._is_annotated(data):
                    unannotated.append(file_path)
            except Exception:
                # Skip corrupted files
                continue

        return sorted(unannotated, key=lambda p: p.stat().st_mtime)

    def _is_annotated(self, example: RAFTExample) -> bool:
        """Check if example has been properly annotated"""
        annotation = example.get('context_annotation', {})

        # Must have oracle context (can be empty list)
        if 'oracle_context' not in annotation:
            return False

        # Must have a quality rating
        if not annotation.get('quality_rating'):
            return False

        return True

    def get_annotation_stats(self) -> dict[str, int]:
        """Get annotation statistics"""
        total = len(list(self.collected_dir.glob("raft_*.json")))
        validated = len(list(self.validated_dir.glob("*_annotated.json")))
        rejected = len(list(self.rejected_dir.glob("raft_*.json")))

        return {
            'total_collected': total,
            'annotated_and_validated': validated,
            'rejected': rejected,
            'pending_annotation': total - validated - rejected
        }
