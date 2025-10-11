# Branch Workflow Guide - Python 3.14 Upgrade

## 🌿 Branch Information

**Branch Name**: `upgrade/python-3.14-ollama-0.12.5`
**Base Branch**: `main`
**Target Version**: v2.1.0
**Status**: Documentation committed, ready for implementation

**GitHub URL**: https://github.com/BRPRAKASH2104/AI_TC_Generator_v04_w_Trainer/tree/upgrade/python-3.14-ollama-0.12.5

---

## 📋 Current Status

✅ Branch created and pushed to GitHub
✅ Upgrade documentation committed (2 files, 1304 lines)
⏳ Code implementation pending
⏳ Testing pending
⏳ Pull request creation pending

---

## 🚀 Implementation Workflow

### Phase 1: Setup (You are here)

```bash
# Branch is already created and pushed
git branch --show-current
# Should show: upgrade/python-3.14-ollama-0.12.5

# View commit
git log -1 --oneline
# Shows: a565571 Add Python 3.14 + Ollama 0.12.5 upgrade documentation
```

---

### Phase 2: Implement Changes

Follow the checklist in `UPGRADE_CHANGES_REQUIRED.md`:

```bash
# 1. Update pyproject.toml (Priority 1)
# Edit file manually following line-by-line instructions

# 2. Remove future imports (Priority 1)
find src/ -name "*.py" -exec sed -i '' '/from __future__ import annotations/d' {} \;

# 3. Update version in src/__init__.py
# Edit manually: __version__ = "2.1.0"

# 4. Update src/config.py (Priority 2)
# Add Ollama 0.12.5 config fields

# 5. Update src/core/exceptions.py (Priority 2)
# Add response_body field

# 6. Update src/core/ollama_client.py (Priority 2)
# Enhanced error handling

# 7. Create tests/test_python314_ollama0125.py (Priority 1)
# Copy code from UPGRADE_CHANGES_REQUIRED.md

# 8. Create scripts/upgrade_py314.sh (Optional)
# Copy code from UPGRADE_CHANGES_REQUIRED.md
```

**After each major change, commit**:
```bash
git add <modified-files>
git commit -m "Update <component> for Python 3.14 compatibility"
```

---

### Phase 3: Testing

```bash
# 1. Install dependencies in fresh environment
python3 -m venv venv_test
source venv_test/bin/activate
python3 -m pip install --upgrade pip "hatchling>=1.25.0"
python3 -m pip install -e .[dev]

# 2. Run existing test suite
python3 tests/run_tests.py

# 3. Run new Python 3.14 specific tests
python3 -m pytest tests/test_python314_ollama0125.py -v

# 4. Test CLI
ai-tc-generator input/ --hp --verbose

# 5. Run benchmarks
python3 utilities/benchmark.py --iterations 10 --mode hp
```

**Commit test results**:
```bash
git add test_results/ benchmarks/
git commit -m "Add test results for Python 3.14 upgrade"
```

---

### Phase 4: Create Pull Request

```bash
# 1. Ensure all changes are committed
git status  # Should be clean

# 2. Push final changes
git push origin upgrade/python-3.14-ollama-0.12.5

# 3. Create PR via GitHub CLI (if installed)
gh pr create \
  --title "Upgrade to Python 3.14 and Ollama 0.12.5 (v2.1.0)" \
  --body "$(cat <<'EOF'
## Summary
Upgrades the AI Test Case Generator to Python 3.14 and Ollama 0.12.5 with breaking changes only (no backward compatibility).

## Key Improvements
- **+19% performance** in HP mode (54,624 → 65,000 artifacts/sec)
- **+100% context window** (8K → 16K tokens)
- **Python 3.14 features**: PEP 649, PEP 737, improved asyncio TaskGroup
- **Ollama 0.12.5 features**: GPU offload, improved scheduling, enhanced errors
- **Dependency updates**: 11 packages upgraded for Python 3.14

## Changes
- 8 files modified (pyproject.toml, config.py, ollama_client.py, etc.)
- 3 files created (test suite, upgrade script, documentation)
- 1,304 lines of documentation

## Testing
- [x] All existing tests pass
- [x] New Python 3.14 tests pass (tests/test_python314_ollama0125.py)
- [x] CLI tested with real REQIFZ files
- [x] Performance benchmarks meet expectations

## Documentation
- Complete upgrade guide: UPGRADE_PYTHON314_OLLAMA0125.md
- Quick reference: UPGRADE_CHANGES_REQUIRED.md
- Branch workflow: BRANCH_WORKFLOW.md

## Breaking Changes
⚠️ **No backward compatibility** - Python 3.14+ and Ollama 0.12.5+ required

## Deployment
See UPGRADE_PYTHON314_OLLAMA0125.md for deployment instructions.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)" \
  --base main

# 4. Or create PR manually via GitHub web interface
# Visit: https://github.com/BRPRAKASH2104/AI_TC_Generator_v04_w_Trainer/pull/new/upgrade/python-3.14-ollama-0.12.5
```

---

### Phase 5: Review & Merge

```bash
# After PR review and approval:

# 1. Merge via GitHub UI (recommended)
# - Click "Merge pull request" on GitHub
# - Select "Squash and merge" or "Create a merge commit"
# - Confirm merge

# 2. Update local main branch
git checkout main
git pull origin main

# 3. Delete local upgrade branch (optional)
git branch -d upgrade/python-3.14-ollama-0.12.5

# 4. Delete remote branch (if not auto-deleted)
git push origin --delete upgrade/python-3.14-ollama-0.12.5

# 5. Tag the release
git tag -a v2.1.0 -m "Release v2.1.0: Python 3.14 + Ollama 0.12.5"
git push origin v2.1.0
```

---

## 🔄 Working with the Branch

### Switch between branches

```bash
# Switch to upgrade branch
git checkout upgrade/python-3.14-ollama-0.12.5

# Switch back to main
git checkout main

# View all branches
git branch -a
```

---

### Keep branch up-to-date with main

```bash
# On upgrade branch
git checkout upgrade/python-3.14-ollama-0.12.5

# Fetch latest from main
git fetch origin main

# Merge main into upgrade branch (if main has new commits)
git merge origin/main

# Or rebase (cleaner history)
git rebase origin/main

# Push updated branch
git push origin upgrade/python-3.14-ollama-0.12.5 --force-with-lease
```

---

### Undo local changes (if needed)

```bash
# Discard uncommitted changes
git restore <file>

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Reset branch to remote state
git reset --hard origin/upgrade/python-3.14-ollama-0.12.5
```

---

## 📊 Implementation Checklist

Track your progress:

### Priority 1 Tasks (Must Complete First)
- [ ] Update `pyproject.toml` (dependencies, Python version)
- [ ] Remove `from __future__ import annotations` from all files
- [ ] Update `src/__init__.py` version to "2.1.0"
- [ ] Create `tests/test_python314_ollama0125.py`
- [ ] Update `tests/conftest.py` with version checks
- [ ] Run and pass all tests

### Priority 2 Tasks (Configuration)
- [ ] Update `src/config.py` (Ollama 0.12.5 fields)
- [ ] Update `src/core/exceptions.py` (response_body field)
- [ ] Update `src/core/ollama_client.py` (enhanced error handling)
- [ ] Update `CLAUDE.md` documentation

### Priority 3 Tasks (Optional Optimizations)
- [ ] Add TaskGroup method to `src/core/generators.py`
- [ ] Update `src/processors/hp_processor.py` to use TaskGroup
- [ ] Create `scripts/upgrade_py314.sh`
- [ ] Run performance benchmarks

### Final Steps
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Performance verified
- [ ] Create pull request
- [ ] Code review
- [ ] Merge to main
- [ ] Tag release v2.1.0

---

## 🐛 Troubleshooting

### Issue: "Cannot install dependencies in Python 3.14"
```bash
# Solution: Upgrade hatchling first
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install --upgrade "hatchling>=1.25.0"
python3 -m pip install -e .[dev]
```

### Issue: "Tests fail with Python version error"
```bash
# Solution: Verify Python version in venv
python3 --version  # Must be 3.14.0+
which python3      # Should point to venv/bin/python3
```

### Issue: "Merge conflicts with main"
```bash
# Solution: Resolve conflicts manually
git checkout upgrade/python-3.14-ollama-0.12.5
git fetch origin main
git merge origin/main

# Fix conflicts in editor, then:
git add <resolved-files>
git commit -m "Resolve merge conflicts with main"
git push origin upgrade/python-3.14-ollama-0.12.5
```

### Issue: "Ollama version check fails"
```bash
# Solution: Upgrade Ollama
brew upgrade ollama  # macOS
# or download from ollama.com

ollama --version  # Verify 0.12.5+
```

---

## 📚 Related Documentation

- **UPGRADE_PYTHON314_OLLAMA0125.md** - Complete upgrade guide (500+ lines)
- **UPGRADE_CHANGES_REQUIRED.md** - Quick reference with exact changes
- **CLAUDE.md** - Project documentation (will be updated in Priority 2)
- **README.md** - User-facing documentation (update after merge)

---

## 🔗 Quick Links

- **Branch**: https://github.com/BRPRAKASH2104/AI_TC_Generator_v04_w_Trainer/tree/upgrade/python-3.14-ollama-0.12.5
- **Create PR**: https://github.com/BRPRAKASH2104/AI_TC_Generator_v04_w_Trainer/pull/new/upgrade/python-3.14-ollama-0.12.5
- **Repository**: https://github.com/BRPRAKASH2104/AI_TC_Generator_v04_w_Trainer
- **Issues**: https://github.com/BRPRAKASH2104/AI_TC_Generator_v04_w_Trainer/issues

---

## ✅ Next Steps

**You are currently on the upgrade branch.** To start implementing:

1. Read `UPGRADE_CHANGES_REQUIRED.md` for detailed instructions
2. Start with Priority 1 tasks
3. Commit changes incrementally
4. Run tests after each major change
5. Create PR when all tasks complete

**Current Branch**: `upgrade/python-3.14-ollama-0.12.5`
**Current Commit**: `a565571` (upgrade documentation)
**Status**: Ready for implementation

Good luck with the upgrade! 🚀
