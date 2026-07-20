"""Tests for large-table chunking in the generator (archived finding 7).

Oversized tables are split into row-chunks that each fit the prompt row limit;
every chunk is generated independently and the results are merged, so all rows
are covered instead of silently sampled.
"""

import json
from unittest.mock import AsyncMock, MagicMock

from src.core.generators import AsyncTestCaseGenerator, TestCaseGenerator


def _generator(max_rows=2):
    gen = TestCaseGenerator(client=MagicMock(), yaml_manager=None)
    gen.prompt_builder.max_table_rows = max_rows
    return gen


def _table(n_rows):
    return {"rows": n_rows, "data": [{"In": str(i), "Out": str(i)} for i in range(n_rows)]}


# Deliberately dissimilar test cases so the fuzzy deduplicator (0.85 threshold)
# does not collapse them; each covers an unrelated scenario.
_THEMES = {
    "a": (
        "Nominal lock",
        "1) Enable ignition, set speed 15 kmph, command door lock",
        "Doors lock within 200 ms",
    ),
    "b": (
        "Low voltage",
        "1) Reduce battery to 8 volts and request unlock sequence",
        "System enters limp-home and rejects the unlock",
    ),
    "c": (
        "Invalid frame",
        "1) Inject a malformed CAN message on the lock bus",
        "Diagnostic trouble code P1234 is logged",
    ),
    "chunk1": (
        "Alpha path",
        "1) Apply stimulus alpha across every wheel sensor",
        "Alpha outputs equal the reference alpha table",
    ),
    "chunk2": (
        "Bravo path",
        "1) Trigger bravo fault injection on the LIN network",
        "Bravo recovery completes without a controller reset",
    ),
    "chunk3": (
        "Gamma path",
        "1) Sweep the gamma parameter from minimum to maximum bound",
        "Gamma response stays inside the tolerance band",
    ),
}


def _tc(step):
    summary, steps, expected = _THEMES[step]
    return {
        "summary_suffix": summary,
        "preconditions": "12V",
        "test_steps": steps,
        "expected_result": expected,
        "test_type": "positive",
    }


# --------------------------------------------------------------------------- #
# _split_oversized_table
# --------------------------------------------------------------------------- #


def test_no_table_returns_none():
    assert _generator()._split_oversized_table({"id": "R", "text": "x"}) is None


def test_small_table_not_split():
    gen = _generator(max_rows=10)
    assert gen._split_oversized_table({"id": "R", "table": _table(5)}) is None


def test_oversized_table_split_preserves_all_rows():
    gen = _generator(max_rows=2)
    chunks = gen._split_oversized_table({"id": "R", "table": _table(5)})
    assert chunks is not None
    # 5 rows / 2 -> chunks of 2, 2, 1
    assert [len(c["table"]["data"]) for c in chunks] == [2, 2, 1]
    assert [c["table"]["rows"] for c in chunks] == [2, 2, 1]
    # Every original row appears exactly once across the chunks, in order.
    flattened = [row for c in chunks for row in c["table"]["data"]]
    assert flattened == _table(5)["data"]


def test_chunks_keep_other_requirement_fields():
    gen = _generator(max_rows=2)
    chunks = gen._split_oversized_table({"id": "R", "heading": "H", "table": _table(3)})
    assert all(c["id"] == "R" and c["heading"] == "H" for c in chunks)


# --------------------------------------------------------------------------- #
# _merge_chunk_results
# --------------------------------------------------------------------------- #


def test_merge_flattens_and_renumbers():
    gen = _generator()
    merged = gen._merge_chunk_results("R", [[_tc("a"), _tc("b")], [_tc("c")]])
    assert isinstance(merged, list)
    assert [tc["test_id"] for tc in merged] == ["R_TC_001", "R_TC_002", "R_TC_003"]
    assert all(tc["requirement_id"] == "R" for tc in merged)


def test_merge_partial_failure_keeps_successes():
    gen = _generator()
    error = {"error": True, "requirement_id": "R", "error_type": "EmptyResponse"}
    merged = gen._merge_chunk_results("R", [[_tc("a")], error])
    assert isinstance(merged, list)
    assert len(merged) == 1


def test_merge_all_failed_returns_error():
    gen = _generator()
    err = {"error": True, "error_type": "EmptyResponse"}
    result = gen._merge_chunk_results("R", [err, err])
    assert isinstance(result, dict)
    assert result["error"] is True
    assert result["error_type"] == "AllChunksFailed"


# --------------------------------------------------------------------------- #
# End-to-end: oversized table generates per chunk and merges
# --------------------------------------------------------------------------- #


def test_oversized_table_generates_per_chunk_and_merges():
    gen = _generator(max_rows=2)
    # Distinct response per chunk so dedup keeps them; 5 rows -> 3 chunks.
    gen.client.generate_completion.side_effect = [
        json.dumps({"test_cases": [_tc("chunk1")]}),
        json.dumps({"test_cases": [_tc("chunk2")]}),
        json.dumps({"test_cases": [_tc("chunk3")]}),
    ]

    result = gen.generate_test_cases_for_requirement(
        {"id": "REQ_1", "text": "req", "table": _table(5)}, model="m"
    )

    assert gen.client.generate_completion.call_count == 3
    assert isinstance(result, list)
    assert len(result) == 3
    assert [tc["test_id"] for tc in result] == ["REQ_1_TC_001", "REQ_1_TC_002", "REQ_1_TC_003"]


async def test_async_oversized_table_generates_per_chunk_and_merges():
    client = MagicMock()
    client.generate_completion = AsyncMock(
        side_effect=[
            json.dumps({"test_cases": [_tc("chunk1")]}),
            json.dumps({"test_cases": [_tc("chunk2")]}),
            json.dumps({"test_cases": [_tc("chunk3")]}),
        ]
    )
    gen = AsyncTestCaseGenerator(client=client, yaml_manager=None)
    gen.prompt_builder.max_table_rows = 2

    result = await gen._generate_test_cases_for_requirement_async(
        {"id": "REQ_1", "text": "req", "table": _table(5)}, model="m"
    )

    assert client.generate_completion.await_count == 3
    assert isinstance(result, list)
    assert len(result) == 3
    assert [tc["test_id"] for tc in result] == ["REQ_1_TC_001", "REQ_1_TC_002", "REQ_1_TC_003"]
