---
name: backend
description: "Skill for the Backend area of AI_TC_Generator_v04_w_Trainer. 48 symbols across 13 files."
---

# Backend

48 symbols | 13 files | Cohesion: 80%

## When to Use

- Working with code in `evaluate/`
- Understanding how resolveNodeAtCursor, registerNavigationCommands, disposable work
- Modifying backend-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/sqlite.ts` | getAllFiles, getNodesByFile, getNode, getNodeAtCursor, searchNodes (+12) |
| `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/cli.ts` | isInstalled, buildGraph, installBackend, isEnoent, toCliResult (+4) |
| `evaluate/test_repos/nextjs/code-review-graph-vscode/src/extension.ts` | registerCommands, findGraphDb, getWorkspaceRoot, navigateToNode, reinitialize (+3) |
| `evaluate/test_repos/nextjs/code-review-graph-vscode/src/views/treeView.ts` | getSymbolChildren, setResults, getChildren |
| `evaluate/test_repos/nextjs/code-review-graph-vscode/src/views/graphWebview.ts` | createOrShow, sendGraphData |
| `evaluate/test_repos/nextjs/code-review-graph-vscode/src/onboarding/installer.ts` | checkAndPrompt, autoInstall |
| `evaluate/test_repos/nextjs/code-review-graph-vscode/src/features/cursorResolver.ts` | resolveNodeAtCursor |
| `evaluate/test_repos/nextjs/code-review-graph-vscode/src/features/navigation.ts` | registerNavigationCommands |
| `evaluate/test_repos/nextjs/code-review-graph-vscode/src/features/reviewAssistant.ts` | disposable |
| `evaluate/test_repos/nextjs/code-review-graph-vscode/src/features/scmDecorations.ts` | update |

## Entry Points

Start here when exploring this area:

- **`resolveNodeAtCursor`** (Function) — `evaluate/test_repos/nextjs/code-review-graph-vscode/src/features/cursorResolver.ts:9`
- **`registerNavigationCommands`** (Function) — `evaluate/test_repos/nextjs/code-review-graph-vscode/src/features/navigation.ts:7`
- **`disposable`** (Function) — `evaluate/test_repos/nextjs/code-review-graph-vscode/src/features/reviewAssistant.ts:57`
- **`disposable`** (Function) — `evaluate/test_repos/nextjs/code-review-graph-vscode/src/features/search.ts:75`
- **`registerWalkthroughCommands`** (Function) — `evaluate/test_repos/nextjs/code-review-graph-vscode/src/onboarding/welcome.ts:12`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `SqliteReader` | Class | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/sqlite.ts` | 155 |
| `resolveNodeAtCursor` | Function | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/features/cursorResolver.ts` | 9 |
| `registerNavigationCommands` | Function | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/features/navigation.ts` | 7 |
| `disposable` | Function | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/features/reviewAssistant.ts` | 57 |
| `disposable` | Function | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/features/search.ts` | 75 |
| `registerWalkthroughCommands` | Function | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/onboarding/welcome.ts` | 12 |
| `activate` | Function | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/extension.ts` | 876 |
| `getAllFiles` | Method | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/sqlite.ts` | 251 |
| `getNodesByFile` | Method | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/sqlite.ts` | 261 |
| `getNode` | Method | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/sqlite.ts` | 271 |
| `getNodeAtCursor` | Method | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/sqlite.ts` | 284 |
| `searchNodes` | Method | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/sqlite.ts` | 297 |
| `getEdgesBySource` | Method | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/sqlite.ts` | 312 |
| `getEdgesByTarget` | Method | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/sqlite.ts` | 320 |
| `getEdgesAmong` | Method | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/sqlite.ts` | 333 |
| `getImpactRadius` | Method | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/sqlite.ts` | 434 |
| `getNodesBySize` | Method | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/sqlite.ts` | 511 |
| `_db` | Method | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/sqlite.ts` | 552 |
| `_rowToNode` | Method | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/sqlite.ts` | 560 |
| `_rowToEdge` | Method | `evaluate/test_repos/nextjs/code-review-graph-vscode/src/backend/sqlite.ts` | 580 |

## How to Explore

1. `context({name: "resolveNodeAtCursor"})` — see callers and callees
2. `query({search_query: "backend"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
