---
name: youtube-to-notebooklm
description: "Автоматизация загрузки YouTube видео/плейлистов в NotebookLM. Извлекает метаданные, транскрипт, комментарии, создаёт блокнот. Триггеры: 'проанализируй видео', 'скушай видео', 'загрузи видео в notebooklm', ссылка на YouTube видео или плейлист."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, AskUserQuestion
---

# YouTube → NotebookLM

## Goal
Принять YouTube ссылку (видео/плейлист), собрать все данные через yt-dlp, загрузить в NotebookLM как структурированные источники, предложить пользователю действия (summary, подкаст, презентация).

## Requirements
- yt-dlp (CLI)
- NotebookLM MCP сервер (настроен и авторизован)
- Папка проекта: `~/youtube-to-notebooklm/downloads/`

## Process

### Step 1: Проверка авторизации
- Вызвать `notebook_list(max_results=1)` — если ошибка авторизации:
  1. Запустить Brave: `"/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" --remote-debugging-port=18800 --no-first-run --no-default-browser-check &`
  2. Авторизоваться: `nlm login --provider openclaw --cdp-url http://127.0.0.1:18800`
  3. Обновить токены: `refresh_auth()`

### Step 2: Парсинг входа
- Определить тип ссылки: одно видео, несколько ссылок, или плейлист
- Если плейлист → получить список видео: `yt-dlp --flat-playlist --print-json <url>`
- Показать пользователю список видео с длительностью, спросить подтверждение

### Step 3: Сбор данных (параллельно для каждого видео)

**3a. Метаданные:**
```bash
yt-dlp --skip-download --print-json --no-warnings "<url>"
```
Извлечь: title, channel, duration, view_count, description, language

**3b. Субтитры:**
```bash
yt-dlp --skip-download --write-auto-sub --sub-lang "en,ru" --sub-format vtt --convert-subs srt -o "$HOME/youtube-to-notebooklm/downloads/%(id)s" "<url>"
```
Если 429 — подождать и повторить. Не критично если не скачались.

**3c. Комментарии (в фоне):**
```bash
yt-dlp --skip-download --write-comments --extractor-args "youtube:comment_sort=top;max_comments=all,all" -o "$HOME/youtube-to-notebooklm/downloads/%(id)s" "<url>"
```

### Step 4: Обработка данных
Можно использовать скрипт: `python3 ~/.claude/skills/youtube-to-notebooklm/scripts/process_video.py <video_id>`

Или вручную:

**Транскрипт:** VTT → чистый текст
- Убрать заголовки WEBVTT, таймкоды, теги, дубликаты
- Группировать по 4 предложения в параграф
- Сохранить: `<video_id>_transcript.txt`

**Комментарии:** info.json → структурированный текст
- Сортировать по лайкам (top first)
- Формат: `@author (N likes): текст`, ответы с `  > `
- Если > 5MB — разбить на части
- Сохранить: `<video_id>_comments.txt`

### Step 5: Категоризация
- Одно видео / одна тема → один блокнот
- Несколько тем → предложить пользователю варианты группировки (несколько опций)
- Название блокнота: краткое, отражающее тему

### Step 6: Создание блокнота и загрузка источников
1. `notebook_create(title=...)`
2. Для каждого видео:
   - `source_add(type=url, url=youtube_url, wait=true)` — NotebookLM сам вытянет транскрипт
   - `source_add(type=text, title="Comments: ...", text=curated_comments, wait=true)`

### Step 7: Предложить действия (human-in-the-loop)
Спросить пользователя через AskUserQuestion (multiSelect=true):
- **Summary (отчёт)** — краткий обзор ключевых идей
- **Аудиоподкаст** — deep dive диалог
- **Презентация** — slide deck
- **Оставить как есть**

### Step 8: Генерация и скачивание
1. `studio_create(notebook_id=..., artifact_type=..., confirm=True)`
2. `studio_status` — поллить до завершения
3. `download_artifact(output_path=~/youtube-to-notebooklm/downloads/...)`
4. Сообщить путь к файлу

### Step 9: Анализ контента (self-improvement)
- Проанализировать содержание видео на полезные инсайты
- Показать пользователю, спросить подтверждение
- Обновить memory файлы если подтверждено

## Rules
- ВСЕГДА проверять авторизацию NotebookLM перед началом (Step 1)
- НЕ скачивать само видео — только метаданные, субтитры, комментарии
- Всегда использовать абсолютные пути с $HOME для yt-dlp -o
- Комментарии курировать (top по лайкам), не сырой дамп
- При 429 от YouTube — подождать 5-10 секунд и повторить
- Показывать прогресс на каждом этапе
- Предлагать несколько вариантов, не один
