# Task: Build the configuration system with Pydantic models

Priority: 1
State: queued
Created: 2026-02-28T01:01:00Z
Depends-On: agent/task-20260228010000-create-project-scaffolding
Scope: src/config.py, config/config.yaml, tests/test_config.py

## Description

Implement the configuration loading system for the viral_channel project.

All configuration is stored in a single config/config.yaml file and loaded into
validated Pydantic models. Environment variables can be referenced in YAML values
using ${VAR_NAME} syntax and are resolved at load time from os.environ.

### Pydantic Models to Create (in src/config.py):

**GeneralConfig:**
- project_name: str = "Last SiX Hours"
- log_level: str = "INFO"
- log_dir: str = "logs"
- working_dir: str = "working"
- archive_dir: str = "archive"
- timezone: str = "UTC"

**LLMProviderConfig:**
- name: str
- base_url: str
- api_key: str = ""
- model: str
- max_tokens: int = 4096
- temperature: float = 0.7
- timeout_seconds: int = 120
- max_retries: int = 3

**LLMConfig:**
- primary: LLMProviderConfig
- fallback: LLMProviderConfig | None = None

**VoiceConfig:**
- name: str
- engine: str
- reference_audio: str = ""
- language: str = "en"
- speed: float = 1.0

**TTSEngineConfig:**
- name: str
- model_path: str
- device: str = "cuda:0"
- sample_rate: int = 22050

**TTSConfig:**
- primary_engine: str
- fallback_engine: str = "piper"
- engines: list[TTSEngineConfig]
- default_voice: str
- voices: list[VoiceConfig]

**AudioConfig:**
- narration_lufs: float = -16.0
- clip_audio_lufs: float = -26.0
- background_music_lufs: float = -32.0
- ducking_db: float = -12.0
- sentence_pause_ms: int = 300
- segment_pause_ms: int = 500
- music_fade_sec: float = 3.0
- output_sample_rate: int = 48000
- output_channels: int = 2

**VideoConfig:**
- target_duration_min: int = 480 (8 minutes in seconds)
- target_duration_max: int = 600 (10 minutes in seconds)
- target_clips: int = 10
- clip_duration_min: int = 20
- clip_duration_max: int = 90
- resolution: str = "1920x1080"
- fps: int = 30
- codec: str = "libx264"
- crf: int = 20
- preset: str = "medium"
- audio_codec: str = "aac"
- audio_bitrate: str = "192k"
- pixel_format: str = "yuv420p"
- transition_duration: float = 0.5
- fade_duration: float = 0.5
- max_source_duration_seconds: int = 3600
- clip_extraction_methods_priority: list[str] = ["most_replayed", "transcript", "audio_energy", "scene_detection"]
- shorts_count_per_video: int = 2
- shorts_duration_min: int = 30
- shorts_duration_max: int = 60

**DiscoveryConfig:**
- lookback_hours: int = 6
- max_candidates_per_niche: int = 30
- min_views: int = 10000
- min_viral_score: float = 0.4
- youtube_daily_quota_limit: int = 10000
- reddit_subreddits: dict[str, list[str]] (niche -> subreddit list)
- reddit_min_score: int = 100
- scoring_weight_view_velocity: float = 0.30
- scoring_weight_reddit: float = 0.20
- scoring_weight_like_ratio: float = 0.15
- scoring_weight_comment_velocity: float = 0.15
- scoring_weight_recency: float = 0.20

**ChannelConfig:**
- name: str
- niche: str
- enabled: bool = True
- youtube_category_id: int
- youtube_credentials_file: str
- schedule_times_utc: list[str]
- voice: str
- hashtags: list[str]
- standard_tags: list[str]
- youtube_search_queries: list[str]

**TelegramConfig:**
- bot_token: str
- authorized_user_ids: list[int]
- review_timeout_hours: int = 2
- reminder_after_hours: float = 1.0
- quiet_hours_start: int = 23
- quiet_hours_end: int = 7

**YouTubeUploadConfig:**
- chunk_size_bytes: int = 10485760 (10 MB)
- max_retries: int = 3
- default_privacy: str = "private"
- default_language: str = "en"

**SchedulerConfig:**
- max_concurrent_pipelines: int = 2
- max_concurrent_downloads: int = 4
- max_concurrent_renders: int = 1
- job_store_path: str = "data/scheduler_jobs.sqlite"

**BrandingConfig:**
- channel_display_name: str = "LAST SIX HOURS"
- font_path: str = "assets/fonts/default.ttf"
- title_font_size: int = 72
- label_font_size: int = 120
- lower_third_font_size: int = 36
- primary_color: str = "#FFFFFF"
- secondary_color: str = "#FFD700"
- background_color: str = "#000000"
- watermark_path: str = ""
- watermark_opacity: float = 0.3

**AppConfig (root):**
- general: GeneralConfig
- llm: LLMConfig
- tts: TTSConfig
- audio: AudioConfig
- video: VideoConfig
- discovery: DiscoveryConfig
- channels: list[ChannelConfig]
- telegram: TelegramConfig
- youtube_upload: YouTubeUploadConfig
- scheduler: SchedulerConfig
- branding: BrandingConfig

### Functions to Implement:

```python
def load_config(path: str = "config/config.yaml") -> AppConfig:
    """
    Load configuration from YAML file with environment variable substitution.

    1. Read YAML file
    2. Walk the parsed dict and replace ${VAR_NAME} patterns with os.environ values
    3. If an env var is not set, log a warning and keep the ${VAR_NAME} placeholder
    4. Parse into AppConfig via Pydantic model_validate
    5. Return validated AppConfig
    """

def _substitute_env_vars(data: dict | list | str) -> dict | list | str:
    """Recursively substitute ${VAR_NAME} patterns in config values."""
```

### config/config.yaml

Create a complete config.yaml with sensible defaults for all fields. Use ${VAR_NAME}
for secrets. Include two example channel configs: "gaming" and "sports".

Example structure:
```yaml
general:
  project_name: "Last SiX Hours"
  log_level: "INFO"
  log_dir: "logs"
  working_dir: "working"
  archive_dir: "archive"
  timezone: "UTC"

llm:
  primary:
    name: "deepseek-local"
    base_url: "${LLM_BASE_URL}"
    api_key: "${LLM_API_KEY}"
    model: "deepseek-r1:32b"
    max_tokens: 4096
    temperature: 0.7
    timeout_seconds: 120
    max_retries: 3
  fallback:
    name: "openai-fallback"
    base_url: "https://api.openai.com/v1"
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4o-mini"
    max_tokens: 4096
    temperature: 0.7
    timeout_seconds: 60
    max_retries: 2

# ... all other sections with full defaults ...
```

### tests/test_config.py

Write tests covering:
- Loading a valid config from a temp YAML file
- Missing required fields raise ValidationError
- Environment variable substitution works (set os.environ in test)
- Missing env vars keep the ${VAR_NAME} placeholder and log a warning
- Default values are correctly applied when fields are omitted
- Channel config validation (enabled flag, schedule times format)
- Scoring weights must sum to 1.0 within tolerance

## Acceptance Criteria

- [ ] src/config.py has all Pydantic models listed above
- [ ] load_config() loads YAML, substitutes env vars, returns validated AppConfig
- [ ] config/config.yaml has all sections with sensible defaults
- [ ] Environment variable substitution handles missing vars gracefully
- [ ] tests/test_config.py has at least 7 test functions covering all scenarios listed
- [ ] All duration/count fields have appropriate validators (gt=0 where appropriate)
- [ ] Scoring weights are validated to sum to approximately 1.0

## Critical Constraints

- Use pydantic v2 (BaseModel with model_validator, field_validator)
- Environment variable substitution must handle missing vars gracefully (log warning, keep placeholder)
- No emojis in any output, default config values, or log messages
- Config must be importable as: from src.config import load_config, AppConfig
- Use PyYAML for YAML parsing
- All field types must have explicit type annotations
- Do NOT import from any other src/ module (config.py has no internal dependencies)

## Reference Files

- SPEC.md (Section 7 -- Configuration)
- DESIGN.md (Section 4, Task T02)
