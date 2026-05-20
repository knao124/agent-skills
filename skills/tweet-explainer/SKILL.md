---
name: tweet-explainer
description: Use this skill when the user asks Codex to read, summarize, explain, or turn into an HTML article a Tweet/X post URL. Try browser-based public extraction first to avoid X API usage, then fall back to the App-only token stored at ~/.x-token when browser extraction cannot reliably obtain the post, X Article, media, or linked content needed for the explanation. Use the existing explain-to-html skill for the final browser-viewable explanation.
license: MIT
---

# Tweet Explainer

## Overview

Use this skill for requests like:

- `このツイートを解説して`
- `このX投稿を読んでHTMLにして`
- `tweet URLを渡すので要約記事を書いて`
- `X Article付きの投稿を読んでまとめて`

The goal is to produce a standalone HTML explanation using the existing `explain-to-html` skill. Data acquisition happens first, with this priority:

1. Browser extraction without using any token.
2. X API fallback with the App-only token stored at `~/.x-token`.
3. Stop if browser extraction fails and `~/.x-token` is missing.

## Required Workflow

### 1. Identify the Target

- Extract the post URL and post ID from the user request.
- Accept common URL forms such as:
  - `https://x.com/<user>/status/<id>`
  - `https://twitter.com/<user>/status/<id>`
  - URLs with query strings such as `?s=20`
- If there are multiple URLs, ask which one to explain unless the user clearly marks the target.

### 2. Try Browser Extraction First

Use available browser tooling when it is available in the current Codex context. Do not use the X API yet. If no browser tool is available, treat browser extraction as unavailable and move to the API fallback.

Open the target URL and collect what can be read from the public page:

- author display name and handle
- post timestamp
- post text
- X Article title and body, if visible
- media descriptions, alt text, image/video context, or card title if visible
- linked URLs and expanded destinations if visible
- public engagement counts when visible

Treat browser extraction as successful only when the visible page contains enough substantive content to explain the post. For a post that only shows a card, a login wall, a truncated X Article, missing media, or unstable/ambiguous content, use the API fallback.

Do not log in, post, like, follow, bookmark, or otherwise mutate X state.

### 3. Fall Back to the App-Only Token

If browser extraction is insufficient, use `scripts/fetch_x_post.py`.

Before calling the script, check that `~/.x-token` exists. If it does not exist, stop and tell the user:

```text
ブラウザから十分な投稿内容を取得できず、API fallbackに必要な ~/.x-token も見つからないため停止しました。
```

Do not continue with guesses or partial summaries when the token file is missing.

Run:

```sh
python3 <skill_dir>/scripts/fetch_x_post.py "<tweet-url-or-id>" --pretty
```

The script:

- reads `~/.x-token` by default
- accepts a raw token or a `Bearer ...` value
- never prints the token
- fetches the post with `tweet.fields=article,...` so X Article content is included when X API returns it
- outputs normalized JSON for explanation

If the script returns:

- `401`: tell the user the token is invalid, empty, or revoked.
- `403`: tell the user the endpoint, plan, or post visibility may not allow App-only access.
- `404`: tell the user the post was not found, deleted, private, or the ID was wrong.
- `429`: tell the user rate limits were hit and stop.

### 4. Use `explain-to-html` for the Final Article

After acquiring the post data, use the existing `explain-to-html` skill to create the final HTML. Do not provide only a chat summary unless the user explicitly forbids file creation.

Pass the explanation target as structured context:

- original URL
- acquisition method: `browser` or `x-api-app-only`
- author, handle, post ID, timestamp
- post text
- X Article title, preview, and plain text when present
- important code blocks or quoted snippets when present
- media/card/link details when available
- public metrics if available
- caveats such as `browser extraction only`, `API returned article metadata only`, or `claims in the post were not independently verified`

The final explanation should:

- distinguish the post/article's claims from confirmed facts
- avoid over-quoting long source text
- include source URL and acquisition method
- mention when API fallback was used
- include the normal `explain-to-html` review/comment UI

## Secret Handling

- Never print, paste, summarize, or write the token from `~/.x-token`.
- Do not include the token in command output, logs, HTML, PR text, or implementation notes.
- Do not commit `.x-token` or any copied token file.

## Script Examples

Parse a URL without using the token:

```sh
python3 skills/tweet-explainer/scripts/fetch_x_post.py \
  "https://x.com/0xDepressionn/status/2055999112470839383?s=20" \
  --parse-only
```

Fetch via App-only token:

```sh
python3 skills/tweet-explainer/scripts/fetch_x_post.py \
  "https://x.com/0xDepressionn/status/2055999112470839383?s=20" \
  --pretty
```

Save normalized JSON for handoff into `explain-to-html`:

```sh
python3 skills/tweet-explainer/scripts/fetch_x_post.py "<url>" \
  --pretty \
  --output /tmp/tweet-explainer-post.json
```
