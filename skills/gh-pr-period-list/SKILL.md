---
name: gh-pr-period-list
description: Use this skill when the user asks to list, summarize, or table their own GitHub pull requests for a specified date range with the gh CLI, especially when the range should match either PR open/created time or merge time and the output should include merge timestamps.
license: MIT
---

# GH PR Period List

## Purpose

List the user's own GitHub pull requests for a repository and date range using `gh`.

The default inclusion rule is:

- include a PR when its open time (`createdAt`) is inside the requested period, or
- include a PR when its merge time (`mergedAt`) is inside the requested period.

## Non-Negotiables

- Answer in Japanese unless the user explicitly asks otherwise.
- Use `gh`; do not use web browsing for GitHub PR data.
- Resolve relative or partial dates to absolute dates before querying. If the year is ambiguous, use the current conversation date or ask.
- Default timezone is `Asia/Tokyo` unless the user specifies another timezone.
- Treat date ranges as inclusive local calendar days: start at `00:00:00`, end at `23:59:59.999999`.
- Confirm the effective GitHub author. For `自分`, use the active `gh` account from `gh api user --jq .login`.
- Include merge datetime in the output. For unmerged PRs, show `未merge`.
- Search by both open time and merge time, then de-duplicate by PR number.

## Preferred Script

Use the bundled script instead of rewriting GraphQL and timezone filtering by hand:

```sh
python3 skills/gh-pr-period-list/scripts/list_prs.py \
  --repo OWNER/REPO \
  --start YYYY-MM-DD \
  --end YYYY-MM-DD
```

Useful options:

- `--author LOGIN`: use a specific GitHub login. Omit it, or pass `@me`, for the active `gh` user.
- `--timezone Asia/Tokyo`: change the local timezone used for date filtering and display.
- `--json`: output normalized JSON instead of Markdown.

The script:

1. Resolves the active `gh` login when needed.
2. Converts the requested local date range to a UTC candidate date range.
3. Queries GitHub GraphQL search twice:
   - `created:<UTC-date>..<UTC-date>`
   - `merged:<UTC-date>..<UTC-date>`
4. De-duplicates PRs by number.
5. Filters strictly by local open or merge timestamp.
6. Prints a Markdown table sorted by open time.

## Manual Fallback

If the script cannot be used, run the two searches separately and filter locally:

```sh
gh api graphql \
  -f q='repo:OWNER/REPO is:pr author:LOGIN created:UTC_START_DATE..UTC_END_DATE sort:created-asc' \
  -f query='query($q:String!, $after:String) {
    search(query:$q, type:ISSUE, first:100, after:$after) {
      pageInfo { hasNextPage endCursor }
      nodes {
        ... on PullRequest {
          number title state isDraft createdAt mergedAt url
        }
      }
    }
  }'
```

Repeat with `merged:UTC_START_DATE..UTC_END_DATE`, then de-duplicate and filter with the local timezone. Do not rely only on GitHub search date qualifiers for the final local-day boundary because they are date-only and can include neighboring local dates.

## Output Format

Default response:

```md
`OWNER/REPO` の `LOGIN` PR（openまたはmergeが YYYY-MM-DD〜YYYY-MM-DD TZ）はN件。

| Open日時 | Merge日時 | PR | 状態 | タイトル |
|---|---|---:|---|---|
| 2026-06-01 07:02 | 2026-06-01 08:30 | [#2569](https://github.com/OWNER/REPO/pull/2569) | MERGED | docs: root AGENTS.mdを軽量化 |
```

State display rules:

- `MERGED`: merged PR.
- `OPEN`: open non-draft PR.
- `OPEN / DRAFT`: open draft PR.
- `CLOSED`: closed without merge.

## Common Checks

- If `gh` reports `Could not resolve to a Repository` or `HTTP 404`, state that the repository is not visible to the active account or the repo name may be wrong.
- If the result differs from a created-only search, explain that PRs opened before the period but merged inside the period are intentionally included.
- If there are more than 100 results, ensure pagination was fetched. The bundled script paginates automatically.
