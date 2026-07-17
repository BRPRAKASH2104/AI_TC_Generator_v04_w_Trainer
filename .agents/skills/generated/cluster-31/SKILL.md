---
name: cluster-31
description: "Skill for the Cluster_31 area of AI_TC_Generator_v04_w_Trainer. 11 symbols across 3 files."
---

# Cluster_31

11 symbols | 3 files | Cohesion: 96%

## When to Use

- Working with code in `src/`
- Understanding how test_ollama_client_async_logprobs, generate_response_with_vision, generate_completion work
- Modifying cluster_31-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/core/ollama_client.py` | _build_generate_payload, _load_images_base64, generate_response_with_vision, generate_completion, generate_response (+1) |
| `tests/core/test_vision_fixes.py` | test_missing_image_file_logs_warning, test_permission_denied_logs_specific_error, test_failed_images_returns_count, test_vision_model_uses_vision_context_window |
| `tests/core/test_ollama_logprobs.py` | test_ollama_client_async_logprobs |

## Entry Points

Start here when exploring this area:

- **`test_ollama_client_async_logprobs`** (Function) — `tests/core/test_ollama_logprobs.py:78`
- **`generate_response_with_vision`** (Method) — `src/core/ollama_client.py:184`
- **`generate_completion`** (Method) — `src/core/ollama_client.py:329`
- **`generate_response`** (Method) — `src/core/ollama_client.py:358`
- **`generate_response_with_vision`** (Method) — `src/core/ollama_client.py:377`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_ollama_client_async_logprobs` | Function | `tests/core/test_ollama_logprobs.py` | 78 |
| `generate_response_with_vision` | Method | `src/core/ollama_client.py` | 184 |
| `generate_completion` | Method | `src/core/ollama_client.py` | 329 |
| `generate_response` | Method | `src/core/ollama_client.py` | 358 |
| `generate_response_with_vision` | Method | `src/core/ollama_client.py` | 377 |
| `test_missing_image_file_logs_warning` | Method | `tests/core/test_vision_fixes.py` | 223 |
| `test_permission_denied_logs_specific_error` | Method | `tests/core/test_vision_fixes.py` | 258 |
| `test_failed_images_returns_count` | Method | `tests/core/test_vision_fixes.py` | 292 |
| `test_vision_model_uses_vision_context_window` | Method | `tests/core/test_vision_fixes.py` | 383 |
| `_build_generate_payload` | Function | `src/core/ollama_client.py` | 38 |
| `_load_images_base64` | Function | `src/core/ollama_client.py` | 79 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Generate_response → _load_images_base64` | intra_community | 4 |
| `Generate_response → _build_generate_payload` | intra_community | 4 |
| `Generate_response → _load_images_base64` | cross_community | 4 |
| `Generate_response → _build_generate_payload` | cross_community | 4 |

## How to Explore

1. `context({name: "test_ollama_client_async_logprobs"})` — see callers and callees
2. `query({search_query: "cluster_31"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
