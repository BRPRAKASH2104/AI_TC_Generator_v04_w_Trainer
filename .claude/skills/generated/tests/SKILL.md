---
name: tests
description: "Skill for the Tests area of AI_TC_Generator_v04_w_Trainer. 274 symbols across 81 files."
---

# Tests

274 symbols | 81 files | Cohesion: 72%

## When to Use

- Working with code in `evaluate/`
- Understanding how run, detect_entry_points, trace_flows work
- Modifying tests-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `evaluate/test_repos/nextjs/tests/test_flows.py` | _add_func, _add_call, test_detect_entry_points_no_callers, test_detect_entry_points_framework_pattern, test_detect_entry_points_name_pattern (+18) |
| `evaluate/test_repos/nextjs/tests/test_changes.py` | _add_call, test_risk_score_with_flow_membership, test_analyze_changes_with_flows, test_analyze_changes_returns_expected_keys, test_analyze_changes_risk_score_range (+13) |
| `evaluate/test_repos/nextjs/tests/test_communities.py` | _seed_two_clusters, test_detect_communities_returns_list, test_detect_finds_clusters, test_community_has_required_fields, test_store_and_retrieve_communities (+7) |
| `evaluate/test_repos/httpx/tests/test_main.py` | splitlines, test_get, test_binary, test_follow_redirects, test_auth (+5) |
| `evaluate/test_repos/nextjs/tests/test_incremental.py` | test_incremental_with_no_changes, test_incremental_with_changed_file, test_incremental_deleted_file, test_parallel_build_produces_same_results, _make_chain_store (+4) |
| `evaluate/test_repos/nextjs/tests/test_embeddings.py` | _make_node, test_basic_function, test_method_with_parent, test_with_params_and_return_type, test_file_node_no_kind (+4) |
| `evaluate/test_repos/fastapi/tests/test_dependency_contextmanager.py` | get_state, asyncgen_state, generator_state, asyncgen_state_try, generator_state_try (+4) |
| `evaluate/test_repos/flask/tests/test_views.py` | common_test, test_endpoint_override, Index, OtherView, View (+3) |
| `evaluate/test_repos/nextjs/tests/test_skills.py` | test_install_cursor_config, test_install_windsurf_config, test_install_zed_config, test_install_continue_config, test_install_opencode_config (+2) |
| `evaluate/test_repos/fastapi/tests/test_generate_unique_id_function.py` | test_router_include_overrides_generate_unique_id, test_warn_duplicate_operation_id, test_top_level_generate_unique_id, test_router_overrides_generate_unique_id, test_router_path_operation_overrides_generate_unique_id (+2) |

## Entry Points

Start here when exploring this area:

- **`run`** (Function) — `evaluate/test_repos/nextjs/code_review_graph/eval/benchmarks/flow_completeness.py:10`
- **`detect_entry_points`** (Function) — `evaluate/test_repos/nextjs/code_review_graph/flows.py:75`
- **`trace_flows`** (Function) — `evaluate/test_repos/nextjs/code_review_graph/flows.py:191`
- **`store_flows`** (Function) — `evaluate/test_repos/nextjs/code_review_graph/flows.py:306`
- **`incremental_trace_flows`** (Function) — `evaluate/test_repos/nextjs/code_review_graph/flows.py:354`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `Index` | Class | `evaluate/test_repos/flask/tests/test_views.py` | 18 |
| `OtherView` | Class | `evaluate/test_repos/flask/tests/test_views.py` | 242 |
| `View` | Class | `evaluate/test_repos/flask/tests/test_views.py` | 246 |
| `GetView` | Class | `evaluate/test_repos/flask/tests/test_views.py` | 219 |
| `DeleteView` | Class | `evaluate/test_repos/flask/tests/test_views.py` | 223 |
| `GetDeleteView` | Class | `evaluate/test_repos/flask/tests/test_views.py` | 227 |
| `run` | Function | `evaluate/test_repos/nextjs/code_review_graph/eval/benchmarks/flow_completeness.py` | 10 |
| `detect_entry_points` | Function | `evaluate/test_repos/nextjs/code_review_graph/flows.py` | 75 |
| `trace_flows` | Function | `evaluate/test_repos/nextjs/code_review_graph/flows.py` | 191 |
| `store_flows` | Function | `evaluate/test_repos/nextjs/code_review_graph/flows.py` | 306 |
| `incremental_trace_flows` | Function | `evaluate/test_repos/nextjs/code_review_graph/flows.py` | 354 |
| `get_flows` | Function | `evaluate/test_repos/nextjs/code_review_graph/flows.py` | 469 |
| `get_affected_flows` | Function | `evaluate/test_repos/nextjs/code_review_graph/flows.py` | 556 |
| `detect_communities` | Function | `evaluate/test_repos/nextjs/code_review_graph/communities.py` | 379 |
| `incremental_detect_communities` | Function | `evaluate/test_repos/nextjs/code_review_graph/communities.py` | 435 |
| `store_communities` | Function | `evaluate/test_repos/nextjs/code_review_graph/communities.py` | 475 |
| `get_communities` | Function | `evaluate/test_repos/nextjs/code_review_graph/communities.py` | 528 |
| `get_architecture_overview` | Function | `evaluate/test_repos/nextjs/code_review_graph/communities.py` | 577 |
| `run` | Function | `evaluate/test_repos/nextjs/code_review_graph/eval/benchmarks/build_performance.py` | 11 |
| `review_changes_prompt` | Function | `evaluate/test_repos/nextjs/code_review_graph/prompts.py` | 31 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → Loads` | cross_community | 4 |
| `Verify_prompt_generation → Format_table` | cross_community | 4 |
| `Verify_prompt_generation → Format_info_list` | cross_community | 4 |
| `Verify_prompt_generation → Format_interfaces` | cross_community | 4 |
| `Verify_prompt_generation → Format_image_context` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Code_review_graph | 66 calls |
| Integration | 13 calls |
| Fastapi | 8 calls |
| Tools | 5 calls |
| Background_tasks | 2 calls |
| Eval | 2 calls |

## How to Explore

1. `context({name: "run"})` — see callers and callees
2. `query({search_query: "tests"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
