# YouTube → NotebookLM

Claude Code skill that automatically ingests YouTube videos and playlists into Google NotebookLM — extracting metadata, transcripts, and top comments, then offering to generate summaries, podcasts, or slide decks.

## Features

- **Single video or playlist** — detects link type automatically
- **Full data extraction** — metadata, auto-generated subtitles (en/ru), top comments sorted by likes
- **Smart categorization** — groups related videos into one notebook, asks before splitting
- **Artifact generation** — summary (Briefing Doc), audio podcast (Deep Dive), slide deck, mind map
- **Downloads** — all generated artifacts saved locally to `~/youtube-to-notebooklm/downloads/`

## Prerequisites

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — `brew install yt-dlp` or `pip install yt-dlp`
- [NotebookLM MCP server](https://github.com/jxnl/notebooklm-mcp) — configured and authenticated
- Claude Code

## Installation

### Git clone (recommended)

```bash
# Global (all projects)
git clone https://github.com/222dotcrypto/youtube-to-notebooklm.git ~/.claude/skills/youtube-to-notebooklm

# Project-local
git clone https://github.com/222dotcrypto/youtube-to-notebooklm.git .claude/skills/youtube-to-notebooklm
```

### Manual

Copy `SKILL.md` and `scripts/` to `~/.claude/skills/youtube-to-notebooklm/`.

## Usage

Trigger the skill in Claude Code by:

- Pasting a YouTube link — the skill activates automatically
- Typing: `"analyze this video"`, `"load video into notebooklm"`
- Running: `/youtube-to-notebooklm <url>`

### What happens

1. Checks NotebookLM auth (auto-login if needed)
2. Fetches video metadata, subtitles, and comments via yt-dlp
3. Processes transcript (VTT → clean text) and curates top comments
4. Creates a NotebookLM notebook with structured sources
5. Asks what to generate: summary, podcast, slides, or mind map
6. Downloads generated artifacts locally

## How It Works

```
YouTube URL → yt-dlp (metadata + subtitles + comments)
           → process_video.py (VTT cleanup, comment curation)
           → NotebookLM MCP (create notebook + add sources)
           → Studio (generate artifacts)
           → Download locally
```

## File Structure

```
youtube-to-notebooklm/
├── SKILL.md                    # Skill instructions (agent SOP)
├── scripts/
│   └── process_video.py        # VTT→text converter, comment extractor
└── README.md
```

## License

MIT
