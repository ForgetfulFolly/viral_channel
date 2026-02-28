# Task: Complete the 7 missing SQLAlchemy database models

Priority: 1
Status: spec-in-progress
Created: 2026-02-28T02:02:00Z
Scope: src/database.py, tests/test_database.py

## Description
The initial database implementation (src/database.py) only has 3 of the 10 required
SQLAlchemy models. The existing models (DiscoveredVideo, PipelineRun, Clip) are
correct and should NOT be changed. You must ADD the 7 missing models.

### Already implemented (DO NOT modify these):
- DiscoveredVideo (with indexes: idx_discovered_videos_niche, idx_discovered_videos_processed)
- PipelineRun (with indexes: idx_pipeline_runs_status, idx_pipeline_runs_niche)
- Clip (with index: idx_clips_pipeline)

### Models to ADD (from SPEC.md Section 6):

1. **Script** - Generated scripts for pipeline runs
   - id: Integer, primary key, autoincrement
   - pipeline_run_id: Integer, ForeignKey( pipeline_runs.id), not null
   - opening_text: Text, nullable
   - closing_text: Text, nullable
   - full_script_json: Text (complete script as JSON)
   - total_char_count: Integer
   - estimated_duration_seconds: Float
   - llm_model_used: Text
   - generated_at: DateTime, default=utcnow

2. **TTSAudio** - TTS audio files
   - id: Integer, primary key, autoincrement
   - pipeline_run_id: Integer, ForeignKey(pipeline_runs.id), not null
   - engine_used: String, not null
   - voice_profile: String, nullable
   - audio_file_path: String, nullable
   - duration_seconds: Float, nullable
   - generated_at: DateTime, default=utcnow

3. **Short** - Shorts generated from clips
   - id: Integer, primary key, autoincrement
   - pipeline_run_id: Integer, ForeignKey(pipeline_runs.id), not null
   - clip_id: Integer, ForeignKey(clips.id), nullable
   - file_path: String, nullable
   - duration_seconds: Float, nullable
   - title: String, nullable
   - description: Text, nullable
   - youtube_video_id: String, nullable
   - youtube_url: String, nullable
   - status: String, default=pending
   - uploaded_at: DateTime, nullable

4. **Analytics** - YouTube analytics snapshots
   - id: Integer, primary key, autoincrement
   - youtube_video_id: String, not null
   - measured_at: DateTime, default=utcnow
   - view_count: Integer, nullable
   - like_count: Integer, nullable
   - comment_count: Integer, nullable
   - average_view_duration_seconds: Float, nullable
   - click_through_rate: Float, nullable
   - subscriber_gain: Integer, nullable
   - estimated_revenue_usd: Float, nullable
   - Index: idx_analytics_video on (youtube_video_id, measured_at)

5. **ReviewLog** - Telegram review log entries
   - id: Integer, primary key, autoincrement
   - pipeline_run_id: Integer, ForeignKey(pipeline_runs.id), not null
   - sent_at: DateTime, default=utcnow
   - responded_at: DateTime, nullable
   - action: String, nullable
   - response_detail: String, nullable
   - auto_held: Integer, default=0

6. **ConfigOverride** - Runtime config overrides via Telegram
   - key: String, primary key (NOT autoincrement)
   - value: String, not null
   - updated_at: DateTime, default=utcnow
   - updated_by: String, default=system

7. **ErrorLog** - Error tracking
   - id: Integer, primary key, autoincrement
   - pipeline_run_id: Integer, ForeignKey(pipeline_runs.id), nullable
   - module: String, not null
   - error_type: String, not null
   - error_message: Text, not null
   - stack_trace: Text, nullable
   - occurred_at: DateTime, default=utcnow
   - resolved: Integer, default=0
   - Index: idx_error_log_module on (module, occurred_at)

### Important notes:
- The existing log_error() helper function at the bottom of database.py references
  ErrorLog, which currently does not exist. After adding the ErrorLog model, this
  function will work correctly.
- Follow the EXACT same coding style as the existing models (Mapped[], mapped_column, etc.)
- Add new models AFTER the existing Clip class and BEFORE the helper functions
- Also update tests/test_database.py to add tests for the new models (insert, query, indexes)

## Acceptance Criteria
- [ ] All 7 new models added to src/database.py following existing style
- [ ] Analytics has idx_analytics_video index
- [ ] ErrorLog has idx_error_log_module index
- [ ] ConfigOverride uses key as primary key (no autoincrement id)
- [ ] All ForeignKey references are correct
- [ ] init_db() creates all 10 tables (run and verify)
- [ ] tests/test_database.py has insert/query tests for each new model
- [ ] Existing DiscoveredVideo/PipelineRun/Clip models are NOT modified
- [ ] Existing helper functions (init_db, get_session, get_pending_videos, mark_video_processed, log_error) are NOT modified

## Critical Constraints
- Use SQLAlchemy 2.0+ style (Mapped[], mapped_column) matching existing code
- All DateTime defaults use datetime.utcnow (matching existing pattern)
- Do NOT modify existing models or helper functions
- Do NOT change imports unless you need to add new types
- Add new models between the Clip class and the init_db function
- No emojis in any output

## Reference Files
- SPEC.md (Section 6 -- full SQL schema for all 10 tables)
- src/database.py (current file with 3 models to preserve)
