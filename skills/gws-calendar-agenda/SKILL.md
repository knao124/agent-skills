---
name: gws-calendar-agenda
description: Use this skill when the user asks to fetch, list, summarize, or table their own Google Calendar events for a date or date range with the gws CLI, especially requests such as カレンダーを一覧化, 予定を表にして, 指定期間の予定, 参加状態, or Google Calendar without MCP.
license: MIT
---

# GWS Calendar Agenda

## Purpose

Fetch the user's own Google Calendar events with `gws` and return a compact Japanese Markdown table. Use this instead of MCP.

## Non-Negotiables

- Answer in Japanese unless the user explicitly asks otherwise.
- Use `gws`; do not use MCP.
- Before fetching calendar data with `gws`, always confirm which Google account/calendar identity to use.
- If the user already named the exact account in the current turn, state that account and proceed.
- If the account is not explicit, ask the user which account to use. Use `gws auth status` only to verify the configured account, then ask for confirmation before fetching calendar data.
- If `gws` is missing or unauthenticated, stop and prompt setup instead of using another calendar source.
- Treat calendar contents as private. Keep output scoped to the fields the user requested, and avoid dumping raw event JSON.
- Use absolute dates when resolving relative dates. If the request says `6/1`, resolve the year from the current conversation context or ask if ambiguous.

## Setup Check

Check `gws` before fetching:

```sh
command -v gws
gws auth status
```

If missing:

```sh
brew install googleworkspace-cli
gws auth setup --project <project-id>
gws auth login --readonly --services calendar
```

If `gws auth status` shows a different user than intended, ask the user which account to use and re-authenticate if needed:

```sh
gws auth logout
gws auth login --readonly --services calendar
```

## Fetch Workflow

1. Resolve the requested period to JST absolute datetimes.
   - One day: `timeMin` at `00:00:00+09:00`, `timeMax` at the next day `00:00:00+09:00`.
   - Multi-day range: include all requested dates; use the day after the final date as `timeMax`.
2. Confirm the Google account before fetching if it was not explicit.
3. Fetch from the user's own primary calendar unless the user asks for another calendar.
4. Use `singleEvents: true` and `orderBy: "startTime"` so recurring events are expanded and sorted.
5. Use `maxResults` high enough for the requested period. If `nextPageToken` is present, fetch subsequent pages or clearly state that the result is truncated.

Canonical command shape:

```sh
gws calendar events list \
  --params '{"calendarId":"primary","timeMin":"YYYY-MM-DDT00:00:00+09:00","timeMax":"YYYY-MM-DDT00:00:00+09:00","singleEvents":true,"orderBy":"startTime","maxResults":250}'
```

## Table Format

Return this Markdown table by default:

```md
| 日付 | 時間 | 予定 | 参加状態 | 場所 |
|---|---|---|---|---|
| 06/01（月） | 08:00-08:15 | [int/web] DHK-PMIチーム定例 | 参加 |  |
```

Formatting rules:

- Date: `MM/DD（曜）`, for example `06/01（月）`.
- Time: `HH:MM-HH:MM`. For all-day events, use `終日`.
- Event title: `summary`, or `(no title)` if absent.
- Location: `location`, blank if absent.
- Sort by start datetime ascending.
- Keep overlapping events as separate rows.
- Do not include internal IDs, attendee emails, meeting links, descriptions, or raw recurrence data unless the user asks.

## Participation Status

For the user's own participation status, use the event attendee whose `self` is `true`:

```jq
((.attendees // []) | map(select(.self == true)) | .[0].responseStatus)
```

Map statuses to Japanese labels:

| API value | Output |
|---|---|
| `accepted` | `参加` |
| `declined` | `不参加` |
| `tentative` | `仮参加` |
| `needsAction` | `未回答` |

If no self attendee exists and `organizer.self == true`, output `主催者`.
If the status cannot be determined, output `不明`.

## jq Extraction Example

Use a compact extraction instead of showing raw JSON:

```sh
gws calendar events list \
  --params '{"calendarId":"primary","timeMin":"2026-06-01T00:00:00+09:00","timeMax":"2026-06-02T00:00:00+09:00","singleEvents":true,"orderBy":"startTime","maxResults":250}' |
jq -r '
  def jp_wday:
    ["日","月","火","水","木","金","土"][strptime("%Y-%m-%d") | mktime | strftime("%w") | tonumber];
  def event_date:
    ((.start.dateTime // .start.date) | split("T")[0]) as $d
    | ($d | strptime("%Y-%m-%d") | strftime("%m/%d")) + "（" + ($d | jp_wday) + "）";
  def hm($x): $x | split("T")[1] | split("+")[0] | split(":")[0] + ":" + split(":")[1];
  def event_time:
    if .start.date then "終日" else hm(.start.dateTime) + "-" + hm(.end.dateTime) end;
  def my_status:
    (((.attendees // []) | map(select(.self == true)) | .[0].responseStatus) //
     (if .organizer.self == true then "organizer" else "unknown" end));
  def status_label:
    {"accepted":"参加","declined":"不参加","tentative":"仮参加","needsAction":"未回答","organizer":"主催者","unknown":"不明"}[.] // "不明";
  (.items // [])
  | sort_by(.start.dateTime // .start.date // "")
  | .[]
  | [event_date, event_time, (.summary // "(no title)"), (my_status | status_label), (.location // "")]
  | @tsv
'
```

Convert the TSV rows into the Markdown table above before answering.

## Reporting

- Start with a one-line scope such as `primary カレンダーの 2026-06-01（JST）の予定は13件。`
- Then provide the table.
- If no events exist, say `該当する予定はありませんでした。`
- If pagination was not fully fetched, state that the table is partial and include the last fetched page size.
