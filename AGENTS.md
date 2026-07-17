<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **AI_TC_Generator_v04_w_Trainer** (3797 symbols, 5741 relationships, 130 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

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
| Work in the Integration area (158 symbols) | `.claude/skills/generated/integration/SKILL.md` |
| Work in the Training area (80 symbols) | `.claude/skills/generated/training/SKILL.md` |
| Work in the Tests area (53 symbols) | `.claude/skills/generated/tests/SKILL.md` |
| Work in the Unit area (49 symbols) | `.claude/skills/generated/unit/SKILL.md` |
| Work in the Utilities area (40 symbols) | `.claude/skills/generated/utilities/SKILL.md` |
| Work in the Processors area (32 symbols) | `.claude/skills/generated/processors/SKILL.md` |
| Work in the Cluster_11 area (21 symbols) | `.claude/skills/generated/cluster-11/SKILL.md` |
| Work in the Tools area (15 symbols) | `.claude/skills/generated/tools/SKILL.md` |
| Work in the Cluster_33 area (13 symbols) | `.claude/skills/generated/cluster-33/SKILL.md` |
| Work in the Cluster_40 area (13 symbols) | `.claude/skills/generated/cluster-40/SKILL.md` |
| Work in the Cluster_35 area (11 symbols) | `.claude/skills/generated/cluster-35/SKILL.md` |
| Work in the Cluster_48 area (11 symbols) | `.claude/skills/generated/cluster-48/SKILL.md` |
| Work in the Cluster_19 area (9 symbols) | `.claude/skills/generated/cluster-19/SKILL.md` |
| Work in the Cluster_41 area (9 symbols) | `.claude/skills/generated/cluster-41/SKILL.md` |
| Work in the Cluster_49 area (9 symbols) | `.claude/skills/generated/cluster-49/SKILL.md` |
| Work in the Cluster_83 area (8 symbols) | `.claude/skills/generated/cluster-83/SKILL.md` |
| Work in the Cluster_1 area (7 symbols) | `.claude/skills/generated/cluster-1/SKILL.md` |
| Work in the Cluster_20 area (7 symbols) | `.claude/skills/generated/cluster-20/SKILL.md` |
| Work in the Cluster_82 area (7 symbols) | `.claude/skills/generated/cluster-82/SKILL.md` |
| Work in the Cluster_24 area (6 symbols) | `.claude/skills/generated/cluster-24/SKILL.md` |

<!-- gitnexus:end -->
