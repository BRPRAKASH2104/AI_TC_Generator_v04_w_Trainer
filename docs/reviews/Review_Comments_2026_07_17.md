# Code Review — Full Business-Logic Audit

**Date:** 2026-07-17  
**Scope:** `main.py`, `src/`, active prompts, training utilities, configuration, and tests  
**Method:** GitNexus execution-flow review, caller tracing, focused reproductions, CLI checks, full test suite, lint/format checks, and comparison with the current Ollama API documentation.

## Executive Summary

The core pipeline is sensibly separated into extraction, contextualization, generation, validation/deduplication, and Excel formatting. Recent fixes also consolidated sync/async post-processing and correctly wired HP concurrency. However, four issues can make the product claim success while delivering incomplete or misleading results:

1. partial generation failures still produce a successful exit;
2. normal REQIF `<object>` image references silently lose their saved image and bypass vision processing;
3. the advertised RAFT “training” path does not train on the dataset;
4. malformed model output can become plausible-looking `N/A` Excel rows even when strict validation is requested.

Address these before further refactoring or feature expansion.

## Critical Findings

### [Critical] 1. Partial output is reported as a successful run

`TestCaseGenerator.generate_test_cases_for_requirement()` catches every exception and returns `[]` (`src/core/generators.py:346-393`). The standard processor then continues after an empty result and returns `success=True` whenever at least one requirement produced cases (`src/processors/standard_processor.py:127-171,197-206`). At directory level, both modes reduce all file results to `any(r["success"] ...)` (`main.py:287-313,364-407`).

A focused check confirmed that an `OllamaConnectionError` becomes `[]`. Consequently, one successful requirement or file can mask every other failure, emit an incomplete workbook, and exit with code 0. The processor's specific Ollama exception handlers are also unreachable for generation-time failures.

**Recommendation:** return the structured error contract used by the async generator in both modes; aggregate failed requirement/file IDs; represent partial completion explicitly; and return a non-zero exit unless all requested inputs completed, or unless the user opts into partial success.

### [Critical] 2. External `<object>` images overwrite their usable metadata and disable vision

Image extraction appends saved external files first, then unsaved `<object data="...">` placeholders (`src/core/image_extractor.py:120-131,150-192,208-234,308-345`). `augment_artifacts_with_images()` builds a last-write-wins lookup, so the placeholder overwrites the saved external record for the same path (`src/core/image_extractor.py:644-696`). Model selection and image loading require `saved_path` (`src/config.py:502-509`; `src/core/generators.py:40-64`).

The focused reproduction linked `media/diagram.png` to `{"saved": false}` and selected `llama3.1:8b`, not the vision model. Existing tests cover base64 linking but not the external-file-plus-object collision.

**Recommendation:** resolve `<object>` references to the external record, merge reference metadata into that record, and never replace a saved entry with an unsaved placeholder. Add an end-to-end REQIFZ test asserting both the selected model and the image bytes sent to Ollama.

### [Critical] 3. The RAFT training path never trains on the dataset

`VisionRAFTTrainer.train()` analyzes the dataset, creates a Modelfile, and runs `ollama create` (`src/training/vision_raft_trainer.py:145-167`). The Modelfile contains only `FROM`, runtime parameters, and `SYSTEM`; it contains no adapter, trained weights, or examples (`:258-305`). A successful `ollama create` is recorded as successful “training” (`:307-358`). `ProgressiveRAFTTrainer` is even more explicit: it computes a simulated score from example quality without training a model (`src/training/progressive_trainer.py:323-379`).

This conflicts with the README's fine-tuning and “40-60% better” claims (`README.md:19,233-262`). Per Ollama's [Modelfile reference](https://docs.ollama.com/modelfile) and [model import guide](https://docs.ollama.com/import), a fine-tuned adapter must be produced by a training framework and applied with `ADAPTER` (or trained/fused weights must be imported). A new system prompt is customization, not fine-tuning.

**Recommendation:** rename the current operation to “create prompt-customized model” and remove improvement claims, or implement real adapter training/evaluation and only mark success after verified metrics on a held-out set.

### [Critical] 4. Invalid test-case objects are exported as plausible defaults

The generators check only for a top-level `test_cases` key (`src/core/generators.py:374-386,571-602`). `JSONResponseParser.validate_test_cases_structure()` is unused and expects the retired schema (`src/core/parsers.py:91-108`). When no interface dictionary exists, batch semantic validation skips even data-format validation (`src/core/validators.py:220-229`). `ValidationConfig.fail_on_validation_error` is never consulted (`src/config.py:160-174`). The formatter then supplies “Generated Test,” default preconditions, and `N/A` values (`src/core/formatters.py:97-151`).

With `fail_on_validation_error=True`, a focused reproduction passed `[{}]` through post-processing as `validation_passed=True` and produced an Excel-ready row with `Data=N/A` and `Expected Result=N/A`.

**Recommendation:** define one Pydantic/JSON Schema model for the active five fields, pass that schema through Ollama's supported `format` object, validate every returned item again locally, and honor `fail_on_validation_error` before formatting. See the current [Ollama generate API](https://docs.ollama.com/api/generate).

## Recommended Improvements

### [Recommended] 5. Presets do not reliably control execution

Preset values are merged into `effective_config` (`main.py:168-231`), but dispatch still uses the raw `--hp` flag (`main.py:249-261`). Click's false boolean defaults overwrite preset `verbose`, `debug`, and `performance`, and model-specific defaults overwrite preset concurrency (`src/config.py:677-708,723-764`). A `production` preset reproduction yielded: effective mode `hp`, actual branch `standard`, performance `False`, and concurrency `3` instead of `8`.

**Recommendation:** make tri-state CLI flags (`None` when omitted), dispatch from `effective_config.cli.mode`, and include preset-applied keys in the “explicit override” set so model recommendations do not replace them. Add `CliRunner` tests for every preset.

### [Recommended] 6. RAFT collection controls do not match their documented consent contract

The README says both `enable_raft` and `collect_training_data` must be enabled through `AI_TG_*` variables or `config/cli_config.yaml` (`README.md:223-245`). Neither environment variable is mapped in `apply_cli_overrides()`, and `load_cli_config()` imports only CLI defaults/presets/environments/model settings (`src/config.py:554-584,639-654`). A focused environment check left both flags `False`. Conversely, `BaseProcessor` creates the collector whenever `enable_raft=True`, ignoring `collect_training_data=False` (`src/processors/base_processor.py:52-59`).

**Recommendation:** wire the documented settings, require both flags before writing proprietary requirement/test content, and add tests for all four boolean combinations.

### [Recommended] 7. Large-table coverage is knowingly incomplete and then reported invalid

Tables over 100 rows are reduced to the first and last ten rows, and the model is instructed to cover only those displayed rows (`src/core/prompt_builder.py:170-234`). The validator nevertheless requires one positive case for every original row (`src/core/validators.py:275-328`). `FileProcessingConfig.max_table_rows` is not injected into `PromptBuilder` (`src/config.py:231-252`).

**Recommendation:** chunk large tables into multiple model calls, merge/deduplicate the results, and validate against the rows assigned to each chunk. Avoid treating truncation as successful comprehensive coverage.

### [Recommended] 8. Every requirement receives the full global interface dictionary

`BaseProcessor` attaches every system interface to every requirement (`src/processors/base_processor.py:127-183`), and `PromptBuilder` serializes the full list into every prompt (`src/core/prompt_builder.py:82-85,258-277`). Work and token volume therefore grow approximately with requirements × interfaces, risking the 16K text context and slowing every Ollama call.

**Recommendation:** pre-index interface names, retrieve only exact/fuzzy matches referenced by the requirement and nearby information, and cap the fallback context. Record prompt token estimates so truncation is observable.

### [Recommended] 9. Configuration export can persist credentials in plaintext

`ConfigManager.save_to_file()` dumps the entire model, including `ollama.api_key`, `auth_token`, and environment-loaded `SecretsConfig`, to a normal YAML file (`src/config.py:469-482`). Running `src/config.py` directly invokes that export (`:853-866`). The clients also do not use the declared authentication fields, and URLs are hardcoded to HTTP (`src/config.py:38-48,123-135`; `src/core/ollama_client.py:113-122,313-317`).

**Recommendation:** exclude secret fields from exports, write private files with restrictive permissions, and either remove decorative auth settings or implement HTTPS/Bearer authentication for remote Ollama endpoints.

## Optional Cleanup

- `[Optional]` `_map_reqif_type_to_artifact_type()` matches `"information"` before `"design information"`, making the specific enum branch unreachable (`src/core/extractors.py:386-405`). Decide whether design information is distinct; if so, handle it explicitly in `BaseProcessor`.
- `[Optional]` Relationship parsing now runs, but its parent/child/dependency metadata is not included in prompt variables. Either use it for generation context or avoid the default parsing cost.
- `[Optional]` `--training` remains a placeholder (`main.py:151-159`) while real utilities live under `utilities/`; remove or connect the flag.

## Verification Results

- `python3 -m pytest -q --no-cov -p no:cacheprovider`: **353 passed, 4 skipped, 1 failed**. The failure is `test_ollama_client_model_validation`: it claims not to require Ollama, performs a real request, reverses `model_name`/`prompt`, and checks brittle exception text (`tests/integration/test_real_integration.py:21-44`). Mock the transport or mark/skip it as an external-service test.
- `python3 -m ruff check src main.py utilities prompts/tools`: **passed**.
- `python3 -m ruff format --check ...`: one file would be reformatted (`prompts/tools/validation_and_tools.py`).
- `python3 main.py --help` and `python3 main.py --validate-prompts`: **passed**; one active prompt validated.
- `python3 -m pip check`: **passed**. `pip-audit` is declared only in the optional security extra and was unavailable, so no CVE result is claimed.
- Mypy produced no output for several minutes and was interrupted; type-check status is **inconclusive**, not passing.
- GitNexus reported no dependency cycles. Its PDG/taint layer is not present, so security conclusions are based on source inspection rather than a taint proof.
- Current Ollama documentation confirms that this code's `images`, JSON `format`, `logprobs`, and `top_logprobs` request fields are supported. No API mismatch is reported for those fields.

## Chain-of-Verification

- **Could the image failure be synthetic?** No. Production extraction guarantees external records precede object placeholders, and the focused lookup/model-selection reproduction matched that order.
- **Could training consume the dataset indirectly?** No. The dataset is read only for statistics; neither trainer produces an adapter/weights, and progressive training explicitly simulates scores.
- **Could presets still affect dispatch elsewhere?** No. The effective mode was `hp` while the patched CLI execution selected the standard branch.
- **Could strict validation reject `{}` later?** No. The focused post-processing/formatter run produced a default-filled row while strict failure was enabled.
- **Could partial failures still cause a non-zero exit?** Only when every requirement/file fails. Any successful item makes the processor/directory aggregate successful.

## Suggested Fix Order

1. Make incomplete generation fail explicitly and preserve structured causes.
2. Repair `<object>` image resolution and add a real REQIFZ vision regression test.
3. Enforce a canonical test-case schema before Excel export.
4. Correct the training claims/implementation and collection consent controls.
5. Repair preset precedence, then chunk tables and reduce interface prompt scope.
