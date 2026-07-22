#!/usr/bin/env bash
#
# Verify that the shell examples advertised in the documentation actually work.
#
# Scope: only the invocations that need neither a running Ollama service nor a
# real REQIFZ input file. This is the executable half of review 2026-07-20
# Recommended finding 7 ("treat executable examples as the documentation source
# of truth ... verify shell examples in CI").
#
# Run locally the same way CI does:  bash scripts/verify_doc_examples.sh
#
set -euo pipefail

cd "$(dirname "$0")/.."

fail=0

# Assert a command exits 0.
expect_ok() {
    local desc="$1"; shift
    if "$@" >/dev/null 2>&1; then
        echo "  ok   : $desc"
    else
        echo "  FAIL : $desc (expected exit 0, got $?)"
        fail=1
    fi
}

# Assert a command exits non-zero (documented as an error/unsupported path).
expect_fail() {
    local desc="$1"; shift
    if "$@" >/dev/null 2>&1; then
        echo "  FAIL : $desc (expected non-zero exit, got 0)"
        fail=1
    else
        echo "  ok   : $desc (exits non-zero as documented)"
    fi
}

echo "Verifying documented CLI examples (no Ollama / no input file required)..."

# Core utility invocations documented in README.md / docs/USER_MANUAL.md.
expect_ok "ai-tc-generator --help"             python3 main.py --help
expect_ok "ai-tc-generator --validate-prompts" python3 main.py --validate-prompts
expect_ok "ai-tc-generator --list-templates"   python3 main.py --list-templates

# Training utilities documented in docs/training/README.md expose --help.
expect_ok "utilities/train_vision_model.py --help"  python3 utilities/train_vision_model.py --help
expect_ok "utilities/build_vision_dataset.py --help" python3 utilities/build_vision_dataset.py --help
expect_ok "utilities/annotate_raft.py --help"        python3 utilities/annotate_raft.py --help

# --training is documented as not implemented in this CLI: it must NOT report
# success (Archived finding 12). The training branch runs before any REQIFZ
# parsing, so any existing file satisfies Click's exists=True and reaches it;
# pyproject.toml is always present. Guard that the honesty fix stays in place.
expect_fail "ai-tc-generator --training (unsupported)" python3 main.py pyproject.toml --training

if [ "$fail" -ne 0 ]; then
    echo "Documentation example verification FAILED."
    exit 1
fi
echo "All documented examples verified."
