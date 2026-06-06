#!/usr/bin/env python3
"""Download or transcribe a video/audio source with faster-whisper."""

from __future__ import annotations

import argparse
import inspect
import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"}


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def safe_stem(source: str) -> str:
    parsed = urlparse(source)
    raw = Path(parsed.path).stem if parsed.path else "video"
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in raw)
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned[:80] or "video"


def acquire_source(source: str, work_dir: Path, stem: str) -> Path:
    if not is_url(source):
        path = Path(source).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"source file not found: {path}")
        return path

    work_dir.mkdir(parents=True, exist_ok=True)
    if shutil.which("yt-dlp"):
        output_template = str(work_dir / f"{stem}.%(ext)s")
        run(["yt-dlp", "--no-playlist", "-f", "ba/bestaudio/best", "-o", output_template, source])
        candidates = sorted(work_dir.glob(f"{stem}.*"), key=lambda path: path.stat().st_mtime, reverse=True)
        if candidates:
            return candidates[0]

    if shutil.which("ffmpeg"):
        output = work_dir / f"{stem}.m4a"
        run(["ffmpeg", "-y", "-i", source, "-vn", "-c:a", "copy", str(output)])
        return output

    raise RuntimeError("URL source requires yt-dlp or ffmpeg")


def format_timestamp(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    total_seconds, ms = divmod(millis, 1000)
    minutes, sec = divmod(total_seconds, 60)
    hours, minute = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minute:02d}:{sec:02d}.{ms:03d}"
    return f"{minute:02d}:{sec:02d}.{ms:03d}"


def transcribe(args: argparse.Namespace, media_path: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    try:
        from faster_whisper import WhisperModel
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "faster-whisper is not installed. Install it in a venv, for example: "
            "python3 -m venv /tmp/video-transcribe-venv && "
            "/tmp/video-transcribe-venv/bin/python -m pip install faster-whisper"
        ) from exc

    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)
    options: dict[str, object] = {
        "beam_size": args.beam_size,
        "vad_filter": args.vad_filter,
    }
    if args.language:
        options["language"] = args.language
    signature = inspect.signature(model.transcribe)
    if args.hotwords and "hotwords" in signature.parameters:
        options["hotwords"] = args.hotwords

    segments_iter, info = model.transcribe(str(media_path), **options)
    segments: list[dict[str, object]] = []
    for segment in segments_iter:
        segments.append(
            {
                "start": float(segment.start),
                "end": float(segment.end),
                "text": segment.text.strip(),
            }
        )

    metadata = {
        "source": args.source,
        "media_path": str(media_path),
        "model": args.model,
        "language": getattr(info, "language", None),
        "language_probability": getattr(info, "language_probability", None),
        "duration": getattr(info, "duration", None),
    }
    return metadata, segments


def write_text(path: Path, metadata: dict[str, object], segments: list[dict[str, object]]) -> None:
    lines = [
        f"Source: {metadata.get('source')}",
        f"Media: {metadata.get('media_path')}",
        f"Model: {metadata.get('model')}",
        f"Duration: {metadata.get('duration')}, language: {metadata.get('language')}, probability: {metadata.get('language_probability')}",
        "",
    ]
    for segment in segments:
        start = format_timestamp(float(segment["start"]))
        end = format_timestamp(float(segment["end"]))
        lines.append(f"[{start} - {end}] {segment['text']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(path: Path, metadata: dict[str, object], segments: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"metadata": metadata, "segments": segments}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download or transcribe a video/audio source with faster-whisper.")
    parser.add_argument("source", help="Local media path or direct media/page URL")
    parser.add_argument("--work-dir", default="/tmp/video-explainer", help="Directory for downloaded media")
    parser.add_argument("--stem", help="Stable output stem. Defaults to a slug from the source path")
    parser.add_argument("--model", default="small.en", help="faster-whisper model name")
    parser.add_argument("--device", default="cpu", help="faster-whisper device, e.g. cpu or cuda")
    parser.add_argument("--compute-type", default="int8", help="faster-whisper compute type")
    parser.add_argument("--language", help="Optional language code such as en or ja")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--hotwords", help="Optional hotwords passed to faster-whisper when supported")
    parser.add_argument("--no-vad", dest="vad_filter", action="store_false", help="Disable VAD filtering")
    parser.set_defaults(vad_filter=True)
    parser.add_argument("--output", help="Transcript text output path")
    parser.add_argument("--json", dest="json_output", help="Transcript JSON output path")
    parser.add_argument("--download-only", action="store_true", help="Only resolve/download media and print its path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    work_dir = Path(args.work_dir).expanduser().resolve()
    stem = args.stem or safe_stem(args.source)

    try:
        media_path = acquire_source(args.source, work_dir, stem)
        if args.download_only:
            print(media_path)
            return 0

        metadata, segments = transcribe(args, media_path)
        transcript_path = Path(args.output or work_dir / f"{stem}-transcript.txt").expanduser().resolve()
        json_path = Path(args.json_output or work_dir / f"{stem}-transcript.json").expanduser().resolve()
        write_text(transcript_path, metadata, segments)
        write_json(json_path, metadata, segments)
        print(json.dumps({"media_path": str(media_path), "transcript": str(transcript_path), "json": str(json_path)}, indent=2))
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"command failed with exit code {exc.returncode}: {' '.join(exc.cmd)}", file=sys.stderr)
        return exc.returncode or 1
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
