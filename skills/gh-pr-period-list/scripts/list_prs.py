#!/usr/bin/env python3
"""List own GitHub PRs whose open or merge time falls in a local date range."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Any
from zoneinfo import ZoneInfo


GRAPHQL_QUERY = """
query($q:String!, $after:String) {
  search(query:$q, type:ISSUE, first:100, after:$after) {
    issueCount
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on PullRequest {
        number
        title
        state
        isDraft
        createdAt
        mergedAt
        url
      }
    }
  }
}
"""


@dataclass(frozen=True)
class Period:
    start_local: datetime
    end_local: datetime
    tz_name: str

    @property
    def start_utc(self) -> datetime:
        return self.start_local.astimezone(timezone.utc)

    @property
    def end_utc(self) -> datetime:
        return self.end_local.astimezone(timezone.utc)

    @property
    def search_date_range(self) -> str:
        return f"{self.start_utc.date()}..{self.end_utc.date()}"


def run_json(args: list[str]) -> Any:
    try:
        completed = subprocess.run(args, check=True, text=True, capture_output=True)
    except FileNotFoundError as exc:
        raise SystemExit("gh command is not installed or not in PATH") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        stdout = exc.stdout.strip()
        detail = stderr or stdout or str(exc)
        raise SystemExit(detail) from exc
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Could not parse JSON from command output: {' '.join(args)}") from exc


def gh_login() -> str:
    try:
        completed = subprocess.run(["gh", "api", "user", "--jq", ".login"], check=True, text=True, capture_output=True)
    except FileNotFoundError as exc:
        raise SystemExit("gh command is not installed or not in PATH") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise SystemExit(detail) from exc

    login = completed.stdout.strip()
    if not login:
        raise SystemExit("Could not determine active gh user")
    return login


def parse_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"{label} must be YYYY-MM-DD: {value}") from exc


def parse_period(start: str, end: str, tz_name: str) -> Period:
    try:
        tz = ZoneInfo(tz_name)
    except Exception as exc:  # pragma: no cover - zoneinfo error type varies
        raise SystemExit(f"Unknown timezone: {tz_name}") from exc

    start_day = parse_date(start, "--start")
    end_day = parse_date(end, "--end")
    if end_day < start_day:
        raise SystemExit("--end must be the same day as or after --start")

    return Period(
        start_local=datetime.combine(start_day, time.min, tzinfo=tz),
        end_local=datetime.combine(end_day, time.max, tzinfo=tz),
        tz_name=tz_name,
    )


def graphql_search(query: str) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    after: str | None = None

    while True:
        args = [
            "gh",
            "api",
            "graphql",
            "-f",
            f"q={query}",
            "-f",
            f"query={GRAPHQL_QUERY}",
        ]
        if after:
            args.extend(["-f", f"after={after}"])

        data = run_json(args)
        search = data.get("data", {}).get("search")
        if not isinstance(search, dict):
            raise SystemExit("Unexpected GraphQL response: missing data.search")

        page_nodes = search.get("nodes") or []
        nodes.extend(node for node in page_nodes if isinstance(node, dict))

        page_info = search.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        after = page_info.get("endCursor")
        if not after:
            raise SystemExit("GraphQL pagination failed: missing endCursor")

    return nodes


def parse_github_datetime(value: str | None, tz: ZoneInfo) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(tz)


def in_period(value: datetime | None, period: Period) -> bool:
    return value is not None and period.start_local <= value <= period.end_local


def collect_prs(repo: str, author: str, period: Period) -> list[dict[str, Any]]:
    date_range = period.search_date_range
    queries = [
        f"repo:{repo} is:pr author:{author} created:{date_range} sort:created-asc",
        f"repo:{repo} is:pr author:{author} merged:{date_range} sort:created-asc",
    ]

    by_number: dict[int, dict[str, Any]] = {}
    for query in queries:
        for node in graphql_search(query):
            number = node.get("number")
            if isinstance(number, int):
                by_number[number] = node

    tz = ZoneInfo(period.tz_name)
    filtered: list[dict[str, Any]] = []
    for pr in by_number.values():
        created_local = parse_github_datetime(pr.get("createdAt"), tz)
        merged_local = parse_github_datetime(pr.get("mergedAt"), tz)
        if in_period(created_local, period) or in_period(merged_local, period):
            normalized = dict(pr)
            normalized["createdLocal"] = created_local.isoformat() if created_local else None
            normalized["mergedLocal"] = merged_local.isoformat() if merged_local else None
            normalized["matchedBy"] = [
                label
                for label, matched in (
                    ("open", in_period(created_local, period)),
                    ("merge", in_period(merged_local, period)),
                )
                if matched
            ]
            filtered.append(normalized)

    return sorted(filtered, key=lambda item: (item.get("createdAt") or "", item.get("number") or 0))


def format_dt(value: str | None, tz_name: str) -> str:
    parsed = parse_github_datetime(value, ZoneInfo(tz_name))
    if parsed is None:
        return "未merge"
    return parsed.strftime("%Y-%m-%d %H:%M")


def display_state(pr: dict[str, Any]) -> str:
    state = str(pr.get("state") or "")
    if state == "OPEN" and pr.get("isDraft"):
        return "OPEN / DRAFT"
    return state


def markdown_table(repo: str, author: str, period: Period, prs: list[dict[str, Any]]) -> str:
    start_day = period.start_local.date().isoformat()
    end_day = period.end_local.date().isoformat()
    lines = [
        f"`{repo}` の `{author}` PR（openまたはmergeが {start_day}〜{end_day} {period.tz_name}）は{len(prs)}件。",
        "",
        "| Open日時 | Merge日時 | PR | 状態 | タイトル |",
        "|---|---|---:|---|---|",
    ]
    for pr in prs:
        number = pr["number"]
        title = str(pr.get("title") or "").replace("|", "\\|")
        lines.append(
            "| {created} | {merged} | [#{number}]({url}) | {state} | {title} |".format(
                created=format_dt(pr.get("createdAt"), period.tz_name),
                merged=format_dt(pr.get("mergedAt"), period.tz_name),
                number=number,
                url=pr.get("url") or "",
                state=display_state(pr),
                title=title,
            )
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="GitHub repository in OWNER/REPO format")
    parser.add_argument("--start", required=True, help="Start date in local timezone, YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date in local timezone, YYYY-MM-DD")
    parser.add_argument("--author", default="@me", help="GitHub login. Defaults to active gh user")
    parser.add_argument("--timezone", default="Asia/Tokyo", help="Local timezone for filtering and display")
    parser.add_argument("--json", action="store_true", help="Print normalized JSON instead of Markdown")
    args = parser.parse_args()

    author = gh_login() if args.author in ("", "@me", "me") else args.author
    period = parse_period(args.start, args.end, args.timezone)
    prs = collect_prs(args.repo, author, period)

    if args.json:
        print(json.dumps({"repo": args.repo, "author": author, "timezone": period.tz_name, "count": len(prs), "prs": prs}, ensure_ascii=False, indent=2))
    else:
        print(markdown_table(args.repo, author, period, prs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
