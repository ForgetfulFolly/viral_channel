# Task: Complete the 7 missing SQLAlchemy database models

## Problem Statement
The current implementation of `src/database.py` only contains 3 out of the 10 required SQLAlchemy database models. The missing models are essential for tracking pipeline runs, managing generated content, and maintaining operational logs. Without these models, the application cannot properly manage its state, track progress, or provide necessary analytics.

## Functional Requirements
### FR-1: Add Script Model
- Track generated scripts for pipeline runs
- Fields:
  - id (Integer, PK)
  - pipeline_run_id (FK to PipelineRun.id)
  - opening_text (Text, nullable)
  - closing_text (Text, nullable)
  - full_script_json (Text)
  - total_char_count (Integer)
  - estimated_duration_seconds (Float)
  - llm_model_used (Text)
  - generated_at (DateTime)

### FR-2: Add TTSAudio Model
- Track TTS audio files
- Fields:
  - id (Integer, PK)
  - pipeline_run_id (FK to PipelineRun.id)
  - engine_used (String, not null)
  - voice_profile (String, nullable)
  - audio_file_path (String, nullable)
  - duration_seconds (Float, nullable)
  - generated_at (DateTime)

### FR-3: Add Short Model
- Track shorts generated from clips
- Fields:
  - id (Integer, PK)
  - pipeline_run_id (FK to PipelineRun.id)
  - clip_id (FK to Clip.id, nullable)
  - file_path (String, nullable)
  - duration_seconds (Float, nullable)
  - title (String, nullable)
  - description (Text, nullable)
  - youtube_video_id (String, nullable)
  - youtube_url (String, nullable)
  - status (String, default=pending)
  - uploaded_at (DateTime, nullable)

### FR-4: Add Analytics Model
- Track YouTube analytics snapshots
- Fields:
  - id (Integer, PK)
  - youtube_video_id (String, not null)
  - measured_at (DateTime)
  - view_count (Integer, nullable)
  - like_count (Integer, nullable)
  - comment_count (Integer, nullable)
  - average_view_duration_seconds (Float, nullable)
  - click_through_rate (Float, nullable)
  - subscriber_gain (Integer, nullable)
  - estimated_revenue_usd (Float, nullable)
- Index: idx_analytics_video on (youtube_video_id, measured_at)

### FR-5: Add ReviewLog Model
- Track Telegram review log entries
- Fields:
  - id (Integer, PK)
  - pipeline_run_id (FK to PipelineRun.id)
  - sent_at (DateTime)
  - responded_at (DateTime, nullable)
  - action (String, nullable)
  - response_detail (String, nullable)
  - auto_held (Integer, default=0)

### FR-6: Add ConfigOverride Model
- Track runtime config overrides via Telegram
- Fields:
  - key (String, PK)
  - value (String, not null)
  - updated_at (DateTime)
  - updated_by (String, default=system)

### FR-7: Add ErrorLog Model
- Track errors and their resolution status
- Fields:
  - id (Integer, PK)
  - pipeline_run_id (FK to PipelineRun.id, nullable)
  - module (String, not null)
  - error_type (String, not null)
  - error_message (Text, not null)
  - stack_trace (Text, nullable)
  - occurred_at (DateTime)
  - resolved (Integer, default=0)
- Index: idx_error_log_module on (module, occurred_at)

## Non-Functional Requirements
1. All models must use SQLAlchemy 2.0+ style (Mapped[], mapped_column)
2. DateTime fields must use UTC timestamps with defaults set to utcnow()
3. Indexes must be created for frequently queried columns
4. Foreign key constraints must enforce referential integrity
5. Models must follow PEP 8 naming and coding standards

## Constraints
1. Cannot modify existing models (DiscoveredVideo, PipelineRun, Clip)
2. Cannot alter existing helper functions (init_db, get_session, etc.)
3. Must maintain all existing indexes and relationships
4. All new models must be added in the specified location in src/database.py
5. No new imports can be added unless required for model definitions

## Success Criteria
- [ ] All 7 new models are correctly implemented with proper fields and constraints
- [ ] Indexes (idx_analytics_video, idx_error_log_module) are properly created
- [ ] Foreign key relationships are correctly defined and enforced
- [ ] ConfigOverride uses a String primary key without autoincrement
- [ ] ErrorLog includes stack_trace field for debugging purposes
- [ ] All models follow the same coding style as existing ones
- [ ] Comprehensive test cases are added to tests/test_database.py
- [ ] init_db() function creates all 10 tables successfully

## Out of Scope
- Modifying existing database models or helper functions
- Adding new indexes to existing models
- Implementing validation logic for model fields
- Writing migration scripts for existing databases
- Updating application code to use the new models

## Open Questions
1. Should any additional indexes be added beyond those specified?
2. Are there any field length constraints that need to be enforced?
3. Should any relationships (e.g., backrefs) be established between models?
4. How should nullability be handled for fields marked as nullable?
5. Are there any specific data validation rules that need to be implemented?