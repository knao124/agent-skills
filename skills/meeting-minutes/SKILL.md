---
name: meeting-minutes
description: Create Japanese meeting minutes from meeting recordings, audio/video files, transcripts, screenshots, Notta/Zoom/Teams/Google Meet-style share URLs, or meeting-tool pages. Use when the user asks for 議事録, meeting notes, minutes, 決定事項, TODO/action items, or wants to turn a meeting video/transcript into a shareable Japanese summary with agenda sections.
license: MIT
---

# Meeting Minutes

Create concise, shareable Japanese minutes from a meeting source. Preserve the user's requested granularity and formatting; do not silently rewrite substance during formatting-only revisions.

## Workflow

1. Acquire the source.
   - Accept local audio/video, a direct media URL, a meeting-tool share URL, an existing transcript, screenshots, or pasted notes.
   - If a meeting tool exposes a transcript with speaker labels and timestamps, prefer that transcript over re-running Whisper.
   - If no transcript is available, download/extract the audio and transcribe it with Whisper/faster-whisper. Keep rough timestamps for each segment.
   - If a password, logged-in session, or JavaScript app is involved, use the appropriate browser workflow. Do not repeat secrets in final output.

2. Build evidence.
   - Keep the transcript, metadata, downloaded media, and screenshots in a temporary working directory when files are created.
   - Record the meeting title, date/time, duration, participants if available, and source confidence.
   - Preserve rough timestamps internally even when the final minutes omit them.

3. Use visual context when needed.
   - Capture screenshots at timestamps where the transcript refers to slides, tables, diagrams, UI, API specs, or phrases like "this", "here", "left", "right", or "as shown".
   - Use screenshots to supplement the text, especially for agenda slides, architecture diagrams, API examples, spreadsheets, and decision tables.
   - Treat screenshot-derived content as supplemental evidence; avoid overclaiming uncertain text.

4. Draft the minutes.
   - Group content by agenda or semantic topic, not by speaker turn.
   - Summarize the discussion into "議事"; do not paste a transcript.
   - Extract decisions into "決定内容".
   - Extract owners and next actions into "TODO". If owner is unclear, use the company/team name only when supported by the transcript.
   - Keep the user's confirmed wording when iterating on a draft.

5. Verify before returning.
   - Check that every decision and TODO is grounded in the transcript or visual evidence.
   - Check that the minutes do not introduce new facts during formatting-only edits.
   - If the source has weak audio, missing transcript, or unreadable screenshots, state the limitation briefly.

## Default Output Format

For Japanese sharing, avoid Markdown tables and Markdown bullet syntax by default. Use full-width indentation and the full-width bullet "・".

Use this structure unless the user provides a different one:

```text
■ 議事録

■ mtgタイトル
　<meeting title>

■ 日時
　<date/time>
　※<source note if useful>

■ 議事一覧
　・① <agenda 1>
　・② <agenda 2>
　・③ <agenda 3>

■ ① <agenda 1>

　● 議事
　　・<one discussion sentence>
　　・<one discussion sentence>

　● 決定内容
　　・<decision>
　　・<decision>

　● TODO
　　・<owner>：<action>
　　・<owner>：<action>
```

Formatting rules:
- Prefix all top-level headings with "■ ", including the meeting title blocks and each agenda section: "■ 議事録", "■ mtgタイトル", "■ 日時", "■ 議事一覧", and "■ ① <agenda>".
- Use "①②③..." only for agenda numbers in "■ 議事一覧" and agenda section headings.
- Use "・" for items under "■ 議事一覧", "● 議事", "● 決定内容", and "● TODO".
- Write subsection headings as "　● 議事", "　● 決定内容", and "　● TODO".
- Use full-width spaces for indentation: one "　" before subsection headings, two "　　" before items.
- Split "● 議事" into one sentence per bullet. Do not combine multiple Japanese sentences into one bullet; split at "。" while preserving the user's approved wording.
- Keep "● 議事" concise. Do not add detail solely to create more bullets.
- Include timestamps in final output only when the user asks for them or when they are necessary to resolve ambiguity.

## Iteration Rules

When the user asks to change formatting, only change formatting. Do not alter:
- agenda grouping
- the factual content of "議事"
- decisions
- TODO ownership
- wording the user explicitly approved

When the user challenges accuracy, treat their supplied text as the current source of truth for the revised draft unless it conflicts with the raw transcript. If it conflicts, explain the discrepancy and ask how to handle it.

## Practical Notes

- For video/audio acquisition and transcription tasks, use the `video-explainer` skill as the acquisition/transcription workflow when it is available and applicable.
- Prefer native meeting-tool transcripts with speaker labels over Whisper output because they are usually faster and often include better segmentation.
- If using Whisper, use segment start/end times for rough timing. Word-level timestamps are possible when the transcription script/model supports them, but meeting minutes usually only need segment-level timing.
- For meeting-tool URLs such as Notta, inspect the page and network responses for transcript payloads before downloading video. Download the media only when transcript extraction is unavailable or visual/screenshot evidence is needed.
