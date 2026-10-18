---
name: daily-report
description: "Create or revise Japanese daily reports from supplied work logs or requested GitHub PR, Slack, and Google Calendar sources. Use for 日報を作って, 日報の形式を更新して, or reports for a date range. Include hours on every work item, estimate unknown breakdowns within known daily totals, use separate date and ■ 本日（合計 X.Xh） lines, and omit links and ひとこと by default."
license: MIT
---

# Daily Report

## Overview

Create a Japanese daily report from work records already supplied in the conversation, or collect the requested external activity layers:

- GitHub PRs for development work.
- Google Calendar events for meetings.
- Slack posts for communication and coordination work.

When the user supplies the work records, format those records directly without fetching unrelated sources or asking for Slack/GitHub/Calendar scope. When external collection is needed, use the existing source-specific skills below for only the sources requested by the user.

## Required Skills

These dependencies apply only when collecting the corresponding external source. Supplied-log formatting does not require any of them. Do not bypass a required source-specific skill with ad hoc collection unless the user explicitly asks for a fallback after a blocking failure.

- `$slack-daily-report` for Slack workspace confirmation, own-post retrieval, thread context, and Slack activity grouping.
- `$gh-pr-period-list` for GitHub PR retrieval by open or merge date.
- `$gws-calendar-agenda` for Google Calendar retrieval and participation status handling.

If a skill needed for a requested external source is not installed or not available, stop collection of that source and tell the user to install it from `knao124/agent-skills` with `gh skill`:

```sh
gh skill install knao124/agent-skills slack-daily-report --agent codex --scope user --force
gh skill install knao124/agent-skills gh-pr-period-list --agent codex --scope user --force
gh skill install knao124/agent-skills gws-calendar-agenda --agent codex --scope user --force
```

Then ask the user to retry the daily report request after installation.

## Start By Confirming Scope

For supplied records, resolve dates and daily totals from the conversation and proceed. Before fetching additional private data, ask only for the missing scope of the requested sources; reuse scope already confirmed in the conversation.

For external collection, ask only for applicable missing values:

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

1. Resolve all dates to absolute local dates. Default timezone is `Asia/Tokyo` unless the user specifies otherwise. For supplied records, skip external collection steps 2–4 and group the provided activities by date.
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

For the raw `開発` layer (map it to the final practical themes below):

- Group PRs by repository area or feature based only on PR titles and repository names.
- Keep PR repository, number, title, URL, and status in the source notes. Omit hyperlinks and bare URLs from the final report by default. If the user explicitly requests links, use `[OWNER/REPO #NUMBER TITLE](URL)`.
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

## Hours and Allocation

- Put a duration in hours on every work item, including nested items: `（0.5h）`. Put each category's subtotal next to its name, and the daily total on the separate `■ 本日` line.
- Preserve supplied durations and daily totals. Derive known durations from explicit start/end times; exclude gaps and avoid double-counting overlapping work.
- When a daily total is known but some item durations are missing, distribute the remaining time reasonably across those items. Prefer simple increments such as 0.25h, 0.5h, and 1h; use finer increments when necessary to preserve exact totals. Do not block on an unknown breakdown or ask the user to allocate every item.
- Keep previously agreed estimated allocations unless the user asks to revise them. Estimates apply only to time allocation: do not invent activities, achievements, participants, or links.
- If a daily total is missing and cannot be derived from provided times, ask only for that total. If supplied fixed item times exceed the daily total or otherwise conflict, surface the conflict rather than silently changing fixed durations.
- Mention once outside the report that uncertain breakdowns are approximate. Do not mark every item with repetitive caveats.
- For nested items, the parent duration includes its children. Count the parent once toward the category subtotal; do not add parent and child durations together. Merge short explanations into the timed parent bullet when nesting adds no value.
- Check that work items sum to each category subtotal and that category subtotals sum to each daily total. Include travel only when it is already part of the user's reported work total, and make its duration explicit.
- Estimates in a report are not authorization to modify attendance records or external timesheets. Use actual approved start/end and break times for those actions.

## Final Output Format

Use rendered Markdown in an editable writing block when the host supports it, otherwise ordinary Markdown. Do not wrap reports in code fences unless the user requests raw Markdown.

- Start each day with exactly two lines: `YYYY/MM/DD（曜）`, then `■ 本日（合計 X.Xh）`. Keep a real line break between them; use a Markdown hard break when needed so rendered text also stays on two lines.
- Show daily totals with at least one decimal place, such as `4.0h` or `1.5h`; preserve finer precision when rounding would change the total. Item and category durations may use `2h`, `0.5h`, or `0.25h`.
- Do not add `ひとこと`, impressions, or a closing comment. Follow explicit user overrides when a different heading is requested.
- Group work under inline-code category labels and write the subtotal outside the inline code: `` `共通業務`（3h） ``.
- Reuse the user's categories, such as `共通機能開発`, `個別案件`, and `その他`. For infrastructure and security work, `共通業務` is suitable. Do not force non-development work into `共通機能開発`.
- Use `-` bullets with concrete work descriptions and a duration on every item. Remove Markdown link destinations and bare URLs by default, retaining the descriptive text and useful PR identifiers. Include links only when explicitly requested.
- Omit empty categories. Separate multiple days with `---`. A single multi-day report can occupy one writing block.
- Keep the actual work date even if the attendance system uses a different paired date for a holiday exchange.

Template:

```markdown
2026/06/01（月）  
■ 本日（合計 4.0h）

`共通業務`（2h）

- インフラ定例（0.5h）
- ロードマップ資料作成（1.5h）

`個別案件`（1h）

- PBX連携の打ち合わせ（1h）

`その他`（1h）

- 1on1（0.5h）
- 承認事務（0.5h）
```

For revisions, preserve the same writing-block ID and existing report content unless the user requests further changes. If the user asks to receive copyable text before skill/configuration work, deliver the revised report first, then perform the update and report completion briefly. A request to remove a heading does not authorize reallocating previously agreed hours.

## Reporting Notes

- Answer in Japanese unless the user asks otherwise.
- Before the final report, mention any data source that could not be collected or was truncated.
- Keep raw source tables out of the final answer unless the user asks for raw data.
- Never expose Slack tokens, cookies, private calendar IDs, internal event IDs, or raw API JSON.
