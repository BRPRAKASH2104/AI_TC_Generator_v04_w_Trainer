<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **AI_TC_Generator_v04_w_Trainer** (3670 symbols, 5445 relationships, 128 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({search_query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/AI_TC_Generator_v04_w_Trainer/context` | Codebase overview, check index freshness |
| `gitnexus://repo/AI_TC_Generator_v04_w_Trainer/clusters` | All functional areas |
| `gitnexus://repo/AI_TC_Generator_v04_w_Trainer/processes` | All execution flows |
| `gitnexus://repo/AI_TC_Generator_v04_w_Trainer/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |
| Work in the Integration area (144 symbols) | `.claude/skills/generated/integration/SKILL.md` |
| Work in the Training area (80 symbols) | `.claude/skills/generated/training/SKILL.md` |
| Work in the Tests area (53 symbols) | `.claude/skills/generated/tests/SKILL.md` |
| Work in the Utilities area (40 symbols) | `.claude/skills/generated/utilities/SKILL.md` |
| Work in the Processors area (32 symbols) | `.claude/skills/generated/processors/SKILL.md` |
| Work in the Cluster_8 area (21 symbols) | `.claude/skills/generated/cluster-8/SKILL.md` |
| Work in the Unit area (20 symbols) | `.claude/skills/generated/unit/SKILL.md` |
| Work in the Tools area (15 symbols) | `.claude/skills/generated/tools/SKILL.md` |
| Work in the Cluster_29 area (13 symbols) | `.claude/skills/generated/cluster-29/SKILL.md` |
| Work in the Cluster_36 area (13 symbols) | `.claude/skills/generated/cluster-36/SKILL.md` |
| Work in the Cluster_31 area (11 symbols) | `.claude/skills/generated/cluster-31/SKILL.md` |
| Work in the Cluster_43 area (11 symbols) | `.claude/skills/generated/cluster-43/SKILL.md` |
| Work in the Cluster_44 area (11 symbols) | `.claude/skills/generated/cluster-44/SKILL.md` |
| Work in the Cluster_16 area (9 symbols) | `.claude/skills/generated/cluster-16/SKILL.md` |
| Work in the Cluster_75 area (8 symbols) | `.claude/skills/generated/cluster-75/SKILL.md` |
| Work in the Cluster_74 area (7 symbols) | `.claude/skills/generated/cluster-74/SKILL.md` |
| Work in the Cluster_17 area (6 symbols) | `.claude/skills/generated/cluster-17/SKILL.md` |
| Work in the Cluster_21 area (6 symbols) | `.claude/skills/generated/cluster-21/SKILL.md` |
| Work in the Cluster_30 area (6 symbols) | `.claude/skills/generated/cluster-30/SKILL.md` |
| Work in the Cluster_72 area (6 symbols) | `.claude/skills/generated/cluster-72/SKILL.md` |

<!-- gitnexus:end -->

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
| ------ | ---------- |
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
