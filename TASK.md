# Task: Implement SQLite database with SQLAlchemy models

Priority: 1
Status: spec-in-progress
Created: 2026-02-28T01:02:00Z
Depends-On: agent/task-20260228010000-create-project-scaffolding
Scope: src/database.py, scripts/init_database.py, tests/test_database.py

## Description

Implement the database layer for the viral_channel project using SQLAlchemy 2.0+
ORM. The database stores all pipeline state: discovered videos, pipeline runs,
clips, scripts, TTS audio, shorts, analytics, review log, config overrides, and
error log.

### SQLAlchemy Models to Create (in src/database.py):

All models use SQLAlchemy 2.0 DeclarativeBase + mapped_column style.

**Base:**
```python
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey
from datetime import datetime

class Base(DeclarativeBase):
    pass
```

**DiscoveredVideo:**
- id: int (primary key, autoincrement)
- video_id: str (unique, not null) -- YouTube video ID
- title: str (not null)
- channel_name: str (not null)
- channel_id: str (not null)
- url: str (not null)
- category_id: int | None
- duration_seconds: int | None
- view_count: int | None
- like_count: int | None
- comment_count: int | None
- view_velocity: float | None -- views per hour at discovery
- viral_score: float | None
- niche: str (not null) -- gaming, sports, funny, music
- discovery_source: str | None -- youtube_trending, reddit, etc.
- discovered_at: datetime (default=utcnow)
- processed: int (default=0) -- 0=pending, 1=used, 2=skipped, 3=rejected
- content_id_risk: str (default="unknown") -- low, medium, high, unknown

**PipelineRun:**
- id: int (primary key)
- niche: str (not null)
- cycle_start: datetime (not null)
- cycle_end: datetime (not null)
- status: str (default="pending") -- pending, running, review, approved, uploaded, failed
- started_at: datetime | None
- completed_at: datetime | None
- video_file_path: str | None
- video_duration_seconds: float | None
- video_file_size_bytes: int | None
- youtube_video_id: str | None -- set after upload
- youtube_url: str | None
- error_message: str | None
- retry_count: int (default=0)

**Clip:**
- id: int (primary key)
- pipeline_run_id: int (FK -> pipeline_runs.id, not null)
- discovered_video_id: int (FK -> discovered_videos.id, not null)
- rank_position: int (not null) -- 1-10
- start_time_seconds: float (not null)
- end_time_seconds: float (not null)
- clip_duration_seconds: float (not null)
- extraction_method: str | None -- most_replayed, transcript, audio_energy, scene_detection
- clip_file_path: str | None
- content_id_risk: str (default="unknown")

**Script:**
- id: int (primary key)
- pipeline_run_id: int (FK -> pipeline_runs.id, not null)
- opening_text: str | None
- closing_text: str | None
- full_script_json: str | None -- complete script as JSON text
- total_char_count: int | None
- estimated_duration_seconds: float | None
- llm_model_used: str | None
- generated_at: datetime (default=utcnow)

**TTSAudio:**
- id: int (primary key)
- pipeline_run_id: int (FK -> pipeline_runs.id, not null)
- engine_used: str (not null) -- xtts_v2, piper
- voice_profile: str | None
- audio_file_path: str | None
- duration_seconds: float | None
- generated_at: datetime (default=utcnow)

**Short:**
- id: int (primary key)
- pipeline_run_id: int (FK -> pipeline_runs.id, not null)
- clip_id: int | None (FK -> clips.id)
- file_path: str | None
- duration_seconds: float | None
- title: str | None
- description: str | None
- youtube_video_id: str | None
- youtube_url: str | None
- status: str (default="pending") -- pending, review, uploaded, failed
- uploaded_at: datetime | None

**Analytics:**
- id: int (primary key)
- youtube_video_id: str (not null)
- measured_at: datetime (default=utcnow)
- view_count: int | None
- like_count: int | None
- comment_count: int | None
- average_view_duration_seconds: float | None
- click_through_rate: float | None
- subscriber_gain: int | None
- estimated_revenue_usd: float | None

**ReviewLog:**
- id: int (primary key)
- pipeline_run_id: int (FK -> pipeline_runs.id, not null)
- sent_at: datetime (default=utcnow)
- responded_at: datetime | None
- action: str | None -- approve, reject, hold, skip, redo_script
- response_detail: str | None -- e.g., "skip 4,7"
- auto_held: int (default=0) -- 1 if auto-held due to timeout

**ConfigOverride:**
- key: str (primary key)
- value: str (not null)
- updated_at: datetime (default=utcnow)
- updated_by: str (default="system")

**ErrorLog:**
- id: int (primary key)
- pipeline_run_id: int | None (FK -> pipeline_runs.id)
- module: str (not null)
- error_type: str (not null)
- error_message: str (not null)
- stack_trace: str | None
- occurred_at: datetime (default=utcnow)
- resolved: int (default=0)

### Indexes to Create:

- idx_discovered_videos_niche ON discovered_videos(niche, discovered_at)
- idx_discovered_videos_processed ON discovered_videos(processed)
- idx_pipeline_runs_status ON pipeline_runs(status)
- idx_pipeline_runs_niche ON pipeline_runs(niche, cycle_start)
- idx_clips_pipeline ON clips(pipeline_run_id)
- idx_analytics_video ON analytics(youtube_video_id, measured_at)
- idx_error_log_module ON error_log(module, occurred_at)

### Helper Functions:

```python
def init_db(db_path: str) -> Engine:
    """
    Create SQLAlchemy engine, create all tables and indexes.
    Returns the Engine instance.
    """

def get_session(engine: Engine) -> Session:
    """Create and return a new Session bound to the engine."""

def get_pending_videos(session: Session, niche: str) -> list[DiscoveredVideo]:
    """Get all videos with processed=0 for the given niche."""

def mark_video_processed(session: Session, video_id: str, status: int) -> None:
    """Update a video's processed status (1=used, 2=skipped, 3=rejected)."""

def log_error(session: Session, module: str, error_type: str, message: str,
              pipeline_run_id: int | None = None, stack_trace: str | None = None) -> None:
    """Insert an error into the error_log table."""
```

### scripts/init_database.py:

A standalone CLI script that:
1. Takes --db-path argument (default: data/viral_channel.db)
2. Calls init_db(db_path)
3. Prints confirmation message
4. Usage: `python scripts/init_database.py --db-path data/viral_channel.db`

### tests/test_database.py:

Write tests covering:
- Table creation (all tables exist after init_db)
- Insert and query for each model (at least DiscoveredVideo, PipelineRun, Clip)
- Index existence verification
- Foreign key relationships (Clip -> PipelineRun, Clip -> DiscoveredVideo)
- Helper functions: get_pending_videos, mark_video_processed, log_error
- Default values (processed=0, status="pending", etc.)

## Acceptance Criteria

- [ ] All 10 tables from the schema above are defined as SQLAlchemy 2.0 ORM models
- [ ] All 7 indexes are created
- [ ] init_db() creates all tables and indexes, returns Engine
- [ ] get_session() returns a working Session
- [ ] scripts/init_database.py is runnable and creates the database file
- [ ] tests/test_database.py has at least 8 test functions covering tables, inserts,
      queries, indexes, foreign keys, and helper functions
- [ ] All timestamps default to UTC (datetime.utcnow or datetime.now(timezone.utc))

## Critical Constraints

- Use SQLAlchemy 2.0+ style (DeclarativeBase, mapped_column, Mapped)
- Database path is a parameter to init_db() (not hardcoded)
- All timestamps default to UTC (NOT local time)
- Use Text type for long string fields (full_script_json, stack_trace, error_message)
- Foreign keys must use ForeignKey() with proper references
- No emojis in any field defaults, log messages, or print statements
- Do NOT import from src/config.py (database module is independent)
- Tests must use tmp_path fixture for database file (in-memory or temp file)

## Reference Files

- SPEC.md (Section 6 -- Database Schema)
- DESIGN.md (Section 4, Task T03)
