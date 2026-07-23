# GitHub Commit & Workflow Guidelines

When the user requests a code commit, or when you are finalizing a task, adhere strictly to the following execution sequence.

## 1. Pre-Commit Analysis & Security Checks
* **Status Inspection:** Execute `git status` to capture untracked, modified, or deleted files.
* **Diff Verification:** Execute `git diff` (and `git diff --staged`) to review all modified code lines.
* **Security Audit:** Scan diffs to ensure no API keys, tokens, `.env` files, private credentials, or debug code (e.g., `console.log`, temporary prints) are staged.
* **Style Alignment:** Run `git log -n 5 --oneline` to inspect and adopt the structural style and naming conventions of recent commits.

## 2. Commit Strategy & Staging
* **Atomic Commits:** Isolate unrelated changes into distinct commits (e.g., separate refactoring, core logic, and documentation changes).
* **Explicit Staging:** Avoid `git add .` or `git add -A`. Explicitly stage related files using `git add <file1> <file2>`.
* **Pre-commit Hooks:** 
  * If a pre-commit hook auto-formats or modifies files during execution, stage the modified files and amend/commit automatically.
  * If a pre-commit hook fails due to linter or test errors, fix the issues before retrying. Never use `--no-verify` unless explicitly commanded.

## 3. Message Formatting (Conventional Commits)
All commit messages must adhere strictly to the Conventional Commits specification:
`<type>(<scope>): <description>`

* **Allowed Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`
* **Formatting Rules:**
  * Use lowercase throughout the header.
  * Use imperative mood, present tense (e.g., "add feature", not "added feature").
  * Do NOT end the commit description with a period.
  * Keep the first line under 72 characters.
* **Footer:** Include breaking changes or issue links when applicable (e.g., `Closes #124` or `Fixes #89`).

## 4. GitHub Collaboration & Pull Request Flow
* **Protected Branches:** Never commit or push directly to `main`, `master`, or standard production branches unless explicitly instructed.
* **Branch Creation:** Check the current branch with `git branch --show-current`. If on a default branch, create a short, descriptive branch:
  `git checkout -b <type>/<short-description>` (e.g., `feat/jwt-auth` or `fix/nav-bar-overlap`).
* **Pushing Upstream:** Push staged commits to origin and set the tracking branch:
  `git push -u origin <branch-name>`
* **Pull Request Creation:** Create a PR using the GitHub CLI:
  `gh pr create --fill`
  *(If `--fill` is inadequate, provide a title following Conventional Commits and a concise markdown summary of changes).*