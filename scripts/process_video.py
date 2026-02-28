#!/usr/bin/env python3
"""Обработка данных YouTube видео: VTT → текст, JSON → комментарии"""

import json
import re
import sys
import os
from pathlib import Path

DOWNLOADS_DIR = Path.home() / "youtube-to-notebooklm" / "downloads"
MAX_COMMENT_SIZE_MB = 5


def vtt_to_text(vtt_path: Path) -> str:
    """Конвертирует VTT субтитры в чистый текст"""
    content = vtt_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    text_lines = []
    seen = set()

    for line in lines:
        line = line.strip()
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") or \
           line.startswith("Language:") or "-->" in line or line.isdigit():
            continue
        clean = re.sub(r"<[^>]+>", "", line)
        if clean and clean not in seen:
            seen.add(clean)
            text_lines.append(clean)

    transcript = " ".join(text_lines)
    sentences = re.split(r"(?<=[.!?])\s+", transcript)
    paragraphs = []
    current = []
    for s in sentences:
        current.append(s)
        if len(current) >= 4:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))

    return "\n\n".join(paragraphs)


def extract_comments(info_json_path: Path, max_size_mb: float = MAX_COMMENT_SIZE_MB) -> list[str]:
    """Извлекает комментарии из info.json, возвращает список частей (если > max_size_mb)"""
    data = json.loads(info_json_path.read_text(encoding="utf-8"))
    comments = data.get("comments", [])
    title = data.get("title", "Unknown")
    channel = data.get("channel", "Unknown")

    # Сортируем по лайкам
    comments.sort(key=lambda x: x.get("like_count", 0), reverse=True)

    header = f"Комментарии: {title} ({channel})\nВсего: {len(comments)}\n{'=' * 60}\n"

    lines = [header]
    for c in comments:
        author = c.get("author", "?")
        text = c.get("text", "")
        likes = c.get("like_count", 0)
        parent = c.get("parent", "root")
        prefix = "  > " if parent != "root" else ""
        lines.append(f"{prefix}{author} ({likes} likes): {text}\n")

    full_text = "\n".join(lines)
    size_mb = len(full_text.encode("utf-8")) / (1024 * 1024)

    if size_mb <= max_size_mb:
        return [full_text]

    # Разбиваем на части
    parts = []
    current_part = [header]
    current_size = len(header.encode("utf-8"))

    for line in lines[1:]:
        line_size = len(line.encode("utf-8"))
        if current_size + line_size > max_size_mb * 1024 * 1024:
            parts.append("\n".join(current_part))
            part_num = len(parts) + 1
            current_part = [f"{header}(Часть {part_num})\n"]
            current_size = len(current_part[0].encode("utf-8"))
        current_part.append(line)
        current_size += line_size

    if current_part:
        parts.append("\n".join(current_part))

    return parts


def process_video(video_id: str) -> dict:
    """Обработка одного видео: транскрипт + комментарии"""
    result = {"video_id": video_id, "transcript": None, "comments": [], "metadata": None}

    # Транскрипт
    for lang in ["ru", "en"]:
        vtt_path = DOWNLOADS_DIR / f"{video_id}.{lang}.vtt"
        if vtt_path.exists():
            transcript = vtt_to_text(vtt_path)
            out_path = DOWNLOADS_DIR / f"{video_id}_transcript.txt"
            out_path.write_text(transcript, encoding="utf-8")
            result["transcript"] = str(out_path)
            break

    # Комментарии
    info_path = DOWNLOADS_DIR / f"{video_id}.info.json"
    if info_path.exists():
        parts = extract_comments(info_path)
        for i, part in enumerate(parts):
            suffix = f"_part{i+1}" if len(parts) > 1 else ""
            out_path = DOWNLOADS_DIR / f"{video_id}_comments{suffix}.txt"
            out_path.write_text(part, encoding="utf-8")
            result["comments"].append(str(out_path))

        # Метаданные
        data = json.loads(info_path.read_text(encoding="utf-8"))
        result["metadata"] = {
            "title": data.get("title"),
            "channel": data.get("channel"),
            "duration": data.get("duration_string"),
            "views": data.get("view_count"),
            "language": data.get("language"),
            "comment_count": len(data.get("comments", []))
        }

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python process_video.py <video_id> [video_id2 ...]")
        sys.exit(1)

    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

    results = []
    for vid_id in sys.argv[1:]:
        r = process_video(vid_id)
        results.append(r)
        meta = r.get("metadata") or {}
        print(f"[{vid_id}] {meta.get('title', '?')}")
        print(f"  Транскрипт: {r['transcript'] or 'не найден'}")
        print(f"  Комментарии: {len(r['comments'])} файл(ов)")
        print()

    # Вывод JSON для использования в пайплайне
    json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
