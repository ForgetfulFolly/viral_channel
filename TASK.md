# Task: Create project scaffolding and base files

Priority: 1
Status: spec-in-progress
Created: 2026-02-28T01:00:00Z
Scope: src/, tests/, config/, assets/, scripts/, docs/, voices/, models/, working/, archive/, pyproject.toml, requirements.txt, .gitignore, .env.example, README.md

## Description

Create the full directory structure and base files for the viral_channel project.
This includes all empty __init__.py files, pyproject.toml, requirements.txt,
.gitignore, .env.example, and a README.md.

The project is an automated YouTube content pipeline called "Last SiX Hours" that
discovers viral videos, extracts peak moments, generates narration, assembles
compilation videos, and uploads them to YouTube with human approval via Telegram.

### Directory Structure

Create the following directories and files:

```
src/
  __init__.py
  config.py              (empty placeholder with docstring only)
  database.py            (empty placeholder with docstring only)
  models.py              (empty placeholder with docstring only)
  main.py                (empty placeholder with docstring only)
  discovery/
    __init__.py
    youtube_source.py    (empty placeholder)
    reddit_source.py     (empty placeholder)
    scorer.py            (empty placeholder)
    classifier.py        (empty placeholder)
    dedup.py             (empty placeholder)
    engine.py            (empty placeholder)
  acquisition/
    __init__.py
    downloader.py        (empty placeholder)
    validator.py         (empty placeholder)
  analysis/
    __init__.py
    most_replayed.py     (empty placeholder)
    transcript_analyzer.py (empty placeholder)
    audio_analyzer.py    (empty placeholder)
    clip_extractor.py    (empty placeholder)
    scene_analyzer.py    (empty placeholder)
  scriptgen/
    __init__.py
    generator.py         (empty placeholder)
    validator.py         (empty placeholder)
  tts/
    __init__.py
    engine.py            (empty placeholder)
    xtts_engine.py       (empty placeholder)
    piper_engine.py      (empty placeholder)
    audio_processor.py   (empty placeholder)
  assembly/
    __init__.py
    graphics.py          (empty placeholder)
    timeline.py          (empty placeholder)
    audio_mixer.py       (empty placeholder)
    renderer.py          (empty placeholder)
  thumbnails/
    __init__.py
    generator.py         (empty placeholder)
    frame_selector.py    (empty placeholder)
  shorts/
    __init__.py
    generator.py         (empty placeholder)
    cropper.py           (empty placeholder)
  upload/
    __init__.py
    youtube_uploader.py  (empty placeholder)
    metadata.py          (empty placeholder)
  telegram_bot/
    __init__.py
    bot.py               (empty placeholder)
    notifications.py     (empty placeholder)
    review.py            (empty placeholder)
    commands.py          (empty placeholder)
    file_server.py       (empty placeholder)
  llm/
    __init__.py
    client.py            (empty placeholder)
    prompts.py           (empty placeholder)
  analytics/
    __init__.py
    collector.py         (empty placeholder)
    analyzer.py          (empty placeholder)
    feedback.py          (empty placeholder)
  orchestrator/
    __init__.py
    pipeline.py          (empty placeholder)
    resource_manager.py  (empty placeholder)
    cleanup.py           (empty placeholder)
    scheduler.py         (empty placeholder)
  utils/
    __init__.py
    logging.py           (empty placeholder)
    ffmpeg.py            (empty placeholder)

tests/
  __init__.py
  conftest.py            (empty placeholder)

config/
  config.yaml            (DO NOT CREATE - separate task)
  prompts/               (empty directory, add .gitkeep)

assets/
  fonts/                 (empty directory, add .gitkeep)
  music/                 (empty directory, add .gitkeep)
  watermarks/            (empty directory, add .gitkeep)

voices/                  (empty directory, add .gitkeep)
models/                  (empty directory, add .gitkeep)
working/                 (empty directory, add .gitkeep)
archive/                 (empty directory, add .gitkeep)

scripts/
  (empty, add .gitkeep)

docs/
  (empty, add .gitkeep)
```

### Each placeholder .py file should contain ONLY:

```python
"""
Module description based on file name.
"""
```

### pyproject.toml should include:

- Project name: viral-channel
- Version: 0.1.0
- Description: "Automated YouTube content pipeline -- Last SiX Hours"
- Python requires: >=3.11
- Basic project metadata

### requirements.txt dependencies (pin major version only):

```
# Core
pydantic>=2.0
pyyaml>=6.0
sqlalchemy>=2.0
aiohttp>=3.9
httpx>=0.27

# Video/Audio
yt-dlp>=2024.0

# LLM
openai>=1.0
jinja2>=3.1

# TTS
TTS>=0.22
piper-tts>=1.2

# Telegram
python-telegram-bot>=20.0

# YouTube API
google-api-python-client>=2.0
google-auth-oauthlib>=1.0

# Reddit
praw>=7.0

# Image
Pillow>=10.0

# Scheduling
APScheduler>=3.10

# Analysis
numpy>=1.26

# Testing
pytest>=8.0
pytest-asyncio>=0.23
```

### .gitignore should cover:

- Python: __pycache__, *.pyc, *.pyo, .eggs, *.egg-info, dist, build
- Environment: .env, .env.*, *.env
- IDE: .vscode/, .idea/
- Project-specific: working/, models/*.bin, models/*.pth, voices/*.wav
- OS: .DS_Store, Thumbs.db
- Credentials: config/youtube_*_creds.json

### .env.example entries:

```
YOUTUBE_API_KEY=
TELEGRAM_BOT_TOKEN=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
LLM_API_KEY=
LLM_BASE_URL=http://localhost:11434/v1
```

### README.md:

- Title: Last SiX Hours
- One-line description: Automated YouTube content pipeline
- Point to SPEC.md and DESIGN.md for details
- Basic setup instructions placeholder

## Acceptance Criteria

- [ ] All directories from the structure above exist
- [ ] Every Python package directory has an __init__.py
- [ ] pyproject.toml has correct project metadata, Python >=3.11 requirement
- [ ] requirements.txt lists all dependencies listed above
- [ ] .gitignore covers Python, env files, model files, working dirs, __pycache__
- [ ] .env.example has placeholder entries for all required secrets
- [ ] README.md has project name, one-line description, and references to SPEC.md/DESIGN.md
- [ ] All placeholder .py files have a docstring and nothing else
- [ ] Empty directories have .gitkeep files

## Critical Constraints

- Do NOT write any functional Python code, only project structure files
- Do NOT create config/config.yaml (that is a separate task T02)
- Do NOT include emojis in any file content
- requirements.txt must pin major versions only (e.g., pydantic>=2.0)
- Placeholder .py files must contain ONLY a module docstring
- Use .gitkeep for empty directories that need to be tracked

## Reference Files

- SPEC.md (Section 13 -- Directory Structure)
- DESIGN.md (Section 6 -- Interface Contracts for module names)
