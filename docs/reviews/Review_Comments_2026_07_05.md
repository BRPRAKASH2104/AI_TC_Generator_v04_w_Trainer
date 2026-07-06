# Code Review — Full Codebase Audit

**Date:** 2026-07-05
**Scope:** All of `src/`, `main.py`, `prompts/` (templates + config), `profiles/`
**Focus:** Coding inconsistencies, execution efficiency, prompt quality
**Method:** Full read of core modules; every finding verified by tracing call sites (grep) before being reported.

---

## Executive Summary

The architecture is sound (clean processor/generator/formatter separation, good exception taxonomy, Pydantic config). However, the review found:

- **3 high-impact correctness bugs**, the worst being that the **deduplicator silently deletes distinct test cases** because it compares fields the active prompt schema doesn't produce.
- **1 high-impact efficiency bug**: `--max-concurrent` has **no effect** — HP mode is hard-capped at 2 concurrent Ollama requests.
- **A schema split across the prompt layer**: two templates emit two different test-case field sets (`preconditions`/`test_steps` vs `action`/`data`), and downstream components (dedup, validator, parser) are each keyed to a different one.
- **Vision prompt guidance is silently dropped**: `image_context` is built and passed but no YAML template contains an `{image_context}` placeholder.
- Significant **dead code and config drift** (unwired relationship parsing, unwired `profiles/profiles.yaml`, unimplemented prompt-config features, unused Secrets/Validation/Deduplication config sections).

Findings are ordered by severity within each section, with file:line references.

---

## 1. Correctness Bugs (fix first)

### 1.1 Deduplicator compares the wrong fields → false-positive deletion of test cases ⚠️ CRITICAL

`TestCaseDeduplicator` defaults to `fields_to_compare = ["action", "data", "expected_result"]` (`src/core/deduplicator.py:39`). But the **active** template (`adaptive_default`, the only one loaded per `prompts/config/prompt_config.yaml`) instructs the model to emit `preconditions` / `test_steps` — not `action` / `data`.

Consequence: for any two generated test cases, `action` and `data` are both empty on both sides, which `_calculate_similarity` scores as **1.0 each** (`deduplicator.py:134-136`). The average similarity is `(1.0 + 1.0 + sim(expected_result)) / 3`, so any two test cases whose expected results are only **≥ 0.55 similar** cross the 0.85 duplicate threshold and one is deleted. Table-row tests ("Verify OutputX = 1" vs "Verify OutputX = 2") are exactly this shape — **legitimate row-coverage tests are being silently removed**, which then triggers the "Inadequate table coverage" warnings downstream.

**Fix:** compare the canonical fields with fallback, e.g. `["test_steps", "expected_result", "preconditions"]` or normalize field names before dedup (see §3.1). Also treat "both fields empty" as *neutral* (skip) rather than similarity 1.0.

### 1.2 `validation_passed` flag is computed wrong, and against the wrong list

In both generators (`src/core/generators.py:237-239` and `528-530`):

```python
is_valid = i >= len(validation_report["issues"]) or all(
    entry["test_case_index"] != i + 1 for entry in validation_report["issues"]
)
```

Two defects:
1. The first clause is simply wrong: `issues` is a *list of failing entries*, not index-aligned. Example: 10 test cases, one issue with `test_case_index = 8`. For `i = 7` (test case 8), `7 >= 1` is `True`, so the failing test case is marked `validation_passed = True`. Only the `all(...)` clause is correct — delete the first clause.
2. Validation indices are computed **before** deduplication, but applied to the **post-dedup** list (`generators.py:221-240`). Once dedup removes an item, every subsequent index shifts and the flags land on the wrong test cases. Either validate after dedup, or stamp `validation_passed` on each test-case dict *before* dedup runs.

Related: the dedup "best" strategy scores by `validation_passed` (`deduplicator.py:210`), which is only stamped *after* dedup — so that criterion is always `False` and dead. Stamping before dedup fixes this too.

### 1.3 HP `process_directory` races on shared instance state

`HighPerformanceREQIFZFileProcessor.process_directory` (`src/processors/hp_processor.py:64-89`) gathers `process_file` for all files **concurrently on one instance**, but `process_file` reassigns `self.logger`, `self.extractor`, `self.formatter` and mutates the shared `self.metrics` dict (`hp_processor.py:112-120`). With ≥2 REQIFZ files, logs interleave into the wrong file logger, metrics are cross-contaminated, and `metrics["start_time"]` is overwritten mid-flight. Also, `metrics` is never reset between files even sequentially.

**Fix:** either process files sequentially in `process_directory`, or make per-file state local (create logger/extractor/formatter/metrics inside `process_file` and pass them down).

### 1.4 Unknown signals in `test_steps` pass silently (validator asymmetry)

`_validate_signals` (`src/core/validators.py:140-148`): for the data/test_steps field, an issue is appended **only when a fuzzy close-match exists**. A hallucinated signal with *no* close match is not flagged at all — the opposite of the `action`-field branch (`validators.py:118-132`), which flags both cases. And since the active schema has no `action` field, the strict branch never runs. Net effect: signal-name validation is mostly a no-op today.

### 1.5 Mixed `<th>`/`<td>` rows lose cells in table parsing

`HTMLTableParser._parse_single_table` uses `row.findall(".//th") or row.findall(".//td")` (`src/core/parsers.py:188, 206`). A row containing both header and data cells (common in REQIF exports with row-label headers) keeps only the `th` cells and drops all `td` content. Collect both: `row.findall(".//th") + row.findall(".//td")`.

### 1.6 Divergent static defaults: formatter vs config

`_get_default_test_values` hardcodes v03 defaults — `test_type="RoboFit"`, `components="Infotainment"`, `labels="SYS_DI_VALIDATION_TEST"` (`src/core/formatters.py:159-168`) — while `StaticTestConfig` says `"PROVEtech"`, `"SW_DI_FV"`, `"AI Generated TCs"` (`src/config.py:132-147`). Config wins at runtime, so the formatter constants are misleading dead values that will resurface if anyone constructs the formatter without config. Keep one source of truth (config) and drop the duplicate literals. Note also `defaults.update(metadata)` (`formatters.py:196`) injects unrelated keys (`model`, `source_file`, …) into the defaults dict — harmless today, but fragile.

---

## 2. Execution Efficiency

### 2.1 `--max-concurrent` is ignored — HP mode capped at 2 concurrent requests ⚠️ HIGH

Trace:
- CLI `--max-concurrent` → `ollama.concurrent_requests` (`src/config.py:671-672`) → `HighPerformanceREQIFZFileProcessor(config, max_concurrent)` (`main.py:339-343`).
- The processor passes it to `AsyncTestCaseGenerator(_max_concurrent=…)` — a parameter that is **deliberately unused** (`src/core/generators.py:279, 287-288`: "Concurrency limiting is handled by AsyncOllamaClient's semaphore").
- But the semaphore is built from **`gpu_concurrency_limit`** (default **2**), not `concurrent_requests` (`src/core/ollama_client.py:504-505`).

So `ai-tc-generator input/ --hp --max-concurrent 4` prints "⚡ Concurrency: 4" but actually runs 2-wide. `concurrent_requests` and `cpu_concurrency_limit` are wired to nothing.

**Fix:** pass the effective concurrency into `AsyncOllamaClient` (e.g. `Semaphore(config.concurrent_requests)`), or map the CLI flag onto `gpu_concurrency_limit`. Then delete the unused `_max_concurrent` parameter.

### 2.2 "Parallel" XML extraction is GIL-bound — overhead without speedup

`HighPerformanceREQIFArtifactExtractor` fans `ElementTree` spec-object extraction across a `ThreadPoolExecutor` (`src/core/extractors.py:753-846`). `xml.etree` element traversal is pure-Python and GIL-bound, so threads serialize; the batching/future machinery adds overhead and shares non-thread-safe `Element` objects across threads. Recommend reverting HP extraction to the sequential path (it's already fast) and deleting `_process_spec_objects_concurrent`/`_process_spec_object_batch` — the real HP win is the async Ollama calls, not XML threading.

### 2.3 Blocking call inside the async event loop

`_monitor_performance` calls `process.cpu_percent(interval=0.1)` (`src/processors/hp_processor.py:408`), which **blocks the event loop for 100 ms every 500 ms** (~20% of loop time) while generation tasks are in flight. Use `cpu_percent(interval=None)` (non-blocking, compares to previous call).

### 2.4 Signal-name extraction recomputed per test case

`SemanticValidator.validate_batch` calls `validate_test_case` per test case, and each call re-runs `_extract_signal_names` over the *entire* interface list (`src/core/validators.py:51`). For N test cases × M interfaces that's N×M regex passes; extract once in `validate_batch` and pass the set down.

### 2.5 Prompt bloat: full interface dictionary in every prompt

Every requirement's prompt embeds the *entire* system interface dictionary (`base_processor.py:173`, `prompt_builder.py:68`). For large REQIF files this dominates the 16K context and slows every generation. Consider filtering interfaces to those whose names appear in the requirement/info text, with a cap.

### 2.6 Streaming parser is dead weight

`_parse_reqif_xml_streaming` + `_build_mappings_streaming` (`extractors.py:437-546`) run **two full `iterparse` passes** over an XML byte string that is already fully in memory — and `use_streaming=True` is never set anywhere (standard processor passes `False`, HP uses the parallel path). Either wire it up for genuinely large files or remove it.

### 2.7 Resource hygiene

- `OllamaClient._session` (`requests.Session`) is never closed — add `close()`/context-manager support (`src/core/ollama_client.py:48`).
- Async `_check_version_compatibility` uses blocking `requests` inside an async class (`ollama_client.py:833-840`) — if ever called from the loop it would stall it; it is currently never called (see §5).

---

## 3. Coding Inconsistencies

### 3.1 One pipeline, three test-case schemas

| Component | Fields it expects/produces |
|---|---|
| `adaptive_default` template (ACTIVE) + `PromptBuilder._build_default` | `summary_suffix`, `preconditions`, `test_steps`, `expected_result`, `test_type` |
| `driver_information_default` template (inactive) | `summary_suffix`, `action`, `data`, `expected_result`, `test_type` |
| `JSONResponseParser.validate_test_cases_structure` (`parsers.py:91`) | `summary`, `action`, `data`, `expected_result` — matches **neither** |
| `TestCaseDeduplicator` default fields | `action`, `data`, `expected_result` (§1.1) |
| `SemanticValidator` | checks `action`, falls back `data`→`test_steps` |
| `TestCaseFormatter` | tries every historical name with fallback chains (`formatters.py:97-127`) |

**Recommendation:** define one canonical schema (suggest the active `preconditions`/`test_steps` one) as constants in a single module, normalize AI output to it in **one place** right after JSON parsing (the generators), and strip the multi-name fallbacks from formatter/validator/dedup. This one change eliminates §1.1, §1.4, and a whole category of future bugs.

### 3.2 ~150 lines duplicated between sync and async generators

`TestCaseGenerator.generate_test_cases_for_requirement` and `AsyncTestCaseGenerator._generate_test_cases_for_requirement_async` (`src/core/generators.py:130-264` vs `385-578`) duplicate the entire parse→validate→dedup→enrich pipeline, and have already drifted:
- sync logs table coverage (`generators.py:200-218`), async doesn't;
- sync returns `[]` on failure, async returns structured error dicts — so the two modes report failures differently.

Extract a shared `_postprocess_response(response_text, requirement, generation_time)` used by both, and standardize on the structured-error return.

### 3.3 Ollama client: 4 near-identical request blocks

`generate_completion` and `generate_response_with_vision` ×(sync, async) each rebuild the same payload and the same 5-branch exception ladder (`ollama_client.py:55-157, 175-319, 538-632, 651-787`). `generate_response_with_vision` is a strict superset — `generate_completion` can delegate to it with `image_paths=None`. Additional inconsistencies in the same file:
- Sampling params `top_k=40, top_p=0.9, repeat_penalty=1.1` hardcoded in all 4 payloads while `tfs_z`/`typical_p`/`repeat_last_n` come from config — move all to `OllamaConfig`.
- `_check_version_compatibility` duplicated verbatim in both classes (`321-396` vs `822-900`).
- Copy-paste docstrings: `get_model_info` / `validate_model_compatibility` on the **sync** client say "(async client)" (`416-425, 476-485`).
- `ConfigManager` imported but unused; `OllamaConfig` imported at module level, in `TYPE_CHECKING`, *and* locally in both `__init__`s (`18, 28, 43, 499`).

### 3.4 Sync vs HP output naming and error text drift

- Standard output: `{stem}_TCD_{model}_{ts}.xlsx` (`base_processor.py:206`); HP: `{stem}_TCD_HP_{model}_{ts}.xlsx` via a duplicated method (`hp_processor.py:373-384`). CLAUDE.md documents `{filename}_TCD_{mode}_{model}_{timestamp}` — standard mode emits no mode token. Parameterize `_generate_output_path(mode_tag=…)` and delete the HP copy.
- HP error message "No System Requirements **with tables** found" (`hp_processor.py:139`) is stale — the tables-only filter was removed (see `base_processor.py:154`).

### 3.5 `print()` bypasses the structured logging system

`src/config.py` (55 call sites) and `src/yaml_prompt_manager.py` (10) print directly to stdout while the rest of the app uses structured JSON logging via `app_logger`. Template-selection messages ("❌ Template not found…") never reach the log files. Route through `logging`/`app_logger`.

### 3.6 CLI `--model` sentinel bug

`main.py:213`: `model=model if model != "llama3.1:8b" else None` — a user who *explicitly* passes `--model llama3.1:8b` is treated as "didn't specify," so a preset's model silently wins. Use a `None` default on the click option and resolve the default later (the code's own CAUTION comment at `main.py:214-218` acknowledges this).

### 3.7 Speculative code left in production

`calculate_confidence` (`generators.py:56-107`) is written against a guessed Ollama logprobs format ("CAUTION: This is speculative based on common patterns"). If the guess is wrong it returns `None` (safe), but the Description column then reads "Confidence Score: N/A" for every row. Verify the actual response shape from the pinned Ollama version and either implement it firmly or drop the feature flag `enable_logprobs` default to `False`. Also note the crash risk `f"...{value:.2f}"` if a non-float ever lands in `confidence_score` (`formatters.py:137`).

---

## 4. Prompt Review

### 4.1 `image_context` never reaches the model ⚠️ HIGH (vision quality)

`PromptBuilder._build_from_template` builds a rich `image_context` block (diagram-type analysis instructions, `prompt_builder.py:70, 258-301`) and passes it as a template variable — but **no YAML template contains `{image_context}`** (verified by grep across `prompts/`). Since a `yaml_manager` is always supplied, the template path is always taken and the vision guidance is silently discarded; images are attached with no instructions on how to analyze them. The guidance only survives in the rarely-used hardcoded fallback prompt.

**Fix:** add an `## VISUAL DIAGRAMS:\n{image_context}` section to `adaptive_default` and declare it in the template's optional variables with default `"No diagrams or images provided."`.

### 4.2 Table truncation contradicts the coverage mandate

`format_table` shows only the first 10 + last 10 rows for tables >50 rows (`prompt_builder.py:199-213`), while the template demands "Generate EXACTLY one positive test case for EACH displayed table row … Total positive test cases: MUST equal {row_count}" (`test_generation_adaptive.yaml:109-133`). For a 60-row table the model literally cannot see rows 11–50, guaranteeing coverage-validation warnings. Either show all rows up to `max_table_rows` (config already has this knob at `config.py:244`, also unwired), or adjust the prompt to say coverage is required only for displayed rows and chunk large tables into multiple generation calls.

### 4.3 Invalid JSON inside the JSON example

The example test case embeds `"preconditions": "{voltage_precondition}"`, and the default value contains a **real newline** (`"1. Voltage= 12V\n2. Bat-ON"` in YAML double-quoted scalar). After substitution the example JSON in the prompt contains a raw line break inside a string literal — an invalid-JSON exemplar shown to a model that is told "Your ENTIRE response MUST be valid JSON." Escape it (`1. Voltage= 12V\\n2. Bat-ON`) or move the value out of the example.

### 4.4 Duplicated/contradictory instructions (prompt length)

`adaptive_default` states the row-coverage rule three times (STEP 3 header, "COMPLETE COVERAGE CHECK", and CRITICAL REQUIREMENTS #3) and mixes two count rules ("EXACTLY one per row" vs "5-13 total test cases"). For an 8B model, shorter and single-voiced instructions measurably improve compliance. Suggested trims: state coverage once in CRITICAL REQUIREMENTS; drop the STEP 2 technique catalog for table-based requirements (the technique is forced anyway).

### 4.5 Dead prompt machinery and config drift

- **Selection rules mismatch:** `_auto_select_template` looks for `heading_keywords` / `requirement_id_patterns` (`yaml_prompt_manager.py:224-239`) — neither template file defines them; meanwhile both files define `model_preferences`, which no code reads. Auto-selection therefore always returns the default template. Delete one side or implement the other.
- **`prompt_config.yaml` advertises unimplemented features:** confidence thresholds, hot_reload, caching, template-performance monitoring, log file paths (`prompt_config.yaml` sections `auto_selection.confidence_thresholds`, `caching`, `logging`, `development`) — none are read by `YAMLPromptManager`. Prune to what's real.
- **`error_handling.yaml` doesn't exist** though referenced by config; `get_error_prompt` is also never called. Remove both.
- **`test_generation_v3_structured.yaml` is unreachable** (config loads only the adaptive file), its header misidentifies itself as `test_generation.yaml`, and it carries the conflicting `action`/`data` schema (§3.1). Archive it under `prompts/backups/` or delete it.
- **`prompt_config.yaml` `model_configurations.max_context_length: 4000`** contradicts `OllamaConfig.num_ctx = 16384` — neither reads the other.
- `_substitute_variables` uses sequential `str.replace` (`yaml_prompt_manager.py:282-291`): if one variable's *value* contains `{another_var}` (e.g. requirement text with literal braces), it gets substituted too. Use a single-pass `re.sub` over `\{(\w+)\}` with a lookup.

### 4.6 `profiles/profiles.yaml` is entirely unwired

CLAUDE.md documents `--profile Llama31.HP.Quality`, but `main.py` has only `--preset` (which reads `config/cli_config.yaml` presets), and **no code references `profiles/`** (verified by grep). The profiles also reference five templates (`default-v2`, `telltale-v3`, `validation-comprehensive`, `automotive-ecu-v3`, `development-quick-v1`) that don't exist — only `adaptive_default` does. Either implement `--profile` (parse `Model.Mode.Modifier`, map onto config) or delete `profiles/` and the CLAUDE.md section.

---

## 5. Dead Code Inventory

Verified unreferenced from `src/`, `main.py`, `utilities/` (check `tests/` before deleting):

| Symbol | Location | Note |
|---|---|---|
| `AsyncTestCaseGenerator.generate_test_cases_batch` | `generators.py:311-383` | HP processor uses TaskGroup + `generate_test_cases` instead |
| `AsyncOllamaClient.generate_with_retry` | `ollama_client.py:789-820` | never called; `OllamaConfig.max_retries` therefore also unused |
| `get_model_info`, `validate_model_compatibility` | `ollama_client.py:416-490` | unused |
| `is_feature_available`, `_check_version_compatibility` (both classes) | `ollama_client.py:321-414, 822-918` | version gate never invoked |
| `JSONResponseParser.validate_test_cases_structure` | `parsers.py:80-97` | unused, wrong schema anyway |
| `TestCaseFormatter._build_description` | `formatters.py:211-235` | unused |
| `TestCaseDeduplicator.find_similar_pairs` | `deduplicator.py:244-280` | unused |
| `YAMLPromptManager.get_error_prompt`, `reset_template_usage`, `get_template_usage_summary`, `get_template_info` | `yaml_prompt_manager.py` | unused |
| `parse_and_augment_relationships` + `RequirementRelationshipParser` pipeline hookup | `extractors.py:561-660` | **feature never invoked** by any processor despite `RelationshipConfig.enable_relationship_parsing=True` and CLAUDE.md documenting it in the architecture diagram — wire it into `_extract_artifacts` or mark the config/doc accordingly |
| `_parse_reqif_xml_streaming` + helpers | `extractors.py:437-546` | `use_streaming` never `True` |
| `ValidationConfig`, `DeduplicationConfig` | `config.py:154-188` | never passed to `SemanticValidator`/`TestCaseDeduplicator`; thresholds, enable flags, `keep_strategy`, `fields_to_compare` all ignored (generators hardcode `keep_strategy="best"`, `generators.py:222`) — wiring these also fixes §1.1 |
| `SecretsConfig` AWS/Azure/Slack/GitHub fields, `validate_secrets_for_mode`, `get_secrets_status` | `config.py:251-331, 766-809` | local-only tool; YAGNI |
| `--training` mode | `main.py:147-154` | prints a stub and exits, while real RAFT collection happens via config flags in normal runs — remove the flag or make it set `training.enable_raft` |

---

## 6. Prioritized Recommendations

**P0 — correctness (small diffs, big effect)**
1. Fix dedup field names / add schema normalization (§1.1, §3.1).
2. Fix `validation_passed` logic and stamp it before dedup (§1.2).
3. Wire `--max-concurrent` to the actual semaphore (§2.1).
4. Serialize or isolate HP `process_directory` state (§1.3).

**P1 — prompt quality**
5. Add `{image_context}` to the adaptive template (§4.1).
6. Resolve table-truncation vs full-coverage contradiction (§4.2); escape `voltage_precondition` newline (§4.3).
7. Fix the silent-pass branch in signal validation (§1.4).

**P2 — consolidation**
8. Extract shared post-processing from the two generators (§3.2); collapse the 4 Ollama request blocks (§3.3).
9. Wire `ValidationConfig`/`DeduplicationConfig` into their components (§5).
10. Decide fate of: relationship parsing, streaming parser, threaded XML extraction, `profiles/`, v3_structured template — wire up or delete (§2.2, §2.6, §4.6, §5).

**P3 — hygiene**
11. Replace `print()` with structured logging in `config.py` / `yaml_prompt_manager.py` (§3.5).
12. Fix `--model` sentinel (§3.6), stale HP error text (§3.4), mixed th/td rows (§1.5), unify static defaults (§1.6), close the sync `requests.Session` (§2.7).

---

## Verification Notes (Chain-of-Verification)

- *Is the dedup bug real, or is `fields_to_compare` overridden somewhere?* — Grepped: `TestCaseDeduplicator(` is constructed only in `generators.py` with `logger=` only; `DeduplicationConfig` is never referenced outside `config.py`. Confirmed.
- *Is `adaptive_default` really the active template?* — `prompts/config/prompt_config.yaml` `file_paths.test_generation_prompts` points to `test_generation_adaptive.yaml`; `defaults.template_selection: adaptive_default`. Confirmed.
- *Does `--max-concurrent` reach the semaphore by another path?* — Grepped all uses of `concurrent_requests` / `gpu_concurrency_limit`: semaphore reads only `gpu_concurrency_limit`; `concurrent_requests` is only displayed/logged. Confirmed.
- *Is `image_context` used in any template?* — `grep -rn "image_context" prompts/` returns nothing. Confirmed.
- *Is relationship parsing invoked anywhere?* — Only definition sites match; no processor or CLI call. Confirmed.
