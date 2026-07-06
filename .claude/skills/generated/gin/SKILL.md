---
name: gin
description: "Skill for the Gin area of AI_TC_Generator_v04_w_Trainer. 410 symbols across 36 files."
---

# Gin

410 symbols | 36 files | Cohesion: 70%

## When to Use

- Working with code in `evaluate/`
- Understanding how TestContextReset, New, TestFileDescriptor work
- Modifying gin-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `evaluate/test_repos/gin/context.go` | reset, Next, bodyAllowedForStatus, Render, IndentedJSON (+51) |
| `evaluate/test_repos/gin/context_test.go` | TestContextReset, TestContextSetGetAnyKey, TestContextCopy, TestContextRenderIfErr, TestContextRenderProtoBuf (+33) |
| `evaluate/test_repos/gin/gin.go` | New, ServeHTTP, HandleContext, handleHTTPRequest, serveError (+28) |
| `evaluate/test_repos/gin/routes_test.go` | PerformRequest, testRouteOK, testRouteNotOK, testRouteNotOK2, TestRouterMethod (+24) |
| `evaluate/test_repos/gin/tree_test.go` | catchPanic, testRoutes, TestEmptyWildcardName, TestTreeDoubleWildcard, TestTreeFindCaseInsensitivePath (+20) |
| `evaluate/test_repos/gin/gin_test.go` | TestEngineHandleContext, TestEngineHandleContextManyReEntries, TestEngineHandleContextPreventsMiddlewareReEntry, TestEngineHandleContextNoRouteWithGroupMiddleware, TestEngineHandleContextNoRouteWithEngineMiddleware (+18) |
| `evaluate/test_repos/gin/logger_test.go` | TestLogger, TestLoggerWithConfig, TestLoggerWithFormatter, TestLoggerWithConfigFormatting, TestErrorLogger (+11) |
| `evaluate/test_repos/gin/benchmarks_test.go` | BenchmarkOneRoute, BenchmarkRecoveryMiddleware, BenchmarkLoggerMiddleware, BenchmarkManyHandlers, Benchmark5Params (+10) |
| `evaluate/test_repos/gin/routergroup.go` | Handle, Use, Group, calculateAbsolutePath, handle (+9) |
| `evaluate/test_repos/gin/logger.go` | ErrorLogger, LoggerWithFormatter, LoggerWithWriter, LoggerWithConfig, IsOutputColor (+7) |

## Entry Points

Start here when exploring this area:

- **`TestContextReset`** (Function) — `evaluate/test_repos/gin/context_test.go:276`
- **`New`** (Function) — `evaluate/test_repos/gin/gin.go:201`
- **`TestFileDescriptor`** (Function) — `evaluate/test_repos/gin/gin_integration_test.go:297`
- **`TestEngineHandleContext`** (Function) — `evaluate/test_repos/gin/gin_test.go:653`
- **`TestEngineHandleContextManyReEntries`** (Function) — `evaluate/test_repos/gin/gin_test.go:670`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `TestContextReset` | Function | `evaluate/test_repos/gin/context_test.go` | 276 |
| `New` | Function | `evaluate/test_repos/gin/gin.go` | 201 |
| `TestFileDescriptor` | Function | `evaluate/test_repos/gin/gin_integration_test.go` | 297 |
| `TestEngineHandleContext` | Function | `evaluate/test_repos/gin/gin_test.go` | 653 |
| `TestEngineHandleContextManyReEntries` | Function | `evaluate/test_repos/gin/gin_test.go` | 670 |
| `TestEngineHandleContextPreventsMiddlewareReEntry` | Function | `evaluate/test_repos/gin/gin_test.go` | 707 |
| `TestEngineHandleContextNoRouteWithGroupMiddleware` | Function | `evaluate/test_repos/gin/gin_test.go` | 745 |
| `TestEngineHandleContextNoRouteWithEngineMiddleware` | Function | `evaluate/test_repos/gin/gin_test.go` | 780 |
| `TestEngineHandleContextUseEscapedPathOverride` | Function | `evaluate/test_repos/gin/gin_test.go` | 849 |
| `TestPrepareTrustedCIRDsWith` | Function | `evaluate/test_repos/gin/gin_test.go` | 866 |
| `TestShouldBindUri` | Function | `evaluate/test_repos/gin/githubapi_test.go` | 289 |
| `TestBindUri` | Function | `evaluate/test_repos/gin/githubapi_test.go` | 311 |
| `TestBindUriError` | Function | `evaluate/test_repos/gin/githubapi_test.go` | 333 |
| `TestGithubAPI` | Function | `evaluate/test_repos/gin/githubapi_test.go` | 386 |
| `ErrorLogger` | Function | `evaluate/test_repos/gin/logger.go` | 206 |
| `LoggerWithFormatter` | Function | `evaluate/test_repos/gin/logger.go` | 228 |
| `LoggerWithWriter` | Function | `evaluate/test_repos/gin/logger.go` | 236 |
| `LoggerWithConfig` | Function | `evaluate/test_repos/gin/logger.go` | 244 |
| `TestLogger` | Function | `evaluate/test_repos/gin/logger_test.go` | 21 |
| `TestLoggerWithConfig` | Function | `evaluate/test_repos/gin/logger_test.go` | 85 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Bytesconv | 7 calls |
| Fs | 2 calls |

## How to Explore

1. `context({name: "TestContextReset"})` — see callers and callees
2. `query({search_query: "gin"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
