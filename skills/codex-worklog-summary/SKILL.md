---
name: codex-worklog-summary
description: Use this skill when the user asks to summarize a Codex thread, Codex session, work time, tool execution timeline, or conversation-compressed worklog as folded Markdown text for a PR comment or audit note. Triggers include Codex作業ログ, 会話圧縮メモ, PRに作業時間を残す, rollout log, session log, or a request to output but not post a PR worklog comment.
license: MIT
---

# Codex Worklog Summary

## Purpose

Output a folded Markdown worklog from Codex local session logs. This skill only produces text; it does not create, edit, or comment on pull requests.

Use it to preserve enough context to reconstruct the Codex conversation and work sequence without pasting the full transcript.

## Non-Negotiables

- Answer in Japanese unless the user asks otherwise.
- Produce text only. Do not post a GitHub PR comment, edit a PR body, or open a PR from this skill.
- Treat Codex logs as local/private. Do not include secrets, OAuth client secrets, raw tokens, full tool outputs, browser URLs with sensitive query strings, or raw calendar/email/Slack/private data.
- If the worklog cannot be understood without mentioning sensitive material, blur it absolutely: replace values and private content with generic labels such as `[OAuth client secret]`, `[private calendar detail]`, `[customer name]`, or `[internal URL]`, and describe only the operational role it played.
- Prefer Codex local rollout logs over GitHub timestamps when the user asks about Codex-side time.
- Keep the output folded with `<details>` unless the user asks for another container.
- Do not include `Implementation Summary` or `Verification` sections by default. This skill is for conversation/worklog reconstruction, not PR review evidence.

## Standard Output Format

Use this shape:

```md
<details>
<summary>Codex作業ログ / 会話圧縮メモ</summary>

## Source
- Source: Codex local rollout log
- Thread: `<thread title>`
- Times: JST
- Scope: <PR number/title or user-described scope>

## Time
- 前段含む会話: YYYY-MM-DD HH:MM:SS → HH:MM:SS（X分Y秒）
- PR作業本体: YYYY-MM-DD HH:MM:SS → HH:MM:SS（X分Y秒）
- PR作業中のtool実行: `exec_command` N回、`apply_patch` N回、...

## Conversation Context
- HH:MM:SS ...

## PR Work Timeline
- HH:MM:SS ...

</details>
```

Rename `PR Work Timeline` to `Work Timeline` when the target is not a PR.

## Workflow

1. Determine the target scope.
   - For PR work, use the user request that started the PR-producing work as `PR作業本体` start.
   - Use the final completion report, merge/local install report, or latest relevant assistant message as the end.
   - Keep earlier setup/discovery in `Conversation Context`.
   - If the start or end is ambiguous, ask the user for the boundary before producing the final text.
2. Locate the Codex thread.
   - Check `~/.codex/state_5.sqlite` `threads` for title, thread id, rollout path, and timestamps.
   - If needed, search `~/.codex/session_index.jsonl` and `~/.codex/sessions/**/rollout-*.jsonl` for exact user phrases.
3. Generate a scaffold with the bundled script, then rewrite it into the standard format.
4. Compress semantically:
   - Keep every user request that changed scope or requirements.
   - Keep assistant decisions that explain approach changes, blockers, and recovery.
   - Keep tool failures that affected the path.
   - Keep commits, PR creation, CI, merge, install, and cleanup events when relevant.
   - Omit raw command output unless it is the key evidence for a decision.
   - Redact sensitive facts before writing the final text. Keep the event shape, decision, and timing; remove or generalize the secret, personal data, private content, account identifiers, and exact private URLs.
5. Return only the Markdown text unless the user asks for explanation.

## Script

Use `scripts/codex_worklog_summary.py` to extract a timestamped scaffold from Codex logs:

```sh
python3 skills/codex-worklog-summary/scripts/codex_worklog_summary.py \
  --title-contains "選定 GoogleカレンダーCLI" \
  --scope "PR #21 feat: gwsカレンダー一覧skillを追加" \
  --work-start "2026-06-08 09:04:34" \
  --work-end "2026-06-08 09:15:00"
```

Useful options:

- `--thread-id <id>`: select an exact thread.
- `--title-contains <text>`: select the latest thread whose title contains text.
- `--rollout-path <path>`: read a specific rollout JSONL directly.
- `--work-start` / `--work-end`: local JST time or ISO timestamp.
- `--context-limit <n>`: number of pre-work conversation bullets to keep.

The script output is a scaffold. Before final delivery, tighten wording, merge repetitive assistant progress updates, and remove sensitive details.

## Time Rules

- Use JST by default.
- Include exact dates when the output spans multiple dates.
- Report both broad conversation duration and scoped work duration when both are useful.
- Tool counts should be counted inside the scoped work window, not the whole thread, unless explicitly requested.

## Comment Handoff

When another skill or workflow needs to post this text to a PR, hand off the final Markdown only. The posting workflow should decide whether to run:

```sh
gh pr comment <number> --body-file <file>
```

Do not run that command from this skill.
