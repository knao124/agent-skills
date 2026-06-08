#!/usr/bin/env python3
"""Create a folded Markdown scaffold from a Claude Code transcript JSONL log."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore[assignment]


CLAUDE_HOME = Path(os.environ.get("CLAUDE_CONFIG_DIR") or os.environ.get("CLAUDE_HOME", "~/.claude")).expanduser()
DEFAULT_TZ = "Asia/Tokyo"


@dataclass
class TranscriptInfo:
    session_id: str
    title: str
    transcript_path: Path
    cwd: str | None = None


@dataclass
class Message:
    ts: datetime
    role: str
    text: str


@dataclass
class ToolCall:
    ts: datetime
    name: str


def local_tz(name: str):
    if ZoneInfo is None:
        if name != DEFAULT_TZ:
            raise SystemExit("zoneinfo is unavailable; use the default timezone")
        return timezone.utc
    return ZoneInfo(name)


def parse_ts(value: str, tz_name: str) -> datetime:
    tz = local_tz(tz_name)
    raw = value.strip()
    if raw.endswith("Z"):
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(tz)
    if "T" in raw:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=tz)
        return parsed.astimezone(tz)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=tz)
        except ValueError:
            pass
    raise SystemExit(f"Could not parse timestamp: {value!r}")


def fmt_dt(value: datetime, include_date: bool = True) -> str:
    if include_date:
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value.strftime("%H:%M:%S")


def duration_text(start: datetime, end: datetime) -> str:
    seconds = max(0, int((end - start).total_seconds()))
    hours, rem = divmod(seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours}時間{minutes}分{seconds}秒"
    return f"{minutes}分{seconds}秒"


def truncate(text: str, limit: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def encoded_project_path(path: str | Path) -> str:
    return str(Path(path).expanduser().resolve()).replace("/", "-")


def content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "text":
            continue
        value = item.get("text")
        if isinstance(value, str):
            parts.append(value)
    return "\n".join(parts)


def tool_calls_from_content(content: Any, ts: datetime) -> list[ToolCall]:
    if not isinstance(content, list):
        return []
    calls: list[ToolCall] = []
    for item in content:
        if not isinstance(item, dict) or item.get("type") != "tool_use":
            continue
        name = item.get("name") or "tool_use"
        calls.append(ToolCall(ts=ts, name=str(name)))
    return calls


def transcript_contains(path: Path, needle: str) -> bool:
    if not needle:
        return True
    try:
        with path.open(encoding="utf-8") as fh:
            return any(needle in line for line in fh)
    except OSError:
        return False


def transcript_info(path: Path) -> TranscriptInfo:
    session_id = path.stem
    title = session_id
    cwd: str | None = None
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(item.get("sessionId"), str):
                    session_id = item["sessionId"]
                if isinstance(item.get("slug"), str):
                    title = item["slug"]
                if isinstance(item.get("cwd"), str):
                    cwd = item["cwd"]
                if title != path.stem and cwd:
                    break
    except OSError as exc:
        raise SystemExit(f"Could not read transcript: {path}: {exc}") from exc
    return TranscriptInfo(session_id=session_id, title=title, transcript_path=path, cwd=cwd)


def candidate_transcripts(args: argparse.Namespace) -> list[Path]:
    if args.transcript_path:
        return [Path(args.transcript_path).expanduser()]

    projects_root = CLAUDE_HOME / "projects"
    if not projects_root.exists():
        raise SystemExit(f"Claude projects directory not found: {projects_root}")

    project_dirs: list[Path]
    project_path = args.project_path or os.getcwd()
    encoded_dir = projects_root / encoded_project_path(project_path)
    if encoded_dir.exists():
        project_dirs = [encoded_dir]
    elif args.project_path:
        raise SystemExit(f"Claude project transcript directory not found: {encoded_dir}")
    else:
        project_dirs = [path for path in projects_root.iterdir() if path.is_dir()]

    candidates: list[Path] = []
    for project_dir in project_dirs:
        candidates.extend(project_dir.glob("*.jsonl"))

    if args.session_id:
        candidates = [path for path in candidates if path.stem == args.session_id]
    if args.text_contains:
        candidates = [path for path in candidates if transcript_contains(path, args.text_contains)]
    return sorted(candidates, key=lambda path: path.stat().st_mtime, reverse=True)


def resolve_transcript(args: argparse.Namespace) -> TranscriptInfo:
    candidates = candidate_transcripts(args)
    if not candidates:
        raise SystemExit("No matching Claude Code transcript found")
    path = candidates[0]
    if not path.exists():
        raise SystemExit(f"Transcript log not found: {path}")
    return transcript_info(path)


def read_events(path: Path, tz_name: str) -> tuple[list[Message], list[ToolCall]]:
    messages: list[Message] = []
    calls: list[ToolCall] = []
    tz = local_tz(tz_name)

    with path.expanduser().open(encoding="utf-8") as fh:
        for line in fh:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts_raw = item.get("timestamp")
            if not isinstance(ts_raw, str):
                continue
            ts = parse_ts(ts_raw, tz_name).astimezone(tz)
            item_type = item.get("type")
            if item_type not in ("user", "assistant"):
                continue
            message = item.get("message")
            if not isinstance(message, dict):
                continue
            role = message.get("role") or item_type
            if role not in ("user", "assistant"):
                continue
            content = message.get("content")
            text = content_text(content)
            if text.strip():
                messages.append(Message(ts=ts, role=role, text=text.strip()))
            if item_type == "assistant":
                calls.extend(tool_calls_from_content(content, ts))

    messages.sort(key=lambda value: value.ts)
    calls.sort(key=lambda value: value.ts)
    return messages, calls


def filter_between(values: list[Any], start: datetime, end: datetime) -> list[Any]:
    return [value for value in values if start <= value.ts <= end]


def build_markdown(args: argparse.Namespace, transcript: TranscriptInfo, messages: list[Message], calls: list[ToolCall]) -> str:
    if not messages:
        raise SystemExit("No user/assistant messages found in Claude Code transcript")

    full_start = messages[0].ts
    latest_message_end = messages[-1].ts
    work_start = parse_ts(args.work_start, args.timezone) if args.work_start else full_start
    work_end = parse_ts(args.work_end, args.timezone) if args.work_end else latest_message_end
    if work_end < work_start:
        raise SystemExit("--work-end must be after --work-start")
    full_end = work_end if args.work_end else latest_message_end

    context_messages = [m for m in messages if m.ts < work_start]
    if args.context_limit >= 0:
        context_messages = context_messages[-args.context_limit :]
    work_messages = filter_between(messages, work_start, work_end)
    work_calls = filter_between(calls, work_start, work_end)
    tool_counts = Counter(call.name for call in work_calls)
    tool_text = "、".join(f"`{name}` {count}回" for name, count in sorted(tool_counts.items())) or "なし"
    timeline_header = "PR Work Timeline" if args.pr_mode else "Work Timeline"
    scope = args.scope or transcript.title
    source_label = transcript.title if transcript.title != transcript.session_id else transcript.session_id

    lines = [
        "<details>",
        "<summary>Agent作業ログ / 会話圧縮メモ</summary>",
        "",
        "## Source",
        "- Source: Claude Code local transcript log",
        f"- Session: `{source_label}`",
        f"- Session ID: `{transcript.session_id}`",
        "- Times: JST",
        f"- Scope: {scope}",
        "",
        "## Time",
        f"- 前段含む会話: {fmt_dt(full_start)} → {fmt_dt(full_end, include_date=full_start.date() != full_end.date())}（{duration_text(full_start, full_end)}）",
        f"- {'PR作業本体' if args.pr_mode else '作業本体'}: {fmt_dt(work_start)} → {fmt_dt(work_end, include_date=work_start.date() != work_end.date())}（{duration_text(work_start, work_end)}）",
        f"- 作業中のtool実行: {tool_text}",
        "",
        "## Conversation Context",
    ]

    if context_messages:
        for message in context_messages:
            label = "ユーザー" if message.role == "user" else "Claude"
            lines.append(f"- {fmt_dt(message.ts, include_date=False)} {label}: {truncate(message.text, args.text_limit)}")
    else:
        lines.append("- なし")

    lines.extend(["", f"## {timeline_header}"])
    if work_messages:
        for message in work_messages:
            label = "ユーザー" if message.role == "user" else "Claude"
            lines.append(f"- {fmt_dt(message.ts, include_date=False)} {label}: {truncate(message.text, args.text_limit)}")
    else:
        lines.append("- なし")

    lines.extend(["", "</details>", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-id", help="Exact Claude Code session id")
    parser.add_argument("--project-path", help="Project path whose Claude transcript directory should be searched")
    parser.add_argument("--transcript-path", help="Read a specific transcript JSONL file")
    parser.add_argument("--text-contains", help="Use the latest transcript containing this text")
    parser.add_argument("--scope", help="Scope label shown in the Source section")
    parser.add_argument("--work-start", help="Start of the scoped work window, JST or ISO")
    parser.add_argument("--work-end", help="End of the scoped work window, JST or ISO")
    parser.add_argument("--timezone", default=DEFAULT_TZ, help=f"Output timezone, default {DEFAULT_TZ}")
    parser.add_argument("--context-limit", type=int, default=12, help="Pre-work messages to keep; -1 keeps all")
    parser.add_argument("--text-limit", type=int, default=180, help="Characters per message bullet")
    parser.add_argument("--pr-mode", action="store_true", help="Use PR Work Timeline heading")
    args = parser.parse_args()

    transcript = resolve_transcript(args)
    messages, calls = read_events(transcript.transcript_path, args.timezone)
    sys.stdout.write(build_markdown(args, transcript, messages, calls))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
