# TeamSpirit Local Configuration

Use this reference when the local private config is missing, invalid, or incomplete for the requested task.

## Path

Default path:

```text
${CODEX_HOME:-~/.codex}/teamspirit-monthly-attendance/config.json
```

Use the helper:

```sh
node scripts/teamspirit-config.mjs path
node scripts/teamspirit-config.mjs validate
node scripts/teamspirit-config.mjs example
```

To write a completed config without echoing it back:

```sh
node scripts/teamspirit-config.mjs write <<'JSON'
{
  "version": 1,
  "attendanceUrl": "https://example.lightning.force.com/lightning/n/teamspirit__AtkWorkTimeTab",
  "workplaceHint": "Example workplace Chrome profile or account label",
  "noteFormat": "MM/DD",
  "defaultWeekRules": {
    "1": [["09:00", "12:00"], ["13:00", "17:00"]]
  }
}
JSON
```

The helper creates parent directories and writes the file with `0600` permissions.

## Required Fields

- `version`: currently `1`.
- `attendanceUrl`: full TeamSpirit attendance URL. It should contain `/lightning/n/teamspirit__AtkWorkTimeTab`.
- `workplaceHint`: a short label used to identify the intended Chrome profile, tab, or logged-in account.
- `noteFormat`: usually `MM/DD`.
- `defaultWeekRules`: JavaScript `Date#getDay()` keys as strings. Values are work segments, not break periods.

For工数割合 tasks, also collect:

- `workRatio.jobs[].name`: display label used in summaries.
- `workRatio.jobs[].ratio`: positive numeric weight.
- `workRatio.jobs[].matchText` or `workRatio.jobs[].matchRegex`: matcher for the job row text.
- `workRatio.sliderScale`: usually `10`.

## First-Run Questions

Ask only for missing values:

1. TeamSpirit attendance URL.
2. Workplace/Profile hint that distinguishes the intended Chrome tab.
3. Default weekly work segments, if the user wants them remembered.
4. Note format, defaulting to `MM/DD`.
5. For work-ratio registration: job labels, exact row match text or regex, and ratios.

Do not ask for passwords, cookies, session tokens, API keys, or Salesforce credentials. The skill uses the user's logged-in Chrome session.

## Applying Config

- Use `attendanceUrl` and `workplaceHint` for Chrome tab selection.
- Merge `defaultWeekRules`, `defaultHolidays`, `defaultExcludeDates`, and current user overrides into the attendance script `CONFIG`.
- Convert JSON work-ratio jobs into JavaScript:
  - `matchText`: use as a plain string matcher.
  - `matchRegex`: convert to a JavaScript `RegExp`, inspecting escaping carefully.
- Never run real submissions with the bundled sample values.

## Privacy

The local config may contain workplace URL, account labels, client/job names, and internal matching text. Keep it outside the repository, do not paste it into PRs, and summarize it only in redacted form.
