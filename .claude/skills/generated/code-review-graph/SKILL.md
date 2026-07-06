---
name: code-review-graph
description: "Skill for the Code_review_graph area of AI_TC_Generator_v04_w_Trainer. 200 symbols across 36 files."
---

# Code_review_graph

200 symbols | 36 files | Cohesion: 62%

## When to Use

- Working with code in `evaluate/`
- Understanding how incremental_update, store_with_data, test_cpp_include_resolution work
- Modifying code_review_graph-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `evaluate/test_repos/nextjs/code_review_graph/parser.py` | _is_test_function, _extract_from_tree, _extract_r_constructs, _extract_lua_constructs, _handle_lua_variable_declaration (+37) |
| `evaluate/test_repos/nextjs/code_review_graph/graph.py` | _invalidate_cache, upsert_node, upsert_edge, remove_file_data, store_file_nodes_edges (+24) |
| `evaluate/test_repos/nextjs/code_review_graph/incremental.py` | _should_ignore, incremental_update, on_deleted, _update_file, get_db_path (+16) |
| `evaluate/test_repos/nextjs/code_review_graph/embeddings.py` | _encode_vector, _decode_vector, embed_nodes, _cosine_similarity, search (+7) |
| `evaluate/test_repos/nextjs/code_review_graph/communities.py` | _generate_community_name, _extract_file_prefix, _extract_keywords, _to_slug, _compute_cohesion (+3) |
| `evaluate/test_repos/nextjs/code_review_graph/refactor.py` | rename_preview, find_dead_code, suggest_refactorings, _cleanup_expired, apply_refactor (+1) |
| `evaluate/test_repos/nextjs/code_review_graph/hints.py` | record_nodes, record_files, generate_hints, _track_result, get_session (+1) |
| `evaluate/test_repos/nextjs/tests/test_embeddings.py` | test_roundtrip, test_empty_vector, test_embed_nodes_returns_zero_when_unavailable, test_search_returns_empty_when_unavailable, test_remove_node (+1) |
| `evaluate/test_repos/nextjs/code_review_graph/skills.py` | generate_skills, _inject_instructions, inject_claude_md, inject_platform_instructions, generate_hooks_config (+1) |
| `evaluate/test_repos/nextjs/tests/test_visualization.py` | store_with_data, test_cpp_include_resolution, large_store, test_export_graph_data, test_file_mode_aggregation |

## Entry Points

Start here when exploring this area:

- **`incremental_update`** (Function) — `evaluate/test_repos/nextjs/code_review_graph/incremental.py:421`
- **`store_with_data`** (Function) — `evaluate/test_repos/nextjs/tests/test_visualization.py:11`
- **`test_cpp_include_resolution`** (Function) — `evaluate/test_repos/nextjs/tests/test_visualization.py:144`
- **`large_store`** (Function) — `evaluate/test_repos/nextjs/tests/test_visualization.py:245`
- **`rename_preview`** (Function) — `evaluate/test_repos/nextjs/code_review_graph/refactor.py:48`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `incremental_update` | Function | `evaluate/test_repos/nextjs/code_review_graph/incremental.py` | 421 |
| `store_with_data` | Function | `evaluate/test_repos/nextjs/tests/test_visualization.py` | 11 |
| `test_cpp_include_resolution` | Function | `evaluate/test_repos/nextjs/tests/test_visualization.py` | 144 |
| `large_store` | Function | `evaluate/test_repos/nextjs/tests/test_visualization.py` | 245 |
| `rename_preview` | Function | `evaluate/test_repos/nextjs/code_review_graph/refactor.py` | 48 |
| `find_dead_code` | Function | `evaluate/test_repos/nextjs/code_review_graph/refactor.py` | 175 |
| `suggest_refactorings` | Function | `evaluate/test_repos/nextjs/code_review_graph/refactor.py` | 235 |
| `refactor_func` | Function | `evaluate/test_repos/nextjs/code_review_graph/tools/refactor_tools.py` | 22 |
| `load_config` | Function | `evaluate/test_repos/nextjs/code_review_graph/eval/runner.py` | 43 |
| `run_eval` | Function | `evaluate/test_repos/nextjs/code_review_graph/eval/runner.py` | 101 |
| `get_db_path` | Function | `evaluate/test_repos/nextjs/code_review_graph/incremental.py` | 74 |
| `full_build` | Function | `evaluate/test_repos/nextjs/code_review_graph/incremental.py` | 346 |
| `test_runner_with_mock_repo` | Function | `evaluate/test_repos/nextjs/tests/test_eval.py` | 249 |
| `test_benchmark_review_workflow` | Function | `evaluate/test_repos/nextjs/tests/test_eval.py` | 390 |
| `test_run_all_benchmarks` | Function | `evaluate/test_repos/nextjs/tests/test_eval.py` | 465 |
| `main` | Function | `evaluate/test_repos/nextjs/code_review_graph/cli.py` | 153 |
| `find_repo_root` | Function | `evaluate/test_repos/nextjs/code_review_graph/incremental.py` | 54 |
| `find_project_root` | Function | `evaluate/test_repos/nextjs/code_review_graph/incremental.py` | 66 |
| `main` | Function | `evaluate/test_repos/nextjs/code_review_graph/main.py` | 689 |
| `build_or_update_graph` | Function | `evaluate/test_repos/nextjs/code_review_graph/tools/build.py` | 274 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 48 calls |
| Tools | 15 calls |
| Integration | 12 calls |
| Eval | 4 calls |

## How to Explore

1. `context({name: "incremental_update"})` — see callers and callees
2. `query({search_query: "code_review_graph"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
