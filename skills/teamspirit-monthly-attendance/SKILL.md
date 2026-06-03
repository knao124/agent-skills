---
name: teamspirit-monthly-attendance
description: Strict workflow and reusable browser-console automation for registering monthly attendance corrections in TeamSpirit/Salesforce. Use when the user asks to automate, verify, or submit TeamSpirit/Teamsprit attendance, 勤怠表, 勤怠時刻修正申請, 承認申請, monthly part-time schedules, or console JavaScript for TeamSpirit.
license: MIT
---

# TeamSpirit Monthly Attendance

## Purpose

Register monthly TeamSpirit attendance correction applications from a weekday schedule with fail-stop checks, dry-run verification, and explicit confirmation before any submission.

Use the bundled console script as the canonical implementation. Execute it through the Chrome plugin inside the TeamSpirit Visualforce iframe when possible; paste it into DevTools Console only as the manual fallback.

- `scripts/teamspirit-monthly-console.js`: attendance correction helper. Edit only `CONFIG`; default output is compact.
- `scripts/teamspirit-work-ratio-console.js`: daily job work-ratio helper for the工数 dialog. Edit only `CONFIG`; default output is compact.
- `scripts/teamspirit-config.mjs`: locate, validate, and write the local private config file without echoing its contents.
- `references/configuration.md`: local config schema and first-run setup workflow. Read this whenever config is missing, invalid, or incomplete for the requested task.
- `references/config.example.json`: sanitized example config. Never put real workplace URLs, job names, or internal IDs in the repository copy.
- `references/observed-teamspirit-dom.md`: field IDs and selectors observed on the TeamSpirit attendance page. Read this only when the page/script behavior needs inspection or repair.

## Non-Negotiables

- Answer the user in Japanese.
- Treat TeamSpirit registration as transmission of workplace attendance data. Before clicking individual `承認申請`, show the exact target dates, start/end times,休憩, notes, and total hours, then get explicit approval unless the user has already approved that exact computed plan in the current turn.
- Never press the bottom monthly `承認申請` button unless the user separately and explicitly asks for monthly approval after individual applications are complete.
- Verify the active Chrome profile/account and URL are the intended workplace before running the script. If Chrome control sees a different profile/tab, stop and fix the target instead of operating that other page.
- When using manual DevTools Console fallback, verify the JavaScript context is the Visualforce attendance iframe, usually shown as `AtkWorkTimeView`. If `ttvApplyYYYY-MM-DD` or `dailyWorkCellYYYY-MM-DD` elements are missing, switch the Console context before doing anything else.
- Verify Japanese holidays/current company exclusions for the target month using a current source or user-provided exclusion dates. State absolute dates.
- Fail closed: if a target date has no plus button and it was not listed in `expectedExistingDates`, stop and inspect instead of silently skipping.
- For工数割合 registration, never modify `empWorkSeq*`; those hidden fields are TeamSpirit job row IDs. Use percent mode plus `empWorkSlider*` values only.
- For bulk工数割合 registration, first run one sample target in dry-run or submit mode, reopen that sample date, and confirm the saved row times before running the full target list.
- Do not use Computer Use for bulk TeamSpirit automation, Console polling, or repeated page inspection. It is allowed only for a one-time visual confirmation or emergency click after stating why.
- Console scripts must keep compact output by default. Detailed payloads stay on `window.*_FINAL`; user-facing verification should read `window.*_SUMMARY` or compact marker logs first.
- Do not run the bundled sample `CONFIG` against a real workplace page. Build the run `CONFIG` from the local private config plus the current user request.
- Never commit, paste, or PR the local private config. Treat workplace URL/account hints, job names, client names, and job row matchers as private operational settings.

## Local Configuration

Before any real TeamSpirit browser or Console workflow, resolve the private local config:

1. Use `node scripts/teamspirit-config.mjs path` to get the default config path. It is `${CODEX_HOME:-~/.codex}/teamspirit-monthly-attendance/config.json`.
2. Run `node scripts/teamspirit-config.mjs validate`. If it succeeds and has the fields needed for the requested task, use it.
3. If the config file is missing, invalid, or incomplete, read `references/configuration.md` and ask the user for only the missing values before doing Chrome or Console work.
4. Write the answered config with `node scripts/teamspirit-config.mjs write` so the file is created with private permissions.
5. Use the config to replace placeholders:
   - `attendanceUrl` and `workplaceHint` drive Chrome tab selection.
   - `defaultWeekRules`, `defaultHolidays`, `defaultExcludeDates`, and `noteFormat` seed attendance plans unless the user overrides them.
   - `workRatio.jobs` provides real job labels and matchers for工数割合.
6. If a task needs工数割合 and `workRatio.jobs` is absent, ask for job labels/matchers and ratios, update the local config, then continue.

## Browser Control Policy

Use the lowest-token route that can operate the intended logged-in TeamSpirit page.

1. If the user only asks for calculation, script generation, or skill updates, do not open/control Chrome.
2. Prefer the Chrome plugin for authenticated TeamSpirit pages. Claim the visible intended workplace Chrome tab/profile, verify the URL, and evaluate JavaScript directly in the TeamSpirit Visualforce iframe when the tool supports it.
3. If Chrome plugin control cannot claim the intended tab/profile or cannot evaluate in the Visualforce iframe, use the manual DevTools Console fallback: provide the edited script, have it pasted into the `AtkWorkTimeView` context, then verify via compact summary variables.
4. Do not switch to Computer Use as a bulk fallback. If Chrome control is blocked and manual Console execution is not available, stop and report the blocker.
5. Never infer success from a different Chrome profile, a different Salesforce org, or the Lightning shell document outside the Visualforce iframe.

## Chrome Plugin Procedure

When controlling Chrome, load `chrome:control-chrome` first and follow this order:

1. Initialize the Chrome extension browser runtime once, then call `browser.user.openTabs()`.
2. Select the tab whose URL matches local config `attendanceUrl` and whose visible title/account context matches local config `workplaceHint`. Do not use a tab id that did not come from the current `openTabs()` result.
3. Claim that exact tab with `browser.user.claimTab(tab)` and reuse the returned `tab`.
4. Verify `await tab.url()` and a lightweight frame locator check for `iframe[id^="vfFrameId"]` or a frame containing `[id^="ttvApply"]` / `[id^="dailyWorkCell"]`.
5. If the exposed Chrome API cannot evaluate the console script inside the Visualforce iframe, stop the Chrome path and use manual DevTools Console paste in `AtkWorkTimeView`. Do not try to compensate with Computer Use.
6. After Chrome work, finalize the Chrome browser session and keep the claimed TeamSpirit tab only when the user needs to continue there.

## Token Budget Rules

- Never poll TeamSpirit with accessibility-tree dumps or repeated `get_app_state` calls.
- Do not paste full JSON payloads into chat. Summarize dates, statuses, total hours, and errors.
- Read `window.TS_MONTHLY_SUMMARY` or `window.TS_WORK_RATIO_SUMMARY` first. Read `window.TS_MONTHLY_FINAL` or `window.TS_WORK_RATIO_FINAL` only for a specific failed date.
- Use `copyResultToClipboard` only for compact summaries unless debugging a single failure.

## Workflow

1. Gather inputs:
   - local config from `scripts/teamspirit-config.mjs validate`
   - target year/month
   - weekday work segments from local config or user override
   - holidays/excluded dates from local config and current source/user override
   - existing submitted dates, if any
   - note format from local config, default `MM/DD`

2. Build the plan:
   - Convert multiple work segments into one TeamSpirit start/end plus休憩 gaps.
   - Exclude Saturdays, Sundays, holidays, and `excludeDates`.
   - Compute total minutes from work segments only.
   - Use note `MM/DD` for every target date unless the user explicitly changes it.

3. Show a pre-submit summary:
   - target dates grouped or listed with weekday
   - start/end,休憩, note for each
   - expected existing/skipped dates
   - total hours
   - ask approval if the user has not already approved this exact plan

4. Open/verify TeamSpirit:
   - Follow the Browser Control Policy first.
   - URL path should be `/lightning/n/teamspirit__AtkWorkTimeTab`.
   - Displayed month must match the plan.
   - If using manual Console fallback, DevTools Console context must be the TeamSpirit Visualforce iframe (`AtkWorkTimeView`).

5. Dry-run:
   - Read `scripts/teamspirit-monthly-console.js`.
   - Edit only `CONFIG`.
   - Keep `submit: false`, `dryRun: true`.
   - Set `expectedTargetCount` and `expectedTotalHours` or `expectedTotalMinutes`.
   - Run it in Console.
   - Inspect `window.TS_MONTHLY_SUMMARY` first. Resolve any missing plus, wrong month, unexpected date, or total mismatch before submitting.

6. Submit:
   - Change `submit: true`, `dryRun: false`.
   - Set `confirmSubmit: "SUBMIT_TEAMSPIRIT_ATTENDANCE"`.
   - Keep `expectedTargetCount`, total expectation, `holidays`, and `expectedExistingDates`.
   - Run once. The script submits sequentially and stops on the first unexpected error.

7. Verify and report:
   - Read `window.TS_MONTHLY_SUMMARY`; use `window.TS_MONTHLY_FINAL` only if a specific date needs detail.
   - Confirm each new date is `submitted` and each pre-existing date is `existing`.
   - Confirm target dates no longer have the申請 plus button.
   - Tell the user what was submitted, what was skipped as already existing, total hours, and that monthly approval was not pressed.

## Work Ratio Workflow

Use this for the工数 column after the attendance times already exist.

1. Open/verify TeamSpirit:
   - Follow the Browser Control Policy first.
   - URL path should be `/lightning/n/teamspirit__AtkWorkTimeTab`.
   - Displayed month must match the intended month.
   - If using manual Console fallback, DevTools Console context must be the TeamSpirit Visualforce iframe (`AtkWorkTimeView`).

2. Sample run:
   - Read `scripts/teamspirit-work-ratio-console.js`.
   - Convert local config `workRatio.jobs[].matchText` to string matchers or `matchRegex` to JavaScript `RegExp` values in the script `CONFIG`.
   - Keep the default `targetDates: ["2026-01-05"]` or set exactly one requested sample date.
   - Keep `dryRun: true`, `submit: false`.
   - Run it once and inspect `window.TS_WORK_RATIO_SUMMARY`.
   - If the user asks to register the sample, set `dryRun: false`, `submit: true`, and `confirmSubmit: "SUBMIT_TEAMSPIRIT_WORK_RATIO"` for that single date only.

3. Verify sample persistence:
   - Reopen the same date's工数 dialog.
   - Confirm the expected job rows, slider values, row times, and total time remain saved.
   - For a `7:00` work day with sample ratios `Project A:1` and `Project B:4`, expected times are `1:24` and `5:36`, total `7:00`.

4. Full month:
   - Replace `targetDates` with the exact approved work dates, not a guessed weekday rule.
   - Set `expectedTargetCount`.
   - Run dry-run for the full list and confirm every target row has exactly the expected jobs.
   - Only after user approval, set `submit: true`, `dryRun: false`, and the required confirmation string.

5. Verify and report:
   - Read `window.TS_WORK_RATIO_SUMMARY`; use `window.TS_WORK_RATIO_FINAL` only for a failed date or detailed row audit.
   - Confirm every target date is `submitted`.
   - Reopen at least one representative date after submit and verify persisted times.

## Configuration Conventions

Use weekday keys compatible with JavaScript `Date#getDay()`:

- `1`: Monday
- `2`: Tuesday
- `3`: Wednesday
- `4`: Thursday
- `5`: Friday

Represent work as segments, not breaks:

```js
weekRules: {
  1: [["09:00", "12:00"], ["13:00", "17:00"]],
  3: [["10:00", "12:00"]],
  5: [["09:30", "12:00"], ["13:00", "16:30"]]
}
```

This becomes:

- Monday: start `09:00`, end `17:00`,休憩 `12:00-13:00`
- Wednesday: start `10:00`, end `12:00`,休憩なし
- Friday: start `09:30`, end `16:30`,休憩 `12:00-13:00`

Use `entries` only for one-off overrides:

```js
entries: {
  "2026-06-10": [["10:00", "12:00"]]
}
```

For local config JSON, store the same data under string keys:

```json
{
  "defaultWeekRules": {
    "1": [["09:00", "12:00"], ["13:00", "17:00"]],
    "3": [["10:00", "12:00"]]
  }
}
```

## Failure Handling

- Chrome target/profile not claimable: stop and use manual DevTools Console fallback. Do not continue in a different profile and do not use Computer Use for bulk automation.
- `Console context is not TeamSpirit...`: switch DevTools Console JavaScript context to the Visualforce iframe.
- Month mismatch: navigate/select the correct month before running again.
- Unexpected no-plus date: inspect the row; if it is already `承認待ち`, add that date to `expectedExistingDates` and rerun. Otherwise stop.
- Rest input not found: read `references/observed-teamspirit-dom.md`, inspect the modal DOM, and update the script only after confirming the current field IDs.
- Any submit error: do not continue manually by guessing. Read the compact summary, inspect the affected date only, and report the exact status.
