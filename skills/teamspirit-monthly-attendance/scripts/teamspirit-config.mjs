#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const DEFAULT_DIR = path.join(process.env.CODEX_HOME || path.join(os.homedir(), ".codex"), "teamspirit-monthly-attendance");
const DEFAULT_PATH = path.join(DEFAULT_DIR, "config.json");

const EXAMPLE = {
  version: 1,
  attendanceUrl: "https://example.lightning.force.com/lightning/n/teamspirit__AtkWorkTimeTab",
  workplaceHint: "Example workplace Chrome profile or account label",
  noteFormat: "MM/DD",
  defaultWeekRules: {
    "1": [["09:00", "12:00"], ["13:00", "17:00"]],
    "3": [["10:00", "12:00"]],
    "5": [["09:30", "12:00"], ["13:00", "16:30"]]
  },
  defaultHolidays: [],
  defaultExcludeDates: [],
  workRatio: {
    sliderScale: 10,
    jobs: [
      { name: "Project A", matchText: "Project A", ratio: 1 },
      { name: "Project B", matchText: "Project B", ratio: 4 }
    ]
  }
};

function usage() {
  console.error("usage: teamspirit-config.mjs path|example|validate [path]|write [path]");
}

function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isDateString(value) {
  return /^\d{4}-\d{2}-\d{2}$/.test(String(value || ""));
}

function isTime(value) {
  return /^([01]?\d|2[0-3]):[0-5]\d$/.test(String(value || ""));
}

function validateWeekRules(value, errors, field) {
  if (!isPlainObject(value)) {
    errors.push(`${field} must be an object keyed by JavaScript day numbers as strings`);
    return;
  }
  for (const [day, segments] of Object.entries(value)) {
    if (!/^[0-6]$/.test(day)) {
      errors.push(`${field}.${day} must use a day key from "0" to "6"`);
    }
    if (!Array.isArray(segments) || segments.length === 0) {
      errors.push(`${field}.${day} must be a non-empty array of [from,to] segments`);
      continue;
    }
    for (const [index, segment] of segments.entries()) {
      if (!Array.isArray(segment) || segment.length !== 2 || !isTime(segment[0]) || !isTime(segment[1])) {
        errors.push(`${field}.${day}[${index}] must be [HH:MM, HH:MM]`);
      }
    }
  }
}

function validateDateList(value, errors, field) {
  if (value == null) return;
  if (!Array.isArray(value) || !value.every(isDateString)) {
    errors.push(`${field} must be an array of YYYY-MM-DD strings`);
  }
}

function validateWorkRatio(value, errors, warnings) {
  if (value == null) {
    warnings.push("workRatio is missing; work-ratio tasks must collect job matchers before running");
    return;
  }
  if (!isPlainObject(value)) {
    errors.push("workRatio must be an object");
    return;
  }
  const sliderScale = Number(value.sliderScale ?? 10);
  if (!Number.isFinite(sliderScale) || sliderScale <= 0) {
    errors.push("workRatio.sliderScale must be a positive number");
  }
  if (!Array.isArray(value.jobs) || value.jobs.length === 0) {
    warnings.push("workRatio.jobs is missing; work-ratio tasks must collect job matchers before running");
    return;
  }
  for (const [index, job] of value.jobs.entries()) {
    if (!isPlainObject(job)) {
      errors.push(`workRatio.jobs[${index}] must be an object`);
      continue;
    }
    if (!job.name || typeof job.name !== "string") {
      errors.push(`workRatio.jobs[${index}].name must be a non-empty string`);
    }
    const ratio = Number(job.ratio);
    if (!Number.isFinite(ratio) || ratio <= 0) {
      errors.push(`workRatio.jobs[${index}].ratio must be a positive number`);
    }
    if (!job.matchText && !job.matchRegex) {
      errors.push(`workRatio.jobs[${index}] must have matchText or matchRegex`);
    }
    if (job.matchRegex) {
      try {
        new RegExp(job.matchRegex);
      } catch (error) {
        errors.push(`workRatio.jobs[${index}].matchRegex is invalid: ${error.message}`);
      }
    }
  }
}

function validateConfig(config) {
  const errors = [];
  const warnings = [];

  if (!isPlainObject(config)) {
    return { errors: ["config must be a JSON object"], warnings };
  }
  if (config.version !== 1) {
    errors.push("version must be 1");
  }
  if (!config.attendanceUrl || typeof config.attendanceUrl !== "string") {
    errors.push("attendanceUrl must be a non-empty string");
  } else {
    try {
      const url = new URL(config.attendanceUrl);
      if (url.protocol !== "https:") errors.push("attendanceUrl must use https");
      if (!url.pathname.includes("/lightning/n/teamspirit__AtkWorkTimeTab")) {
        errors.push("attendanceUrl must contain /lightning/n/teamspirit__AtkWorkTimeTab");
      }
    } catch {
      errors.push("attendanceUrl must be a valid URL");
    }
  }
  if (!config.workplaceHint || typeof config.workplaceHint !== "string") {
    errors.push("workplaceHint must be a non-empty string");
  }
  if (config.noteFormat != null && config.noteFormat !== "MM/DD") {
    warnings.push("noteFormat is not MM/DD; confirm the user explicitly wants this");
  }
  validateWeekRules(config.defaultWeekRules, errors, "defaultWeekRules");
  validateDateList(config.defaultHolidays, errors, "defaultHolidays");
  validateDateList(config.defaultExcludeDates, errors, "defaultExcludeDates");
  validateWorkRatio(config.workRatio, errors, warnings);

  return { errors, warnings };
}

function readStdin() {
  return fs.readFileSync(0, "utf8");
}

function readConfig(configPath) {
  const text = fs.readFileSync(configPath, "utf8");
  return JSON.parse(text);
}

function redactedResult(configPath, validation) {
  return {
    ok: validation.errors.length === 0,
    path: configPath,
    warnings: validation.warnings,
    errors: validation.errors
  };
}

const [command, maybePath] = process.argv.slice(2);
const configPath = maybePath || DEFAULT_PATH;

try {
  if (command === "path") {
    console.log(DEFAULT_PATH);
  } else if (command === "example") {
    console.log(JSON.stringify(EXAMPLE, null, 2));
  } else if (command === "validate") {
    const config = readConfig(configPath);
    const validation = validateConfig(config);
    console.log(JSON.stringify(redactedResult(configPath, validation), null, 2));
    if (validation.errors.length > 0) process.exit(1);
  } else if (command === "write") {
    const config = JSON.parse(readStdin());
    const validation = validateConfig(config);
    if (validation.errors.length > 0) {
      console.error(JSON.stringify(redactedResult(configPath, validation), null, 2));
      process.exit(1);
    }
    fs.mkdirSync(path.dirname(configPath), { recursive: true, mode: 0o700 });
    fs.writeFileSync(configPath, `${JSON.stringify(config, null, 2)}\n`, { mode: 0o600 });
    fs.chmodSync(configPath, 0o600);
    console.log(JSON.stringify(redactedResult(configPath, validation), null, 2));
  } else {
    usage();
    process.exit(2);
  }
} catch (error) {
  console.error(JSON.stringify({ ok: false, path: configPath, errors: [error.message] }, null, 2));
  process.exit(1);
}
