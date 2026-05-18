---
name: explain-to-html
description: Write a standalone HTML explanation under `/tmp` when the user asks for an explanation, especially with triggers such as `解説して`, `説明して`, `このコードを解説`, or requests to make the explanation viewable in a browser. Use for code walkthroughs, design explanations, command explanations, and change summaries that should be delivered as an HTML artifact instead of chat-only text.
license: MIT
---

# Explain To Html

## Overview

Use this skill when the explanation itself should be persisted as a browser-viewable file. Investigate the target first, then write a concise standalone HTML page under `/tmp` and reply with the absolute file path plus a short summary in chat.

## Output Contract

- Always create a UTF-8 HTML file under `/tmp`.
- Prefer the filename pattern `/tmp/codex-explain-<topic>-<YYYYMMDD-HHMMSS>.html`.
- Keep the page standalone: inline CSS only, no external assets, no network fetches, no frameworks.
- Default to a concise engineer-facing explanation unless the user specifies another audience.
- If the user explicitly asks for plain text only or says not to write a file, do not use this skill.
- Reply in chat with:
  1. the absolute file path
  2. one short summary of what the file contains
  3. any important caveat that did not fit naturally in the HTML

## Workflow

1. Inspect the requested target enough to explain it accurately.
2. Decide the scope:
   - default: explain what it does, how it works, and the important moving parts
   - for code: include relevant file paths and line references when they materially help
   - for commands or configs: explain purpose, inputs, outputs, and operational caveats
3. Draft a short structure before writing:
   - title
   - summary
   - main sections
   - optional risks, tradeoffs, or next steps
4. Write the HTML file to `/tmp`.
5. Verify the file exists after writing it.
6. Return the path in chat with a 1-3 line summary instead of pasting the full explanation into the conversation.

## Recommended Page Structure

- `header`
  - title
  - generated timestamp
  - target summary
- `main`
  - `Overview`
  - `How It Works`
  - `Important Details`
  - `Examples` when concrete examples improve comprehension
  - `Risks / Notes` when there are caveats
- `footer`
  - referenced files, commands, or links when useful

Prefer short sections and readable spacing over decorative styling.

## HTML Template

Use a simple semantic structure like this and adapt the contents to the task:

```html
<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>...</title>
    <style>
      :root {
        color-scheme: light;
        --bg: #f6f1e8;
        --panel: #fffdf9;
        --text: #1f2937;
        --muted: #5b6470;
        --accent: #9a3412;
        --border: #e7dcc8;
        --code-bg: #f3eadc;
      }
      body {
        margin: 0;
        font-family: "Hiragino Sans", "Noto Sans JP", sans-serif;
        background: linear-gradient(180deg, #f3eadc 0%, #f9f7f2 100%);
        color: var(--text);
      }
      main {
        max-width: 960px;
        margin: 0 auto;
        padding: 48px 24px 80px;
      }
      section, header, footer {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 12px 30px rgba(31, 41, 55, 0.06);
      }
      h1, h2 {
        margin-top: 0;
      }
      code, pre {
        background: var(--code-bg);
        border-radius: 10px;
      }
      pre {
        overflow-x: auto;
        padding: 16px;
      }
      .muted {
        color: var(--muted);
      }
    </style>
  </head>
  <body>
    <main>
      <header>
        <p class="muted">Generated: ...</p>
        <h1>...</h1>
        <p>...</p>
      </header>
      <section>
        <h2>Overview</h2>
        <p>...</p>
      </section>
      <section>
        <h2>How It Works</h2>
        <p>...</p>
      </section>
      <section>
        <h2>Important Details</h2>
        <ul>
          <li>...</li>
        </ul>
      </section>
    </main>
  </body>
</html>
```

## Writing Rules

- Make the page readable on both desktop and mobile.
- Keep CSS inline and moderate in size.
- Prefer neutral, durable explanations over rhetorical prose.
- When citing local files, use absolute paths and line numbers in the HTML body when available.
- Escape or fence code snippets correctly.
- Avoid including hidden reasoning, secrets, tokens, or irrelevant tool output dumps.

## Example Triggers

- `この関数を解説して`
- `この diff を解説して。HTML で見たい`
- `この設定ファイルを説明して`
- `このコマンドが何をしているか解説して`
