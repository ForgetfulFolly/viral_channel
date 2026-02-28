from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ValidationError, Field, model_validator
import yaml
import os
import re
import logging

logger = logging.getLogger("config")
logging.basicConfig(level=logging.INFO)


class GeneralConfig(BaseModel):
    project_name: str = "Last SiX Hours"
    log_level: str = "INFO"
    log_dir: str = "logs"
    working_dir: str = "working"
    archive_dir: str = "archive"
    timezone: str = "UTC"


class LLMProviderConfig(BaseModel):
    name: str
    base_url: str
    api_key: str = ""
    model: str
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout_seconds: int = 120
    max_retries: int = 3


class LLMConfig(BaseModel):
    primary: LLMProviderConfig
    fallback: Optional[LLMProviderConfig] = None


class VoiceConfig(BaseModel):
    name: str
    engine: str
    reference_audio: str = ""
    language: str = "en"
    speed: float = 1.0


class TTSEngineConfig(BaseModel):
    name: str
    model_path: str
    device: str = "cuda:0"
    sample_rate: int = 22050


class TTSConfig(BaseModel):
    primary_engine: str
    fallback_engine: str = "piper"
    engines: List[TTSEngineConfig]
    default_voice: str
    voices: List[VoiceConfig]


class AudioConfig(BaseModel):
    narration_lufs: float = -16.0
    clip_audio_lufs: float = -26.0
    background_music_lufs: float = -32.0
    ducking_db: float = -12.0
    sentence_pause_ms: int = 300
    segment_pause_ms: int = 500
    music_fade_sec: float = 3.0
    output_sample_rate: int = 48000
    output_channels: int = 2


class VideoConfig(BaseModel):
    target_duration_min: int = 480
    target_duration_max: int = 600
    target_clips: int = 10
    clip_duration_min: int = 20
    clip_duration_max: int = 90
    resolution: str = "1920x1080"
    fps: int = 30
    codec: str = "libx264"
    crf: int = 20
    preset: str = "medium"
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"
    pixel_format: str = "yuv420p"
    transition_duration: float = 0.5
    fade_duration: float = 0.5
    max_source_duration_seconds: int = 3600
    clip_extraction_methods_priority: List[str] = ["most_replayed", "transcript", "audio_energy", "scene_detection"]
    shorts_count_per_video: int = 2
    shorts_duration_min: int = 30
    shorts_duration_max: int = 60


class DiscoveryConfig(BaseModel):
    lookback_hours: int = 6
    max_candidates_per_niche: int = 30
    min_views: int = 10000
    min_viral_score: float = 0.4
    youtube_daily_quota_limit: int = 10000
    reddit_subreddits: Dict[str, List[str]]
    reddit_min_score: int = 100
    scoring_weight_view_velocity: float = 0.30
    scoring_weight_reddit: float = 0.20
    scoring_weight_like_ratio: float = 0.15
    scoring_weight_comment_velocity: float = 0.15
    scoring_weight_recency: float = 0.20

    @model_validator(mode="after")
    def validate_scoring_weights(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        total_weight = sum(
            values.get(key, 0)
            for key in [
                "scoring_weight_view_velocity",
                "scoring_weight_reddit",
                "scoring_weight_like_ratio",
                "scoring_weight_comment_velocity",
                "scoring_weight_recency",
            ]
        )
        if not 0.99 <= total_weight <= 1.01:
            raise ValueError("Scoring weights must sum to approximately 1.0")
        return values


class ChannelConfig(BaseModel):
    name: str
    niche: str
    enabled: bool = True
    youtube_category_id: int
    youtube_credentials_file: str
    schedule_times_utc: List[str]
    voice: str
    hashtags: List[str]
    standard_tags: List[str]
    youtube_search_queries: List[str]


class TelegramConfig(BaseModel):
    bot_token: str
    authorized_user_ids: List[int]
    review_timeout_hours: int = 2
    reminder_after_hours: float = 1.0
    quiet_hours_start: int = 23
    quiet_hours_end: int = 7


class YouTubeUploadConfig(BaseModel):
    chunk_size_bytes: int = 10485760
    max_retries: int = 3
    default_privacy: str = "private"
    default_language: str = "en"


class SchedulerConfig(BaseModel):
    max_concurrent_pipelines: int = 2
    max_concurrent_downloads: int = 4
    max_concurrent_renders: int = 1
    job_store_path: str = "data/scheduler_jobs.sqlite"


class BrandingConfig(BaseModel):
    channel_display_name: str = "LAST SIX HOURS"
    font_path: str = "assets/fonts/default.ttf"
    title_font_size: int = 72
    label_font_size: int = 120
    lower_third_font_size: int = 36
    primary_color: str = "#FFFFFF"
    secondary_color: str = "#FFD700"
    background_color: str = "#000000"
    watermark_path: str = ""
    watermark_opacity: float = 0.3


class AppConfig(BaseModel):
    general: GeneralConfig
    llm: LLMConfig
    tts: TTSConfig
    audio: AudioConfig
    video: VideoConfig
    discovery: DiscoveryConfig
    channels: List[ChannelConfig]
    telegram: TelegramConfig
    youtube_upload: YouTubeUploadConfig
    scheduler: SchedulerConfig
    branding: BrandingConfig


def _substitute_env_vars(data: Union[Dict, List, str]) -> Union[Dict, List, str]:
    """
    Recursively substitute ${VAR_NAME} patterns in configuration values.

    Args:
        data (Union[Dict, List, str]): Configuration data.

    Returns:
        Union[Dict, List, str]: Configuration data with substituted environment variables.
    """
    if isinstance(data, dict):
        return {key: _substitute_env_vars(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_substitute_env_vars(item) for item in data]
    elif isinstance(data, str):
        matches = re.findall(r"\$\{(\w+)\}", data)
        for match in matches:
            env_value = os.getenv(match)
            if env_value is None:
                logger.warning(f"Environment variable {match} is not set. Keeping placeholder.")
            else:
                data = data.replace(f"${{{match}}}", env_value)
        return data
    return data


def load_config(path: str = "config/config.yaml") -> AppConfig:
    """
    Load configuration from YAML file with environment variable substitution.

    Args:
        path (str): Path to the YAML configuration file.

    Returns:
        AppConfig: Validated configuration object.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValidationError: If the configuration data is invalid.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file)

    substituted_config = _substitute_env_vars(raw_config)
    try:
        return AppConfig.model_validate(substituted_config)
    except ValidationError as e:
        logger.error("Configuration validation failed", exc_info=e)
        raise e