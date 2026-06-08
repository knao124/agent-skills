---
name: daily-report
description: "Use this skill when Codex needs to create a Japanese daily report from GitHub PRs, Slack posts, and Google Calendar events for a specified date or date range. Trigger on requests such as 日報を作って, 6/1-6/5の日報, Slack/PR/カレンダーを統合して日報化, or when the user wants the final Slack-postable bullet format. This skill orchestrates existing skills: slack-daily-report, gh-pr-period-list, and gws-calendar-agenda."
license: MIT
---

# Daily Report

## Overview

Create a Japanese daily report by combining three raw activity layers:

- GitHub PRs for development work.
- Google Calendar events for meetings.
- Slack posts for communication and coordination work.

This skill only orchestrates, filters, groups, and formats. Always use the existing source-specific skills for data collection.

## Required Skills

Use all three skills below. Do not bypass them with ad hoc direct collection unless the user explicitly asks for a fallback after a blocking failure.

- `$slack-daily-report` for Slack workspace confirmation, own-post retrieval, thread context, and Slack activity grouping.
- `$gh-pr-period-list` for GitHub PR retrieval by open or merge date.
- `$gws-calendar-agenda` for Google Calendar retrieval and participation status handling.

If any required skill is not installed or not available, stop before collecting data and tell the user to install it from `knao124/agent-skills` with `gh skill`:

```sh
gh skill install knao124/agent-skills slack-daily-report --agent codex --scope user --force
gh skill install knao124/agent-skills gh-pr-period-list --agent codex --scope user --force
gh skill install knao124/agent-skills gws-calendar-agenda --agent codex --scope user --force
```

Then ask the user to retry the daily report request after installation.

## Start By Confirming Scope

Before fetching private data, ask for the source scope unless the current user message already names it explicitly.

Ask for:

- Slack workspace: workspace name, URL, or selector for `$slack-daily-report`.
- GitHub repositories: one or more `OWNER/REPO` values for `$gh-pr-period-list`.
- Calendar identity: Google account and calendar target for `$gws-calendar-agenda`; default to `primary` only after the user confirms the account.
- Date or date range if the user did not provide one.

Keep the question concise. Example:

```text
日報作成のため、Slack workspace、参照するGitHub repository一覧、利用するGoogleカレンダーアカウントを教えてください。日付範囲も未指定ならあわせてください。
```

If the user provided all values in the current turn, state the resolved scope and proceed.

## Collection Workflow

1. Resolve all dates to absolute local dates. Default timezone is `Asia/Tokyo` unless the user specifies otherwise.
2. Invoke `$gh-pr-period-list` once per repository for the full requested date range.
   - Include PRs whose open date or merge date falls inside the range.
   - Prefer JSON output when available so PRs can be grouped by local date.
   - For the final development section, use only PR-derived information. Do not add Slack-derived development topics to `開発`.
3. Invoke `$gws-calendar-agenda` for the requested date range and confirmed calendar account.
   - After obtaining the calendar rows, filter them for the final report.
   - Keep only participation statuses `参加` and `主催者` by default.
   - Remove `未回答`, `仮参加`, `不参加`, and `不明`.
   - Remove unclear blocking/private events such as `予定あり`, `NG枠`, blank titles, and `(no title)`.
   - Keep event times and titles. Omit location unless the user asks for it.
4. Invoke `$slack-daily-report` for the requested date range and confirmed workspace.
   - Use its own-post retrieval and thread-context guidance.
   - Use its grouped themes and concrete summaries as the raw Slack layer.
   - For the final report, omit Slack-writing-time estimates unless the user explicitly asks for time estimates.
5. Merge the three layers by date.

## Grouping Rules

Use a small number of practical themes. Prefer concrete product/project names over generic categories.

For `開発`:

- Group PRs by repository area or feature based only on PR titles and repository names.
- Link every PR in Markdown.
- Use this link format exactly:
  `[OWNER/REPO #NUMBER TITLE](URL)`
- If a PR is not merged, append status after the link, for example `（OPEN / DRAFT）` or `（CLOSED）`.
- If the same PR is opened and merged on the same report date, list it once.
- If a PR is opened on one report date and merged on another, it may appear on both dates because both dates contain PR activity.

For `会議`:

- List filtered calendar events chronologically.
- Use `HH:MM-HH:MM TITLE`.
- If no events remain after filtering, write `該当予定なし`.

For `slack`:

- Group into themes from Slack content and thread context.
- Summarize actions, decisions, confirmations, and coordination work.
- Do not copy long message text.
- Avoid including purely casual messages unless they explain work coordination. If only casual/short messages exist, group them as `その他`.

## Final Output Format

Return one fenced Markdown code block per date. Do not put all dates in a single code block.

Inside each code block:

- Start with a plain date line: `YYYY/MM/DD（曜）`.
- Do not use Markdown headings such as `#` or `##`.
- Use only bullet lists for sections.
- Use `* 開発`, `* 会議`, and `* slack` as top-level bullets.
- Express nesting with exactly four half-width spaces per level.
- Keep section names lowercase for `slack`.
- If a layer has no data, include one bullet such as `該当PRなし`, `該当予定なし`, or `Slack上の該当投稿なし`.

Template:

```markdown
2026/06/01（月）

* 開発
    * ドキュメント・作業環境整備
        * [dhk-devs/canvas-ai #2569 docs: root AGENTS.mdを軽量化](https://github.com/dhk-devs/canvas-ai/pull/2569)
* 会議
    * 08:00-08:15 [int/web] DHK-PMIチーム定例
    * 11:50-12:00 月初朝礼
* slack
    * SLI/SLO・エラートリアージ運用
        * DHKでも利用するため、aimstar側のskill共有を依頼
        * 共有されたskillを一旦利用する方針を確認
```

For multiple days, repeat the same fenced-block shape once per date.

## Reporting Notes

- Answer in Japanese unless the user asks otherwise.
- Before the final report, mention any data source that could not be collected or was truncated.
- Keep raw source tables out of the final answer unless the user asks for raw data.
- Never expose Slack tokens, cookies, private calendar IDs, internal event IDs, or raw API JSON.
