## Code Audit — Recent Changes

### Test Results

159 passed, 1 failed, 14 skipped (7.68s)

Failing test: `tests/integration/test_end_to_end.py::TestEndToEndWorkflows::test_standard_mode_complete_workflow`

---

### Issues Found

#### ISSUE 1 — BUG (test failure): Wrong mock return type in end-to-end test
**File:** `tests/integration/test_end_to_end.py:85`

The mock is set up as:
```python
mock_client.generate_completion.return_value = (json.dumps(mock_ai_response), 0.99)
```
This returns a **tuple** `(str, float)`. The real `OllamaClient.generate_completion` returns a **dict** (the full Ollama JSON object, e.g. `{"response": "...", "done": true, ...}`). In `TestCaseGenerator.generate_test_cases_for_requirement` (generators.py:173), the code branches on `isinstance(full_response, dict)`. A tuple is not a dict, so the code takes the `else` branch and calls `str(full_response)`, producing `"('[{\"test_cases\": ...}]', 0.99)"` — invalid JSON. The subsequent regex-based JSON extraction in `FastJSONResponseParser` then fails with `"expected string or bytes-like object, got 'list'"` because the stringified tuple is not a recognisable JSON structure.

The mock should be:
```python
mock_client.generate_completion.return_value = {"response": json.dumps(mock_ai_response), "done": True}
```

This is a **regression introduced alongside the recent changes** — the mock was not updated when `generate_completion` was changed to return the full response dict rather than a `(text, confidence)` tuple.

#### ISSUE 2 — BUG (pre-existing, exposed by e2e test): Real `heading` field is raw XHTML in production, not plain text
**File:** `src/processors/base_processor.py:133`

When processing a real `.reqifz` file, the extractor returns `text` values as raw serialised XML strings:
```
<ns0:THE-VALUE xmlns:html="..." xmlns:ns0="..."><html:p>Door Control System...</html:p></ns0:THE-VALUE>
```
`_build_augmented_requirements` sets `current_heading = obj.get("text", "No Heading")` directly from this raw field. The augmented requirement then carries a multi-line XML blob as its `heading`. This raw XML blob is passed into `PromptBuilder._build_from_template` and `_build_default`, making the heading unreadable in the generated prompt, and it is what the standard_processor logs verbatim in the "Processing requirement" info line.

The `_clean_text_for_logging` static method already exists on `BaseProcessor` (line 62) and correctly strips XML tags — it is used for the `debug` log at line 135 but the `heading` stored in `augmented_requirement` at line 162 is never cleaned. The prompt builder and downstream formatter receive the raw XHTML blob. Unit tests in `TestContextAwareProcessing` pass only because `create_test_heading` stores a pre-cleaned `text` field that is already legible — they do not reproduce the production extractor's XHTML output.

#### ISSUE 3 — MISSING FIX: `AsyncOllamaClient` has no `generate_with_retry` equivalent for `OllamaModelNotFoundError`; the fix exists only in the async client
**File:** `src/core/ollama_client.py:789–820`

The changelog says `generate_with_retry` now re-raises non-retriable exceptions. Looking at the file, `generate_with_retry` exists **only** on `AsyncOllamaClient` (line 789). The synchronous `OllamaClient` class has no `generate_with_retry` method at all — so the "fix" only applies to the async path. This is not a regression, but the audit question was specifically whether the async-only fix was intentional or an oversight. Given both classes share common logic (e.g. `_check_version_compatibility`), the absence of a sync counterpart is an asymmetry worth flagging. If callers of the sync client ever need retry-with-non-retriable-bypass, they have no supported path.

#### ISSUE 4 — EDGE CASE: `load_cli_config` silently ignores unknown YAML keys
**File:** `src/config.py:569–573`

```python
current = self.cli.model_dump()
for key, value in cli_data.items():
    if key in current:
        current[key] = value
self.cli = self.cli.__class__.model_validate(current)
```
The `if key in current` guard is correct — unknown keys from YAML are filtered before `model_validate`. However, `model_dump()` serialises `Path` fields (e.g. `input_directory`, `output_directory`) as `PosixPath` objects, not strings. When these are re-validated by `model_validate`, Pydantic re-coerces them correctly, so this is not a crash. But if a YAML file contains `input_directory: /some/path` (string), it replaces the `PosixPath` value with a string before `model_validate` re-coerces it — this works. Edge case is benign but worth noting.

#### ISSUE 5 — EDGE CASE: `_selection_rules` cache is stale after `reload_prompts()`
**File:** `src/yaml_prompt_manager.py:324–327`

`reload_prompts()` calls `load_all_prompts()`. `load_all_prompts()` at line 125 sets `self._selection_rules = data.get("prompt_selection", {})` when the file loads successfully, but if the file load **fails** (exception path at line 131), `self._selection_rules` is left at its previous cached value rather than being reset. This means after a failed reload, `_auto_select_template` continues using stale rules silently. The fix would be to set `self._selection_rules = None` before attempting the load, or inside the `except` block.

Additionally, `reload_prompts()` never resets `_selection_rules` to `None` before calling `load_all_prompts()`, so a reload that removes the `prompt_selection` key from the YAML file (returning `{}`) would store `{}` correctly — but an exception mid-reload leaves the old dict in place.

#### ISSUE 6 — SECURITY NOTE: `SecretsConfig.model_post_init` uses `object.__setattr__` on a non-frozen model
**File:** `src/config.py:303`

`SecretsConfig` is a plain `BaseModel` (not `model_config = ConfigDict(frozen=True)`). Using `object.__setattr__` to bypass Pydantic's normal assignment is unnecessary here — normal attribute assignment (`self.field_name = value`) works on unfrozen models. The `object.__setattr__` pattern is the correct Pydantic idiom exclusively for **frozen** models (where `self.field_name = value` would raise `ValidationError`). Using it on an unfrozen model bypasses Pydantic's field validators and `model_validators` for the assigned fields, which means if a secret value were to contain an invalid type, Pydantic would not catch it.

This is low severity (all values are `str | None` with no additional validators), but the approach is misleading and inconsistent with the unfrozen model config. Normal assignment should be used instead.

---

### Confirmed Correct

- **`src/app_logger.py:25`** — Forward reference `"AppLogger | None"` is the correct form for a module-level annotation that refers to a class defined later in the same file. The fix is valid and necessary.

- **`src/config.py:573`** — `model_validate(current)` correctly replaces the former `**current` or `parse_obj` patterns. Pydantic v2 `model_validate` accepts a dict and runs full field coercion and validators, which is the right approach here.

- **`src/core/ollama_client.py:789–820`** (`AsyncOllamaClient.generate_with_retry`) — The non-retriable re-raise pattern is correct. `except non_retriable: raise` re-raises before the generic `except Exception` clause captures it, and `last_exception` is re-raised after exhausted retries. The empty-response fallback `return ""` at line 820 is safe (all retries returned empty without raising).

- **`src/core/ollama_client.py:416–474`** (`OllamaClient.get_model_info`) — Using `self._session` (the persistent `requests.Session`) instead of a new session per call is correct and consistent with `generate_completion`. The docstring still says "async client" at line 418 — minor copy-paste artefact, not a functional issue.

- **`src/yaml_prompt_manager.py:124–125`** — Caching `_selection_rules` during `load_all_prompts()` is correct. It avoids a disk read on every call to `_auto_select_template`. The `None` sentinel check at line 218 provides a clean fallback to config defaults when the file was not found.

- **`tests/conftest.py`** — `mock_async_ollama_client` being an `AsyncMock` is correct. The explicit `__aenter__`/`__aexit__` setup ensures the fixture works when the client is used as an async context manager. `mock_client.generate_response = AsyncMock(return_value=_response)` correctly overrides the method on the `AsyncMock` base.

- **`tests/core/test_base_processor.py` (`TestContextAwareProcessing`)** — Migration to XHTML helpers is internally consistent: `create_test_heading`, `create_test_information`, and `create_test_requirement` all produce the same XHTML-wrapped `text` format, so assertions using `in req["info_list"][0]["text"]` correctly search within the XHTML string. Tests pass (159 pass).

- **`tests/integration/test_processors.py`** (`TestHighPerformanceREQIFZFileProcessor.test_process_file_success`) — Un-skipping is valid. The test correctly mocks all four HP processor dependencies, uses `AsyncMock` for `generate_test_cases`, and the split assert (`result["success"] is True`, `result["total_test_cases"] == 2`) is clearer than a compound assert.
