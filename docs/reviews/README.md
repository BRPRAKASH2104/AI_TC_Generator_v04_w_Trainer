# Code Review Reports Archive

This directory contains the historical code-review reports that document the
codebase's health, quality metrics, and evolution over time. Reviews are listed
newest-first. Each entry notes the reviewer, the state **at the time of that
review**, and — where the finding has since been resolved — a pointer to the
current disposition.

> **Source of truth for open work:** the most recent report
> (`Review_Comments_2026_07_24.md`) tracks the current branch-review findings.
> Older reports are historical; most of their findings have since been fixed
> (see the "Recurring findings" table below).

---

## Available Reviews (newest first)

### 2026-07-24 — Vision RAFT evaluation branch review *(current / live)*
**File:** `Review_Comments_2026_07_24.md`

Reviews `feat/vision-raft-evaluate-model` against `main` and the 2026-07-20
baseline. The evaluator is a material improvement over the TODO stub. It raised
two Critical correctness blockers — failed baselines reporting positive lift,
and a "coverage" metric that rewards duplicate or canonical-invalid raw output —
**both fixed on the branch (`bc26473`)**. The recommended validation,
experiment-design, live-test, and documentation follow-ups plus the optional
CLI-guard item were **also fixed on the branch (`e2f43ad`)**, so all 2026-07-24
findings are now addressed. Original recommendation: **request changes**.

### 2026-07-20 — Full-scope review *(historical baseline)*
**File:** `Review_Comments_2026_07_20.md`

Historical baseline for the current branch review. Findings are tagged
`[Archived] / [Recommended] / [New Critical]` with per-item **Fixed / Open**
status. Its remaining Recommended 10 work closed on 2026-07-23: quality gates
(`10c4d64`), trainer/processor coverage (`68de923`), and high-complexity
function extraction (`edcc61f`).

### 2026-07-17 — Business-logic audit
**File:** `Review_Comments_2026_07_17.md`

Four Critical findings, all now resolved in the 07-20 line:
1. partial generation failures reported as a successful (exit-0) run;
2. external `<object>` images overwrote saved metadata and disabled vision;
3. the RAFT "training" path never trains on the dataset (system-prompt customization, not fine-tuning);
4. malformed model output exported as plausible `N/A` Excel rows despite strict validation.

### 2026-07-05 — Full codebase audit (correctness / efficiency / prompts)
**File:** `Review_Comments_2026_07_05.md`

- **Critical:** deduplicator compared `action`/`data` (fields the active template
  never produces) → silently deleted legitimate row-coverage test cases. **Fixed**
  and now guarded in CLAUDE.md (canonical schema = `summary_suffix`,
  `preconditions`, `test_steps`, `expected_result`, `test_type`).
- **High:** `--max-concurrent` ignored (HP hard-capped at 2). **Fixed.**
- Schema split across prompt/dedup/validator/parser; `image_context` never reached
  the model; large dead-code / config-drift inventory.

### 2026-04-06 — 4-agent parallel swarm review
**File:** `Review_Comments_2026_04_06.md`
**Supporting inputs:** `parts/audit_arch.md`, `parts/audit_code.md`

15 action items across four themes: silent exception swallowing, test-suite
validity (fixtures using plain-text dicts instead of XHTML helpers), documentation
drift (Python/Ollama versions, entry points), and config hygiene (unsupported model
names, `mode:` strings, RAFT-on-by-default, committed internal hostnames). All
CLAUDE.md critical invariants passed. Most items subsequently fixed.

### 2026-03-02 — Comprehensive review (Opus 4.6)
**File:** `Review_Comments_2026_03_02.md`

10 Critical / 37 Recommended / 10 Optional. Headline Criticals — HP `TypeError` on
`AsyncTestCaseGenerator` instantiation, validation-index mismatch after dedup, XML
entity-expansion (Billion Laughs) vulnerability, `src/__init__` version mismatch,
`assert True` false-positive tests. XXE **fixed 2026-07-22** via `defusedxml`
(`3943f3b`); the dedup/validation and HP issues fixed in the 07-05/07-17 line.

### 2025-12-31 — Re-review + codebase review (AntiGravity)
**Files:** `Re_Review_Report_2025_12_31.md`, `Review_Comments_2025_12_31.md`

Post-restoration re-review. Architecture praised; flagged a failing test suite and
369 ruff issues to auto-clean, plus a recommendation to decompose the long
`_generate_test_cases_for_requirement_async`. Test suite and lint since green.

### 2025-12-06 — Post-AntiGravity comprehensive review
**File:** `Review_Comments_2025_12_06.md`
**Supporting:** `2025-12-06_Progress_Summary.md`,
`2025-12-06_Test_Verification_Report.md`, `2025-12-06_Vision_Implementation_Fix_Plan.md`

Confirmed the AntiGravity vision fixes (v2.3.0). Raised two long-running items:
**24 high-complexity functions** (complexity 16–19) and **32% overall test
coverage** (0% for processors/training). These mapped to 07-20 Recommended 10
(b) and (c) and closed on 2026-07-23.

### 2025-12-05 — Vision model implementation review (AntiGravity)
**File:** `2025-12-05_Review_Comments_AntiGravity.md`

Reviewed the hybrid vision path. Critical: in-memory Base64 OOM risk on large
images; High: silent failure on image load (model told to "analyze the diagram"
with no image); plus dimension validation, vision context sizing, and temp-image
cleanup. Drove the v2.3.0 image-preprocessing + `--clean-temp` work.

### 2025-10-24 — Comprehensive review (v2.1.0)
**File:** `2025-10-24_code_review.md`

Health 8.5/10. Two Criticals that broke HP mode: `hp_processor` calling a
non-existent `generate_test_cases()`, and a broken installed-package entry point.
Both since fixed (public async method added; packaging fixed `404dbfa`).

### 2025-10-11 — Comprehensive review + findings (v2.1.0 → v2.3.0)
**Files:** `2025-10-11_comprehensive_review.md` (1,200+ lines),
`2025-10-11_codebase_review_findings.md`

Health 9.2/10. Same HP-method and packaging Criticals as 10-24, plus streaming
formatter schema mismatch ("Tests" vs "LinkTest"/"Feature Group") and lxml-only XML
streaming APIs. Streaming formatter now unified on the 16-column schema
(guarded in CLAUDE.md).

### 2025-10-07 — Initial codebase review (v1.5.0 → v2.1.0)
**File:** `2025-10-07_codebase_review.md` (909 lines)

Health 8.2/10 (projected 9.5/10 with fixes). 298 quality issues (119 auto-fixable),
28 functions >50 lines, 37 classes missing `__slots__`. Drove the 88% quality-issue
reduction and `__slots__` rollout documented in the 10-11 report.

---

## Recurring findings → current status

The same core defects surfaced across multiple reviews until fixed. Current state:

| Recurring finding | First raised | Status |
|---|---|---|
| HP mode broken (`generate_test_cases` / `TypeError`) | 2025-10-11 | ✅ Fixed |
| Broken installed-package entry point / wheel | 2025-10-11 | ✅ Fixed (`404dbfa`) |
| Deduplicator deletes valid test cases (wrong fields) | 2026-03-02 | ✅ Fixed (CLAUDE.md guard) |
| Validation index mismatch after dedup | 2026-03-02 | ✅ Fixed (stamp-before-dedup) |
| `--max-concurrent` ignored | 2026-07-05 | ✅ Fixed |
| XML entity expansion (XXE / Billion Laughs) | 2026-03-02 | ✅ Fixed (`defusedxml`, `3943f3b`) |
| Partial failure reported as success | 2026-07-17 | ✅ Fixed |
| Invalid `{}` test cases exported as `N/A` rows | 2026-07-17 | ✅ Fixed (typed JSON schema) |
| RAFT "training" doesn't fine-tune | 2026-07-17 | ✅ Honestly re-worded (`8d10a5f`) |
| Silent image-load failure / vision OOM | 2025-12-05 | ✅ Fixed (v2.3.0 preprocessing) |
| Doc drift / stale deps / CI `continue-on-error` / secrets in export | 2026-03-02 · 04-06 | ✅ Fixed |
| Whole-repo ruff + mypy gates weaker than core | 2025-12-06 | ✅ Fixed (`10c4d64`, 2026-07-23) |
| High-complexity functions (`process_file`, etc.) | 2025-12-06 | ✅ Fixed (`edcc61f`, 2026-07-23) |
| Low trainer / processor test coverage | 2025-12-06 | ✅ Fixed (`68de923`, 2026-07-23) |
| **A/B evaluator accepts a failed baseline as positive lift** | 2026-07-24 | ✅ Fixed on branch (`bc26473`) — paired, validity-aware comparison |
| **Raw output count is mislabeled as model coverage** | 2026-07-24 | ✅ Fixed on branch (`bc26473`) — dedup'd `unique_valid` decision metric |

**Net:** the older multi-review backlog is closed. Both 2026-07-24 merge-blocking
evaluator Criticals were fixed on `feat/vision-raft-evaluate-model` (`bc26473`),
and the review's recommended validation, experiment-design, live-test, and
documentation follow-ups plus the optional CLI-guard item were fixed on the same
branch (`e2f43ad`). All 2026-07-24 findings are addressed; the branch remains
unmerged pending re-review.

---

## Review Methodology

All reviews follow the framework in:
- `System_Intructions.md` — agent behaviour guidelines
- `CLAUDE.md` — development best practices and critical invariants

## Adding New Reviews

1. **Create dated file:** `Review_Comments_YYYY_MM_DD.md` (or `YYYY-MM-DD_description.md`).
2. **Update this README:** add a newest-first entry and, if the finding recurs,
   a row in the "Recurring findings" table.
3. **Reference from CLAUDE.md** where a finding becomes a durable invariant.

---

**Review Frequency:** as needed (major versions, or on request)
**Last Updated:** 2026-07-24
