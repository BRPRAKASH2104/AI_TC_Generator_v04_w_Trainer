"""LLM-as-judge content scorer for RAFT evaluation (Phase 3b).

Matches generated test cases to the held-out reference answer by *meaning*
(semantic precision/recall/F1) and rates the generation on a holistic 0–1
quality rubric, using a local Ollama judge model. Implements the widened
``ContentScorer`` protocol; determinism relies on the client's configured
temperature (default 0.0), so correctness is pinned by mocked unit tests.
"""

import json
from typing import Any

from src.core.parsers import JSONResponseParser
from src.training.content_scorer import ContentScore, _prf

_MATCH_PROMPT = """You are grading generated automotive test cases against a reference (gold) set.

Two test cases MATCH when they exercise the same scenario or behavior, even if worded differently.

Generated test cases:
{generated}

Reference (gold) test cases:
{reference}

Return ONLY a JSON object of the matches, using the 0-based numbers above:
{{"matches": [[generated_number, reference_number], ...]}}
Each generated case matches at most one reference case and vice versa. If nothing matches, return {{"matches": []}}."""

_QUALITY_PROMPT = """You are grading the overall quality of generated automotive test cases against a reference (gold) set.

Judge the correctness, completeness, and testability of the generated cases relative to the gold set, as a single holistic score.

Generated test cases:
{generated}

Reference (gold) test cases:
{reference}

Return ONLY a JSON object:
{{"quality": <a number from 0.0 to 1.0>, "rationale": "<one short sentence>"}}"""


class LLMJudgeScorer:
    """Semantic precision/recall/F1 + holistic quality via a local LLM judge.

    Makes two model calls per generation (matching, then quality). Each call
    fails independently to None so one fault never wipes the other score.
    """

    __slots__ = ("judge_model",)

    def __init__(self, judge_model: str = "llama3.1:8b") -> None:
        """Initialize the judge.

        Args:
            judge_model: Fixed evaluator model name; used when ``score`` is
                called without an explicit ``judge_model``.
        """
        self.judge_model = judge_model

    def score(
        self,
        generated_cases: list[dict],
        reference_cases: list[dict],
        *,
        client: Any = None,
        judge_model: str | None = None,
    ) -> ContentScore | None:
        """Score generated cases against reference cases with an LLM judge.

        Args:
            generated_cases: Canonical, deduplicated generated test cases.
            reference_cases: Canonical, deduplicated reference test cases.
            client: Ollama client; lazily constructed if None.
            judge_model: Overrides the instance's judge model when provided.

        Returns:
            A ``ContentScore``, or None when there are no reference cases.
        """
        if not reference_cases:
            return None
        if not generated_cases:
            return {"precision": None, "recall": 0.0, "f1": 0.0, "quality": None}

        model = judge_model or self.judge_model
        if client is None:
            from src.core.ollama_client import OllamaClient

            client = OllamaClient()

        precision, recall, f1 = self._run_matching(client, model, generated_cases, reference_cases)
        quality = self._run_quality(client, model, generated_cases, reference_cases)
        return {"precision": precision, "recall": recall, "f1": f1, "quality": quality}

    @staticmethod
    def _numbered(cases: list[dict]) -> str:
        """Render cases as a 0-based numbered list for a judge prompt."""
        return "\n".join(
            f"{i}. summary: {tc.get('summary_suffix', '')} | "
            f"preconditions: {tc.get('preconditions', '')} | "
            f"steps: {tc.get('test_steps', '')} | "
            f"expected: {tc.get('expected_result', '')}"
            for i, tc in enumerate(cases)
        )

    @staticmethod
    def _parse(text: str | dict) -> dict | None:
        """Extract a JSON object from a raw model response."""
        raw = text if isinstance(text, str) else json.dumps(text)
        parsed = JSONResponseParser.extract_json_from_response(raw)
        return parsed if isinstance(parsed, dict) else None

    def _run_matching(
        self, client: Any, model: str, generated: list[dict], reference: list[dict]
    ) -> tuple[float | None, float | None, float | None]:
        """Return (precision, recall, f1), or (None, None, None) on any fault."""
        try:
            prompt = _MATCH_PROMPT.format(
                generated=self._numbered(generated), reference=self._numbered(reference)
            )
            text = client.generate_completion(
                model, prompt, is_json=True, return_full_response=False
            )
            parsed = self._parse(text)
            pairs = parsed.get("matches") if parsed else None
            if not isinstance(pairs, list):
                return None, None, None
            matched = self._count_valid_pairs(pairs, len(generated), len(reference))
            return _prf(matched, len(generated), len(reference))
        except Exception:  # noqa: BLE001 - a judge fault must not abort the run
            return None, None, None

    @staticmethod
    def _count_valid_pairs(pairs: list, n_generated: int, n_reference: int) -> int:
        """Count valid, in-range, one-to-one [gen, ref] index pairs."""
        used_gen: set[int] = set()
        used_ref: set[int] = set()
        count = 0
        for pair in pairs:
            if not (isinstance(pair, (list, tuple)) and len(pair) == 2):
                continue
            g, r = pair
            if not (isinstance(g, int) and isinstance(r, int)):
                continue
            if not (0 <= g < n_generated and 0 <= r < n_reference):
                continue
            if g in used_gen or r in used_ref:
                continue
            used_gen.add(g)
            used_ref.add(r)
            count += 1
        return count

    def _run_quality(
        self, client: Any, model: str, generated: list[dict], reference: list[dict]
    ) -> float | None:
        """Return the clamped [0,1] holistic quality, or None on any fault."""
        try:
            prompt = _QUALITY_PROMPT.format(
                generated=self._numbered(generated), reference=self._numbered(reference)
            )
            text = client.generate_completion(
                model, prompt, is_json=True, return_full_response=False
            )
            parsed = self._parse(text)
            if not parsed or "quality" not in parsed:
                return None
            return max(0.0, min(1.0, float(parsed["quality"])))
        except Exception:  # noqa: BLE001 - a judge fault must not abort the run
            return None
