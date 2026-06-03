// TeamSpirit work ratio helper.
// Paste this entire file into DevTools Console in the TeamSpirit Visualforce iframe.
// Edit CONFIG first from the local private config plus the current request.
// Default sample mode is dry-run for the sample date only.
(async () => {
  "use strict";

  const SAMPLE_WORK_DATES = [
    "2026-01-05"
  ];

  const CONFIG = {
    year: 2026,
    month: 1,

    // Keep the default as one sample date. For multiple approved work days, set:
    // targetDates: SAMPLE_WORK_DATES,
    targetDates: ["2026-01-05"],
    expectedTargetCount: 1,

    ratios: [
      { name: "Project A", match: /Project A/, ratio: 1 },
      { name: "Project B", match: /Project B/, ratio: 4 }
    ],
    // TeamSpirit percent mode uses a 0-10 slider. User ratios are weights;
    // 1:4 becomes 2:8 on the slider.
    sliderScale: 10,

    // Default mode cannot submit. Real registration requires all three:
    // dryRun: false, submit: true, confirmSubmit: "SUBMIT_TEAMSPIRIT_WORK_RATIO"
    dryRun: true,
    submit: false,
    confirmSubmit: "",

    requireMonthLabel: true,
    requireExactJobMatches: true,
    allowUnexpectedJobs: false,
    requirePositiveRealTime: true,
    verifyTimeSum: true,
    // Browser clipboard writes may be blocked from DevTools; results are always on window.TS_WORK_RATIO_FINAL.
    outputMode: "compact", // "compact" or "full"
    copyResultToClipboard: false,
    stopOnError: true
  };

  const REQUIRED_CONFIRM = "SUBMIT_TEAMSPIRIT_WORK_RATIO";
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const pad2 = (n) => String(n).padStart(2, "0");

  function isVisible(element) {
    if (!element) return false;
    const style = getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    return style.display !== "none" && style.visibility !== "hidden" && rect.width >= 0 && rect.height >= 0;
  }

  async function waitFor(predicate, timeoutMs, label) {
    const started = Date.now();
    let lastError = null;
    while (Date.now() - started < timeoutMs) {
      try {
        const value = predicate();
        if (value) return value;
      } catch (error) {
        lastError = error;
      }
      await sleep(100);
    }
    throw new Error(`Timed out waiting for ${label || "condition"}${lastError ? `: ${lastError.message}` : ""}`);
  }

  function normalizeText(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function parseHHMM(value, label) {
    const match = /(\d{1,3}):([0-5]\d)/.exec(String(value || ""));
    if (!match) throw new Error(`Invalid time${label ? ` for ${label}` : ""}: ${value}`);
    return Number(match[1]) * 60 + Number(match[2]);
  }

  function minutesToTime(minutes) {
    return `${Math.floor(minutes / 60)}:${pad2(minutes % 60)}`;
  }

  function assertTeamSpiritContext(config) {
    if (!document.querySelector('[id^="dailyWorkCell"]')) {
      throw new Error("Console context is not TeamSpirit attendance iframe. Switch DevTools JavaScript context to AtkWorkTimeView.");
    }
    if (config.requireMonthLabel) {
      const bodyText = document.body.innerText || "";
      const labels = [`${config.year}年${pad2(config.month)}月`, `${config.year}年${config.month}月`];
      if (!labels.some((label) => bodyText.includes(label))) {
        throw new Error(`Displayed month was not confirmed as ${config.year}-${pad2(config.month)}. Select the correct month before running.`);
      }
    }
  }

  function buildTargets(config) {
    if (!Array.isArray(config.targetDates) || config.targetDates.length === 0) {
      throw new Error("CONFIG.targetDates must contain at least one YYYY-MM-DD date.");
    }
    const seen = new Set();
    const targets = config.targetDates.map((date) => {
      const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date);
      if (!match) throw new Error(`Invalid target date: ${date}`);
      if (Number(match[1]) !== config.year || Number(match[2]) !== config.month) {
        throw new Error(`${date}: target date is outside CONFIG year/month.`);
      }
      if (seen.has(date)) throw new Error(`Duplicate target date: ${date}`);
      seen.add(date);
      return date;
    });
    if (config.expectedTargetCount != null && targets.length !== Number(config.expectedTargetCount)) {
      throw new Error(`Target count mismatch: expected ${config.expectedTargetCount}, got ${targets.length}`);
    }
    return targets;
  }

  function compileRatios(config) {
    if (!Array.isArray(config.ratios) || config.ratios.length === 0) {
      throw new Error("CONFIG.ratios must contain at least one job ratio.");
    }
    const sliderScale = Number(config.sliderScale ?? 10);
    if (!Number.isFinite(sliderScale) || sliderScale <= 0) {
      throw new Error(`Invalid sliderScale: ${config.sliderScale}`);
    }
    const rules = config.ratios.map((ratioConfig, index) => {
      const ratio = Number(ratioConfig.ratio);
      if (!Number.isFinite(ratio) || ratio < 0) {
        throw new Error(`Invalid ratio at index ${index}: ${ratioConfig.ratio}`);
      }
      if (ratio === 0 && config.requireExactJobMatches) {
        throw new Error(`Zero ratio is not allowed for required job at index ${index}.`);
      }
      if (!(ratioConfig.match instanceof RegExp) && typeof ratioConfig.match !== "string") {
        throw new Error(`Ratio match must be a RegExp or string at index ${index}.`);
      }
      return {
        name: ratioConfig.name || String(ratioConfig.match),
        match: ratioConfig.match,
        ratio
      };
    });
    const totalRatio = rules.reduce((sum, rule) => sum + rule.ratio, 0);
    if (!Number.isFinite(totalRatio) || totalRatio <= 0) {
      throw new Error("Total ratio must be greater than zero.");
    }
    return rules.map((rule) => ({
      ...rule,
      targetSliderValue: Number(((rule.ratio / totalRatio) * sliderScale).toFixed(3))
    }));
  }

  function inspectWorkCell(date) {
    const cell = document.getElementById(`dailyWorkCell${date}`);
    const row = cell ? cell.closest("tr") : null;
    return {
      date,
      hasWorkCell: Boolean(cell),
      hasPlus: Boolean(cell && cell.querySelector(".png-add")),
      text: normalizeText(cell ? cell.innerText || cell.textContent : ""),
      rowText: normalizeText(row ? row.innerText || row.textContent : "").slice(0, 240)
    };
  }

  function compactWorkInspection(item) {
    return {
      date: item.date,
      hasWorkCell: item.hasWorkCell,
      hasPlus: item.hasPlus,
      text: item.text,
      rowText: item.rowText ? item.rowText.slice(0, 120) : ""
    };
  }

  function compactAppliedState(state) {
    return {
      job: state.job,
      ratio: state.ratio,
      targetSliderValue: state.targetSliderValue,
      sliderValue: state.sliderValue,
      time: state.timeText,
      minutes: state.minutes
    };
  }

  function compactResult(result) {
    return {
      date: result.date,
      status: result.status,
      message: result.message,
      realTime: result.realTime,
      totalTime: result.totalTime,
      applied: (result.applied || []).map(compactAppliedState),
      unexpectedJobs: (result.unexpected || []).map((row) => `#${row.index} ${row.text.slice(0, 80)}`),
      after: result.after ? compactWorkInspection(result.after) : undefined
    };
  }

  function statusCounts(results) {
    return (results || []).reduce((counts, result) => {
      const key = result.status || "unknown";
      counts[key] = (counts[key] || 0) + 1;
      return counts;
    }, {});
  }

  function summarizePayload(payload) {
    const results = payload.results || [];
    const summary = {
      mode: payload.mode,
      year: payload.year,
      month: payload.month,
      targetCount: (payload.targets || []).length,
      targets: payload.targets || [],
      ratios: payload.ratios || [],
      inspection: (payload.inspection || []).map(compactWorkInspection),
      statuses: statusCounts(results),
      results: results.map(compactResult)
    };
    summary.errors = summary.results.filter((result) => result.status === "error");
    return summary;
  }

  async function openWorkDialog(date) {
    const cell = document.getElementById(`dailyWorkCell${date}`);
    if (!cell) throw new Error(`${date}: dailyWorkCell not found`);
    const target = cell.querySelector(".png-add") || cell.querySelector("a") || cell;
    target.click();

    const dialog = await waitFor(() => {
      const element = document.getElementById("dialogWorkBalance");
      return element && isVisible(element) ? element : null;
    }, 10000, `${date}: work dialog`);

    const expectedDateText = `${Number(date.slice(0, 4))}年${Number(date.slice(5, 7))}月${Number(date.slice(8, 10))}日`;
    const actualDateText = normalizeText(document.getElementById("empWorkDate")?.textContent || dialog.textContent);
    if (!actualDateText.includes(expectedDateText)) {
      throw new Error(`${date}: opened dialog date mismatch. Expected ${expectedDateText}, got ${actualDateText.slice(0, 80)}`);
    }
    return dialog;
  }

  function getRealTimeMinutes(date) {
    const label = normalizeText(document.getElementById("empWorkRealTime")?.textContent || "");
    const minutes = parseHHMM(label, `${date} real time`);
    if (CONFIG.requirePositiveRealTime && minutes <= 0) {
      throw new Error(`${date}: real work time is zero.`);
    }
    return minutes;
  }

  function getRowText(index) {
    const seq = document.getElementById(`empWorkSeq${index}`);
    if (!seq) return "";
    const row = seq.closest("tr") || seq.parentElement;
    return normalizeText(row ? row.innerText || row.textContent : "");
  }

  function getWorkRows() {
    const rows = [];
    for (let index = 0; ; index += 1) {
      const seq = document.getElementById(`empWorkSeq${index}`);
      if (!seq) break;
      const rowText = getRowText(index);
      rows.push({
        index,
        seq: seq.value,
        text: rowText
      });
    }
    if (rows.length === 0) throw new Error("No work job rows found in dialog.");
    return rows;
  }

  function matchesJob(row, matcher) {
    if (matcher instanceof RegExp) return matcher.test(row.text);
    return row.text.includes(matcher);
  }

  function matchRatioRows(rows, ratioRules, config) {
    const used = new Set();
    const matched = ratioRules.map((rule) => {
      const matches = rows.filter((row) => matchesJob(row, rule.match));
      if (matches.length === 0) throw new Error(`Job not found: ${rule.name}`);
      if (matches.length > 1) throw new Error(`Job matched multiple rows: ${rule.name}`);
      const row = matches[0];
      if (used.has(row.index)) throw new Error(`Multiple ratio rules matched the same row: ${rule.name}`);
      used.add(row.index);
      return { ...rule, row };
    });

    const unexpected = rows.filter((row) => !used.has(row.index));
    if (unexpected.length > 0 && !config.allowUnexpectedJobs) {
      throw new Error(`Unexpected job rows: ${unexpected.map((row) => `#${row.index} ${row.text}`).join(" | ")}`);
    }
    if (config.requireExactJobMatches && used.size !== ratioRules.length) {
      throw new Error("Not all ratio rules were matched exactly.");
    }
    return { matched, unexpected };
  }

  function clickPercentMode(index) {
    const label = document.getElementById(`btnPercentLabel${index}`);
    if (!label) throw new Error(`Missing percent label for row ${index}`);
    label.click();
    const radio = document.getElementById(`btnPercent${index}`);
    if (radio && !radio.checked) {
      throw new Error(`Percent mode was not selected for row ${index}`);
    }
  }

  function sliderFor(index) {
    const slider = window.dijit && window.dijit.byId ? window.dijit.byId(`empWorkSlider${index}`) : null;
    if (!slider) throw new Error(`Missing Dojo slider empWorkSlider${index}`);
    return slider;
  }

  function setRatioValue(rowIndex, sliderValue) {
    clickPercentMode(rowIndex);
    const slider = sliderFor(rowIndex);
    slider.set("value", sliderValue);
    if (typeof slider.onChange === "function") slider.onChange(sliderValue);
    if (slider.domNode) slider.domNode.dispatchEvent(new Event("change", { bubbles: true }));
    return slider;
  }

  function readDisplayedTime(index) {
    const candidates = [
      document.getElementById(`empTimeLabel${index}`),
      document.getElementById(`empInputTime${index}`),
      document.getElementById(`empWorkTime${index}`)
    ].filter(Boolean);
    for (const element of candidates) {
      const value = element.value != null ? element.value : element.textContent;
      if (/\d{1,3}:[0-5]\d/.test(String(value || ""))) return normalizeText(value);
    }
    const rowText = getRowText(index);
    const matches = [...rowText.matchAll(/\d{1,3}:[0-5]\d/g)];
    return matches.length > 0 ? matches[matches.length - 1][0] : "";
  }

  function readRowState(row) {
    const slider = sliderFor(row.index);
    const percent = document.getElementById(`btnPercent${row.index}`);
    const timeText = readDisplayedTime(row.index);
    return {
      index: row.index,
      seq: row.seq,
      text: row.text,
      percentChecked: percent ? Boolean(percent.checked) : null,
      sliderValue: slider.get("value"),
      timeText,
      minutes: timeText ? parseHHMM(timeText, `row ${row.index}`) : null
    };
  }

  async function applyRatiosToOpenDialog(date, ratioRules, config) {
    const realMinutes = getRealTimeMinutes(date);
    const rows = getWorkRows();
    const { matched, unexpected } = matchRatioRows(rows, ratioRules, config);

    for (const item of matched) {
      setRatioValue(item.row.index, item.targetSliderValue);
    }

    await waitFor(() => {
      const states = matched.map((item) => readRowState(item.row));
      const ready = states.every((state, index) =>
        state.timeText &&
        Math.abs(Number(state.sliderValue) - Number(matched[index].targetSliderValue)) < 0.001
      );
      return ready ? states : null;
    }, 5000, `${date}: time labels after ratio changes`);

    const states = matched.map((item) => ({
      date,
      job: item.name,
      ratio: item.ratio,
      targetSliderValue: item.targetSliderValue,
      ...readRowState(item.row)
    }));
    const totalMinutes = states.reduce((sum, state) => sum + Number(state.minutes || 0), 0);
    if (config.verifyTimeSum && totalMinutes !== realMinutes) {
      throw new Error(`${date}: allocation total mismatch. Expected ${minutesToTime(realMinutes)}, got ${minutesToTime(totalMinutes)}`);
    }

    return {
      date,
      realTime: minutesToTime(realMinutes),
      realMinutes,
      rows,
      applied: states,
      unexpected,
      totalTime: minutesToTime(totalMinutes)
    };
  }

  async function closeWorkDialog() {
    const cancel = document.getElementById("empWorkCancel") || document.getElementById("empWorkClose");
    if (cancel && isVisible(cancel)) {
      cancel.click();
      await waitFor(() => {
        const dialog = document.getElementById("dialogWorkBalance");
        return !dialog || !isVisible(dialog);
      }, 10000, "work dialog close");
    }
  }

  async function submitOpenDialog(date) {
    const ok = document.getElementById("empWorkOk");
    if (!ok) throw new Error(`${date}: register button empWorkOk not found`);
    ok.click();
    await waitFor(() => {
      const dialog = document.getElementById("dialogWorkBalance");
      return !dialog || !isVisible(dialog);
    }, 15000, `${date}: work dialog close after register`);
    await waitFor(() => {
      const cell = document.getElementById(`dailyWorkCell${date}`);
      return cell && normalizeText(cell.textContent || cell.innerText) ? cell : null;
    }, 30000, `${date}: work cell refresh`);
  }

  async function maybeCopy(payload) {
    window.TS_WORK_RATIO_LAST_COPIED = payload;
    if (!CONFIG.copyResultToClipboard) return;
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
      }
    } catch (error) {
      console.warn("[TS_WORK_RATIO_COPY_FAILED]", error.message);
    }
  }

  function printSummary(payload) {
    const summary = summarizePayload(payload);
    window.TS_WORK_RATIO_SUMMARY = summary;
    if (CONFIG.outputMode === "full") {
      const rows = [];
      for (const result of payload.results || []) {
        if (!result.applied) continue;
        for (const state of result.applied) {
          rows.push({
            date: result.date,
            job: state.job,
            ratio: state.ratio,
            targetSliderValue: state.targetSliderValue,
            sliderValue: state.sliderValue,
            time: state.timeText
          });
        }
      }
      if (rows.length > 0) console.table(rows);
      console.log("[TS_WORK_RATIO_PAYLOAD]", payload);
    }
    console.log("[TS_WORK_RATIO_SUMMARY]", summary);
    return summary;
  }

  function buildPayload(mode, targets, inspection, ratioRules, results) {
    return {
      mode,
      year: CONFIG.year,
      month: CONFIG.month,
      targets,
      inspection,
      ratios: ratioRules.map((rule) => ({
        name: rule.name,
        ratio: rule.ratio,
        targetSliderValue: rule.targetSliderValue
      })),
      results
    };
  }

  window.TS_WORK_RATIO_RUNNING = true;
  window.TS_WORK_RATIO_RESULTS = [];

  try {
    assertTeamSpiritContext(CONFIG);
    const targets = buildTargets(CONFIG);
    const ratioRules = compileRatios(CONFIG);
    const inspection = targets.map((date) => inspectWorkCell(date));

    if (!CONFIG.dryRun && CONFIG.submit && CONFIG.confirmSubmit !== REQUIRED_CONFIRM) {
      throw new Error(`Refusing to submit. Set confirmSubmit to ${JSON.stringify(REQUIRED_CONFIRM)} after checking the dry-run result.`);
    }

    const results = [];
    for (const date of targets) {
      console.log("[TS_WORK_RATIO_START]", compactWorkInspection(inspectWorkCell(date)));
      try {
        await openWorkDialog(date);
        const applied = await applyRatiosToOpenDialog(date, ratioRules, CONFIG);
        if (CONFIG.dryRun || !CONFIG.submit) {
          await closeWorkDialog();
          results.push({ ...applied, status: "dryRun" });
        } else {
          await submitOpenDialog(date);
          results.push({ ...applied, status: "submitted", after: inspectWorkCell(date) });
        }
        window.TS_WORK_RATIO_RESULTS = results;
      } catch (error) {
        await closeWorkDialog().catch(() => {});
        const result = { date, status: "error", message: error.message, after: inspectWorkCell(date) };
        results.push(result);
        window.TS_WORK_RATIO_RESULTS = results;
        console.error("[TS_WORK_RATIO_ERROR]", compactResult(result));
        const partialPayload = buildPayload("partial", targets, inspection, ratioRules, results);
        window.TS_WORK_RATIO_FINAL = partialPayload;
        printSummary(partialPayload);
        if (CONFIG.stopOnError) throw error;
      }
    }

    const payload = buildPayload(CONFIG.dryRun || !CONFIG.submit ? "dryRun" : "submit", targets, inspection, ratioRules, results);
    window.TS_WORK_RATIO_DRY_RUN = payload.mode === "dryRun" ? payload : window.TS_WORK_RATIO_DRY_RUN;
    window.TS_WORK_RATIO_FINAL = payload;
    const summary = printSummary(payload);
    await maybeCopy(summary);
    console.log("[TS_WORK_RATIO_DONE]", summary);
    return summary;
  } finally {
    window.TS_WORK_RATIO_RUNNING = false;
  }
})();
