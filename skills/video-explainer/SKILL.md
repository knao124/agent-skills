---
name: video-explainer
description: Use this skill when Codex needs to inspect, download, transcribe, summarize, explain, or turn a video or video URL into a detailed explanation/article. Trigger on requests such as "この動画を見て", "音声を文字起こしして", "トランスクリプト抽出して", "動画を記事化して", X/Twitter videos, local .mp4/.mov/.m4a/.mp3 files, HLS/DASH media, or workflows that need source extraction, transcript creation, copyright-safe quoting, and optional explain-to-html output.
license: MIT
---

# Video Explainer

## Overview

Use this skill to turn a video into a reliable explanation artifact. The workflow is: identify the source, acquire the media or audio, transcribe with timestamps, correct obvious recognition errors, then produce a copyright-safe detailed summary or `explain-to-html` article.

## Required Workflow

### 1. Identify the target

- Extract the video URL, local path, post ID, or page URL from the user request.
- If the target is an X/Twitter post, use `tweet-explainer` first to collect visible post metadata. Then extract media from the browser/network only as needed.
- If the target is a local file, do not browse. Work from the provided path.
- If there are multiple videos and the user did not identify the target, ask which one to process.
- Do not log in, like, repost, comment, subscribe, or mutate the source website.

### 2. Acquire media safely

- Prefer the lowest-bitrate audio stream that is clear enough for transcription.
- Save intermediate media under `/tmp` with a stable name containing the source ID or a short slug.
- For public pages, use browser/network inspection, `yt-dlp`, or `ffmpeg` depending on what is available and least brittle.
- For HLS/DASH playlists, prefer `ffmpeg -i <playlist> -vn -c:a copy <audio-file>` when it works; otherwise download segments explicitly.
- Stop rather than bypass DRM, paywalls, age gates, private content, or a login wall the user did not authorize.
- Keep source URL, duration, media path, and acquisition method in notes for the final article.

### 3. Transcribe

Use `scripts/transcribe_media.py` for local files or media URLs when practical:

```sh
python3 <skill_dir>/scripts/transcribe_media.py \
  "<video-or-audio-path-or-url>" \
  --model small.en \
  --compute-type int8 \
  --output /tmp/video-transcript.txt \
  --json /tmp/video-transcript.json
```

Guidance:

- Use `small.en` or `medium.en` for English. Use `small`, `medium`, or another multilingual model for non-English audio.
- Use `--language en` when the language is known; omit it if detection is needed.
- Use `--hotwords` for product names, people, commands, and domain terms such as `Claude Code`, `MCP`, `Routines`, `/loop`, or `JetBrains IDE`.
- If `faster-whisper` is missing, create a throwaway venv under `/tmp` or tell the user what dependency is missing before continuing.
- Preserve timestamps. They are needed for detailed reconstruction and for checking suspicious transcript lines.
- After transcription, manually correct obvious terms by comparing repeated context and, if needed, spot-checking the audio.

### 4. Build the explanation

For a video article, include:

- A short top summary explaining what the article is about.
- A source section near the top with URL, author/page if known, video duration, acquisition method, and transcript caveat.
- A detailed timestamped section, usually titled like `まず、この動画は何を言っているか`.
- A conceptual explanation section that turns the video into practical models, examples, or workflows.
- A risks/notes section when the video discusses automation, security, legal, medical, financial, or operational topics.
- A footer with local transcript path and media path when useful.

Write enough detail that a reader can reconstruct the argument, examples, and sequence of the video without watching it. Do not publish the full transcript unless the user explicitly asks and copyright policy allows it.

### 5. Use `explain-to-html` when article output is requested

If the user asks to article-ize, publish, share, or make the explanation browser-viewable, use `explain-to-html` for the final artifact.

Pass structured context:

- source URL and acquisition method
- video duration
- transcript path
- corrected terms
- timestamped outline
- short quote list, if any
- caveats about automatic transcription and source visibility

If publishing to another repository is requested, follow that repository's change workflow and verify the published page.

## Copyright and Quoting Rules

- Avoid publishing a full transcript or long verbatim passages from a video.
- Use short quotes only when they are important evidence or capture the speaker's exact framing.
- Prefer paraphrased timestamped summaries for the detailed section.
- Keep source attribution visible near the top of the article.
- If the user asks for a verbatim transcript, provide local transcript paths or a limited excerpt instead of placing a long transcript in a public page unless the applicable policy permits it.

## Failure Modes

- If media extraction fails, report the exact blocker: login wall, missing media URL, DRM, downloader missing, network failure, or unsupported container.
- If audio is too noisy, say so and mark low-confidence sections in the article.
- If transcription confidence is poor, use a larger model or ask for a better source file.
- If a source page contains only third-party claims, distinguish video content from verified facts.
