"""Live-Ollama calibration of the LLM judge (Phase 3c).

The unit tests use scripted scorers and so cannot tell whether the real judge
is any good. This test runs the llm column of the calibration harness against a
real Ollama and asserts the declared bands — in particular ``paraphrase``, the
case that justifies the LLM judge's cost over the deterministic scorer.

Opt-in: marked ``integration`` (excluded by ``-m "not integration"``) and
``slow``, and it skips itself when no reachable Ollama with the judge model is
available.
"""

import pytest
import requests

from src.config import ConfigManager
from src.core.ollama_client import OllamaClient
from src.training.judge_calibration import CalibrationReport, format_report, run_calibration
from src.training.judge_calibration_cases import DEFAULT_CALIBRATION_CASES
from src.training.llm_judge_scorer import LLMJudgeScorer

JUDGE_MODEL = "llama3.1:8b"


def _ollama_reason() -> str | None:
    """Return None when a reachable Ollama has JUDGE_MODEL, else a skip reason."""
    config = ConfigManager()
    tags_url = f"http://{config.ollama.host}:{config.ollama.port}/api/tags"
    try:
        response = requests.get(tags_url, timeout=2)
        response.raise_for_status()
        names = {model.get("name", "") for model in response.json().get("models", [])}
    except requests.RequestException as exc:
        return f"Ollama not reachable at {tags_url}: {exc}"

    family = JUDGE_MODEL.split(":", 1)[0]
    if not any(name == JUDGE_MODEL or name.startswith(family) for name in names):
        return f"model {JUDGE_MODEL} not pulled (available: {sorted(names)})"
    return None


# Probe once at collection, not twice — each call is a live HTTP request.
_SKIP_REASON = _ollama_reason()

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.skipif(_SKIP_REASON is not None, reason=_SKIP_REASON or ""),
]


@pytest.fixture(scope="module")
def llm_report() -> CalibrationReport:
    """Run the llm calibration column once for the whole module."""
    return run_calibration(
        LLMJudgeScorer(judge_model=JUDGE_MODEL),
        "llm",
        DEFAULT_CALIBRATION_CASES,
        client=OllamaClient(),
        judge_model=JUDGE_MODEL,
    )


def test_no_case_faulted(llm_report: CalibrationReport) -> None:
    """No calibration case should raise inside the scorer."""
    errors = [(r["name"], r["error"]) for r in llm_report["results"] if r["error"]]
    assert errors == [], f"judge faulted on: {errors}"


def test_identity_is_recognised(llm_report: CalibrationReport) -> None:
    """Generated == reference must land inside the identity band."""
    result = next(r for r in llm_report["results"] if r["name"] == "identity")
    assert result["passed"], f"identity breached its band: {result['score']}"


def test_disjoint_gets_no_credit(llm_report: CalibrationReport) -> None:
    """Completely unrelated generations must land inside the disjoint band."""
    result = next(r for r in llm_report["results"] if r["name"] == "disjoint")
    assert result["passed"], f"disjoint breached its band: {result['score']}"


def test_judge_beats_overlap_on_paraphrases(llm_report: CalibrationReport) -> None:
    """The discriminating case — this is what justifies the LLM judge's cost."""
    result = next(r for r in llm_report["results"] if r["name"] == "paraphrase")
    assert result["passed"], (
        f"the LLM judge did not clear the paraphrase band: {result['score']}. "
        "This is a real finding: report it rather than widening the band."
    )


def test_whole_llm_column_passes(llm_report: CalibrationReport) -> None:
    """The full llm scorecard column must pass with no breached bands."""
    failures = [r["name"] for r in llm_report["results"] if not r["passed"]]
    assert failures == [], f"llm breached bands for: {failures}\n{format_report([llm_report])}"
