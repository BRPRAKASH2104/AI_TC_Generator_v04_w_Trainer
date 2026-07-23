# GitHub Commit & Workflow Guidelines
When requested to commit code or finalize a task, strictly adhere to the following execution sequence.

## 1. Pre-Commit Analysis & Security Checks
* **DO** check the current branch *before* creating or editing files: `git branch --show-current`.
* **DO** run `git status` to identify all modified, untracked, or deleted files before staging.
* **DO** run `git diff` and `git diff --staged` to audit modified lines (and check untracked files explicitly).
* **DO NOT** commit staged files without scanning for hardcoded secrets, `.env` variables, API keys, credentials, or temporary debug logs (e.g., `console.log`, `print()`, `debugger`).
* **DO** run `git log -n 5 --oneline` to match the repository's commit style and history format.

## 2. Commit Strategy & Staging
* **DO** break unrelated changes into separate, isolated commits (e.g., keep refactoring, core logic, and documentation separate).
* **DO** explicitly stage files by name: `git add <file1> <file2>`.
* **DO NOT** use `git add .` or `git add -A` under any circumstances to prevent accidental staging.
* **DO NOT** use `--no-verify` to bypass failing pre-commit hooks unless explicitly instructed by the user.
* **DO** fix any linting, formatting, or test failures thrown by pre-commit hooks before attempting to commit again. If a hook auto-formats files, stage those auto-formatted files and amend or complete the commit.

## 3. Message Formatting (Conventional Commits)
All commit messages must strictly follow the format: `<type>(<scope>): <description>`

* **DO** restrict `<type>` strictly to: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, or `chore`.
* **DO** use lowercase text and imperative present-tense verbs (e.g., `feat(auth): add jwt token validation`).
* **DO** keep the primary subject line under 72 characters.
* **DO NOT** put a trailing period (`.`) at the end of the commit summary line.
* **DO NOT** use past tense (e.g., write `add`, not `added`; `fix`, not `fixed`).
* **DO** include footers like `Closes #124` or `Fixes #89` if a related issue is identified in the prompt or context.

## 4. Branching & Lifecycle Management
* **DO** inspect the current working branch using `git branch --show-current` prior to making changes or staging commands.
* **When on `main` or `master`:**
  * **DO NOT** commit code or push directly to `main` or `master` unless explicitly instructed by the user.
  * **DO** immediately create and switch to a new branch before modifying or staging files:
    `git checkout -b <type>/<short-description>` (e.g., `feat/jwt-auth`, `fix/nav-bar-overlap`).
* **When on a feature or fix branch:**
  * **DO** keep all ongoing work, incremental commits, and pushes on this active branch.
  * **DO NOT** switch back to `main`/`master` or delete the active branch until changes are merged.
* **Push & Pull Request Execution:**
  * **DO** set the upstream tracking branch on first push: `git push -u origin <branch-name>`.
  * **DO** open Pull Requests using the GitHub CLI: `gh pr create --fill`. If `--fill` fails or prompts interactively, use explicit flags: `gh pr create --title "<type>(<scope>): <description>" --body "<summary of changes>"`.
  * **DO NOT** checkout or pull into `main`/`master` until the PR has been officially merged.