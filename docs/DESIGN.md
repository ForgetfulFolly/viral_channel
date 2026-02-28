# Last SiX Hours -- Comprehensive Design & Agent Task Plan

**Version:** 1.0
**Date:** February 28, 2026
**Spec Reference:** SPEC.md
**Agent Reference:** trading-agent (git-native, phased task execution)

---

## Table of Contents

1. [Execution Strategy](#1-execution-strategy)
2. [Workspace Setup](#2-workspace-setup)
3. [Dependency Graph](#3-dependency-graph)
4. [Task Definitions](#4-task-definitions)
5. [Implementation Order](#5-implementation-order)
6. [Interface Contracts](#6-interface-contracts)
7. [Agent Configuration](#7-agent-configuration)
8. [Human Review Checkpoints](#8-human-review-checkpoints)
9. [Testing Strategy](#9-testing-strategy)
10. [Risk Register](#10-risk-register)

---

## 1. Execution Strategy

### 1.1 How the Agent Works (Summary)

The trading-agent operates on a git-native task model:

1. Tasks are created as `agent/task-*` branches with a `TASK.md` file
2. A worker on MM5000 polls for unclaimed branches, claims one atomically via git push
3. The worker runs three phases: SPEC -> DESIGN -> IMPLEMENT
4. Each phase calls an LLM (DeepSeek-R1 32B on MM5000 via Ollama, zero cost)
5. After implementation, the worker self-validates (syntax check, pytest, imports)
6. On success, `REVIEW.md` is written -- human reviews before merging
7. Lessons are auto-extracted for future tasks

### 1.2 Execution Environment

| Node | Role | LLM | Speed |
|---|---|---|---|
| MM5000 (Dell R730) | Primary worker | DeepSeek-R1:32B via Ollama | ~15-25 tok/s per P40 |
| Windows workstation | Task creation, review, interactive | GPT-4o via GitHub Models | Fast (cloud) |

**Estimated throughput:** 3-4 completed tasks per 8-hour overnight window on MM5000.

### 1.3 Task Sizing Principle

Each task should be **one focused module or component** -- small enough that the agent can hold the full context in a single LLM pass (~24K usable tokens on DeepSeek-R1:32B with 32K context). Tasks that touch more than 3-4 files should be split.

### 1.4 Phased Rollout

Tasks are organized into 6 phases matching the SPEC implementation phases. Each phase's tasks have dependency chains so the agent processes them in correct order. Phase 1 tasks have no dependencies. Phase 2 tasks depend on Phase 1 completion, etc.

---

## 2. Workspace Setup

### 2.1 Initialize viral_channel for Agent Use

Before the agent can work, the workspace needs:

1. **Agent config** at `.agent/config.yaml`
2. **Context file** at `.agent/context.md` describing the project
3. **Base project structure** (directories, pyproject.toml, requirements.txt)
4. **The agent repo** cloned or symlinked on MM5000

### 2.2 .agent/config.yaml

```yaml
workspace:
  name: viral_channel
  description: "Automated YouTube channel pipeline -- Last SiX Hours"

blocked_paths:
  - ".git/"
  - "*.env"
  - ".env*"
  - "config/youtube_*_creds.json"
  - "voices/"
  - "models/"
  - "_agent_ref/"

context:
  architecture: ".agent/context.md"
```

### 2.3 .agent/context.md

```markdown
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
```

---

## 3. Dependency Graph

```
PHASE 0: Foundation (no dependencies)
  T01: Project scaffolding
  T02: Configuration system
  T03: Database schema
  T04: Logging utility

PHASE 1: Core Modules (depend on Phase 0)
  T05: LLM abstraction layer        <- T02
  T06: FFmpeg utility wrapper        <- T01
  T07: YouTube API client            <- T02
  T08: Reddit API client             <- T02
  T09: Viral score calculator        <- T02

PHASE 1B: Pipeline Modules (depend on Phase 1)
  T10: Discovery engine              <- T07, T08, T09, T05, T03
  T11: Video downloader              <- T06, T03
  T12: Most Replayed scraper         <- T01
  T13: Transcript analyzer           <- T05
  T14: Audio energy analyzer         <- T06
  T15: Clip extractor                <- T06, T03

PHASE 2: Content Production (depend on Phase 1B)
  T16: Scene analysis orchestrator   <- T12, T13, T14, T15
  T17: Script generator              <- T05, T03
  T18: TTS engine abstraction        <- T02
  T19: XTTS v2 engine implementation <- T18
  T20: Piper engine implementation   <- T18
  T21: Audio processor               <- T06

PHASE 3: Assembly & Output (depend on Phase 2)
  T22: Graphics generator            <- T06, T02
  T23: Timeline builder              <- T06
  T24: Audio mixer                   <- T06
  T25: Video renderer                <- T22, T23, T24
  T26: Thumbnail generator           <- T05, T22
  T27: Shorts generator              <- T06, T15
  T28: YouTube uploader              <- T07, T03
  T29: Metadata generator            <- T05

PHASE 4: Communication & Control (depend on Phase 3)
  T30: Telegram bot core             <- T02, T03
  T31: Telegram review flow          <- T30, T28
  T32: Telegram commands             <- T30, T03
  T33: File preview server           <- T30
  T34: Pipeline orchestrator         <- T10, T11, T16, T17, T18, T25, T28, T31
  T35: Scheduler                     <- T34

PHASE 5: Analytics & Polish (depend on Phase 4)
  T36: Analytics collector           <- T07, T03
  T37: Analytics feedback engine     <- T36, T05
  T38: Main entry point              <- T34, T35, T30
  T39: Integration tests             <- T38
```

---

## 4. Task Definitions

Each task below is defined in the exact format needed for the agent's TASK.md.
Create each as a git branch: `agent/task-YYYYMMDDHHMMSS-<slug>`.

---

### T01: Project Scaffolding

```markdown
# Task: Create project scaffolding and base files

Priority: 1
State: queued
Created: 2026-02-28T00:00:00Z
Scope: src/, tests/, config/, assets/, scripts/, docs/

## Description
Create the full directory structure and base files for the viral_channel project.
This includes all empty __init__.py files, pyproject.toml, requirements.txt,
.gitignore, .env.example, and a README.md.

Reference SPEC.md Section 13 for the complete file/folder structure.

Do NOT create any implementation code -- only empty __init__.py files, project
metadata, and skeleton files.

## Acceptance Criteria
- [ ] All directories from SPEC.md Section 13 exist
- [ ] Every Python package directory has an __init__.py
- [ ] pyproject.toml has correct project metadata, Python >=3.11 requirement
- [ ] requirements.txt lists all dependencies from SPEC.md Section 3.3
- [ ] .gitignore covers Python, env files, model files, working dirs, __pycache__
- [ ] .env.example has placeholder entries for all required secrets
- [ ] README.md has project name, one-line description, and "See SPEC.md"

## Critical Constraints
- Do NOT write any functional Python code, only project structure files
- Do NOT create config.yaml yet (separate task)
- Do NOT include emojis in any file
- requirements.txt must pin major versions only (e.g., httpx>=0.27)
```

---

### T02: Configuration System

```markdown
# Task: Build the configuration system with Pydantic models

Priority: 1
State: queued
Created: 2026-02-28T00:00:01Z
Depends-On: agent/task-*-create-project-scaffolding
Scope: src/config.py, config/config.yaml, tests/test_config.py

## Description
Implement the configuration loading system as described in SPEC.md Section 7.

Create Pydantic BaseModel classes for every configuration section:
- GeneralConfig, LLMProviderConfig, LLMConfig, TTSEngineConfig, TTSConfig,
  VoiceConfig, ChannelConfig, DiscoveryConfig, VideoConfig, AudioConfig,
  TelegramConfig, YouTubeUploadConfig, SchedulerConfig, BrandingConfig

Create a root AppConfig model that contains all sub-configs. Implement:
- load_config(path: str) -> AppConfig: Load from YAML, merge env vars
- Environment variable substitution: ${VAR_NAME} in YAML values resolved from os.environ
- Validation: Pydantic validates all fields, raises clear errors for missing/invalid config

Also create config/config.yaml with all default values from SPEC.md Section 7.1.

## Acceptance Criteria
- [ ] src/config.py has all Pydantic models matching SPEC.md Section 7 config structure
- [ ] load_config() loads YAML, substitutes env vars, returns validated AppConfig
- [ ] config/config.yaml matches SPEC.md Section 7.1 exactly (with the 8-10 min target durations)
- [ ] tests/test_config.py has tests for: loading valid config, missing required fields,
      env var substitution, default values, channel config validation
- [ ] All duration/count fields have appropriate min/max validators

## Critical Constraints
- Use pydantic v2 (BaseModel with model_validator, field_validator)
- Environment variable substitution must handle missing vars gracefully (log warning, keep placeholder)
- No emojis in any output or default config values
- Config must be importable as: from src.config import load_config, AppConfig

## Reference Files
- SPEC.md (Section 7)
```

---

### T03: Database Schema and Models

```markdown
# Task: Implement SQLite database with SQLAlchemy models

Priority: 1
State: queued
Created: 2026-02-28T00:00:02Z
Depends-On: agent/task-*-create-project-scaffolding
Scope: src/database.py, scripts/init_database.py, tests/test_database.py

## Description
Implement the database layer as described in SPEC.md Section 6.

Create SQLAlchemy ORM models for all tables:
- DiscoveredVideo, PipelineRun, Clip, Script, TTSAudio, Short,
  Analytics, ReviewLog, ConfigOverride, ErrorLog

Create helper functions:
- init_db(db_path: str) -> Engine: Create engine and all tables
- get_session(engine: Engine) -> Session: Get a new session
- Common query helpers: get_pending_videos(niche), get_pipeline_run(id),
  mark_video_processed(video_id, status), log_error(module, error_type, message)

Create scripts/init_database.py that initializes an empty database.

## Acceptance Criteria
- [ ] All 10 tables from SPEC.md Section 6 are defined as SQLAlchemy models
- [ ] All indexes from SPEC.md Section 6 are created
- [ ] init_db() creates all tables and indexes
- [ ] scripts/init_database.py is a runnable script that creates the database
- [ ] tests/test_database.py tests: table creation, insert/query for each model,
      index existence, foreign key relationships

## Critical Constraints
- Use SQLAlchemy 2.0+ style (mapped_column, DeclarativeBase)
- Database path comes from config (but init_db accepts a path parameter for testing)
- All timestamps default to UTC (not local time)
- No emojis in any field defaults or log messages

## Reference Files
- SPEC.md (Section 6)
```

---

### T04: Logging Utility

```markdown
# Task: Create structured logging utility

Priority: 2
State: queued
Created: 2026-02-28T00:00:03Z
Depends-On: agent/task-*-create-project-scaffolding
Scope: src/utils/logging.py, tests/test_logging.py

## Description
Create a logging utility that provides structured JSON logging for the pipeline.

Implement:
- setup_logging(log_dir: str, log_level: str, module_name: str) -> Logger
- Logs to both stderr and rotating file (10MB max, 5 backups)
- JSON format with fields: timestamp, level, module, message, extra (dict)
- Console output is human-readable (not JSON) for development
- File output is JSON-lines format for machine parsing
- No emojis in any log output

## Acceptance Criteria
- [ ] setup_logging returns a configured Logger
- [ ] File logs are JSON-lines format with timestamp, level, module, message
- [ ] Console logs are human-readable format
- [ ] Log rotation works (RotatingFileHandler)
- [ ] tests/test_logging.py tests: setup, file output format, rotation config

## Critical Constraints
- Use Python standard logging module (no external dependencies)
- No emojis in any log output or format strings
- Module name is included in every log line

## Reference Files
- SPEC.md (Section 12)
```

---

### T05: LLM Abstraction Layer

```markdown
# Task: Build the LLM abstraction layer with provider support

Priority: 2
State: queued
Created: 2026-02-28T00:00:04Z
Depends-On: agent/task-*-build-the-configuration-system
Scope: src/llm/, tests/test_llm_client.py

## Description
Implement the LLM abstraction layer as described in SPEC.md Section 8.

Create the following in src/llm/:
- client.py: LLMClient class with methods:
  - async complete(prompt, system_prompt=None, **kwargs) -> str
  - async complete_json(prompt, system_prompt=None, schema=None, **kwargs) -> dict
  - async classify(text, categories, **kwargs) -> str
  - async summarize(text, max_length=200, **kwargs) -> str
- prompts.py: PromptManager class that loads Jinja2 templates from config/prompts/
  - load_prompt(template_name, **variables) -> str

The LLMClient uses the openai AsyncOpenAI SDK with configurable base_url.
This makes it compatible with OpenAI, DeepSeek, vLLM, Ollama, and any
OpenAI-compatible endpoint.

Implement fallback chain: try primary provider, retry on failure up to
max_attempts, then try fallback provider.

## Acceptance Criteria
- [ ] LLMClient initializes from LLMConfig (primary + fallback)
- [ ] complete() sends a chat completion request and returns the text response
- [ ] complete_json() parses the response as JSON, retries if parse fails
- [ ] classify() returns one of the provided categories
- [ ] summarize() returns text under max_length
- [ ] Fallback chain works: primary fails -> retry -> fallback provider
- [ ] PromptManager loads .j2 templates and renders with variables
- [ ] tests/test_llm_client.py mocks the openai client and tests all methods,
      fallback behavior, JSON parsing, retry logic

## Critical Constraints
- Use the openai Python SDK (openai.AsyncOpenAI) -- NOT httpx directly
- base_url and model come from config -- never hardcoded
- All methods are async
- JSON parsing retries up to 3 times with a corrective prompt
- No emojis in any system prompt or output

## Reference Files
- SPEC.md (Section 8)
```

---

### T06: FFmpeg Utility Wrapper

```markdown
# Task: Create FFmpeg utility wrapper for video and audio operations

Priority: 2
State: queued
Created: 2026-02-28T00:00:05Z
Depends-On: agent/task-*-create-project-scaffolding
Scope: src/utils/ffmpeg.py, tests/test_ffmpeg.py

## Description
Create a utility module that wraps common FFmpeg operations used throughout
the pipeline. All video and audio processing goes through this module.

Implement these functions (all call ffmpeg via subprocess):
- extract_clip(input_path, output_path, start_sec, end_sec, fade_sec=0.5) -> Path
- normalize_audio(input_path, output_path, target_lufs=-16) -> Path
- get_media_info(path) -> dict  (duration, resolution, codec, fps, audio_channels)
- extract_audio(input_path, output_path, format="wav") -> Path
- concat_videos(input_paths, output_path, transition_sec=0.5) -> Path
- overlay_text(input_path, output_path, text, position, font_path, font_size, color) -> Path
- overlay_image(input_path, output_path, image_path, position, duration_sec=None) -> Path
- scene_detect(input_path, threshold=0.3) -> list[float]  (timestamps of scene changes)
- create_silent_audio(output_path, duration_sec, sample_rate=48000) -> Path
- mix_audio_tracks(tracks: list[dict], output_path) -> Path
    (each track: {path, volume_db, start_sec})
- render_video(inputs: dict, output_path, resolution, fps, codec, crf, audio_codec, audio_bitrate) -> Path
    (the main render function that takes a complex filter graph)

Each function:
- Validates that input files exist before calling ffmpeg
- Raises a clear exception on ffmpeg failure (with stderr output)
- Returns the Path to the output file on success
- Uses subprocess.run with timeout

## Acceptance Criteria
- [ ] All functions listed above are implemented
- [ ] get_media_info parses ffprobe JSON output correctly
- [ ] Error handling includes ffmpeg stderr in exception message
- [ ] All functions have type hints and docstrings
- [ ] tests/test_ffmpeg.py tests: get_media_info parsing, command construction
      for each function (mock subprocess), error handling on non-zero exit

## Critical Constraints
- Call ffmpeg/ffprobe via subprocess.run, NOT via ffmpeg-python or moviepy
- Always use -y flag (overwrite output)
- Always use -hide_banner -loglevel error for clean stderr
- Timeout defaults to 600 seconds (configurable per function)
- Validate input file existence before building the command
- No emojis in error messages

## Reference Files
- SPEC.md (Sections 4.3, 4.5, 4.6)
```

---

### T07: YouTube API Client

```markdown
# Task: Build YouTube Data API v3 client wrapper

Priority: 2
State: queued
Created: 2026-02-28T00:00:06Z
Depends-On: agent/task-*-build-the-configuration-system
Scope: src/discovery/youtube_source.py, src/upload/youtube_uploader.py, scripts/setup_youtube_oauth.py, tests/test_youtube.py

## Description
Create two YouTube API wrapper modules:

1. src/discovery/youtube_source.py -- Discovery (uses API key, no OAuth):
   - get_trending(region_code, category_id=None) -> list[dict]
   - search_recent(query, published_after, max_results=50) -> list[dict]
   - get_video_details(video_ids: list[str]) -> list[dict]
   - get_most_replayed_heatmap(video_id) -> list[dict] | None
     (scrapes the YouTube player page, not an API call)
   - Track quota usage internally (log warnings at 80% of daily limit)

2. src/upload/youtube_uploader.py -- Upload (uses OAuth):
   - async upload_video(file_path, metadata: dict, credentials_file: str) -> str
     (returns YouTube video ID, uses resumable upload)
   - async set_thumbnail(video_id, thumbnail_path, credentials_file) -> bool
   - async update_video_status(video_id, privacy_status, credentials_file) -> bool
   - Handle OAuth token refresh automatically

3. scripts/setup_youtube_oauth.py -- One-time setup:
   - CLI script that runs the OAuth consent flow
   - Saves credentials to the specified JSON file
   - Usage: python scripts/setup_youtube_oauth.py --output config/youtube_gaming_creds.json

## Acceptance Criteria
- [ ] Discovery functions return normalized dicts with: video_id, title, channel_name,
      channel_id, view_count, like_count, comment_count, published_at, duration, category_id, url
- [ ] Quota tracking logs a warning when 80% of daily_quota_limit is reached
- [ ] Upload uses resumable upload protocol with configurable chunk size
- [ ] OAuth token refresh is handled automatically (no manual re-auth)
- [ ] Most Replayed scraper handles videos without heatmap data (returns None)
- [ ] tests/test_youtube.py mocks google API client and tests: trending parsing,
      search result normalization, quota tracking, upload flow, token refresh

## Critical Constraints
- Use google-api-python-client and google-auth-oauthlib
- API key and quota limit come from config
- OAuth credentials file paths come from per-channel config
- No emojis in any metadata or log messages
- Handle API errors gracefully (rate limit -> retry with backoff, quota exceeded -> log and return empty)

## Reference Files
- SPEC.md (Sections 4.1, 4.8, 14.3)
```

---

### T08: Reddit API Client

```markdown
# Task: Build Reddit API client for viral content discovery

Priority: 3
State: queued
Created: 2026-02-28T00:00:07Z
Depends-On: agent/task-*-build-the-configuration-system
Scope: src/discovery/reddit_source.py, tests/test_reddit.py

## Description
Create a Reddit viral content discovery module using PRAW.

Implement src/discovery/reddit_source.py:
- RedditSource class initialized with config (client_id, client_secret, user_agent)
- get_viral_youtube_links(subreddits: list[str], min_score: int, max_age_hours: int) -> list[dict]
  Scans subreddits for posts with YouTube links, filters by score and age.
  Returns list of dicts with: reddit_post_id, youtube_video_id, youtube_url,
  post_title, subreddit, score, num_comments, created_utc, upvote_ratio
- Extract YouTube video IDs from various URL formats:
  youtube.com/watch?v=, youtu.be/, youtube.com/shorts/

## Acceptance Criteria
- [ ] RedditSource initializes a PRAW Reddit instance
- [ ] get_viral_youtube_links scans hot+rising posts from given subreddits
- [ ] YouTube URL extraction handles all common formats (watch, youtu.be, shorts, embed)
- [ ] Posts without YouTube links are silently skipped
- [ ] Rate limiting is handled by PRAW internally
- [ ] tests/test_reddit.py mocks PRAW and tests: URL extraction for all formats,
      filtering by score/age, handling of non-YouTube posts

## Critical Constraints
- Use PRAW (Python Reddit API Wrapper)
- Credentials come from config (client_id, client_secret, user_agent)
- Read-only access (no posting, no voting)
- No emojis in log messages

## Reference Files
- SPEC.md (Section 4.1)
```

---

### T09: Viral Score Calculator

```markdown
# Task: Implement viral score calculation module

Priority: 3
State: queued
Created: 2026-02-28T00:00:08Z
Depends-On: agent/task-*-build-the-configuration-system
Scope: src/discovery/scorer.py, tests/test_scorer.py

## Description
Implement the viral scoring algorithm from SPEC.md Section 4.1.

Create src/discovery/scorer.py:
- ViralScorer class initialized with scoring weights from config
- calculate_score(video_data: dict) -> float
  Computes: w1*view_velocity + w2*reddit_score + w3*like_ratio +
  w4*comment_velocity + w5*recency_factor
  All components are normalized to 0-1 range before weighting.
- normalize_view_velocity(velocity: float) -> float
  (log-scale normalization, configurable ceiling)
- normalize_reddit_score(score: int) -> float
  (log-scale, capped)
- calculate_like_ratio(likes: int, views: int) -> float
- normalize_comment_velocity(comments_per_hour: float) -> float
- calculate_recency_factor(published_at: datetime, now: datetime) -> float
  (1.0 if just published, decays to 0 over lookback_hours window)

## Acceptance Criteria
- [ ] All normalization functions return values in 0.0-1.0 range
- [ ] Weights come from config (discovery.scoring.weight_*)
- [ ] Score is a weighted sum in 0.0-1.0 range
- [ ] Videos with zero views/likes/comments get score 0.0 without errors
- [ ] tests/test_scorer.py tests: each normalization function, edge cases (zero values,
      very large values), weight application, recency decay curve

## Critical Constraints
- All weights must sum to 1.0 (validate in __init__)
- Handle division by zero gracefully
- Recency factor uses exponential decay, not linear
- No emojis

## Reference Files
- SPEC.md (Section 4.1 scoring algorithm)
```

---

### T10: Discovery Engine Orchestrator

```markdown
# Task: Build the discovery engine that combines all sources

Priority: 3
State: queued
Created: 2026-02-28T00:00:09Z
Depends-On: agent/task-*-build-youtube-data-api, agent/task-*-build-reddit-api, agent/task-*-implement-viral-score, agent/task-*-build-the-llm-abstraction, agent/task-*-implement-sqlite-database
Scope: src/discovery/engine.py, src/discovery/classifier.py, src/discovery/dedup.py, tests/test_discovery.py

## Description
Build the discovery engine orchestrator that combines YouTube and Reddit sources,
scores videos, classifies them into niches, deduplicates, and returns ranked candidates.

Create:
1. src/discovery/classifier.py:
   - classify_niche(video_data: dict, llm_client: LLMClient) -> str
     Uses YouTube category_id first (fast), falls back to LLM classification
     of title+description if category is ambiguous.
   - CATEGORY_NICHE_MAP: dict mapping YouTube category IDs to niche names

2. src/discovery/dedup.py:
   - is_duplicate(video_id: str, session: Session) -> bool
   - is_similar(title: str, duration: int, session: Session) -> bool
     (fuzzy title match + duration within 5 seconds = probable reupload)

3. src/discovery/engine.py:
   - DiscoveryEngine class
   - async discover(niche: str, channel_config: ChannelConfig) -> list[DiscoveredVideo]
     Full pipeline: query sources -> score -> classify -> dedup -> rank -> return top N
   - Saves all discovered videos to database (even ones not selected)

## Acceptance Criteria
- [ ] discover() returns a ranked list of DiscoveredVideo objects
- [ ] Videos already in the database (by video_id) are skipped
- [ ] Similar videos (fuzzy title match) are flagged
- [ ] Classification uses category_id map first, LLM fallback second
- [ ] Results are sorted by viral_score descending
- [ ] max_candidates_per_niche from config limits the returned count
- [ ] tests/test_discovery.py mocks YouTube/Reddit sources and tests:
      full pipeline, deduplication, classification, ranking

## Critical Constraints
- Discovery sources are called concurrently (asyncio.gather)
- Database writes happen even for rejected/skipped videos (for future dedup)
- LLM classification is only used when category_id mapping is ambiguous
- No emojis

## Reference Files
- SPEC.md (Section 4.1)
```

---

### T11: Video Downloader

```markdown
# Task: Build video downloader using yt-dlp Python API

Priority: 3
State: queued
Created: 2026-02-28T00:00:10Z
Depends-On: agent/task-*-create-ffmpeg-utility, agent/task-*-implement-sqlite-database
Scope: src/acquisition/downloader.py, src/acquisition/validator.py, tests/test_acquisition.py

## Description
Implement video acquisition as described in SPEC.md Section 4.2.

Create:
1. src/acquisition/downloader.py:
   - VideoDownloader class initialized with config
   - async download(video_id: str, url: str) -> DownloadResult
     Downloads video + subtitles using yt-dlp Python API
     Returns DownloadResult(video_path, subtitle_path, metadata)
   - async download_batch(videos: list[dict], max_concurrent: int) -> list[DownloadResult]
     Downloads multiple videos with concurrency limit (asyncio.Semaphore)

2. src/acquisition/validator.py:
   - validate_download(video_path: Path, expected_duration: int = None) -> bool
     Checks file exists, size > 0, duration within expected range,
     codec is valid, resolution is acceptable
   - Uses get_media_info from ffmpeg utility

## Acceptance Criteria
- [ ] yt-dlp Python API is used (not subprocess calls to yt-dlp CLI)
- [ ] Downloads to configurable working directory with {video_id}.mp4 naming
- [ ] Subtitles downloaded in json3 format when available
- [ ] Concurrent downloads limited by semaphore
- [ ] Videos over max_source_duration_seconds are skipped
- [ ] validate_download checks file integrity via ffprobe
- [ ] tests/test_acquisition.py mocks yt-dlp and tests: download options,
      subtitle fetching, validation logic, batch concurrency

## Critical Constraints
- Use yt-dlp as a Python library (import yt_dlp), not subprocess
- Download format: bestvideo[height<=1080]+bestaudio/best[height<=1080]
- Merge output format: mp4
- Socket timeout: 30 seconds, retries: 3
- Skip videos longer than max_source_duration_seconds (from config, default 3600)
- No emojis in log messages

## Reference Files
- SPEC.md (Section 4.2)
```

---

### T12: Most Replayed Heatmap Scraper

```markdown
# Task: Implement YouTube Most Replayed heatmap scraper

Priority: 4
State: queued
Created: 2026-02-28T00:00:11Z
Depends-On: agent/task-*-create-project-scaffolding
Scope: src/analysis/most_replayed.py, tests/test_most_replayed.py

## Description
Implement a scraper that extracts the "Most Replayed" heatmap data from
YouTube video pages. This data shows which segments viewers rewatch most.

Create src/analysis/most_replayed.py:
- async get_most_replayed(video_id: str) -> list[dict] | None
  Fetches the YouTube watch page HTML, parses the player config JSON,
  and extracts heatmap marker data.
  Returns list of {start_sec: float, end_sec: float, intensity: float}
  sorted by intensity descending.
  Returns None if heatmap data is not available.
- get_peak_segment(heatmap: list[dict], target_duration: float) -> tuple[float, float]
  Returns (start_sec, end_sec) of the highest-intensity segment of
  approximately the target duration.

## Acceptance Criteria
- [ ] Fetches the YouTube watch page and parses embedded JSON
- [ ] Extracts heatMarkers or equivalent data from player config
- [ ] Returns None gracefully when heatmap is unavailable
- [ ] get_peak_segment returns the best continuous segment near target_duration
- [ ] tests/test_most_replayed.py mocks HTTP responses with sample player JSON,
      tests parsing, missing data handling, peak segment selection

## Critical Constraints
- Use httpx for HTTP requests (async)
- Parse the ytInitialPlayerResponse JSON from the page source
- The heatmap data format may change -- code should fail gracefully
- No authentication needed (public page scraping)
- No emojis

## Reference Files
- SPEC.md (Section 4.3, Method 1)
```

---

### T13: Transcript Analyzer

```markdown
# Task: Build LLM-based transcript analyzer for scene selection

Priority: 4
State: queued
Created: 2026-02-28T00:00:12Z
Depends-On: agent/task-*-build-the-llm-abstraction
Scope: src/analysis/transcript_analyzer.py, tests/test_transcript_analyzer.py

## Description
Implement transcript-based scene analysis that uses the LLM to identify
the most engaging moment in a video transcript.

Create src/analysis/transcript_analyzer.py:
- parse_subtitles(subtitle_path: Path) -> list[dict]
  Parse json3 subtitle file into list of {start_sec, end_sec, text}
- async find_peak_moment(transcript: list[dict], title: str, llm_client: LLMClient) -> tuple[float, float]
  Sends transcript + title to LLM, asks it to identify the most dramatic/
  surprising/entertaining moment. Returns (start_sec, end_sec).
  Uses the clip_analysis.j2 prompt template.

## Acceptance Criteria
- [ ] parse_subtitles handles json3 format correctly
- [ ] find_peak_moment sends a structured prompt and parses timestamp response
- [ ] Handles transcripts that are too long by chunking/truncating to fit context window
- [ ] Returns reasonable defaults if LLM response is unparseable (middle of video)
- [ ] tests/test_transcript_analyzer.py tests: subtitle parsing, prompt construction,
      response parsing, fallback behavior

## Critical Constraints
- LLM calls go through LLMClient (never direct API calls)
- Prompt template loaded via PromptManager from config/prompts/clip_analysis.j2
- Truncate transcript to ~4000 tokens if too long (keep beginning, middle, end samples)
- No emojis in prompts or outputs

## Reference Files
- SPEC.md (Section 4.3, Method 2)
```

---

### T14: Audio Energy Analyzer

```markdown
# Task: Implement audio energy analysis for scene detection

Priority: 4
State: queued
Created: 2026-02-28T00:00:13Z
Depends-On: agent/task-*-create-ffmpeg-utility
Scope: src/analysis/audio_analyzer.py, tests/test_audio_analyzer.py

## Description
Implement audio energy analysis that identifies high-energy segments
(crowd reactions, shouting, music drops, laughter) in video audio.

Create src/analysis/audio_analyzer.py:
- extract_energy_profile(audio_path: Path, window_sec: float = 1.0) -> list[dict]
  Loads audio, computes RMS energy over sliding windows.
  Returns list of {start_sec, end_sec, energy: float}
- find_energy_peak(energy_profile: list[dict], target_duration: float) -> tuple[float, float]
  Returns (start_sec, end_sec) for the highest-energy segment of
  approximately target_duration seconds.

## Acceptance Criteria
- [ ] Energy profile computed using numpy on raw audio PCM data
- [ ] Peak detection finds the window with maximum average energy
- [ ] Handles silent audio (all zeros) without crashing
- [ ] tests/test_audio_analyzer.py tests: energy computation on synthetic audio,
      peak detection, edge cases (silent audio, very short audio)

## Critical Constraints
- Use numpy for computation (NOT librosa -- keep dependencies light)
- Extract audio to raw PCM via ffmpeg utility before analysis
- Window size and overlap are configurable (default 1.0s window, 0.5s hop)
- No emojis

## Reference Files
- SPEC.md (Section 4.3, Method 3)
```

---

### T15: Clip Extractor

```markdown
# Task: Build clip extraction module using FFmpeg

Priority: 4
State: queued
Created: 2026-02-28T00:00:14Z
Depends-On: agent/task-*-create-ffmpeg-utility, agent/task-*-implement-sqlite-database
Scope: src/analysis/clip_extractor.py, tests/test_clip_extractor.py

## Description
Implement clip extraction that takes a source video and timestamp range,
extracts the clip, normalizes it, and saves it.

Create src/analysis/clip_extractor.py:
- async extract_clip(
      video_path: Path,
      start_sec: float,
      end_sec: float,
      output_dir: Path,
      video_id: str,
      config: VideoConfig
  ) -> ClipResult
  Extracts the clip using ffmpeg utility, re-encodes to consistent format
  (H.264, 1080p, 30fps, AAC), normalizes audio, adds fade in/out.
  Returns ClipResult(clip_path, duration_sec, actual_start, actual_end)
- enforce_duration_limits(start_sec, end_sec, min_dur, max_dur) -> tuple[float, float]
  Adjusts timestamps to respect min/max clip duration from config.

## Acceptance Criteria
- [ ] Clip extracted at correct timestamps
- [ ] Audio normalized to clip_audio level
- [ ] Fade in/out applied (configurable duration)
- [ ] Duration enforced between clip_duration_min and clip_duration_max
- [ ] Output filename: {video_id}_{start}_{end}.mp4
- [ ] tests/test_clip_extractor.py tests: duration enforcement, fade parameters,
      output naming, command construction

## Critical Constraints
- Uses src/utils/ffmpeg.py functions (extract_clip, normalize_audio)
- Re-encode to H.264/AAC even if source is already H.264 (consistent output)
- No emojis

## Reference Files
- SPEC.md (Section 4.3)
```

---

### T16: Scene Analysis Orchestrator

```markdown
# Task: Build scene analysis orchestrator combining all methods

Priority: 5
State: queued
Created: 2026-02-28T00:00:15Z
Depends-On: agent/task-*-most-replayed-scraper, agent/task-*-transcript-analyzer, agent/task-*-audio-energy-analyzer, agent/task-*-clip-extractor
Scope: src/analysis/scene_analyzer.py, tests/test_scene_analyzer.py

## Description
Build the orchestrator that tries multiple scene analysis methods in priority
order and extracts the best clip from each source video.

Create src/analysis/scene_analyzer.py:
- SceneAnalyzer class initialized with config and dependencies (llm_client)
- async analyze_and_extract(video_path: Path, video_id: str, subtitle_path: Path | None,
      output_dir: Path) -> ClipResult | None
  Tries methods in priority order from config (default: most_replayed,
  transcript, audio_energy, scene_detection). Returns the clip from the
  first method that succeeds. Returns None if all methods fail.
- Logs which method was used for each clip (stored in database)

## Acceptance Criteria
- [ ] Methods tried in config-specified priority order
- [ ] Falls through to next method on failure
- [ ] Returns None (does not crash) if all methods fail
- [ ] Extraction method name stored in ClipResult for database logging
- [ ] tests/test_scene_analyzer.py tests: priority ordering, fallback behavior,
      all-methods-fail case, method selection logging

## Critical Constraints
- Method priority order comes from config (video.clip_extraction.methods_priority)
- Each method has a timeout (30 seconds default)
- No emojis

## Reference Files
- SPEC.md (Section 4.3)
```

---

### T17: Script Generator

```markdown
# Task: Build narration script generator

Priority: 5
State: queued
Created: 2026-02-28T00:00:16Z
Depends-On: agent/task-*-build-the-llm-abstraction, agent/task-*-implement-sqlite-database
Scope: src/scriptgen/generator.py, src/scriptgen/validator.py, config/prompts/script_generation.j2, tests/test_scriptgen.py

## Description
Implement the script generation module from SPEC.md Section 4.4.

Create:
1. config/prompts/script_generation.j2 -- Jinja2 template for the script prompt
   (see SPEC.md Section 4.4 for the full prompt structure)

2. src/scriptgen/generator.py:
   - ScriptGenerator class
   - async generate_script(clips: list[ClipData], niche: str, cycle_time: str,
         llm_client: LLMClient) -> ScriptResult
     Renders the prompt template with clip data, sends to LLM,
     parses the JSON response into a ScriptResult.
   - ScriptResult dataclass: opening, closing, clips list (each with intro, outro)

3. src/scriptgen/validator.py:
   - validate_script(script: ScriptResult, min_clips: int, max_chars: int) -> list[str]
     Returns list of validation error messages (empty = valid).
     Checks: all clips have intro+outro, char count within range,
     no emojis detected, opening and closing exist.

## Acceptance Criteria
- [ ] Prompt template matches SPEC.md Section 4.4 structure
- [ ] LLM response parsed as JSON into ScriptResult
- [ ] Validation catches missing segments, over-length scripts, emojis
- [ ] Retry up to 3 times if JSON parse or validation fails
- [ ] tests/test_scriptgen.py tests: prompt rendering, JSON parsing,
      validation rules, retry on invalid response

## Critical Constraints
- Prompt loaded via PromptManager (Jinja2 template)
- LLM calls via LLMClient.complete_json()
- Target 3,500-5,500 total characters
- No emojis in prompt, system message, or expected output
- Clip count is dynamic (8-10), not hardcoded

## Reference Files
- SPEC.md (Section 4.4)
```

---

### T18: TTS Engine Abstraction

```markdown
# Task: Create TTS engine abstraction layer with plugin architecture

Priority: 5
State: queued
Created: 2026-02-28T00:00:17Z
Depends-On: agent/task-*-build-the-configuration-system
Scope: src/tts/engine.py, tests/test_tts_engine.py

## Description
Implement the TTS abstraction layer from SPEC.md Section 9.

Create src/tts/engine.py:
- TTSEngine (abstract base class):
  - async synthesize(text: str, voice_config: dict) -> bytes (raw audio)
  - async synthesize_batch(segments: list[str], voice_config: dict) -> list[bytes]
  - def get_available_voices() -> list[str]
  - def estimate_duration(text: str) -> float (rough estimate based on char count)
  - def is_available() -> bool (check if model/device is accessible)

- TTSEngineRegistry:
  - register(name: str, engine_class: type)
  - get(name: str, config: dict) -> TTSEngine
  - list_engines() -> list[str]

- get_tts_engine(config: TTSConfig) -> TTSEngine
  Factory function that returns the configured primary engine,
  or falls back to the fallback engine if primary is unavailable.

## Acceptance Criteria
- [ ] TTSEngine is an ABC with all methods defined
- [ ] TTSEngineRegistry allows registering and retrieving engines by name
- [ ] get_tts_engine tries primary, falls back to fallback from config
- [ ] estimate_duration returns seconds based on ~15 chars/second heuristic
- [ ] tests/test_tts_engine.py tests: registry, factory function, fallback behavior,
      duration estimation

## Critical Constraints
- Engine name strings (e.g., "xtts_v2", "piper") come from config, never hardcoded in engine.py
- All synthesis methods are async
- No emojis

## Reference Files
- SPEC.md (Section 9)
```

---

### T19: XTTS v2 Engine Implementation

```markdown
# Task: Implement Coqui XTTS v2 TTS engine

Priority: 6
State: queued
Created: 2026-02-28T00:00:18Z
Depends-On: agent/task-*-create-tts-engine-abstraction
Scope: src/tts/xtts_engine.py, scripts/download_tts_models.py, tests/test_xtts_engine.py

## Description
Implement the XTTS v2 TTS engine that clones a voice from a reference audio
sample and generates speech on GPU.

Create:
1. src/tts/xtts_engine.py:
   - XTTSEngine(TTSEngine) class
   - __init__(model_path, device, sample_rate): Load XTTS v2 model
   - synthesize(text, voice_config): Generate speech using reference audio cloning
   - is_available(): Check CUDA availability and model files exist
   - Registers itself: TTSEngineRegistry.register("xtts_v2", XTTSEngine)

2. scripts/download_tts_models.py:
   - Downloads XTTS v2 model files to the configured model directory
   - Verifies download integrity
   - CLI usage: python scripts/download_tts_models.py --model xtts_v2 --output models/xtts_v2/

## Acceptance Criteria
- [ ] XTTSEngine loads the XTTS v2 model and generates audio from text + reference
- [ ] Voice cloning uses a reference WAV file path from voice_config
- [ ] GPU device selection from config (cuda:0, cpu, etc.)
- [ ] is_available() returns False if CUDA unavailable or model missing
- [ ] download script fetches model from Hugging Face / Coqui model hub
- [ ] tests/test_xtts_engine.py tests: initialization, is_available check,
      error handling for missing model (mock torch/TTS imports)

## Critical Constraints
- Use the TTS library (pip install TTS) for XTTS v2
- Model path comes from config
- Device comes from config -- not hardcoded to cuda:0
- Graceful error if torch/CUDA not available (is_available returns False)
- No emojis

## Reference Files
- SPEC.md (Section 9)
```

---

### T20: Piper TTS Engine Implementation

```markdown
# Task: Implement Piper TTS engine as CPU fallback

Priority: 6
State: queued
Created: 2026-02-28T00:00:19Z
Depends-On: agent/task-*-create-tts-engine-abstraction
Scope: src/tts/piper_engine.py, tests/test_piper_engine.py

## Description
Implement the Piper TTS engine as a CPU-only fallback when GPU is unavailable.

Create src/tts/piper_engine.py:
- PiperEngine(TTSEngine) class
- __init__(model_path, sample_rate): Load Piper voice model
- synthesize(text, voice_config): Generate speech using Piper
- is_available(): Check model files exist
- Registers itself: TTSEngineRegistry.register("piper", PiperEngine)

Piper runs entirely on CPU, is extremely fast (~50x realtime), but has
lower quality than XTTS v2. It does NOT support voice cloning.

## Acceptance Criteria
- [ ] PiperEngine generates audio from text using a pretrained voice
- [ ] No GPU required
- [ ] is_available() checks model file existence
- [ ] Audio output is consistent format (WAV, configurable sample rate)
- [ ] tests/test_piper_engine.py tests: initialization, synthesis call mock,
      availability check

## Critical Constraints
- Use piper-tts Python package
- Model path from config
- This is the fallback engine -- it MUST work without GPU
- No emojis

## Reference Files
- SPEC.md (Section 9)
```

---

### T21: Audio Processor

```markdown
# Task: Build audio processing pipeline for TTS output

Priority: 5
State: queued
Created: 2026-02-28T00:00:20Z
Depends-On: agent/task-*-create-ffmpeg-utility
Scope: src/tts/audio_processor.py, tests/test_audio_processor.py

## Description
Implement audio post-processing for TTS output as described in SPEC.md Section 4.5.

Create src/tts/audio_processor.py:
- split_sentences(text: str) -> list[str]
  Split script text into sentences (by period, question mark, exclamation).
  Handle abbreviations (Mr., Dr., etc.) and ellipses gracefully.
- concatenate_with_pauses(audio_segments: list[Path], pause_ms: int, output_path: Path) -> Path
  Concatenate audio files with silence gaps between them.
- normalize_narration(audio_path: Path, target_lufs: float, output_path: Path) -> Path
  Normalize to broadcast standard using ffmpeg loudnorm.
- process_narration(raw_segments: list[Path], config: AudioConfig, output_path: Path) -> NarrationResult
  Full pipeline: concatenate -> compress -> normalize -> export.
  Returns NarrationResult(path, duration_sec, per_segment_durations)

## Acceptance Criteria
- [ ] Sentence splitting handles common edge cases
- [ ] Pauses between segments are configurable (default 300ms)
- [ ] Normalization targets configurable LUFS (default -16)
- [ ] per_segment_durations are measured accurately (needed for video timeline)
- [ ] tests/test_audio_processor.py tests: sentence splitting edge cases,
      pause insertion, duration measurement

## Critical Constraints
- Uses ffmpeg utility for audio operations
- Silence generation via ffmpeg (not numpy)
- No emojis

## Reference Files
- SPEC.md (Section 4.5)
```

---

### T22: Graphics Generator

```markdown
# Task: Build video graphics generator using Pillow

Priority: 6
State: queued
Created: 2026-02-28T00:00:21Z
Depends-On: agent/task-*-create-ffmpeg-utility, agent/task-*-build-the-configuration-system
Scope: src/assembly/graphics.py, tests/test_graphics.py

## Description
Create video overlay graphics using Pillow as described in SPEC.md Section 4.6.

Create src/assembly/graphics.py:
- generate_intro_frame(channel_name, niche, date_range, config: BrandingConfig) -> Path
  1920x1080 image with channel logo area, "LAST SIX HOURS" text, niche label, date
- generate_clip_label(number: int, config: BrandingConfig) -> Path
  1920x1080 image with large "NUMBER {N}" text centered
- generate_lower_third(title: str, creator: str, view_count: int, config: BrandingConfig) -> Path
  Semi-transparent bar at bottom with clip info
- generate_outro_frame(channel_name, config: BrandingConfig) -> Path
  "Subscribe" CTA, "See you in 6 hours", channel branding
- All graphics use fonts and colors from BrandingConfig

## Acceptance Criteria
- [ ] All graphics are 1920x1080 PNG files
- [ ] Text is legible (appropriate font size, contrast, outline/shadow)
- [ ] Colors and fonts come from BrandingConfig
- [ ] Lower third has semi-transparent background (alpha channel)
- [ ] No emojis in any generated text
- [ ] tests/test_graphics.py tests: each function produces a valid PNG of correct dimensions,
      text content matches inputs

## Critical Constraints
- Use Pillow (PIL) only -- no external graphics libraries
- Font paths come from config (assets/fonts/)
- View count formatted with commas (1,234,567)
- No emojis in any generated text

## Reference Files
- SPEC.md (Section 4.6 visual elements)
```

---

### T23: Timeline Builder

```markdown
# Task: Build video timeline construction module

Priority: 6
State: queued
Created: 2026-02-28T00:00:22Z
Depends-On: agent/task-*-create-ffmpeg-utility
Scope: src/assembly/timeline.py, tests/test_timeline.py

## Description
Create the timeline builder that defines the exact sequence of visual and
audio elements for the final video.

Create src/assembly/timeline.py:
- TimelineEntry dataclass:
  type: str (intro, clip_label, narration, clip, transition, outro)
  start_sec: float
  duration_sec: float
  source_path: Path
  audio_path: Path | None
  overlay_path: Path | None (for lower thirds)

- build_timeline(
      clips: list[ClipData],
      narration: NarrationResult,
      graphics: dict[str, Path],
      config: VideoConfig
  ) -> list[TimelineEntry]
  Constructs the full ordered timeline with exact timing for every element.
  Calculates total duration and validates it falls within target range.

- get_clip_timestamps(timeline: list[TimelineEntry]) -> dict[int, float]
  Returns {clip_rank: start_timestamp_in_final_video} for description generation.

## Acceptance Criteria
- [ ] Timeline entries are in chronological order with no gaps or overlaps
- [ ] Total duration falls within target_duration_min and target_duration_max
- [ ] Narration durations match actual audio file durations
- [ ] Transitions between clips are accounted for
- [ ] get_clip_timestamps returns correct timestamps for video description
- [ ] tests/test_timeline.py tests: ordering, duration calculation, timestamp extraction,
      gap detection

## Critical Constraints
- Intro duration: 3-5 seconds
- Clip label duration: 1.5 seconds
- Transition duration: 0.5-1.0 seconds
- All timing derived from actual audio/clip file durations (not estimates)
- No emojis

## Reference Files
- SPEC.md (Section 4.6)
```

---

### T24: Audio Mixer

```markdown
# Task: Build multi-track audio mixer with ducking

Priority: 6
State: queued
Created: 2026-02-28T00:00:23Z
Depends-On: agent/task-*-create-ffmpeg-utility
Scope: src/assembly/audio_mixer.py, tests/test_audio_mixer.py

## Description
Implement audio mixing with ducking as described in SPEC.md Section 4.6.

Create src/assembly/audio_mixer.py:
- mix_final_audio(
      timeline: list[TimelineEntry],
      music_path: Path,
      config: AudioConfig,
      output_path: Path
  ) -> Path
  Mixes three audio tracks:
    1. Narration at config.narration_lufs (-16 LUFS)
    2. Clip original audio at config.clip_audio_lufs (-26 LUFS)
    3. Background music at config.background_music_lufs (-32 LUFS)
  Applies ducking: when narration plays, tracks 2 and 3 are attenuated
  by config.ducking_db (-12 dB).

- select_background_music(niche: str, music_dir: Path) -> Path
  Selects a random music track from the appropriate mood subdirectory.

- calculate_narration_ratio(timeline: list[TimelineEntry]) -> float
  Returns the ratio of narration audio duration to total video duration.
  Must be >= 0.60 for copyright compliance.

## Acceptance Criteria
- [ ] Three audio tracks mixed correctly with proper levels
- [ ] Ducking applied during narration segments
- [ ] Music loops if shorter than video duration
- [ ] Music fades in/out (configurable fade duration)
- [ ] Narration ratio calculation is accurate
- [ ] tests/test_audio_mixer.py tests: ducking timing, ratio calculation,
      music selection, level settings

## Critical Constraints
- All mixing done via FFmpeg (complex filter graph)
- Narration ratio MUST be >= 0.60 (raise error if not)
- Music selection is random but deterministic per niche (seeded)
- No emojis

## Reference Files
- SPEC.md (Section 4.6 audio mixing)
```

---

### T25: Video Renderer

```markdown
# Task: Build the final video renderer

Priority: 7
State: queued
Created: 2026-02-28T00:00:24Z
Depends-On: agent/task-*-graphics-generator, agent/task-*-timeline-builder, agent/task-*-audio-mixer
Scope: src/assembly/renderer.py, tests/test_renderer.py

## Description
Build the renderer that assembles the final video from timeline, graphics,
clips, and mixed audio.

Create src/assembly/renderer.py:
- VideoRenderer class
- async render(
      timeline: list[TimelineEntry],
      mixed_audio_path: Path,
      output_path: Path,
      config: VideoConfig
  ) -> RenderResult
  Constructs an FFmpeg complex filter graph that:
  1. Concatenates all video segments in timeline order
  2. Overlays graphics (intro, clip labels, lower thirds, outro)
  3. Adds transitions between clips (crossfade)
  4. Muxes with mixed audio track
  5. Encodes to final output (H.264, CRF from config, AAC audio)
  Returns RenderResult(path, duration_sec, file_size_bytes)

- build_ffmpeg_command(timeline, audio_path, output_path, config) -> list[str]
  Constructs the full ffmpeg command with filter graph. Separated for testability.

## Acceptance Criteria
- [ ] Final video matches config resolution (1920x1080), fps (30), codec (H.264)
- [ ] All timeline segments appear in correct order
- [ ] Overlays are positioned correctly
- [ ] Audio is synced with video
- [ ] File size is reasonable (target ~500MB-1GB for 8-10 min at CRF 20)
- [ ] tests/test_renderer.py tests: command construction, filter graph structure,
      output validation (mock subprocess)

## Critical Constraints
- Single FFmpeg call for the entire render (not multiple passes)
- Use -preset from config (default "medium")
- Pixel format: yuv420p (maximum compatibility)
- Timeout: 600 seconds for render
- No emojis

## Reference Files
- SPEC.md (Section 4.6)
```

---

### T26: Thumbnail Generator

```markdown
# Task: Build YouTube thumbnail generator

Priority: 7
State: queued
Created: 2026-02-28T00:00:25Z
Depends-On: agent/task-*-build-the-llm-abstraction, agent/task-*-graphics-generator
Scope: src/thumbnails/generator.py, src/thumbnails/frame_selector.py, config/prompts/thumbnail_text.j2, tests/test_thumbnails.py

## Description
Implement thumbnail generation from SPEC.md Section 4.7.

Create:
1. src/thumbnails/frame_selector.py:
   - select_best_frame(clip_path: Path) -> Path
     Extract frames from the top clip, score by contrast and saturation,
     return the path to the best frame image.

2. config/prompts/thumbnail_text.j2:
   - Template for LLM to generate 3-5 word thumbnail text

3. src/thumbnails/generator.py:
   - async generate_thumbnail(
         top_clip_path: Path,
         clip_title: str,
         niche: str,
         llm_client: LLMClient,
         config: BrandingConfig
     ) -> Path
   Uses frame_selector to get best frame, LLM to generate text,
   Pillow to compose: frame + saturation boost + text overlay + watermark.
   Output: 1280x720 JPEG, under 2MB.

## Acceptance Criteria
- [ ] Frame selection picks the most visually interesting frame
- [ ] LLM generates clickable, short text (3-5 words, no emojis)
- [ ] Final thumbnail is 1280x720 JPEG under 2MB
- [ ] Text has outline/shadow for readability
- [ ] Channel watermark in corner
- [ ] tests/test_thumbnails.py tests: frame scoring, Pillow composition,
      size/format validation

## Critical Constraints
- LLM calls via LLMClient only
- No emojis in thumbnail text prompt or output
- Use Pillow for all image operations
- JPEG quality tuned to stay under 2MB

## Reference Files
- SPEC.md (Section 4.7)
```

---

### T27: Shorts Generator

```markdown
# Task: Build YouTube Shorts generator

Priority: 7
State: queued
Created: 2026-02-28T00:00:26Z
Depends-On: agent/task-*-create-ffmpeg-utility, agent/task-*-clip-extractor
Scope: src/shorts/generator.py, src/shorts/cropper.py, tests/test_shorts.py

## Description
Implement Shorts generation from SPEC.md Section 4.9.

Create:
1. src/shorts/cropper.py:
   - smart_crop_to_vertical(input_path: Path, output_path: Path) -> Path
     Crop 16:9 video to 9:16 using center crop or motion-based tracking.
     Center crop is the default. Smart crop uses frame differencing to
     track the region of interest.

2. src/shorts/generator.py:
   - async generate_shorts(
         clips: list[ClipData],
         niche: str,
         llm_client: LLMClient,
         config: VideoConfig
     ) -> list[ShortResult]
   Takes the top N clips (config.shorts.count_per_video), crops each
   to vertical, adds hook text overlay (LLM-generated), adds branding.
   Returns list of ShortResult(path, title, duration).

## Acceptance Criteria
- [ ] Shorts are 9:16 (1080x1920), 30-60 seconds
- [ ] Hook text appears in first second (large, readable)
- [ ] Channel branding at end
- [ ] LLM generates a hook line for each Short (no emojis)
- [ ] tests/test_shorts.py tests: crop dimensions, duration limits,
      hook text generation, output format

## Critical Constraints
- Vertical crop via FFmpeg crop filter (not Pillow)
- Resolution: 1080x1920
- Include #Shorts in title metadata
- No emojis in any text overlay or title

## Reference Files
- SPEC.md (Section 4.9)
```

---

### T28: YouTube Uploader (Upload Logic)

```markdown
# Task: Build YouTube upload execution module

Priority: 7
State: queued
Created: 2026-02-28T00:00:27Z
Depends-On: agent/task-*-build-youtube-data-api, agent/task-*-implement-sqlite-database
Scope: src/upload/youtube_uploader.py, tests/test_upload.py

## Description
This task extends the YouTube API client (T07) with the full upload workflow
including metadata application, thumbnail setting, and status tracking.

Enhance src/upload/youtube_uploader.py with:
- async upload_and_publish(
      video_path: Path,
      metadata: VideoMetadata,
      thumbnail_path: Path,
      credentials_file: str,
      config: YouTubeUploadConfig
  ) -> UploadResult
  Full workflow: upload as private -> set thumbnail -> return video ID.
  Does NOT set to public (that happens after Telegram approval).
- async publish(video_id: str, credentials_file: str) -> bool
  Sets video to public after human approval.

## Acceptance Criteria
- [ ] Resumable upload with configurable chunk size
- [ ] Thumbnail applied after upload
- [ ] Video stays private until explicit publish() call
- [ ] Upload retries on transient failures (3 attempts)
- [ ] UploadResult includes: video_id, url, upload_status
- [ ] tests/test_upload.py tests: upload flow with mocked API, retry on failure,
      thumbnail application, publish status change

## Critical Constraints
- Never auto-publish -- always requires explicit publish() call
- Quota tracking (log upload cost)
- No emojis in any metadata

## Reference Files
- SPEC.md (Section 4.8)
```

---

### T29: Metadata Generator

```markdown
# Task: Build video metadata generator for YouTube

Priority: 7
State: queued
Created: 2026-02-28T00:00:28Z
Depends-On: agent/task-*-build-the-llm-abstraction
Scope: src/upload/metadata.py, config/prompts/title_generation.j2, config/prompts/description_generation.j2, config/prompts/tag_generation.j2, tests/test_metadata.py

## Description
Implement metadata generation for YouTube uploads.

Create src/upload/metadata.py:
- async generate_metadata(
      clips: list[ClipData],
      niche: str,
      cycle_time: str,
      timeline_timestamps: dict[int, float],
      llm_client: LLMClient,
      channel_config: ChannelConfig
  ) -> VideoMetadata

VideoMetadata dataclass: title, description, tags, category_id, privacy_status

- Title: "Last SiX Hours: {Niche} -- {date} {time} Edition"
  (LLM can suggest a more engaging title based on top clip)
- Description: follows template from SPEC.md Appendix B
  (summary + timestamps + credits + links + hashtags)
- Tags: LLM-generated based on clip content, always includes standard tags
- Category ID: from channel config

Also create prompt templates:
- config/prompts/title_generation.j2
- config/prompts/description_generation.j2
- config/prompts/tag_generation.j2

## Acceptance Criteria
- [ ] Title includes channel name, niche, date
- [ ] Description includes auto-generated timestamps from timeline
- [ ] Description includes credit for every source creator with link
- [ ] Tags include standard tags + LLM-generated niche tags
- [ ] Total tag length under 500 characters
- [ ] No emojis in any metadata field
- [ ] tests/test_metadata.py tests: title format, description structure,
      tag length limit, timestamp formatting, credit generation

## Critical Constraints
- All LLM calls via LLMClient
- Prompt templates via PromptManager
- Description timestamps formatted as MM:SS
- No emojis anywhere in metadata

## Reference Files
- SPEC.md (Section 4.8, Appendix B)
```

---

### T30: Telegram Bot Core

```markdown
# Task: Build Telegram bot core with authentication

Priority: 8
State: queued
Created: 2026-02-28T00:00:29Z
Depends-On: agent/task-*-build-the-configuration-system, agent/task-*-implement-sqlite-database
Scope: src/telegram_bot/bot.py, src/telegram_bot/notifications.py, tests/test_telegram.py

## Description
Implement the Telegram bot foundation from SPEC.md Section 4.10.

Create:
1. src/telegram_bot/bot.py:
   - TelegramBot class
   - async start(): Initialize bot with token from config, set up handlers
   - User authentication: only respond to user IDs in config.telegram.authorized_user_ids
   - Register command handlers (defined in separate modules)
   - Webhook or long-polling mode (configurable)

2. src/telegram_bot/notifications.py:
   - Format functions that produce plain-text messages (no emojis):
   - format_review_notification(pipeline_run, clips, flags) -> str
   - format_status_message(pipeline_statuses) -> str
   - format_error_alert(error) -> str
   - format_digest(stats) -> str
   All follow the formats in SPEC.md Appendix A.

## Acceptance Criteria
- [ ] Bot initializes with token from config
- [ ] Unauthorized users are silently ignored
- [ ] Notification messages match SPEC.md Appendix A format exactly
- [ ] No emojis in any message format
- [ ] tests/test_telegram.py tests: auth check, message formatting,
      unauthorized user rejection

## Critical Constraints
- Use python-telegram-bot v20+ (async)
- Bot token from config (via env var)
- Authorized user IDs from config
- All message text is plain text with basic Markdown -- NO emojis
- Do not hardcode any user IDs

## Reference Files
- SPEC.md (Section 4.10, Appendix A)
```

---

### T31: Telegram Review Flow

```markdown
# Task: Implement Telegram review approval workflow

Priority: 8
State: queued
Created: 2026-02-28T00:00:30Z
Depends-On: agent/task-*-build-telegram-bot-core, agent/task-*-youtube-uploader
Scope: src/telegram_bot/review.py, tests/test_review.py

## Description
Implement the human review flow over Telegram.

Create src/telegram_bot/review.py:
- ReviewManager class
- async send_for_review(pipeline_run_id: int, bot: TelegramBot) -> None
  Sends review notification + preview clip + full video link to authorized user.
  Creates inline keyboard with buttons: APPROVE, REJECT, HOLD, SKIP CLIPS, REDO SCRIPT
  Records in review_log table.
- async handle_approval(pipeline_run_id: int) -> None
  Triggers YouTube upload and publish.
- async handle_rejection(pipeline_run_id: int) -> None
  Marks pipeline run as rejected in database.
- async handle_hold(pipeline_run_id: int) -> None
  Marks as held for later review.
- async handle_skip_clips(pipeline_run_id: int, clip_numbers: list[int]) -> None
  Removes specified clips and queues regeneration.
- Timeout logic: auto-hold after config.telegram.review_timeout_hours
- Reminder at config.telegram.reminder_after_hours

## Acceptance Criteria
- [ ] Review notification sent with inline keyboard buttons
- [ ] Each button triggers the correct handler
- [ ] Timeout auto-holds the video
- [ ] Reminder sent at configured time
- [ ] All actions logged in review_log table
- [ ] tests/test_review.py tests: approval flow, rejection, hold, timeout,
      skip clips parsing

## Critical Constraints
- InlineKeyboardMarkup for buttons (not ReplyKeyboard)
- Only authorized users can press buttons
- Quiet hours: suppress notifications during config.telegram.quiet_hours
- No emojis in button labels or messages

## Reference Files
- SPEC.md (Section 4.10)
```

---

### T32: Telegram Commands

```markdown
# Task: Implement Telegram bot command handlers

Priority: 8
State: queued
Created: 2026-02-28T00:00:31Z
Depends-On: agent/task-*-build-telegram-bot-core, agent/task-*-implement-sqlite-database
Scope: src/telegram_bot/commands.py, tests/test_commands.py

## Description
Implement all Telegram command handlers from SPEC.md Section 4.10.

Create src/telegram_bot/commands.py:
- /status -- Show pipeline status across all channels
- /pause [channel] -- Pause a channel's pipeline
- /resume [channel] -- Resume a paused channel
- /stats -- Upload counts, view counts, errors summary
- /errors -- Recent errors from error_log table
- /queue -- Videos awaiting review
- /config [key] [value] -- Update runtime config override
- /force_upload [id] -- Upload a held video
- /help -- Command reference

Each command queries the database and returns a formatted response.

## Acceptance Criteria
- [ ] All commands from the spec are implemented
- [ ] /status queries pipeline_runs table for each channel
- [ ] /pause and /resume update a runtime config flag
- [ ] /config writes to config_overrides table
- [ ] /help returns the full command list
- [ ] tests/test_commands.py tests: each command handler with mocked database

## Critical Constraints
- Only authorized users can execute commands
- Responses are plain text, no emojis
- /config only allows safe keys (whitelist in code)
- /force_upload checks that the video exists and is in "held" state

## Reference Files
- SPEC.md (Section 4.10)
```

---

### T33: File Preview Server

```markdown
# Task: Build simple HTTP file server for video previews

Priority: 8
State: queued
Created: 2026-02-28T00:00:32Z
Depends-On: agent/task-*-build-telegram-bot-core
Scope: src/telegram_bot/file_server.py, tests/test_file_server.py

## Description
Create a simple HTTP server that serves video preview files so the user
can watch full videos before approving uploads.

Create src/telegram_bot/file_server.py:
- PreviewServer class
- start(host, port, base_dir): Start an aiohttp or simple HTTP server
- stop(): Shutdown cleanly
- get_preview_url(filename: str) -> str: Returns full URL for a file
- Only serves files from the configured preview directory
- No directory listing (security)
- Basic auth optional (configurable)

## Acceptance Criteria
- [ ] Serves video files from a single configured directory
- [ ] Returns 404 for files outside that directory (no path traversal)
- [ ] get_preview_url constructs correct URL from config base_url
- [ ] tests/test_file_server.py tests: file serving, 404 for missing files,
      path traversal prevention

## Critical Constraints
- Use aiohttp.web (already in async ecosystem) or http.server
- Bind to config host/port
- No directory listing at / endpoint
- Sanitize filenames to prevent path traversal (../)
- No emojis in any response

## Reference Files
- SPEC.md (Section 4.10)
```

---

### T34: Pipeline Orchestrator

```markdown
# Task: Build the main pipeline orchestrator

Priority: 9
State: queued
Created: 2026-02-28T00:00:33Z
Depends-On: agent/task-*-discovery-engine, agent/task-*-video-downloader, agent/task-*-scene-analysis-orchestrator, agent/task-*-script-generator, agent/task-*-create-tts-engine-abstraction, agent/task-*-video-renderer, agent/task-*-youtube-uploader, agent/task-*-telegram-review-flow
Scope: src/orchestrator/pipeline.py, src/orchestrator/resource_manager.py, src/orchestrator/cleanup.py, tests/test_pipeline.py

## Description
Build the main pipeline orchestrator that runs a full pipeline cycle for
one niche channel.

Create:
1. src/orchestrator/pipeline.py:
   - PipelineRunner class
   - async run(niche: str, channel_config: ChannelConfig) -> PipelineResult
     Executes all 9 phases from SPEC.md Section 5.1:
     Discovery -> Acquisition -> Analysis -> Script -> TTS -> Assembly ->
     Review (send to Telegram, wait) -> Upload -> Cleanup
   - Each phase is a separate async method for clarity
   - Pipeline state tracked in pipeline_runs table
   - On failure: log error, update status, send Telegram alert

2. src/orchestrator/resource_manager.py:
   - ResourceManager class
   - Semaphores for: concurrent_pipelines, concurrent_downloads, concurrent_renders
   - GPU lock for TTS inference
   - Methods: acquire_download_slot(), acquire_render_slot(), acquire_gpu()

3. src/orchestrator/cleanup.py:
   - cleanup_working_files(pipeline_run_id: int, working_dir: Path)
   - archive_video(video_path: Path, archive_dir: Path) -> Path
   - prune_archives(archive_dir: Path, max_age_days: int)

## Acceptance Criteria
- [ ] Full pipeline executes all 9 phases in order
- [ ] Pipeline state updated in database at each phase boundary
- [ ] Resource manager enforces concurrency limits
- [ ] Failure in one phase does not crash the orchestrator
- [ ] Cleanup removes temp files after completion
- [ ] tests/test_pipeline.py tests: phase ordering, state transitions,
      failure handling, resource locking (mock all modules)

## Critical Constraints
- Each phase wrapped in try/except -- failures are logged and handled
- Pipeline run has a total timeout (config.guardrails equivalent)
- Review phase blocks until Telegram response (or timeout)
- No emojis in any log or status message

## Reference Files
- SPEC.md (Section 5.1)
```

---

### T35: Scheduler

```markdown
# Task: Build the APScheduler-based job scheduler

Priority: 9
State: queued
Created: 2026-02-28T00:00:34Z
Depends-On: agent/task-*-pipeline-orchestrator
Scope: src/orchestrator/scheduler.py, tests/test_scheduler.py

## Description
Implement the scheduler that triggers pipeline runs per SPEC.md Section 4.11.

Create src/orchestrator/scheduler.py:
- PipelineScheduler class
- setup(config: AppConfig): Register all channel schedules
- start(): Start the APScheduler event loop
- stop(): Graceful shutdown
- For each enabled channel, schedule pipeline runs at config times
  (e.g., gaming at 00:30, 06:30, 12:30, 18:30 UTC)
- Check for paused channels before triggering
- Use persistent job store (SQLite) so schedules survive restarts
- Log each scheduled trigger and completion

## Acceptance Criteria
- [ ] All enabled channels are scheduled at their configured times
- [ ] Paused channels are skipped (check config_overrides table)
- [ ] Persistent job store via SQLAlchemy (not in-memory)
- [ ] Graceful shutdown on SIGTERM/SIGINT
- [ ] tests/test_scheduler.py tests: schedule registration, pause check,
      trigger logic (mock APScheduler)

## Critical Constraints
- Use APScheduler 3.x (stable) with CronTrigger for each scheduled time
- Timezone: always UTC
- Max concurrent pipelines enforced via ResourceManager
- No emojis in log messages

## Reference Files
- SPEC.md (Sections 4.11, 5.2)
```

---

### T36: Analytics Collector

```markdown
# Task: Build YouTube Analytics data collector

Priority: 10
State: queued
Created: 2026-02-28T00:00:35Z
Depends-On: agent/task-*-build-youtube-data-api, agent/task-*-implement-sqlite-database
Scope: src/analytics/collector.py, tests/test_analytics.py

## Description
Implement analytics collection from SPEC.md Section 4.12.

Create src/analytics/collector.py:
- AnalyticsCollector class
- async collect_video_stats(video_ids: list[str], credentials_file: str) -> list[dict]
  Fetches view count, like count, comment count, average view duration
  for each video. Stores snapshot in analytics table.
- async collect_all_recent(hours: int = 48) -> None
  Collects stats for all videos uploaded in the last N hours.
- Schedule: run every 6 hours (triggered by scheduler)

## Acceptance Criteria
- [ ] Fetches stats via YouTube Data API
- [ ] Stores timestamped snapshots in analytics table
- [ ] Handles videos that have been deleted or made private
- [ ] tests/test_analytics.py tests: stat fetching, storage, missing video handling

## Critical Constraints
- Use YouTube Data API (reporting API requires additional setup)
- Quota-efficient: batch video IDs in single API call (up to 50 per call)
- No emojis

## Reference Files
- SPEC.md (Section 4.12)
```

---

### T37: Analytics Feedback Engine

```markdown
# Task: Build analytics feedback and recommendation engine

Priority: 10
State: queued
Created: 2026-02-28T00:00:36Z
Depends-On: agent/task-*-analytics-collector, agent/task-*-build-the-llm-abstraction
Scope: src/analytics/analyzer.py, src/analytics/feedback.py, config/prompts/performance_analysis.j2, tests/test_feedback.py

## Description
Implement the feedback loop from SPEC.md Section 4.12.

Create:
1. src/analytics/analyzer.py:
   - analyze_performance(niche: str, days: int = 7) -> PerformanceReport
     Computes: avg views, avg watch time, avg CTR, subscriber gain,
     Content ID claim rate, best/worst performing videos.

2. src/analytics/feedback.py:
   - async generate_recommendations(report: PerformanceReport, llm_client: LLMClient) -> list[str]
     Sends performance data to LLM, gets optimization recommendations.
   - async send_weekly_digest(bot: TelegramBot, report: PerformanceReport, recommendations: list[str])
     Formats and sends a weekly summary via Telegram.

3. config/prompts/performance_analysis.j2:
   - Template for LLM performance analysis prompt

## Acceptance Criteria
- [ ] Performance report covers all key metrics
- [ ] LLM recommendations are actionable (e.g., "reduce clip length to 20s")
- [ ] Weekly digest formatted per SPEC.md Appendix A style (no emojis)
- [ ] tests/test_feedback.py tests: report generation, LLM recommendation parsing,
      digest formatting

## Critical Constraints
- LLM calls via LLMClient
- Recommendations sent to Telegram for approval before applying
- No automatic parameter changes without human approval
- No emojis

## Reference Files
- SPEC.md (Section 4.12)
```

---

### T38: Main Entry Point

```markdown
# Task: Build main application entry point

Priority: 10
State: queued
Created: 2026-02-28T00:00:37Z
Depends-On: agent/task-*-pipeline-orchestrator, agent/task-*-scheduler, agent/task-*-build-telegram-bot-core
Scope: src/main.py, tests/test_main.py

## Description
Create the main entry point that starts all services.

Create src/main.py:
- async main():
  1. Load configuration
  2. Initialize database
  3. Initialize LLM client
  4. Initialize TTS engine
  5. Start Telegram bot
  6. Start file preview server
  7. Start scheduler
  8. Run event loop until shutdown signal
- CLI arguments:
  --config PATH (default: config/config.yaml)
  --single-run NICHE (run one pipeline immediately, skip scheduler)
  --init-db (initialize database and exit)
- Signal handling: SIGTERM/SIGINT triggers graceful shutdown
- Startup health checks: verify APIs reachable, GPU available, disk space ok

## Acceptance Criteria
- [ ] Application starts all services in correct order
- [ ] --single-run mode works for testing
- [ ] --init-db creates the database
- [ ] Graceful shutdown on signal
- [ ] Health checks log warnings for unavailable services
- [ ] tests/test_main.py tests: argument parsing, startup sequence (mocked services)

## Critical Constraints
- Use argparse for CLI
- asyncio.run(main()) as the top-level call
- No emojis in startup/shutdown messages

## Reference Files
- SPEC.md (Section 4.11)
```

---

### T39: Integration Tests

```markdown
# Task: Write integration tests for full pipeline

Priority: 10
State: queued
Created: 2026-02-28T00:00:38Z
Depends-On: agent/task-*-main-entry-point
Scope: tests/test_integration.py, tests/conftest.py

## Description
Write integration tests that verify the pipeline works end-to-end with
mocked external services.

Create:
1. tests/conftest.py:
   - Shared fixtures: temp_db, mock_llm_client, mock_tts_engine,
     mock_youtube_client, mock_reddit_client, sample_config,
     temp_working_dir, sample_video_file, sample_subtitle_file

2. tests/test_integration.py:
   - test_discovery_to_clips: Discovery -> Download -> Analyze -> Extract
   - test_script_to_audio: Script generation -> TTS -> Audio processing
   - test_assembly_to_render: Graphics -> Timeline -> Mix -> Render
   - test_full_pipeline_mock: Full pipeline with all external services mocked
   - test_config_loading: Load real config.yaml and validate

## Acceptance Criteria
- [ ] conftest.py provides reusable fixtures for all test files
- [ ] Integration tests exercise multiple modules working together
- [ ] All external APIs mocked (no network calls in tests)
- [ ] Full pipeline test verifies correct state transitions in database
- [ ] Tests are independent and can run in any order

## Critical Constraints
- Use pytest fixtures with tmp_path for all file operations
- Mock yt-dlp, YouTube API, Reddit API, Telegram API, TTS engines
- Tests must pass without GPU, FFmpeg, or network access
- No emojis

## Reference Files
- SPEC.md (Section 9 -- Testing Strategy)
```

---

## 5. Implementation Order

### Summary Table

| Phase | Tasks | Priority | Est. Agent Time | Dependencies |
|---|---|---|---|---|
| **Phase 0: Foundation** | T01, T02, T03, T04 | 1-2 | 1-2 nights | None |
| **Phase 1: Core Modules** | T05, T06, T07, T08, T09 | 2-3 | 2-3 nights | Phase 0 |
| **Phase 1B: Pipeline Modules** | T10, T11, T12, T13, T14, T15 | 3-4 | 2-3 nights | Phase 1 |
| **Phase 2: Content Production** | T16, T17, T18, T19, T20, T21 | 5-6 | 2-3 nights | Phase 1B |
| **Phase 3: Assembly & Output** | T22, T23, T24, T25, T26, T27, T28, T29 | 6-7 | 3-4 nights | Phase 2 |
| **Phase 4: Communication** | T30, T31, T32, T33, T34, T35 | 8-9 | 2-3 nights | Phase 3 |
| **Phase 5: Analytics & Polish** | T36, T37, T38, T39 | 10 | 1-2 nights | Phase 4 |
| **Total** | 39 tasks | | **~13-20 overnight sessions** | |

### Parallel Execution Within Phases

Within each phase, tasks without direct dependencies can run concurrently on multiple workers:

- **Phase 0:** T01 first, then T02+T03+T04 in parallel
- **Phase 1:** T05+T06+T07+T08+T09 all in parallel (each depends only on Phase 0)
- **Phase 1B:** T11+T12+T13+T14+T15 in parallel; T10 after T07+T08+T09 merge
- **Phase 2:** T17+T18+T21 in parallel; T16 after T12-T15; T19+T20 after T18
- etc.

---

## 6. Interface Contracts

### Core Data Types

```python
# Used across modules -- define in src/models.py or per-module

@dataclass
class DiscoveredVideo:
    video_id: str
    title: str
    channel_name: str
    channel_id: str
    url: str
    view_count: int
    like_count: int
    comment_count: int
    view_velocity: float
    viral_score: float
    niche: str
    discovery_source: str

@dataclass
class DownloadResult:
    video_path: Path
    subtitle_path: Path | None
    metadata: dict

@dataclass
class ClipData:
    clip_path: Path
    source_video_id: str
    source_title: str
    source_creator: str
    source_url: str
    start_sec: float
    end_sec: float
    duration_sec: float
    extraction_method: str
    rank: int
    view_count: int

@dataclass
class ScriptResult:
    opening: str
    closing: str
    clips: list[dict]  # each: {number, intro, outro}
    total_chars: int
    estimated_duration_sec: float

@dataclass
class NarrationResult:
    audio_path: Path
    duration_sec: float
    segment_paths: list[Path]
    segment_durations: list[float]

@dataclass
class RenderResult:
    video_path: Path
    duration_sec: float
    file_size_bytes: int

@dataclass
class ShortResult:
    video_path: Path
    title: str
    duration_sec: float
    source_clip_rank: int

@dataclass
class VideoMetadata:
    title: str
    description: str
    tags: list[str]
    category_id: int
    privacy_status: str

@dataclass
class UploadResult:
    video_id: str
    url: str
    status: str

@dataclass
class PipelineResult:
    pipeline_run_id: int
    niche: str
    status: str
    video_path: Path | None
    upload_result: UploadResult | None
    shorts_results: list[ShortResult]
    error: str | None
```

---

## 7. Agent Configuration

### 7.1 Workspace .agent/config.yaml

Create this file in the viral_channel workspace so the agent knows how to
operate here:

```yaml
workspace:
  name: viral_channel
  description: "Automated YouTube pipeline -- Last SiX Hours"

blocked_paths:
  - ".git/"
  - "*.env"
  - ".env*"
  - "config/youtube_*_creds.json"
  - "voices/*.wav"
  - "models/"
  - "_agent_ref/"
  - "assets/music/"
  - "assets/fonts/"
```

### 7.2 Node Configuration for This Project

On MM5000, the agent config already has Ollama with DeepSeek-R1:32B configured.
No changes needed -- the agent can pick up viral_channel tasks using the same
worker process that handles trading tasks.

To point the worker at this workspace:
```bash
python -m trading_agent worker --workspace /path/to/viral_channel --node-id mm5000
```

Or add a second workspace to the config and run a second worker instance.

### 7.3 Task Creation Script

To create all tasks, run from the Windows workstation:

```powershell
cd e:\viral_channel

# Phase 0
python _agent_ref/task_creator.py "Create project scaffolding and base files" --priority 1
python _agent_ref/task_creator.py "Build the configuration system with Pydantic models" --priority 1
python _agent_ref/task_creator.py "Implement SQLite database with SQLAlchemy models" --priority 1
python _agent_ref/task_creator.py "Create structured logging utility" --priority 2

# Phase 1 (create after Phase 0 merges)
# ... etc.
```

Tasks should be created phase-by-phase. Only create the next phase's tasks
after the current phase's REVIEW.md files are confirmed and merged.

---

## 8. Human Review Checkpoints

### After Each Phase

| Checkpoint | What to Review | Accept Criteria |
|---|---|---|
| Phase 0 complete | Project structure, config, DB schema | Files exist, tests pass, config loads |
| Phase 1 complete | LLM client, FFmpeg wrapper, API clients | Mock tests pass, interfaces match contracts |
| Phase 1B complete | Discovery, download, analysis modules | Integration between modules works |
| Phase 2 complete | Scripts, TTS, audio | Generated script is coherent, TTS produces audio |
| Phase 3 complete | Assembly, render, thumbnails, Shorts | Video renders correctly, thumbnail looks good |
| Phase 4 complete | Telegram bot, pipeline orchestrator | Bot responds, pipeline runs end-to-end |
| Phase 5 complete | Analytics, main entry point | Full system operational |

### After Each Task (Agent-Generated REVIEW.md)

The agent produces a REVIEW.md on each task branch. Review:
1. Does the code match the SPEC.md requirements?
2. Do tests pass?
3. Are there any hardcoded values that should be in config?
4. Are there emojis anywhere? (grep for common emoji patterns)
5. Does the interface match the contracts in Section 6?

Merge approved task branches into main before creating next-phase tasks.

---

## 9. Testing Strategy

### Unit Tests (Per Task)

Every task includes its own test file. Tests must:
- Mock all external services
- Use tmp_path for file operations
- Not require network, GPU, or FFmpeg
- Cover happy path + at least 2 error cases

### Integration Tests (T39)

After all modules are built:
- Full pipeline with mocked externals
- Configuration loading with real config.yaml
- Database state transitions
- Multi-module data flow

### Manual Testing (Human)

Before going live:
- Run single pipeline with real YouTube API (on a test channel)
- Verify video quality, audio sync, narration pacing
- Test Telegram bot interactions
- Test with various viral video types (short clips, long videos, music, gaming)
- Verify Content ID behavior on test uploads

---

## 10. Risk Register

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Agent generates code that does not integrate between modules | High | Medium | Interface contracts defined in Section 6; review at each phase |
| YouTube API quota insufficient | Medium | High | Apply for quota increase early; use multiple projects |
| Most Replayed heatmap format changes | Low | Medium | Graceful fallback to transcript/audio analysis |
| Content ID claims block monetization | High | High | Short clips, high narration ratio, creator credits |
| TTS quality insufficient for viewer retention | Medium | Low | A/B test engines, iterate on voice profiles |
| FFmpeg filter graphs too complex for agent to generate | Medium | Medium | Simplify to multi-pass rendering if needed |
| 32K context window insufficient for complex tasks | Medium | Medium | Keep tasks small; use GitHub Models (128K) for large tasks |

---

## Appendix: Quick Reference

### Creating a Task

```bash
# From the viral_channel workspace
python _agent_ref/task_creator.py "<description from T## above>" --priority <N>
```

### Checking Status

```bash
python _agent_ref/status.py --workspace /path/to/viral_channel
```

### Viewing Worker Logs

```bash
tail -f worker_mm5000.log | python -m json.tool
```

---

**End of Design Document**
