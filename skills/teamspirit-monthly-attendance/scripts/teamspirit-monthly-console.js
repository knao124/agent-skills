// TeamSpirit monthly attendance correction helper.
// Paste this entire file into DevTools Console in the TeamSpirit Visualforce iframe.
// Edit CONFIG first from the local private config plus the current request.
// Default sample mode is dry-run and cannot submit.
(async () => {
  "use strict";

  const CONFIG = {
    year: 2026,
    month: 1,

    // Keep dryRun true until the user has approved the exact computed plan.
    dryRun: true,
    submit: false,
    confirmSubmit: "",

    // Set these on every real run so accidental month/rule edits fail fast.
    expectedTargetCount: null,
    expectedTotalHours: null, // Example: "24:00"
    expectedTotalMinutes: null,

    // Add Japanese holidays/company exclusions as YYYY-MM-DD.
    holidays: [],
    excludeDates: [],

    // Add dates that are already confirmed as submitted/承認待ち.
    // Submit mode fails if a target date has no plus and is not listed here.
    expectedExistingDates: [],

    // One-off date overrides. These win over weekRules.
    entries: {},

    // JavaScript day-of-week keys: 0=Sun, 1=Mon, ..., 6=Sat.
    weekRules: {
      1: [["09:00", "12:00"], ["13:00", "17:00"]],
      3: [["10:00", "12:00"]],
      5: [["09:30", "12:00"], ["13:00", "16:30"]]
    },

    noteFormat: "MM/DD",
    requireMonthLabel: true,
    outputMode: "compact", // "compact" or "full"
    copyResultToClipboard: false,
    stopOnError: true
  };

  const REQUIRED_CONFIRM = "SUBMIT_TEAMSPIRIT_ATTENDANCE";
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const pad2 = (n) => String(n).padStart(2, "0");
  const dateString = (year, month, day) => `${year}-${pad2(month)}-${pad2(day)}`;
  const mmdd = (date) => date.slice(5).replace("-", "/");

  function parseTime(value) {
    const match = /^([01]?\d|2[0-3]):([0-5]\d)$/.exec(String(value).trim());
    if (!match) throw new Error(`Invalid time: ${value}`);
    return Number(match[1]) * 60 + Number(match[2]);
  }

  function minutesToTime(minutes) {
    return `${pad2(Math.floor(minutes / 60))}:${pad2(minutes % 60)}`;
  }

  function parseExpectedHours(value) {
    if (value == null || value === "") return null;
    const match = /^(\d+):([0-5]\d)$/.exec(String(value).trim());
    if (!match) throw new Error(`Invalid expectedTotalHours: ${value}`);
    return Number(match[1]) * 60 + Number(match[2]);
  }

  function assertTeamSpiritContext(config) {
    if (!document.querySelector('[id^="ttvApply"]')) {
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

  function normalizeSegments(rawSegments, date) {
    if (!Array.isArray(rawSegments) || rawSegments.length === 0) {
      throw new Error(`${date}: segments are empty`);
    }
    const segments = rawSegments.map((segment) => {
      if (!Array.isArray(segment) || segment.length !== 2) {
        throw new Error(`${date}: invalid segment ${JSON.stringify(segment)}`);
      }
      const from = parseTime(segment[0]);
      const to = parseTime(segment[1]);
      if (to <= from) throw new Error(`${date}: segment end must be after start: ${segment.join("-")}`);
      return { from, to, fromText: minutesToTime(from), toText: minutesToTime(to) };
    }).sort((a, b) => a.from - b.from);

    for (let i = 1; i < segments.length; i += 1) {
      if (segments[i].from < segments[i - 1].to) {
        throw new Error(`${date}: overlapping work segments`);
      }
    }
    return segments;
  }

  function buildPlan(config) {
    const excluded = new Set([...(config.holidays || []), ...(config.excludeDates || [])]);
    const entryDates = new Set(Object.keys(config.entries || {}));
    const lastDay = new Date(Date.UTC(config.year, config.month, 0)).getUTCDate();
    const plan = [];

    for (let day = 1; day <= lastDay; day += 1) {
      const date = dateString(config.year, config.month, day);
      if (excluded.has(date)) continue;

      const dow = new Date(Date.UTC(config.year, config.month - 1, day)).getUTCDay();
      const rawSegments = entryDates.has(date) ? config.entries[date] : (config.weekRules || {})[String(dow)] || (config.weekRules || {})[dow];
      if (!rawSegments) continue;

      const segments = normalizeSegments(rawSegments, date);
      const rests = [];
      for (let i = 1; i < segments.length; i += 1) {
        if (segments[i - 1].to < segments[i].from) {
          rests.push([minutesToTime(segments[i - 1].to), minutesToTime(segments[i].from)]);
        }
      }
      if (rests.length > 1) {
        throw new Error(`${date}: this script supports one rest interval per day. Add support only after inspecting the current dialog DOM.`);
      }

      const workMinutes = segments.reduce((sum, segment) => sum + segment.to - segment.from, 0);
      plan.push({
        date,
        dow,
        start: segments[0].fromText,
        end: segments[segments.length - 1].toText,
        rest: rests,
        note: config.noteFormat === "MM/DD" ? mmdd(date) : mmdd(date),
        workMinutes,
        segments: segments.map((segment) => [segment.fromText, segment.toText])
      });
    }

    const totalMinutes = plan.reduce((sum, entry) => sum + entry.workMinutes, 0);
    if (config.expectedTargetCount != null && plan.length !== Number(config.expectedTargetCount)) {
      throw new Error(`Target count mismatch: expected ${config.expectedTargetCount}, got ${plan.length}`);
    }
    const expectedMinutes = config.expectedTotalMinutes != null ? Number(config.expectedTotalMinutes) : parseExpectedHours(config.expectedTotalHours);
    if (expectedMinutes != null && totalMinutes !== expectedMinutes) {
      throw new Error(`Total mismatch: expected ${minutesToTime(expectedMinutes)}, got ${minutesToTime(totalMinutes)}`);
    }

    return {
      year: config.year,
      month: config.month,
      totalMinutes,
      totalHours: minutesToTime(totalMinutes),
      targetCount: plan.length,
      plan
    };
  }

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

  function setFieldValue(element, value) {
    if (!element) throw new Error(`Missing field for value ${value}`);
    element.focus();
    element.value = value;
    for (const eventName of ["input", "change", "blur"]) {
      element.dispatchEvent(new Event(eventName, { bubbles: true }));
    }
  }

  function textInputs(container) {
    return [...container.querySelectorAll("input")]
      .filter((input) => {
        const type = (input.getAttribute("type") || "text").toLowerCase();
        return ["", "text", "tel", "time"].includes(type) && !input.disabled && isVisible(input);
      });
  }

  function inspectDate(date) {
    const cell = document.getElementById(`ttvApply${date}`);
    const row = cell ? cell.closest("tr") : null;
    return {
      date,
      hasApplyCell: Boolean(cell),
      hasPlus: Boolean(cell && cell.querySelector(".png-add")),
      rowText: (row && row.innerText ? row.innerText : "").replace(/\s+/g, " ").trim().slice(0, 240)
    };
  }

  function compactEntry(entry) {
    return {
      date: entry.date,
      dow: entry.dow,
      start: entry.start,
      end: entry.end,
      rest: entry.rest.map((r) => r.join("-")).join(","),
      note: entry.note,
      hours: minutesToTime(entry.workMinutes)
    };
  }

  function compactInspection(item) {
    return {
      date: item.date,
      hasApplyCell: item.hasApplyCell,
      hasPlus: item.hasPlus,
      rowText: item.rowText ? item.rowText.slice(0, 120) : ""
    };
  }

  function compactResult(result) {
    return {
      date: result.date,
      status: result.status,
      reason: result.reason,
      message: result.message,
      submitted: result.beforeSubmit ? {
        start: result.beforeSubmit.start,
        end: result.beforeSubmit.end,
        rest: (result.beforeSubmit.rest || []).map((r) => r.join("-")).join(","),
        note: result.beforeSubmit.note
      } : undefined,
      afterHasPlus: result.after ? result.after.hasPlus : undefined,
      afterText: result.after && result.after.rowText ? result.after.rowText.slice(0, 120) : undefined
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
    const planSummary = payload.summary || {};
    const results = payload.results || [];
    const summary = {
      mode: payload.mode,
      year: planSummary.year,
      month: planSummary.month,
      targetCount: planSummary.targetCount,
      totalHours: planSummary.totalHours,
      totalMinutes: planSummary.totalMinutes,
      statuses: statusCounts(results),
      plannedDates: (planSummary.plan || []).map(compactEntry),
      inspection: (payload.inspection || []).map(compactInspection),
      results: results.map(compactResult)
    };
    summary.errors = summary.results.filter((result) => result.status === "error");
    return summary;
  }

  async function openReviseDialog(entry) {
    const cell = document.getElementById(`ttvApply${entry.date}`);
    if (!cell) throw new Error(`${entry.date}: application cell not found`);
    const plus = cell.querySelector(".png-add");
    if (!plus) throw new Error(`${entry.date}: application plus not found`);

    plus.click();
    const menu = await waitFor(() => {
      const element = document.getElementById("applyNew_reviseTime");
      return element && isVisible(element) ? element : null;
    }, 10000, "勤怠時刻修正申請 menu");
    menu.click();

    await waitFor(() => {
      const start = document.getElementById("dialogApplyStartTime1");
      return start && isVisible(start) ? start : null;
    }, 10000, "attendance correction dialog");
  }

  async function fillDialog(entry) {
    setFieldValue(document.getElementById("dialogApplyStartTime1"), entry.start);
    setFieldValue(document.getElementById("dialogApplyEndTime1"), entry.end);

    const restCheckbox = document.getElementById("dialogApplyReviseRestChk1");
    if (!restCheckbox) throw new Error(`${entry.date}: rest checkbox not found`);

    if (entry.rest.length > 0) {
      if (!restCheckbox.checked) {
        restCheckbox.click();
      }
      const restBody = await waitFor(() => {
        const body = document.getElementById("dialogApplyReviseRestBody1");
        return body && isVisible(body) ? body : null;
      }, 5000, "rest input body");
      const inputs = textInputs(restBody);
      if (inputs.length < 2) throw new Error(`${entry.date}: rest time inputs not found`);
      setFieldValue(inputs[0], entry.rest[0][0]);
      setFieldValue(inputs[1], entry.rest[0][1]);
    } else if (restCheckbox.checked) {
      restCheckbox.click();
    }

    setFieldValue(document.getElementById("dialogApplyNote1"), entry.note);

    return {
      start: document.getElementById("dialogApplyStartTime1")?.value || "",
      end: document.getElementById("dialogApplyEndTime1")?.value || "",
      restChecked: Boolean(document.getElementById("dialogApplyReviseRestChk1")?.checked),
      rest: entry.rest,
      note: document.getElementById("dialogApplyNote1")?.value || ""
    };
  }

  async function submitEntry(entry) {
    await openReviseDialog(entry);
    const beforeSubmit = await fillDialog(entry);

    const done = document.getElementById("empApplyDone1");
    if (!done) throw new Error(`${entry.date}: individual approval button not found`);
    done.click();

    await waitFor(() => {
      const currentDone = document.getElementById("empApplyDone1");
      return !currentDone || !isVisible(currentDone);
    }, 10000, "dialog close after submit");

    await waitFor(() => !inspectDate(entry.date).hasPlus, 30000, `${entry.date} plus button to disappear`);
    return { date: entry.date, status: "submitted", beforeSubmit, after: inspectDate(entry.date) };
  }

  function printSummary(payload) {
    const summary = summarizePayload(payload);
    window.TS_MONTHLY_SUMMARY = summary;
    if (CONFIG.outputMode === "full") {
      console.table(summary.plannedDates);
      console.table(summary.inspection);
      console.log("[TS_MONTHLY_PAYLOAD]", payload);
    }
    console.log("[TS_MONTHLY_SUMMARY]", summary);
    return summary;
  }

  function maybeCopy(payload) {
    if (CONFIG.copyResultToClipboard && typeof copy === "function") {
      copy(JSON.stringify(payload, null, 2));
    }
  }

  window.TS_MONTHLY_RUNNING = true;
  window.TS_MONTHLY_RESULTS = [];

  try {
    assertTeamSpiritContext(CONFIG);
    const summary = buildPlan(CONFIG);
    const inspection = summary.plan.map((entry) => inspectDate(entry.date));
    const dryRunPayload = { mode: "dryRun", summary, inspection };
    window.TS_MONTHLY_DRY_RUN = dryRunPayload;
    window.TS_MONTHLY_FINAL = dryRunPayload;
    const dryRunSummary = printSummary(dryRunPayload);

    if (CONFIG.dryRun || !CONFIG.submit) {
      maybeCopy(dryRunSummary);
      console.log("[TS_MONTHLY_DRY_RUN_DONE]", dryRunSummary);
      return dryRunSummary;
    }

    if (CONFIG.confirmSubmit !== REQUIRED_CONFIRM) {
      throw new Error(`Refusing to submit. Set confirmSubmit to ${JSON.stringify(REQUIRED_CONFIRM)} after user approval.`);
    }

    const expectedExisting = new Set(CONFIG.expectedExistingDates || []);
    const unexpectedNoPlus = inspection.filter((item) => !item.hasPlus && !expectedExisting.has(item.date));
    if (unexpectedNoPlus.length > 0) {
      throw new Error(`Unexpected no-plus dates: ${unexpectedNoPlus.map((item) => item.date).join(", ")}`);
    }

    const results = [];
    for (const entry of summary.plan) {
      const current = inspectDate(entry.date);
      if (!current.hasPlus) {
        if (expectedExisting.has(entry.date)) {
          const result = { date: entry.date, status: "existing", reason: "listed in expectedExistingDates", after: current };
          results.push(result);
          window.TS_MONTHLY_RESULTS = results;
          console.log("[TS_MONTHLY_SKIP_EXISTING]", compactResult(result));
          continue;
        }
        const result = { date: entry.date, status: "error", message: "plus disappeared unexpectedly before submit", after: current };
        results.push(result);
        window.TS_MONTHLY_RESULTS = results;
        window.TS_MONTHLY_FINAL = { mode: "submitPartial", summary, results };
        window.TS_MONTHLY_SUMMARY = summarizePayload(window.TS_MONTHLY_FINAL);
        console.error("[TS_MONTHLY_SUBMIT_ERROR]", compactResult(result));
        console.log("[TS_MONTHLY_SUMMARY]", window.TS_MONTHLY_SUMMARY);
        throw new Error(`${entry.date}: plus disappeared unexpectedly before submit`);
      }

      console.log("[TS_MONTHLY_SUBMIT_START]", compactEntry(entry));
      try {
        const result = await submitEntry(entry);
        results.push(result);
        window.TS_MONTHLY_RESULTS = results;
        console.log("[TS_MONTHLY_SUBMIT_DONE]", compactResult(result));
      } catch (error) {
        const result = { date: entry.date, status: "error", message: error.message, after: inspectDate(entry.date) };
        results.push(result);
        window.TS_MONTHLY_RESULTS = results;
        window.TS_MONTHLY_FINAL = { mode: "submitPartial", summary, results };
        window.TS_MONTHLY_SUMMARY = summarizePayload(window.TS_MONTHLY_FINAL);
        console.error("[TS_MONTHLY_SUBMIT_ERROR]", compactResult(result));
        console.log("[TS_MONTHLY_SUMMARY]", window.TS_MONTHLY_SUMMARY);
        if (CONFIG.stopOnError) throw error;
      }
    }

    const finalPayload = { mode: "submit", summary, results };
    window.TS_MONTHLY_FINAL = finalPayload;
    const finalSummary = printSummary(finalPayload);
    maybeCopy(finalSummary);
    console.log("[TS_MONTHLY_DONE]", finalSummary);
    return finalSummary;
  } finally {
    window.TS_MONTHLY_RUNNING = false;
  }
})();
