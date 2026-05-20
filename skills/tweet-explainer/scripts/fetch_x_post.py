#!/usr/bin/env python3
"""Fetch and normalize an X post using an App-only bearer token.

The token is read from ~/.x-token by default and is never printed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TOKEN_FILE = Path("~/.x-token").expanduser()
POST_ID_RE = re.compile(r"(?:status|statuses)/(\d+)")
NUMERIC_ID_RE = re.compile(r"^\d{5,}$")

TWEET_FIELDS = ",".join(
    [
        "article",
        "attachments",
        "author_id",
        "card_uri",
        "context_annotations",
        "conversation_id",
        "created_at",
        "display_text_range",
        "entities",
        "lang",
        "note_tweet",
        "public_metrics",
        "referenced_tweets",
        "suggested_source_links",
        "suggested_source_links_with_counts",
        "text",
    ]
)
EXPANSIONS = ",".join(
    [
        "article.cover_media",
        "author_id",
        "attachments.media_keys",
        "referenced_tweets.id",
        "referenced_tweets.id.author_id",
    ]
)
USER_FIELDS = ",".join(
    [
        "created_at",
        "description",
        "name",
        "public_metrics",
        "username",
        "verified",
    ]
)
MEDIA_FIELDS = ",".join(
    [
        "alt_text",
        "height",
        "preview_image_url",
        "type",
        "url",
        "width",
    ]
)


class FetchError(RuntimeError):
    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def parse_post_id(value: str) -> str:
    value = value.strip()
    if NUMERIC_ID_RE.fullmatch(value):
        return value

    parsed = urllib.parse.urlparse(value)
    path = parsed.path or value
    match = POST_ID_RE.search(path)
    if match:
        return match.group(1)

    raise FetchError(
        "Could not extract a Tweet/X post ID. Expected a numeric ID or a URL like https://x.com/user/status/123.",
        exit_code=2,
    )


def read_token(path: Path) -> str:
    if not path.exists():
        raise FetchError(
            f"Missing {path}. Browser extraction failed and App-only fallback requires this token file.",
            exit_code=2,
        )

    token = path.read_text(encoding="utf-8").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    token = token.strip("'\"")

    if not token:
        raise FetchError(f"{path} is empty. App-only fallback requires a bearer token.", exit_code=2)
    return token


def fetch_post(post_id: str, token: str) -> dict[str, Any]:
    query = urllib.parse.urlencode(
        {
            "tweet.fields": TWEET_FIELDS,
            "expansions": EXPANSIONS,
            "user.fields": USER_FIELDS,
            "media.fields": MEDIA_FIELDS,
        }
    )
    url = f"https://api.x.com/2/tweets/{post_id}?{query}"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise FetchError(format_http_error(exc.code, detail)) from exc
    except urllib.error.URLError as exc:
        raise FetchError(f"Network error while calling X API: {exc.reason}") from exc

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise FetchError(f"X API returned invalid JSON: {exc}") from exc

    if "data" not in payload:
        raise FetchError(f"X API response did not include data: {json.dumps(payload, ensure_ascii=False)}")
    return payload


def format_http_error(status_code: int, detail: str) -> str:
    try:
        parsed = json.loads(detail)
        compact_detail = json.dumps(parsed, ensure_ascii=False)
    except json.JSONDecodeError:
        compact_detail = detail.strip()

    hints = {
        401: "Token is invalid, empty, expired, or revoked.",
        403: "App-only access may be forbidden for this endpoint, plan, or post visibility.",
        404: "The post was not found, deleted, private, or the ID is wrong.",
        429: "X API rate limit was reached.",
    }
    hint = hints.get(status_code, "X API request failed.")
    return f"X API HTTP {status_code}: {hint} Detail: {compact_detail}"


def find_by_id(items: list[dict[str, Any]], item_id: str | None) -> dict[str, Any] | None:
    if not item_id:
        return None
    for item in items:
        if item.get("id") == item_id or item.get("media_key") == item_id:
            return item
    return None


def normalize_post(payload: dict[str, Any], requested_url: str, post_id: str) -> dict[str, Any]:
    data = payload.get("data", {})
    includes = payload.get("includes", {})
    users = includes.get("users", [])
    media = includes.get("media", [])

    author = find_by_id(users, data.get("author_id"))
    article = data.get("article") or {}
    article_entities = article.get("entities") or {}
    code_blocks = article_entities.get("code") or []
    cover_media = find_by_id(media, article.get("cover_media"))

    urls = (data.get("entities") or {}).get("urls") or []
    normalized_urls = [
        {
            "url": item.get("url"),
            "expanded_url": item.get("expanded_url") or item.get("unwound_url"),
            "display_url": item.get("display_url"),
            "status": item.get("status"),
        }
        for item in urls
    ]

    return {
        "source": "x-api-app-only",
        "requested_url": requested_url,
        "post_id": post_id,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "post": {
            "id": data.get("id"),
            "text": data.get("text"),
            "created_at": data.get("created_at"),
            "lang": data.get("lang"),
            "conversation_id": data.get("conversation_id"),
            "public_metrics": data.get("public_metrics"),
            "urls": normalized_urls,
            "referenced_tweets": data.get("referenced_tweets"),
        },
        "author": normalize_author(author),
        "article": {
            "title": article.get("title"),
            "preview_text": article.get("preview_text"),
            "plain_text": article.get("plain_text"),
            "cover_media": normalize_media(cover_media),
            "media_entity_ids": article.get("media_entities"),
            "code_blocks": [
                {
                    "language": block.get("language"),
                    "code": block.get("code"),
                }
                for block in code_blocks
            ],
        },
        "media": [normalize_media(item) for item in media],
        "errors": payload.get("errors"),
    }


def normalize_author(author: dict[str, Any] | None) -> dict[str, Any] | None:
    if not author:
        return None
    return {
        "id": author.get("id"),
        "name": author.get("name"),
        "username": author.get("username"),
        "verified": author.get("verified"),
        "description": author.get("description"),
        "created_at": author.get("created_at"),
        "public_metrics": author.get("public_metrics"),
    }


def normalize_media(media: dict[str, Any] | None) -> dict[str, Any] | None:
    if not media:
        return None
    return {
        "media_key": media.get("media_key"),
        "type": media.get("type"),
        "url": media.get("url"),
        "preview_image_url": media.get("preview_image_url"),
        "width": media.get("width"),
        "height": media.get("height"),
        "alt_text": media.get("alt_text"),
    }


def write_output(data: dict[str, Any], output: Path | None, pretty: bool) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2 if pretty else None)
    if output:
        output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch an X post using ~/.x-token App-only bearer token.")
    parser.add_argument("tweet", help="Tweet/X post URL or numeric post ID.")
    parser.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_FILE, help="Path to App-only bearer token file.")
    parser.add_argument("--output", type=Path, help="Write normalized JSON to this file instead of stdout.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument("--include-raw", action="store_true", help="Include the raw X API payload under raw_payload.")
    parser.add_argument("--parse-only", action="store_true", help="Only parse and print the post ID without reading token or calling X API.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        post_id = parse_post_id(args.tweet)
        if args.parse_only:
            write_output({"post_id": post_id, "requested_url": args.tweet}, args.output, args.pretty)
            return 0

        token = read_token(args.token_file.expanduser())
        payload = fetch_post(post_id, token)
        normalized = normalize_post(payload, args.tweet, post_id)
        if args.include_raw:
            normalized["raw_payload"] = payload
        write_output(normalized, args.output, args.pretty)
        return 0
    except FetchError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
