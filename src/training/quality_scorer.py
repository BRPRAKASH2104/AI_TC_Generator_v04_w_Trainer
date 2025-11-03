"""
Automated Quality Assessment for RAFT Training Examples

This module provides automated quality scoring for training examples to help
prioritize which examples need human annotation and identify quality patterns.
"""

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from logging import Logger

type RAFTExample = dict[str, Any]


@dataclass(slots=True)
class QualityMetrics:
    """Quality metrics for a RAFT training example (with vision support)"""

    relevance_score: float = 0.0  # How well oracle context relates to requirement
    context_diversity: float = 0.0  # Diversity of context types
    context_quantity: float = 0.0  # Amount of context provided
    requirement_complexity: float = 0.0  # Complexity of requirement text
    # Vision metrics (v2.2.0+)
    image_quality_score: float = 0.0  # Quality/usefulness of images
    image_relevance_score: float = 0.0  # How relevant images are to requirement
    has_images: bool = False  # Whether example includes images
    # Overall
    overall_score: float = 0.0  # Combined quality score


@dataclass(slots=True)
class QualityAssessment:
    """Complete quality assessment result"""

    example_id: str
    metrics: QualityMetrics
    recommendations: list[str]
    priority: str  # 'high', 'medium', 'low'


class QualityScorer:
    """
    Automated quality assessment for RAFT training examples.

    This class analyzes training examples and provides quality scores and
    recommendations to help prioritize human annotation efforts.
    """

    __slots__ = ("logger", "weights", "domain_keywords")

    def __init__(self, logger: Logger | None = None):
        self.logger = logger

        # Scoring weights (adjusted for vision support v2.2.0)
        self.weights = {
            "relevance": 0.30,
            "diversity": 0.15,
            "quantity": 0.15,
            "complexity": 0.15,
            "image_quality": 0.15,  # NEW: Image quality contribution
            "image_relevance": 0.10,  # NEW: Image relevance contribution
        }

        # Keyword sets for relevance scoring
        self.domain_keywords = {
            "automotive": [
                "vehicle",
                "car",
                "engine",
                "transmission",
                "brake",
                "steering",
                "ABS",
                "ESP",
                "ECU",
                "CAN",
                "LIN",
                "FlexRay",
                "ADAS",
                "safety",
                "emission",
                "fuel",
                "battery",
                "electric",
                "hybrid",
                "autonomous",
            ],
            "aerospace": [
                "aircraft",
                "avionics",
                "flight",
                "altitude",
                "pressure",
                "temperature",
                "navigation",
                "radar",
                "GPS",
                "inertial",
                "hydraulics",
                "pneumatics",
            ],
            "medical": [
                "patient",
                "therapy",
                "diagnosis",
                "monitoring",
                "alarm",
                "sensor",
                "dosage",
                "infusion",
                "ventilation",
                "anesthesia",
                "radiation",
            ],
        }

    def assess_example_quality(self, example: RAFTExample) -> QualityAssessment:
        """
        Assess the quality of a single RAFT training example (with vision support).

        Args:
            example: RAFT training example to assess

        Returns:
            Quality assessment with scores and recommendations
        """
        example_id = example.get("requirement_id", "UNKNOWN")
        requirement_text = example.get("requirement_text", "")
        context = example.get("retrieved_context", {})

        # Calculate individual metrics
        relevance_score = self._calculate_relevance_score(requirement_text, context)
        context_diversity = self._calculate_context_diversity(context)
        context_quantity = self._calculate_context_quantity(context)
        requirement_complexity = self._calculate_requirement_complexity(requirement_text)

        # Vision metrics (v2.2.0+)
        has_images = example.get("has_images", False)
        image_quality_score = 0.0
        image_relevance_score = 0.0

        if has_images:
            images = example.get("images", [])
            image_quality_score = self._calculate_image_quality_score(images)
            image_relevance_score = self._calculate_image_relevance_score(requirement_text, images)

        # Calculate overall score (adjusted for vision)
        if has_images:
            # Weight distribution includes image metrics
            overall_score = (
                relevance_score * self.weights["relevance"]
                + context_diversity * self.weights["diversity"]
                + context_quantity * self.weights["quantity"]
                + requirement_complexity * self.weights["complexity"]
                + image_quality_score * self.weights["image_quality"]
                + image_relevance_score * self.weights["image_relevance"]
            )
        else:
            # Text-only: Normalize without image weights
            text_weight_sum = sum(
                self.weights[k] for k in ["relevance", "diversity", "quantity", "complexity"]
            )
            overall_score = (
                relevance_score * self.weights["relevance"]
                + context_diversity * self.weights["diversity"]
                + context_quantity * self.weights["quantity"]
                + requirement_complexity * self.weights["complexity"]
            ) / text_weight_sum

        metrics = QualityMetrics(
            relevance_score=relevance_score,
            context_diversity=context_diversity,
            context_quantity=context_quantity,
            requirement_complexity=requirement_complexity,
            image_quality_score=image_quality_score,
            image_relevance_score=image_relevance_score,
            has_images=has_images,
            overall_score=overall_score,
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, example)

        # Determine priority
        priority = self._determine_priority(metrics)

        return QualityAssessment(
            example_id=example_id,
            metrics=metrics,
            recommendations=recommendations,
            priority=priority,
        )

    def _calculate_relevance_score(self, requirement_text: str, context: dict) -> float:
        """
        Calculate how relevant the context is to the requirement.

        This analyzes lexical overlap and semantic relationships between
        the requirement and retrieved context.
        """
        if not requirement_text or not context:
            return 0.0

        req_lower = requirement_text.lower()
        req_words = set(re.findall(r"\b\w+\b", req_lower))

        total_context_text = ""

        # Collect all context text
        for context_type in ["heading", "info_artifacts", "interfaces"]:
            if context_type == "heading":
                heading = context.get("heading", {})
                if isinstance(heading, dict) and "text" in heading:
                    total_context_text += " " + heading["text"]
                elif isinstance(heading, str):
                    total_context_text += " " + heading
            elif context_type == "info_artifacts":
                artifacts = context.get("info_artifacts", [])
                for artifact in artifacts:
                    if isinstance(artifact, dict) and "text" in artifact:
                        total_context_text += " " + artifact["text"]
            elif context_type == "interfaces":
                interfaces = context.get("interfaces", [])
                for iface in interfaces:
                    if isinstance(iface, dict) and "text" in iface:
                        total_context_text += " " + iface["text"]

        ctx_lower = total_context_text.lower()
        ctx_words = set(re.findall(r"\b\w+\b", ctx_lower))

        # Calculate lexical overlap
        if req_words:
            overlap = len(req_words.intersection(ctx_words))
            overlap_score = overlap / len(req_words)
        else:
            overlap_score = 0.0

        # Domain-specific relevance bonus
        domain_bonus = self._calculate_domain_relevance(req_lower, ctx_lower)

        # Combined score
        relevance_score = min(1.0, overlap_score + domain_bonus * 0.3)

        return relevance_score

    def _calculate_domain_relevance(self, req_text: str, ctx_text: str) -> float:
        """Calculate domain-specific relevance bonus"""
        for _domain, keywords in self.domain_keywords.items():
            req_domain_score = sum(1 for kw in keywords if kw.lower() in req_text) / len(keywords)
            ctx_domain_score = sum(1 for kw in keywords if kw.lower() in ctx_text) / len(keywords)

            # Bonus if both requirement and context mention domain keywords
            if req_domain_score > 0.1 and ctx_domain_score > 0.1:
                return 0.2  # 20% bonus for domain alignment

        return 0.0

    def _calculate_context_diversity(self, context: dict) -> float:
        """Calculate diversity of context types and sources"""
        diversity_score = 0.0
        has_heading = False
        has_info = False
        has_interfaces = False

        # Check for heading
        heading = context.get("heading", {})
        if (
            isinstance(heading, dict)
            and heading.get("text")
            or isinstance(heading, str)
            and heading.strip()
        ):
            has_heading = True

        # Check for info artifacts
        info_artifacts = context.get("info_artifacts", [])
        if info_artifacts and len(info_artifacts) > 0:
            has_info = True

        # Check for interfaces
        interfaces = context.get("interfaces", [])
        if interfaces and len(interfaces) > 0:
            has_interfaces = True

        # Base diversity score
        context_types = sum([has_heading, has_info, has_interfaces])
        diversity_score = context_types / 3.0  # Normalize to 0-1 range

        # Bonus for multiple info artifacts
        if has_info and len(info_artifacts) > 1:
            diversity_score = min(1.0, diversity_score + 0.1)

        return diversity_score

    def _calculate_context_quantity(self, context: dict) -> float:
        """Calculate the quantity/amount of context provided"""
        total_chars = 0

        # Count heading text
        heading = context.get("heading", {})
        if isinstance(heading, dict) and "text" in heading:
            total_chars += len(heading["text"])
        elif isinstance(heading, str):
            total_chars += len(heading)

        # Count info artifacts
        info_artifacts = context.get("info_artifacts", [])
        for artifact in info_artifacts:
            if isinstance(artifact, dict) and "text" in artifact:
                total_chars += len(artifact["text"])

        # Count interfaces
        interfaces = context.get("interfaces", [])
        for iface in interfaces:
            if isinstance(iface, dict) and "text" in iface:
                total_chars += len(iface["text"])

        # Normalize to 0-1 scale (1000+ characters = full score)
        quantity_score = min(1.0, total_chars / 1000.0)

        return quantity_score

    def _calculate_requirement_complexity(self, requirement_text: str) -> float:
        """Calculate complexity of the requirement"""
        if not requirement_text:
            return 0.0

        text = requirement_text.strip()

        # Length complexity
        length_score = min(1.0, len(text) / 200.0)

        # Structural complexity (number of clauses)
        clause_indicators = ["shall", "must", "should", "will", "may", "can", "if", "when", "then"]
        clauses = sum(1 for indicator in clause_indicators if indicator in text.lower())
        clause_score = min(1.0, clauses / 3.0)

        # Technical complexity (special characters, numbers)
        tech_patterns = [r"\b\d+\.\d+\b", r"[A-Z]{3,}", r"[<>]=", r"±", r"°", r"%"]
        tech_score = sum(1 for pattern in tech_patterns if re.search(pattern, text)) / len(
            tech_patterns
        )

        # Combined complexity score
        complexity_score = length_score * 0.4 + clause_score * 0.4 + tech_score * 0.2

        return complexity_score

    def _calculate_image_quality_score(self, images: list[dict[str, Any]]) -> float:
        """
        Calculate quality of images for training.

        Considers:
        - Image size (larger = more detail)
        - Format (vector > raster)
        - Number of images (diversity)
        - Proper encoding
        """
        if not images:
            return 0.0

        quality_score = 0.0

        # Base score: Has images
        quality_score += 0.3

        # Size quality: Prefer larger images (more detail)
        sizes = [img.get("size_bytes", 0) for img in images]
        if sizes:
            avg_size = sum(sizes) / len(sizes)
            # Good size: 50KB - 500KB
            if 50_000 <= avg_size <= 500_000:
                quality_score += 0.3
            elif avg_size > 500_000:
                quality_score += 0.2  # Very large, might be excessive
            else:
                quality_score += 0.1  # Small, limited detail

        # Format quality: Vector formats > raster
        formats = [img.get("format", "").upper() for img in images]
        vector_formats = {"SVG"}
        high_quality_raster = {"PNG", "TIFF"}

        vector_count = sum(1 for fmt in formats if fmt in vector_formats)
        hq_raster_count = sum(1 for fmt in formats if fmt in high_quality_raster)

        format_score = (vector_count * 0.15 + hq_raster_count * 0.10) / len(images)
        quality_score += min(0.2, format_score)

        # Diversity bonus: Multiple images provide different perspectives
        image_count = len(images)
        if image_count >= 3:
            quality_score += 0.2
        elif image_count == 2:
            quality_score += 0.15
        elif image_count == 1:
            quality_score += 0.05

        # Annotation quality: Check if images are annotated
        annotated_count = sum(
            1 for img in images if img.get("image_type") or img.get("description")
        )
        if annotated_count > 0:
            quality_score += (annotated_count / len(images)) * 0.1

        return min(1.0, quality_score)

    def _calculate_image_relevance_score(
        self, requirement_text: str, images: list[dict[str, Any]]
    ) -> float:
        """
        Calculate how relevant images are to the requirement.

        Uses image descriptions and types to assess relevance.
        """
        if not images or not requirement_text:
            return 0.0

        relevance_score = 0.0
        req_lower = requirement_text.lower()

        # Check for visual keywords in requirement
        visual_keywords = [
            "diagram",
            "state",
            "flow",
            "chart",
            "graph",
            "timing",
            "sequence",
            "transition",
            "ui",
            "interface",
            "display",
            "screen",
            "button",
            "menu",
            "visual",
            "shown",
            "depicted",
        ]

        visual_mention_count = sum(1 for kw in visual_keywords if kw in req_lower)
        if visual_mention_count > 0:
            relevance_score += 0.3  # Requirement explicitly references visuals

        # Check image type annotations
        image_types = [img.get("image_type") for img in images if img.get("image_type")]
        if image_types:
            # Relevant types for automotive requirements
            relevant_types = {
                "state_machine",
                "timing_diagram",
                "flow_chart",
                "sequence_diagram",
                "block_diagram",
                "signal_flow",
                "ui_mockup",
                "parameter_table",
            }

            relevant_count = sum(
                1 for img_type in image_types if img_type and img_type.lower() in relevant_types
            )

            if relevant_count > 0:
                relevance_score += (relevant_count / len(images)) * 0.4

        # Check image descriptions for keyword overlap
        for img in images:
            description = img.get("description", "").lower()
            if description:
                desc_words = set(re.findall(r"\b\w+\b", description))
                req_words = set(re.findall(r"\b\w+\b", req_lower))

                if desc_words and req_words:
                    overlap = len(desc_words.intersection(req_words))
                    overlap_score = min(0.3, overlap / len(req_words))
                    relevance_score += overlap_score / len(images)

        # Oracle annotation bonus
        oracle_count = sum(1 for img in images if img.get("relevance") == "oracle")
        if oracle_count > 0:
            relevance_score += (oracle_count / len(images)) * 0.2

        return min(1.0, relevance_score)

    def _generate_recommendations(self, metrics: QualityMetrics, example: RAFTExample) -> list[str]:
        """Generate specific recommendations based on quality metrics"""
        recommendations = []

        if metrics.relevance_score < 0.3:
            recommendations.append("Low relevance: Consider adding more domain-specific context")

        if metrics.context_diversity < 0.5:
            recommendations.append(
                "Low diversity: Include different types of context (heading, info, interfaces)"
            )

        if metrics.context_quantity < 0.3:
            recommendations.append("Insufficient context: Add more detailed context information")

        if metrics.requirement_complexity < 0.3:
            recommendations.append(
                "Simple requirement: Consider if this adds value to training set"
            )

        # Specific context type recommendations
        context = example.get("retrieved_context", {})
        if not context.get("heading", {}).get("text"):
            recommendations.append("Missing heading: Consider adding section header context")

        info_count = len(context.get("info_artifacts", []))
        if info_count < 2:
            recommendations.append(
                f"Limited info artifacts ({info_count}): Add more background information"
            )

        interface_count = len(context.get("interfaces", []))
        if interface_count == 0:
            recommendations.append(
                "No interface context: Consider adding system interface definitions"
            )

        # Vision-specific recommendations (v2.2.0+)
        if metrics.has_images:
            if metrics.image_quality_score < 0.4:
                recommendations.append(
                    "Low image quality: Use higher resolution or vector format diagrams"
                )

            if metrics.image_relevance_score < 0.3:
                recommendations.append(
                    "Images may not be relevant: Verify diagrams match requirement context"
                )

            # Check if images are annotated
            images = example.get("images", [])
            unannotated_count = sum(
                1 for img in images if not img.get("image_type") and not img.get("description")
            )
            if unannotated_count > 0:
                recommendations.append(
                    f"{unannotated_count} image(s) need annotation: Add image_type and description"
                )

        return recommendations

    def _determine_priority(self, metrics: QualityMetrics) -> str:
        """Determine annotation priority based on quality metrics"""
        if metrics.overall_score >= 0.7:
            return "high"  # Good examples - prioritize for validation
        elif metrics.overall_score >= 0.4:
            return "medium"  # Medium quality - standard priority
        else:
            return "low"  # Low quality - may need regeneration or rejection

    def batch_assess_quality(
        self, examples_dir: str | Path, max_examples: int = 100
    ) -> dict[str, Any]:
        """
        Assess quality of multiple examples and provide summary statistics.

        Args:
            examples_dir: Directory containing RAFT example files
            max_examples: Maximum number of examples to assess

        Returns:
            Quality assessment summary
        """
        examples_path = Path(examples_dir)
        if not examples_path.exists():
            return {"error": f"Directory {examples_dir} does not exist"}

        # Get example files
        json_files = list(examples_path.glob("raft_*.json"))[:max_examples]

        assessments = []
        priority_counts = defaultdict(int)
        score_distribution = {"high": 0, "medium": 0, "low": 0}

        for file_path in json_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    example = json.load(f)

                assessment = self.assess_example_quality(example)
                assessments.append(assessment)

                priority_counts[assessment.priority] += 1
                score_distribution[assessment.priority] += 1

            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to assess {file_path}: {e}")
                continue

        # Calculate summary statistics
        if assessments:
            scores = [a.metrics.overall_score for a in assessments]
            avg_score = sum(scores) / len(scores)
            median_score = sorted(scores)[len(scores) // 2]

            relevance_scores = [a.metrics.relevance_score for a in assessments]
            avg_relevance = sum(relevance_scores) / len(relevance_scores)

            recommendations = []
            for assessment in assessments:
                recommendations.extend(assessment.recommendations)

            # Most common recommendations
            rec_counts = defaultdict(int)
            for rec in recommendations:
                rec_counts[rec] += 1

            top_recommendations = sorted(rec_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        else:
            avg_score = median_score = avg_relevance = 0.0
            top_recommendations = []

        return {
            "total_assessed": len(assessments),
            "score_distribution": dict(score_distribution),
            "average_score": avg_score,
            "median_score": median_score,
            "average_relevance": avg_relevance,
            "top_recommendations": top_recommendations,
            "priority_breakdown": dict(priority_counts),
        }

    def suggest_improvements(self, assessment: QualityAssessment) -> dict[str, Any]:
        """
        Suggest specific improvements for a low-quality example.

        Args:
            assessment: Quality assessment result

        Returns:
            Suggested improvements
        """
        improvements = {
            "required_actions": [],
            "optional_actions": [],
            "regeneration_recommended": False,
        }

        metrics = assessment.metrics

        # Critical improvements
        if metrics.relevance_score < 0.2:
            improvements["regeneration_recommended"] = True
            improvements["required_actions"].append(
                "Regenerate context with better retrieval algorithm"
            )

        if metrics.context_quantity < 0.2:
            improvements["required_actions"].append(
                "Add more context information to retrieved documents"
            )

        # Optional improvements
        if metrics.context_diversity < 0.3:
            improvements["optional_actions"].append(
                "Incorporate different types of context documents"
            )

        if metrics.requirement_complexity < 0.2:
            improvements["optional_actions"].append("Select more complex requirements for training")

        return improvements
