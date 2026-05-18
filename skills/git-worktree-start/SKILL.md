---
name: git-worktree-start
description: Prepare a git repository for code changes by syncing the base branch with origin, creating a dedicated worktree, and starting a codex-prefixed branch before editing files. Use when the user asks to implement, fix, refactor, or otherwise modify files in a repository.
license: MIT
---

# Git Worktree Start

## Overview

Use this skill before making code changes in a git repository. The goal is to start from the latest base branch, isolate the task in a dedicated worktree, and keep the actual work on a `codex/` branch.

## When To Use

- The user asks to implement, fix, refactor, or otherwise change files in a git repository.
- The task will require edits, tests, commits, or PR work.
- Skip this skill for read-only investigation, code review, or documentation-only discussion unless the user also wants committed file changes.

## Standard Sequence

1. Identify the repository root, the base branch, and whether the current worktree is clean.
2. Run `git fetch origin`.
3. Sync the local base branch to `origin/<base>` before starting the task.
4. Create a dedicated worktree at a sibling path such as `../<repo>-<task-slug>`.
5. Create a task branch named `codex/<task-slug>` from `origin/<base>` as part of `git worktree add -b`.
6. Continue all edits, tests, commits, and PR work inside the new worktree.

## Preferred Commands

Run the setup in this order whenever the repository state allows it:

```sh
git fetch origin
git switch <base>
git pull --ff-only origin <base>
git worktree add -b codex/<task-slug> ../<repo>-<task-slug> origin/<base>
```

## Guardrails

- Never use `git reset --hard`, `git checkout --`, or other destructive commands to force the base branch into sync.
- If the current worktree has uncommitted changes, do not reuse it for the new task. Leave it untouched and find a clean worktree for syncing the base branch.
- If the base branch cannot be fast-forwarded cleanly, stop and resolve that state before creating the new worktree.
- If `codex/<task-slug>` already exists, append a numeric suffix such as `codex/<task-slug>-2`.
- If the target worktree path already exists, choose a new sibling path rather than overwriting it.
- After setup, explicitly tell the user which absolute worktree path and branch name are being used for the task.

## Notes

- Prefer `origin/<base>` as the starting point for the new branch, even if the local base branch was just updated.
- If another skill handles the main task afterward, finish this setup first and then continue with that skill in the new worktree.

## Example

```sh
git fetch origin
git switch main
git pull --ff-only origin main
git worktree add -b codex/fix-login-timeout ../repo-fix-login-timeout origin/main
```
