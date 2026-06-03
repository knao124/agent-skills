# Observed TeamSpirit DOM

Use this reference only when the script needs inspection or repair.

## Page and Context

- Salesforce Lightning path: `/lightning/n/teamspirit__AtkWorkTimeTab`
- DevTools Console context must be the TeamSpirit Visualforce iframe, observed as `vfFrameId_... (AtkWorkTimeView)`.
- In the wrong context, `document.getElementById("ttvApplyYYYY-MM-DD")` is missing.
- For Codex-driven runs, prefer Chrome plugin evaluation in the intended workplace Chrome tab/profile. If direct iframe evaluation is unavailable, use manual DevTools Console paste in `AtkWorkTimeView`.
- Do not use Computer Use accessibility-tree polling for this page. Salesforce/TeamSpirit exposes a very large tree; compact `window.TS_*_SUMMARY` variables are the verification source.

## Monthly Table

- Application cell per date: `ttvApplyYYYY-MM-DD`
- Application plus button inside the cell: `.png-add`
- After an individual application is submitted, the plus button disappears and the申請 column shows a status such as `承認待ち`.
- Work cell per date: `dailyWorkCellYYYY-MM-DD`
- Work plus button inside the work cell: `.png-add`
- After work ratios are registered, the work cell may show a total time such as `7:00`; clicking the cell itself can reopen the work dialog even when `.png-add` is gone.

## Application Menu

Clicking the date's申請 plus opens a menu.

- `applyNew_reviseTime`: 勤怠時刻修正申請

## Attendance Correction Dialog

- `dialogApplyStartTime1`: 出社
- `dialogApplyEndTime1`: 退社
- `dialogApplyReviseRestChk1`: 休憩修正 checkbox
- `dialogApplyReviseRestBody1`: 休憩 input row container
- `dialogApplyNote1`: 備考
- `empApplyDone1`: individual dialog `承認申請`
- `empApplyCancel1`: cancel

## Work Balance Dialog

Clicking the date's工数 plus/cell opens工数実績入力.

- Dialog root: `dialogWorkBalance`
- Date label: `empWorkDate`
- Real work time label: `empWorkRealTime`, observed as `実労働時間：7:00`
- Job table body: `empWorkTableBody`
- Register button: `empWorkOk`
- Cancel/close: `empWorkCancel`, `empWorkClose`
- Hidden job row IDs: `empWorkSeq0`, `empWorkSeq1`, ...
- Percent labels/buttons per row: `btnPercentLabel0`, `btnPercent0`, ...
- Clock labels per row: `btnClock2Label0`, ...
- Dojo sliders per row: `dijit.byId("empWorkSlider0")`, ...
- Time labels/inputs per row: `empTimeLabel0`, `empInputTime0`, ...
- Total label/footer: `empWorkTotalTime`, visible footer total

Observed ratio behavior:

- User ratios are weights. TeamSpirit percent mode uses a 0-10 slider, so ratio `1:4` must be normalized to slider values `2` and `8`.
- Percent mode with slider values `2` and `8` should produce `1:24` and `5:36` for `7:00` real work time.
- Job row text is workplace-specific. Match it with sanitized `CONFIG.ratios[].match` patterns and never commit real job names, client names, or internal job IDs to shared skill repositories.

## Important Distinction

The bottom page-level `承認申請` button is monthly approval. Do not press it during individual attendance correction registration unless the user explicitly asks for monthly approval.

`empWorkSeq*` values are TeamSpirit's internal job row identifiers. Do not write ratios into them.
