# viral_channel -- Project Context

## What This Project Is
An automated YouTube content pipeline called "Last SiX Hours" that discovers
viral videos, extracts peak moments, generates narration, assembles compilation
videos, and uploads them to YouTube with human approval via Telegram.

## Tech Stack
- Python 3.11+
- FFmpeg for all video/audio processing
- yt-dlp for video downloads
- SQLite via SQLAlchemy for state management
- Pydantic for configuration validation
- APScheduler for job scheduling
- python-telegram-bot for human review
- OpenAI-compatible SDK for LLM calls (any provider)
- Coqui XTTS v2 / Piper for text-to-speech
- Pillow for thumbnail/graphic generation
- google-api-python-client for YouTube uploads

## Key Architecture Rules
1. ALL LLM calls go through src/llm/client.py (LLMClient class)
2. ALL TTS calls go through src/tts/engine.py (TTSEngine base class)
3. No hardcoded model names anywhere -- everything in config.yaml
4. No emojis in any output, message, template, or log
5. Config is loaded via src/config.py using Pydantic models
6. Database models are in src/database.py using SQLAlchemy
7. Each module is independent and communicates through the database and filesystem
8. All async code uses Python asyncio

## File Layout
See SPEC.md Section 13 for full directory structure.
Source code lives in src/ with subpackages:
  discovery/, acquisition/, analysis/, scriptgen/, tts/, assembly/,
  thumbnails/, shorts/, upload/, telegram_bot/, llm/, analytics/,
  orchestrator/, utils/

## Testing
- pytest with conftest.py fixtures
- Each module has a corresponding test file in tests/
- Mock external services (YouTube API, Reddit API, Telegram)
- Validation tests for config parsing, script structure, audio levels

## Design Patterns
- Abstract base classes for LLM providers and TTS engines
- Plugin registration pattern for TTS engines
- Repository pattern for database access
- Pipeline pattern for the main workflow
- Configuration via YAML + env vars + runtime overrides
