"""Unit tests for the RAFT ``QualityScorer``.

Coverage for review 2026-07-20 Recommended finding 10(b): the training modules
carried little direct test coverage. ``quality_scorer.py`` was at ~12%.

These tests exercise each scoring component with concrete inputs and, crucially,
assert **dataset influence** — that a content-rich example scores materially
higher than a degenerate one. The scorer is pure/deterministic (no I/O, no
Ollama), so every assertion is on real returned values, not placeholders.
"""

import json

import pytest

from src.training.quality_scorer import (
    QualityAssessment,
    QualityMetrics,
    QualityScorer,
)


@pytest.fixture
def scorer():
    return QualityScorer()


def _rich_example():
    """A high-quality automotive example: domain keywords, diverse context, complex req."""
    return {
        "requirement_id": "REQ_RICH",
        "requirement_text": (
            "The vehicle ECU shall monitor the brake pressure via the CAN bus and "
            "must disable the ABS when the value exceeds 12.5 bar, if the engine is running."
        ),
        "retrieved_context": {
            "heading": {"text": "Brake Control System"},
            "info_artifacts": [
                {"text": "The brake ECU communicates over CAN with the ABS module."},
                {"text": "Vehicle safety requires the engine torque to be limited."},
            ],
            "interfaces": [
                {"text": "CAN signal BrakePressure, range 0-20 bar"},
            ],
        },
    }


def _poor_example():
    """A degenerate example: no context, trivial requirement."""
    return {
        "requirement_id": "REQ_POOR",
        "requirement_text": "It works.",
        "retrieved_context": {},
    }


# ---------------------------------------------------------------------------
# Dataset-influence: the headline property the review wanted verified.
# ---------------------------------------------------------------------------


def test_rich_example_scores_higher_than_poor(scorer):
    rich = scorer.assess_example_quality(_rich_example())
    poor = scorer.assess_example_quality(_poor_example())

    assert isinstance(rich, QualityAssessment)
    assert rich.metrics.overall_score > poor.metrics.overall_score
    # The gap should be substantial, not marginal noise.
    assert rich.metrics.overall_score - poor.metrics.overall_score > 0.2


def test_scores_are_bounded_0_to_1(scorer):
    for example in (_rich_example(), _poor_example()):
        m = scorer.assess_example_quality(example).metrics
        for value in (
            m.relevance_score,
            m.context_diversity,
            m.context_quantity,
            m.requirement_complexity,
            m.overall_score,
        ):
            assert 0.0 <= value <= 1.0


def test_priority_tracks_score(scorer):
    assert scorer.assess_example_quality(_poor_example()).priority == "low"
    # Priority is derived purely from overall_score thresholds.
    assert scorer._determine_priority(QualityMetrics(overall_score=0.75)) == "high"
    assert scorer._determine_priority(QualityMetrics(overall_score=0.5)) == "medium"
    assert scorer._determine_priority(QualityMetrics(overall_score=0.1)) == "low"


# ---------------------------------------------------------------------------
# Relevance / domain
# ---------------------------------------------------------------------------


def test_relevance_zero_without_text_or_context(scorer):
    assert scorer._calculate_relevance_score("", {"heading": {"text": "x"}}) == 0.0
    assert scorer._calculate_relevance_score("something", {}) == 0.0


def test_relevance_rewards_lexical_overlap(scorer):
    req = "brake pressure sensor calibration"
    overlapping = {"info_artifacts": [{"text": "brake pressure sensor value"}]}
    disjoint = {"info_artifacts": [{"text": "completely unrelated banana content"}]}
    assert scorer._calculate_relevance_score(req, overlapping) > scorer._calculate_relevance_score(
        req, disjoint
    )


def test_domain_relevance_bonus_requires_both_sides(scorer):
    # >=3 automotive keywords on each side triggers the 0.2 bonus.
    auto_text = "vehicle engine brake steering ECU CAN"
    assert scorer._calculate_domain_relevance(auto_text, auto_text) == pytest.approx(0.2)
    # Only one side mentions the domain -> no bonus.
    assert scorer._calculate_domain_relevance(auto_text, "plain text here") == 0.0
    # Too few keywords -> no bonus.
    assert scorer._calculate_domain_relevance("engine only", "engine only") == 0.0


# ---------------------------------------------------------------------------
# Diversity / quantity / complexity
# ---------------------------------------------------------------------------


def test_context_diversity_counts_types(scorer):
    none_ctx = scorer._calculate_context_diversity({})
    heading_only = scorer._calculate_context_diversity({"heading": {"text": "H"}})
    all_three = scorer._calculate_context_diversity(
        {
            "heading": {"text": "H"},
            "info_artifacts": [{"text": "i"}],
            "interfaces": [{"text": "iface"}],
        }
    )
    assert none_ctx == 0.0
    assert heading_only == pytest.approx(1 / 3)
    assert all_three == pytest.approx(1.0)


def test_context_diversity_bonus_for_multiple_info(scorer):
    single = scorer._calculate_context_diversity({"info_artifacts": [{"text": "a"}]})
    multiple = scorer._calculate_context_diversity(
        {"info_artifacts": [{"text": "a"}, {"text": "b"}]}
    )
    assert multiple > single


def test_context_quantity_normalizes_and_caps(scorer):
    assert scorer._calculate_context_quantity({}) == 0.0
    small = scorer._calculate_context_quantity({"heading": {"text": "x" * 500}})
    assert small == pytest.approx(0.5)
    huge = scorer._calculate_context_quantity({"heading": {"text": "x" * 5000}})
    assert huge == 1.0  # capped


def test_requirement_complexity(scorer):
    assert scorer._calculate_requirement_complexity("") == 0.0
    simple = scorer._calculate_requirement_complexity("Do it.")
    complex_req = scorer._calculate_requirement_complexity(
        "The ECU shall verify the value if it exceeds 12.5 and must react when CAN "
        "signals ABS, then it will report >= 90% within 200ms." * 2
    )
    assert complex_req > simple
    assert 0.0 <= complex_req <= 1.0


# ---------------------------------------------------------------------------
# Vision metrics
# ---------------------------------------------------------------------------


def test_image_quality_zero_without_images(scorer):
    assert scorer._calculate_image_quality_score([]) == 0.0


def test_image_quality_rewards_size_format_count(scorer):
    poor = scorer._calculate_image_quality_score([{"size_bytes": 100, "format": "BMP"}])
    good = scorer._calculate_image_quality_score(
        [
            {"size_bytes": 120_000, "format": "SVG", "image_type": "state_machine"},
            {"size_bytes": 200_000, "format": "PNG", "description": "brake flow"},
            {"size_bytes": 150_000, "format": "PNG", "image_type": "timing_diagram"},
        ]
    )
    assert good > poor
    assert 0.0 <= good <= 1.0


def test_image_relevance_needs_text_and_images(scorer):
    assert scorer._calculate_image_relevance_score("req", []) == 0.0
    assert scorer._calculate_image_relevance_score("", [{"image_type": "state_machine"}]) == 0.0


def test_image_relevance_rewards_visual_keywords_and_types(scorer):
    req = "The state machine diagram shows the transition flow of the display."
    images = [
        {
            "image_type": "state_machine",
            "description": "state machine of display",
            "relevance": "oracle",
        },
    ]
    score = scorer._calculate_image_relevance_score(req, images)
    assert score > 0.0
    assert score <= 1.0


def test_has_images_changes_overall_weighting(scorer):
    example = _rich_example()
    example["has_images"] = True
    example["images"] = [
        {
            "size_bytes": 120_000,
            "format": "PNG",
            "image_type": "state_machine",
            "description": "brake",
        },
    ]
    result = scorer.assess_example_quality(example)
    assert result.metrics.has_images is True
    assert result.metrics.image_quality_score > 0.0


# ---------------------------------------------------------------------------
# Recommendations / suggestions
# ---------------------------------------------------------------------------


def test_recommendations_flag_poor_example(scorer):
    recs = scorer.assess_example_quality(_poor_example()).recommendations
    joined = " ".join(recs).lower()
    assert recs  # non-empty
    assert "relevance" in joined or "context" in joined


def test_suggest_improvements_recommends_regeneration_for_low_relevance(scorer):
    assessment = scorer.assess_example_quality(_poor_example())
    improvements = scorer.suggest_improvements(assessment)
    assert improvements["regeneration_recommended"] is True
    assert improvements["required_actions"]


def test_suggest_improvements_clean_for_rich_example(scorer):
    assessment = scorer.assess_example_quality(_rich_example())
    improvements = scorer.suggest_improvements(assessment)
    assert improvements["regeneration_recommended"] is False


# ---------------------------------------------------------------------------
# Batch assessment (I/O + failure paths)
# ---------------------------------------------------------------------------


def test_batch_missing_directory_returns_error(scorer, tmp_path):
    result = scorer.batch_assess_quality(tmp_path / "does_not_exist")
    assert "error" in result


def test_batch_assesses_and_summarizes(scorer, tmp_path):
    for i, example in enumerate((_rich_example(), _poor_example())):
        (tmp_path / f"raft_{i:03d}.json").write_text(json.dumps(example), encoding="utf-8")

    result = scorer.batch_assess_quality(tmp_path)
    assert result["total_assessed"] == 2
    assert 0.0 <= result["average_score"] <= 1.0
    assert sum(result["score_distribution"].values()) == 2


def test_batch_skips_malformed_json(scorer, tmp_path):
    (tmp_path / "raft_000.json").write_text(json.dumps(_rich_example()), encoding="utf-8")
    (tmp_path / "raft_001.json").write_text("{ not valid json", encoding="utf-8")

    result = scorer.batch_assess_quality(tmp_path)
    # Only the valid file is counted; the malformed one is skipped, not fatal.
    assert result["total_assessed"] == 1
