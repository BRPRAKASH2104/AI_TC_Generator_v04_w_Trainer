## Architecture & Dead Code Audit

Date: 2026-04-06

---

### Dead Code / Residual Issues

#### 1. `src/yaml_prompt_manager.py` — `_selection_rules` caching

**PASS with one residual risk.**

- `_selection_rules` is correctly declared in `__slots__` (line 26) and initialised to `None` in `__init__` (line 42).
- `load_all_prompts` sets `self._selection_rules = data.get("prompt_selection", {})` (line 125) when the test generation YAML is found. If the file is missing, `self._selection_rules` is left as `None`.
- `_auto_select_template` guards against that correctly: it falls back to config defaults when `self._selection_rules is None` (lines 218–220).
- **No old disk-read code path survives.** The cache is the only path.

**Residual risk — stale cache on multiple `load_all_prompts` calls.**
`reload_prompts` calls `load_all_prompts` directly (line 326), which overwrites `_selection_rules`. This is safe and intentional. However, `load_all_prompts` is also called from `__init__` (line 45). If any external caller invokes `load_all_prompts()` directly (not through `reload_prompts`), the cache is correctly refreshed. No stale-cache issue exists today, but `load_all_prompts` is a `public` method that does not reset `template_usage_count`, creating an inconsistency if called mid-run. This is not a dead code issue but is a latent API hazard: callers should always use `reload_prompts()` rather than calling `load_all_prompts()` directly.

Action: Make `load_all_prompts` private (`_load_all_prompts`) or document the expected call contract.

---

#### 2. `src/core/ollama_client.py` — throwaway `temp_session` in `_check_version_compatibility`

**FAIL — residual throwaway session at line 835.**

`OllamaClient.__init__` correctly creates `self._session` (line 48) and all main request methods (`generate_completion`, `generate_response_with_vision`, the sync get at line 332, and line 428) use `self._session`. That part of the refactor is complete.

However, `_check_version_compatibility` — which is defined **once** and shared by both `OllamaClient` (line 321) and `AsyncOllamaClient` (line 822) via copy — still creates a throwaway `requests.Session()` at line 835:

```
835:    temp_session = requests.Session()
836:    response = temp_session.get(...)
```

For `OllamaClient` this means the version check leaks a session that is never closed (no `temp_session.close()` call, no context manager). For `AsyncOllamaClient` the use of a synchronous `requests` call inside an async class is intentional (the docstring notes it), but the throwaway session is still a resource leak.

**Fix:** Replace with `with requests.Session() as temp_session:` (requests.Session supports context manager), or — since `OllamaClient` already owns `self._session` — pass the appropriate session as a parameter, or simply call `self._session.get(...)` in the sync variant and keep the throwaway only in the async variant wrapped in a `with` block.

---

#### 3. `src/config.py` — `load_cli_config` and `setattr` loop

**PASS — old `setattr` loop is gone.**

The only `setattr` call remaining is `object.__setattr__` at line 303, which is inside `SecretsConfig.model_post_init` and is unrelated to the `load_cli_config` change. That usage is correct Pydantic practice for mutating a frozen-adjacent field during post-init.

`load_cli_config` now uses the Pydantic `model_validate` round-trip pattern (lines 569–573):

```python
current = self.cli.model_dump()
for key, value in cli_data.items():
    if key in current:
        current[key] = value
self.cli = self.cli.__class__.model_validate(current)
```

**Residual concern — direct mutation of dict sub-fields after `model_validate`.**
Lines 577–581 mutate `self.cli.presets`, `self.cli.environments`, and `self.cli.model_configs` directly on the Pydantic model instance after reassignment:

```python
self.cli.presets.update(config_data["presets"])
```

`CLIConfig` does not set `model_config = ConfigDict(frozen=True)`, so Pydantic V2 allows this. The mutation is safe at runtime but bypasses validation for those sub-keys. If a malformed YAML produces a non-dict value for `presets`, it will silently corrupt the in-memory state rather than raising a `ValidationError`. This is a minor consistency issue, not dead code.

**No other method in `ConfigManager` mutates `self.cli` directly.** `apply_cli_overrides` correctly works on `config_dict` and returns a new instance via `ConfigManager.model_validate(config_dict)` (line 743).

---

#### 4. `tests/` — deleted `test_ollama_compatibility.py`

**PASS — no orphan references found.**

A search across all files in `tests/` found zero imports from `test_ollama_compatibility` and zero references to that module. `tests/conftest.py` imports are clean: it imports only from `tests.helpers` and stdlib/pytest. The integration test directory (`tests/integration/`) contains: `e2e_runner_script.py`, `test_e2e_wrapper.py`, `test_edge_cases.py`, `test_end_to_end.py`, `test_processors.py`, `test_real_integration.py`. None reference the deleted file.

---

#### 5. Root-level stray files

**WARN — two files of concern.**

| File | Status |
|---|---|
| `main.py` | Correct — documented entry point |
| `claude-flow.config.json` | Correct — project tool config, should be in `.gitignore` if not already |
| `REQIFZ_ANALYSIS_REPORT.json` | **Stray output artefact.** No source code generates this filename. It is not listed in `.gitignore` and has no apparent owner. Likely a manually run analysis dump left at root. Should be moved to `output/` or deleted. |
| `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`, `System_Intructions.md` | Expected project documentation |
| `example.md` | Unclear purpose — appears to be a stray scratch file. Review and remove or move to `docs/`. |

---

### Architecture Consistency

#### Check 1: `generate_with_retry` symmetry between `OllamaClient` and `AsyncOllamaClient`

**FAIL — asymmetric.**

`generate_with_retry` exists **only** in `AsyncOllamaClient` (line 789). `OllamaClient` (sync) has no equivalent method. CLAUDE.md states the two clients are supposed to be symmetric. Any caller relying on `generate_with_retry` on the sync client will get an `AttributeError` at runtime. If retry logic is not needed on the sync path, the asymmetry should be explicitly documented; otherwise a sync `generate_with_retry` should be added.

#### Check 2: `load_cli_config` — Pydantic `model_validate` with nested models

**PASS with caveat.**

`CLIConfig` (lines 394–427) contains no nested `BaseModel` sub-fields. Its fields are: `str`, `int`, `bool`, `Path`, `Path | None`, and three `dict[str, dict[str, Any]]` fields (`presets`, `environments`, `model_configs`). Because there are no nested Pydantic model instances inside `CLIConfig`, the `model_validate(current)` round-trip is safe — `model_dump()` on a `CLIConfig` produces plain dicts and scalars that `model_validate` can re-hydrate without loss.

**Caveat:** If `CLIConfig` ever gains a nested `BaseModel` field in future, the `model_dump()` + key-by-key dict merge + `model_validate` pattern will still work correctly because `model_dump()` recursively serialises nested models to dicts. So the pattern is structurally safe going forward.

#### Check 3: `_selection_rules` caching thread-safety for HP (async/concurrent) path

**WARN — not thread-safe, but currently safe in practice.**

`YAMLPromptManager` is instantiated once per processor run and passed as a shared object into `PromptBuilder`. In the HP path (`hp_processor.py`), multiple coroutines call `get_test_prompt()` concurrently, which reads `self._selection_rules` and mutates `self.template_usage_count` and `self.last_selected_template` without any lock.

Python's GIL protects dict `get` and assignment operations from corruption, so there is no data race in CPython. However:
- `self.last_selected_template` can reflect the last writer's value rather than the current coroutine's value — it is functionally unreliable under concurrency.
- `self.template_usage_count` dict updates (`+= 1`) are not atomic across a read-modify-write, which can produce undercounts under high concurrency.

The cached `_selection_rules` dict is read-only after `load_all_prompts`, so it is safe. The risk is in the per-call mutable fields. These are used only for summary/diagnostic output, not for correctness of generated prompts. Severity: low for correctness, medium for diagnostic accuracy.

Action: Either guard `last_selected_template` and `template_usage_count` updates with `threading.Lock`, or switch to per-coroutine tracking and aggregate at the end.

#### Check 4: New `conftest.py` mocking patterns vs. other integration tests

**PASS.**

`tests/conftest.py` uses `unittest.mock.Mock` and `AsyncMock` for `mock_ollama_client` and `mock_async_ollama_client` fixtures. A review of the integration test files shows this is the consistent pattern across `test_processors.py` and `test_end_to_end.py`. The async client fixture correctly adds `__aenter__`/`__aexit__` mocks, matching how `AsyncOllamaClient` is used as an async context manager in `hp_processor.py`. No inconsistency found.

---

### Profile `mode` Field Consistency

#### `profiles/profiles.yaml` — mode values

**PASS.**

All `mode` values in `profiles/profiles.yaml` use `"hp"` or `"standard"`, which match the `CLIConfig.mode` field pattern (`^(standard|hp|training)$` at line 401 of `src/config.py`).

#### `profiles/sample-profiles-edited.yaml` and `profiles/sample-profiles.yaml` — mode values

**FAIL — stale `"high-performance"` mode strings.**

`sample-profiles-edited.yaml` contains `mode: "high-performance"` at lines 42, 52, and 71. `sample-profiles.yaml` contains `mode: "high-performance"` at lines 57, 84, 130, 159, 174, 207, 222, 255, 288, 321, 369, and 385.

`CLIConfig.mode` rejects `"high-performance"` with a Pydantic `ValidationError` (the pattern only allows `standard`, `hp`, or `training`). Any user who loads one of these sample profiles via `--preset` will get a runtime error.

These are labelled "sample" files, but `config/cli_config.yaml` may reference them as examples. They must be updated to `"hp"`.

#### How `mode` is actually used at runtime

The `mode` field from a preset is mapped to `cli.mode` (line 180 of `main.py`). However, `main.py` never branches on `effective_config.cli.mode` to select the processor. The actual branch is the `--hp` CLI flag (line 246: `if hp:`). The `mode` field in `CLIConfig` is stored but **never read back** to drive processor selection. This means:

- Loading a preset with `mode: "hp"` does not automatically enable HP processing; the user must also pass `--hp` (or `--high-performance`).
- The `mode` field in `CLIConfig` is effectively dead configuration data from a control-flow perspective.
- The only live use of the string `"high-performance"` is in log calls (e.g., `main.py:348`, `376`, `396`), which are log metadata, not branching logic.

This is an architectural inconsistency: the profile system implies `mode` controls processing path, but it does not.

---

### Files to Remove or Relocate

| File | Action |
|---|---|
| `/REQIFZ_ANALYSIS_REPORT.json` (root) | Remove or move to `output/`; add to `.gitignore` if auto-generated |
| `/example.md` (root) | Review and remove or move to `docs/`; violates CLAUDE.md rule against stray root files |
| `profiles/sample-profiles.yaml` | Update all `mode: "high-performance"` to `mode: "hp"` (12 occurrences) |
| `profiles/sample-profiles-edited.yaml` | Update all `mode: "high-performance"` to `mode: "hp"` (3 occurrences) |

---

### All Clear

The following items reviewed cleanly with no issues:

- `YAMLPromptManager.__slots__` and `__init__` correctly declare and initialise `_selection_rules: dict | None = None`.
- The old disk-read code path in `_auto_select_template` is fully removed; only the cache path remains.
- `load_cli_config` old `setattr` loop is completely gone. `object.__setattr__` at line 303 is an unrelated, correct Pydantic pattern in `SecretsConfig`.
- No other method in `ConfigManager` mutates `self.cli` directly except `load_cli_config`.
- The deleted `tests/integration/test_ollama_compatibility.py` has zero remaining references across the test suite.
- `tests/conftest.py` imports are clean; `mock_async_ollama_client` correctly mocks `__aenter__`/`__aexit__` to match the context-manager protocol.
- `profiles/profiles.yaml` (the active profile file) uses only valid mode strings (`"hp"`, `"standard"`).
- `OllamaClient` main request methods (lines 101, 264, 332, 428) all use `self._session`; the session refactor is complete for those call sites.
- `CLIConfig` contains no nested Pydantic `BaseModel` fields, so the `model_validate` round-trip in `load_cli_config` is safe today and remains safe if only primitive/dict fields are added.
- `AsyncOllamaClient.__slots__` and `__init__` mirror `OllamaClient` for `_version_validated` and `_available_features`.
