---
name: slack-daily-report
description: Use this skill when Codex needs to create a daily report, timesheet-like activity summary, or raw work log from the user's own Slack posts for a specified date range. Trigger on requests such as "Slackから日報を作って", "6/1-6/7のSlackのやりとりをまとめて", "自分の投稿を日付・テーマ・内容・作業時間で表にして", or when combining Slack activity with git/calendar data later. Requires agent-slack, explicit Slack workspace confirmation, own-post retrieval, and output in both table and date-summary formats with Slack-writing-time estimates.
license: MIT
---

# Slack Daily Report

## Overview

Use `agent-slack` to retrieve the user's own Slack posts for a specified period and convert them into a daily-report raw table plus a date summary. Treat the time estimate as **Slack communication time inferred from message volume**, not actual implementation time.

## Safety And Setup

- Use `agent-slack` for Slack access. If `agent-slack` is missing, stop and ask the user to install or authenticate it before continuing:

```sh
agent-slack --help
agent-slack auth whoami
```

- If no usable workspace is configured, prompt setup instead of guessing. Suggested setup commands:

```sh
agent-slack auth import-desktop
agent-slack auth import-chrome
agent-slack auth import-firefox
agent-slack auth parse-curl
```

- Before reading messages, always confirm which Slack workspace to use. If the user names a workspace, verify it with `agent-slack auth whoami` and `agent-slack auth test --workspace <selector>`. If multiple plausible workspaces exist and the user did not specify one, ask a concise clarification.
- Use read-only commands only: `auth whoami`, `auth test`, `search messages`, `message list`, `channel list`, `user get/list`. Do not send, draft, edit, delete, react, invite, create channels, mark read, save later, or upload unless the user explicitly asks.
- Never expose full tokens, cookies, or secrets. `agent-slack auth whoami` redacts secrets; do not print config files that may contain raw secrets.

## Required Workflow

### 1. Confirm Workspace And User

Run:

```sh
agent-slack auth whoami
agent-slack auth test --workspace "<workspace-selector>"
```

Use the `user_id` from `auth test` as the target for "my posts". Keep the workspace selector in every later command, even if it is the default workspace.

### 2. Normalize Dates

- Interpret user dates in the user's local timezone unless they specify otherwise.
- For an inclusive end date, pass `--before` as the day after the end date. Example: for `2026-06-01` through `2026-06-07`, use `--after 2026-06-01 --before 2026-06-08`.
- Include days with no Slack posts in the final output as `Slack上の該当投稿なし`.
- Add Japanese weekday labels: `月`, `火`, `水`, `木`, `金`, `土`, `日`.

### 3. Fetch Own Posts

Start with:

```sh
agent-slack search messages "" \
  --workspace "<workspace-selector>" \
  --user "<user_id>" \
  --after YYYY-MM-DD \
  --before YYYY-MM-DD_PLUS_ONE \
  --limit 200 \
  --max-content-chars -1 \
  --resolve-users
```

If the result count is exactly `200`, do not assume it is complete. Split the query by day. If any single day still returns `200`, split by channel using `agent-slack channel list` plus channel-filtered searches.

For important threads where the user's post is only a reply or the surrounding context is necessary, fetch the thread with:

```sh
agent-slack message list "<permalink>" \
  --workspace "<workspace-selector>" \
  --max-body-chars 1200 \
  --resolve-users
```

Use thread context to improve the summary, but calculate Slack-writing time from the user's own messages only unless the user asks otherwise.

### 4. Group Into Report Rows

Create rows by `date + theme`, not by individual message. Merge nearby messages when they support the same work theme. Prefer concrete business/action themes over channel names.

Each row must have:

- `日付`
- `曜日`
- `テーマ`
- `具体的な内容`
- `作業時間`

Write `具体的な内容` as a concise action summary. Include concrete nouns, systems, projects, people, or decisions when visible in Slack. Avoid copying long message text.

### 5. Estimate Slack Writing Time

Estimate time from message volume, not from the clock span between messages.

Use this default model unless the user specifies another one:

- Count the user's characters in each row's source messages. Japanese, ASCII, URLs, and mentions all count as characters.
- Add per-message overhead for reading context, choosing wording, and sending:
  - `1.0 minute` per text message
  - `1.0 minute` per file-only message
- Add typing/composition time:
  - `characters / 60` minutes
- Row raw minutes:

```text
raw_minutes = (total_characters / 60) + message_count
```

- Convert to hours and round **up** to the nearest `0.25h`:

```text
work_hours = ceil(raw_minutes / 15) * 0.25
```

- If a row has at least one source message, the minimum displayed time is `0.25h`.
- If a day has no source messages, display `-`.
- Label these values as Slack-writing-time estimates if there is any risk the user may read them as actual work duration.

## Output Format

Always provide both formats unless the user asks for only one.

### Table

Use this exact column order:

```md
| 日付 | 曜日 | テーマ | 具体的な内容 | 作業時間 |
|---|---|---|---|---|
| 2026-06-01 | 月 | Slack上の該当なし | 自分の投稿なし | - |
| 2026-06-02 | 火 | バイセル不備確認AI Phase2 | 利用方針・リリース目途を確認し、売上影響を踏まえて推進意図を共有 | 0.5h |
```

### Date Summary

Use this shape:

```md
**2026-06-02（火）**
- 工数計上・休日設定の確認と提出報告（0.25h）
- バイセル不備確認AI Phase2 の方針確認と売上影響の共有（0.5h）
```

For days with no posts:

```md
**2026-06-01（月）**
- Slack上の該当投稿なし
```

## Final Notes

- State the workspace, user, period, and retrieved message count before the report when useful.
- Mention if the result hit an API/search limit and how it was mitigated.
- If the user plans to combine git or calendar later, keep the Slack table as a raw activity layer and avoid overfitting it into a final daily report.
