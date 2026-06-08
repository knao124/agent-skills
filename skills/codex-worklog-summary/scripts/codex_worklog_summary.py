#!/usr/bin/env python3
"""Create a folded Markdown scaffold from a Codex rollout JSONL log."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
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


CODEX_HOME = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
DEFAULT_TZ = "Asia/Tokyo"


@dataclass
class ThreadInfo:
    id: str
    title: str
    rollout_path: Path
    created_at: int | None = None
    updated_at: int | None = None


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


def content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        for key in ("text", "input_text", "output_text"):
            value = item.get(key)
            if isinstance(value, str):
                parts.append(value)
                break
    return "\n".join(parts)


def resolve_thread(args: argparse.Namespace) -> ThreadInfo:
    if args.rollout_path:
        path = Path(args.rollout_path).expanduser()
        return ThreadInfo(id=args.thread_id or path.stem, title=args.title_contains or path.stem, rollout_path=path)

    db_path = CODEX_HOME / "state_5.sqlite"
    if not db_path.exists():
        raise SystemExit(f"Codex state DB not found: {db_path}")

    where = ""
    params: tuple[Any, ...] = ()
    if args.thread_id:
        where = "where id = ?"
        params = (args.thread_id,)
    elif args.title_contains:
        where = "where title like ?"
        params = (f"%{args.title_contains}%",)

    query = f"""
        select id, title, rollout_path, created_at, updated_at
        from threads
        {where}
        order by updated_at desc
        limit 1
    """
    with sqlite3.connect(db_path) as con:
        row = con.execute(query, params).fetchone()
    if row is None:
        raise SystemExit("No matching Codex thread found")
    return ThreadInfo(id=row[0], title=row[1], rollout_path=Path(row[2]), created_at=row[3], updated_at=row[4])


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
            if item.get("type") != "response_item":
                continue
            payload = item.get("payload")
            if not isinstance(payload, dict):
                continue
            payload_type = payload.get("type")
            if payload_type == "message":
                role = payload.get("role")
                if role not in ("user", "assistant"):
                    continue
                text = content_text(payload.get("content"))
                if not text.strip() or text.lstrip().startswith("<environment_context>"):
                    continue
                messages.append(Message(ts=ts, role=role, text=text.strip()))
            elif payload_type in ("function_call", "custom_tool_call", "tool_search_call", "web_search_call"):
                name = payload.get("name") or payload_type
                calls.append(ToolCall(ts=ts, name=str(name)))
    return messages, calls


def filter_between(values: list[Any], start: datetime, end: datetime) -> list[Any]:
    return [value for value in values if start <= value.ts <= end]


def build_markdown(args: argparse.Namespace, thread: ThreadInfo, messages: list[Message], calls: list[ToolCall]) -> str:
    if not messages:
        raise SystemExit("No user/assistant messages found in rollout log")

    full_start = messages[0].ts
    latest_message_end = messages[-1].ts
    work_start = parse_ts(args.work_start, args.timezone) if args.work_start else full_start
    work_end = parse_ts(args.work_end, args.timezone) if args.work_end else latest_message_end
    if work_end < work_start:
        raise SystemExit("--work-end must be after --work-start")
    full_end = work_end if args.work_end else messages[-1].ts

    context_messages = [m for m in messages if m.ts < work_start]
    if args.context_limit >= 0:
        context_messages = context_messages[-args.context_limit :]
    work_messages = filter_between(messages, work_start, work_end)
    work_calls = filter_between(calls, work_start, work_end)
    tool_counts = Counter(call.name for call in work_calls)
    tool_text = "、".join(f"`{name}` {count}回" for name, count in sorted(tool_counts.items())) or "なし"
    timeline_header = "PR Work Timeline" if args.pr_mode else "Work Timeline"
    scope = args.scope or thread.title

    lines = [
        "<details>",
        "<summary>Codex作業ログ / 会話圧縮メモ</summary>",
        "",
        "## Source",
        "- Source: Codex local rollout log",
        f"- Thread: `{thread.title}`",
        f"- Thread ID: `{thread.id}`",
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
            label = "ユーザー" if message.role == "user" else "Codex"
            lines.append(f"- {fmt_dt(message.ts, include_date=False)} {label}: {truncate(message.text, args.text_limit)}")
    else:
        lines.append("- なし")

    lines.extend(["", f"## {timeline_header}"])
    if work_messages:
        for message in work_messages:
            label = "ユーザー" if message.role == "user" else "Codex"
            lines.append(f"- {fmt_dt(message.ts, include_date=False)} {label}: {truncate(message.text, args.text_limit)}")
    else:
        lines.append("- なし")

    lines.extend(["", "</details>", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--thread-id", help="Exact Codex thread id")
    parser.add_argument("--title-contains", help="Use the latest thread whose title contains this text")
    parser.add_argument("--rollout-path", help="Read a specific rollout JSONL file")
    parser.add_argument("--scope", help="Scope label shown in the Source section")
    parser.add_argument("--work-start", help="Start of the scoped work window, JST or ISO")
    parser.add_argument("--work-end", help="End of the scoped work window, JST or ISO")
    parser.add_argument("--timezone", default=DEFAULT_TZ, help=f"Output timezone, default {DEFAULT_TZ}")
    parser.add_argument("--context-limit", type=int, default=12, help="Pre-work messages to keep; -1 keeps all")
    parser.add_argument("--text-limit", type=int, default=180, help="Characters per message bullet")
    parser.add_argument("--pr-mode", action="store_true", help="Use PR Work Timeline heading")
    args = parser.parse_args()

    thread = resolve_thread(args)
    if not thread.rollout_path.exists():
        raise SystemExit(f"Rollout log not found: {thread.rollout_path}")
    messages, calls = read_events(thread.rollout_path, args.timezone)
    sys.stdout.write(build_markdown(args, thread, messages, calls))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
