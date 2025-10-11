"""
Progressive RAFT Training with Curriculum Learning

This module implements progressive training strategies that gradually increase
complexity and difficulty to improve model learning effectiveness.
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from logging import Logger
from pathlib import Path
from typing import Any

from .quality_scorer import QualityScorer

type RAFTExample = dict[str, Any]
type TrainingPhase = dict[str, Any]


class CurriculumPhase(Enum):
    """Progressive training curriculum phases"""

    FOUNDATION = "foundation"  # Basic requirements, simple context
    INTERMEDIATE = "intermediate"  # Complex requirements, mixed context
    ADVANCED = "advanced"  # Edge cases, conflicting context, domain expertise


@dataclass
class TrainingProgress:
    """Tracks training curriculum progress"""

    current_phase: CurriculumPhase = CurriculumPhase.FOUNDATION
    phase_completed_examples: int = 0
    total_trained_examples: int = 0
    phase_quality_threshold: float = 0.7
    last_evaluation_score: float = 0.0
    graduated_phases: list[CurriculumPhase] = field(default_factory=list)
    phase_start_time: float | None = None
    training_history: list[dict] = field(default_factory=list)


@dataclass
class CurriculumStage:
    """Defines requirements for a curriculum stage"""

    name: str
    min_examples: int
    min_quality_score: float
    requirement_complexity_range: tuple[float, float]
    context_diversity_min: float
    allowed_context_types: list[str]
    difficulty_features: list[str]


class ProgressiveRAFTTrainer:
    """
    Progressive RAFT training with curriculum learning.

    This trainer implements staged learning where model progresses from simple
    to complex examples, improving learning effectiveness and generalization.
    """

    def __init__(
        self,
        validated_dir: str | Path = "training_data/validated",
        output_dir: str | Path = "training_data/models",
        logger: Logger | None = None,
    ):
        """
        Initialize progressive trainer.

        Args:
            validated_dir: Directory with validated RAFT examples
            output_dir: Directory for trained models
            logger: Optional logger
        """
        self.validated_dir = Path(validated_dir)
        self.output_dir = Path(output_dir)
        self.logger = logger
        self.quality_scorer = QualityScorer(logger)

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize training progress
        self.progress = TrainingProgress()
        self._load_progress()

        # Define curriculum stages
        self.curriculum = self._define_curriculum()

    def _define_curriculum(self) -> dict[CurriculumPhase, CurriculumStage]:
        """Define progressive training curriculum"""
        return {
            CurriculumPhase.FOUNDATION: CurriculumStage(
                name="Foundation Training",
                min_examples=50,
                min_quality_score=0.6,
                requirement_complexity_range=(0.0, 0.4),
                context_diversity_min=0.3,
                allowed_context_types=["heading", "info"],
                difficulty_features=[],
            ),
            CurriculumPhase.INTERMEDIATE: CurriculumStage(
                name="Intermediate Training",
                min_examples=100,
                min_quality_score=0.7,
                requirement_complexity_range=(0.2, 0.7),
                context_diversity_min=0.5,
                allowed_context_types=["heading", "info", "interface"],
                difficulty_features=["multiple_context_types", "technical_terms"],
            ),
            CurriculumPhase.ADVANCED: CurriculumStage(
                name="Advanced Training",
                min_examples=150,
                min_quality_score=0.8,
                requirement_complexity_range=(0.5, 1.0),
                context_diversity_min=0.7,
                allowed_context_types=["heading", "info", "interface"],
                difficulty_features=[
                    "multiple_context_types",
                    "technical_terms",
                    "edge_cases",
                    "conflicting_context",
                    "domain_specific",
                ],
            ),
        }

    def start_curriculum_training(
        self, model_name: str = "progressive-raft-model"
    ) -> dict[str, Any]:
        """
        Start progressive curriculum training.

        Args:
            model_name: Name for the trained model

        Returns:
            Training results and progress summary
        """
        if self.logger:
            self.logger.info(f"🚀 Starting progressive RAFT training: {model_name}")

        training_results = {
            "model_name": model_name,
            "phases_completed": [],
            "total_examples_trained": 0,
            "final_performance_score": 0.0,
            "training_duration": 0.0,
            "issues_encountered": [],
        }

        start_time = time.time()

        try:
            # Load validated examples
            all_examples = self._load_validated_examples()

            if not all_examples:
                training_results["issues_encountered"].append("No validated examples found")
                return training_results

            # Organize examples by curriculum phase
            phase_examples = self._organize_examples_by_phase(all_examples)

            # Train each phase sequentially
            for phase in CurriculumPhase:
                if phase in self.progress.graduated_phases:
                    if self.logger:
                        self.logger.info(f"⏭️  Skipping graduated phase: {phase.value}")
                    continue

                self.progress.current_phase = phase
                self.progress.phase_start_time = time.time()

                if self.logger:
                    self.logger.info(f"📚 Training phase: {phase.value}")

                # Train this phase
                phase_result = self._train_phase(phase, phase_examples[phase], model_name)

                if phase_result["success"]:
                    training_results["phases_completed"].append(
                        {
                            "phase": phase.value,
                            "examples_trained": len(phase_examples[phase]),
                            "final_score": phase_result.get("phase_score", 0.0),
                        }
                    )

                    self.progress.graduated_phases.append(phase)
                else:
                    training_results["issues_encountered"].extend(phase_result.get("issues", []))
                    break  # Stop training if a phase fails

            training_results["total_examples_trained"] = sum(
                len(phase_examples[phase])
                for phase in CurriculumPhase
                if any(p["phase"] == phase.value for p in training_results["phases_completed"])
            )

            training_results["final_performance_score"] = self._evaluate_final_performance()
            training_results["training_duration"] = time.time() - start_time

            # Save progress
            self._save_progress()

        except Exception as e:
            training_results["issues_encountered"].append(f"Training failed: {str(e)}")
            if self.logger:
                self.logger.error(f"Progressive training failed: {e}")

        return training_results

    def _load_validated_examples(self) -> list[RAFTExample]:
        """Load all validated training examples"""
        validated_files = list(self.validated_dir.glob("*_annotated.json"))

        examples = []
        for file_path in validated_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    example = json.load(f)
                    examples.append(example)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to load {file_path}: {e}")

        if self.logger:
            self.logger.info(f"📚 Loaded {len(examples)} validated training examples")

        return examples

    def _organize_examples_by_phase(
        self, examples: list[RAFTExample]
    ) -> dict[CurriculumPhase, list[RAFTExample]]:
        """
        Organize examples into curriculum phases based on quality metrics.

        Returns:
            Dictionary mapping phases to their examples
        """
        phase_examples = {phase: [] for phase in CurriculumPhase}

        # Assess quality of each example
        assessments = []
        for example in examples:
            assessment = self.quality_scorer.assess_example_quality(example)
            assessments.append((example, assessment))

        # Sort by quality score (best examples first)
        assessments.sort(key=lambda x: x[1].metrics.overall_score, reverse=True)

        # Organize into phases with progressive difficulty
        for example, assessment in assessments:
            metrics = assessment.metrics

            # Determine appropriate phase based on metrics
            if metrics.requirement_complexity <= 0.4 and metrics.context_diversity >= 0.3:
                phase_examples[CurriculumPhase.FOUNDATION].append(example)
            elif metrics.requirement_complexity <= 0.7 and metrics.context_diversity >= 0.5:
                phase_examples[CurriculumPhase.INTERMEDIATE].append(example)
            else:
                phase_examples[CurriculumPhase.ADVANCED].append(example)

        # Log phase distribution
        if self.logger:
            for phase, exs in phase_examples.items():
                self.logger.info(f"Phase {phase.value}: {len(exs)} examples")

        return phase_examples

    def _train_phase(
        self, phase: CurriculumPhase, examples: list[RAFTExample], model_name: str
    ) -> dict[str, Any]:
        """
        Train a specific curriculum phase.

        Args:
            phase: Curriculum phase to train
            examples: Examples for this phase
            model_name: Base model name

        Returns:
            Phase training results
        """
        stage = self.curriculum[phase]

        if self.logger:
            self.logger.info(f"🎯 Training phase {phase.value} with {len(examples)} examples")

        result = {
            "phase": phase.value,
            "examples_available": len(examples),
            "success": False,
            "phase_score": 0.0,
            "issues": [],
        }

        # Check minimum requirements
        if len(examples) < stage.min_examples:
            result["issues"].append(
                f"Insufficient examples: {len(examples)} < {stage.min_examples}"
            )
            return result

        try:
            # Simulate progressive training (in real implementation, this would call actual training)
            training_score = self._simulate_phase_training(phase, examples)

            # Evaluate phase completion
            if training_score >= stage.min_quality_score:
                result["success"] = True
                result["phase_score"] = training_score
                self.progress.phase_completed_examples += len(examples)

                if self.logger:
                    self.logger.info(
                        f"✅ Phase {phase.value} completed with score: {training_score:.3f}"
                    )
            else:
                result["issues"].append(
                    f"Training score {training_score:.3f} below threshold {stage.min_quality_score}"
                )

        except Exception as e:
            result["issues"].append(f"Phase training failed: {str(e)}")
            if self.logger:
                self.logger.error(f"Phase {phase.value} training failed: {e}")

        return result

    def _simulate_phase_training(
        self, phase: CurriculumPhase, examples: list[RAFTExample]
    ) -> float:
        """
        Simulate phase training and return performance score.

        In real implementation, this would train the model and evaluate performance.
        """
        # Simulate training based on example quality
        total_quality = 0.0
        count = 0

        for example in examples:
            assessment = self.quality_scorer.assess_example_quality(example)
            total_quality += assessment.metrics.overall_score
            count += 1

        # Phase-specific training effectiveness
        phase_multiplier = {
            CurriculumPhase.FOUNDATION: 0.8,
            CurriculumPhase.INTERMEDIATE: 0.7,
            CurriculumPhase.ADVANCED: 0.6,
        }

        base_score = total_quality / count if count > 0 else 0.0
        training_score = base_score * phase_multiplier.get(phase, 0.7)

        # Add progressive learning bonus (later phases benefit from earlier training)
        phase_bonus = len(self.progress.graduated_phases) * 0.05
        training_score = min(1.0, training_score + phase_bonus)

        return training_score

    def _evaluate_final_performance(self) -> float:
        """Evaluate final trained model performance"""
        # In real implementation, this would load the trained model and evaluate
        # For now, return a score based on training progress
        graduated_count = len(self.progress.graduated_phases)
        total_phases = len(CurriculumPhase)

        return (graduated_count / total_phases) * 0.9  # Max 0.9, room for improvement

    def get_training_recommendations(self) -> list[str]:
        """Get recommendations for improving training effectiveness"""
        recommendations = []

        # Check example distribution
        all_examples = self._load_validated_examples()
        phase_examples = self._organize_examples_by_phase(all_examples)

        for phase, examples in phase_examples.items():
            stage = self.curriculum[phase]
            if len(examples) < stage.min_examples:
                recommendations.append(
                    f"Add {stage.min_examples - len(examples)} more examples to {phase.value} phase"
                )

        # Check quality distribution
        quality_stats = self.quality_scorer.batch_assess_quality(self.validated_dir)
        avg_quality = quality_stats.get("average_score", 0.0)

        if avg_quality < 0.7:
            recommendations.append(
                "Overall example quality is low. Consider human validation or context regeneration"
            )

        # Check phase progression
        total_phases = len(CurriculumPhase)
        completed_phases = len(self.progress.graduated_phases)

        if completed_phases < total_phases:
            recommendations.append(
                f"Only {completed_phases}/{total_phases} phases completed. Focus on remaining phases"
            )

        # Default recommendations
        if not recommendations:
            recommendations.append(
                "Training curriculum looks good. Consider adding more diverse examples for better generalization"
            )

        return recommendations

    def _load_progress(self):
        """Load training progress from file"""
        progress_file = self.output_dir / "training_progress.json"
        if progress_file.exists():
            try:
                with open(progress_file, encoding="utf-8") as f:
                    data = json.load(f)
                    # Restore progress (would need more sophisticated serialization in real implementation)
                    self.progress.total_trained_examples = data.get("total_trained_examples", 0)
            except Exception:
                pass  # Use defaults

    def _save_progress(self):
        """Save training progress to file"""
        progress_file = self.output_dir / "training_progress.json"

        progress_data = {
            "current_phase": self.progress.current_phase.value,
            "total_trained_examples": self.progress.total_trained_examples,
            "graduated_phases": [p.value for p in self.progress.graduated_phases],
            "last_evaluation_score": self.progress.last_evaluation_score,
        }

        try:
            with open(progress_file, "w", encoding="utf-8") as f:
                json.dump(progress_data, f, indent=2)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to save training progress: {e}")

    def get_curriculum_status(self) -> dict[str, Any]:
        """Get current curriculum training status"""
        all_examples = self._load_validated_examples()
        phase_examples = self._organize_examples_by_phase(all_examples)

        return {
            "current_phase": self.progress.current_phase.value,
            "graduated_phases": [p.value for p in self.progress.graduated_phases],
            "examples_per_phase": {
                phase.value: len(examples) for phase, examples in phase_examples.items()
            },
            "total_examples": len(all_examples),
            "recommendations": self.get_training_recommendations(),
        }
