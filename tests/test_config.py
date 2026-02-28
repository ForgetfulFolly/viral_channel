import os
import tempfile
import pytest
import yaml
from pydantic import ValidationError
from unittest.mock import patch
from src.config import load_config, AppConfig, _substitute_env_vars


def test_load_valid_config():
    """Test loading a valid configuration file."""
    config_data = """
    general:
      project_name: "Test Project"
      log_level: "DEBUG"
      log_dir: "test_logs"
      working_dir: "test_working"
      archive_dir: "test_archive"
      timezone: "UTC"
    llm:
      primary:
        name: "test-llm"
        base_url: "http://test-llm.com"
        api_key: "test-key"
        model: "test-model"
        max_tokens: 1024
        temperature: 0.5
        timeout_seconds: 60
        max_retries: 2
    tts:
      primary_engine: "test-engine"
      fallback_engine: "test-fallback"
      engines:
        - name: "engine1"
          model_path: "path/to/model1"
          device: "cpu"
          sample_rate: 44100
      default_voice: "test-voice"
      voices:
        - name: "voice1"
          engine: "engine1"
          language: "en"
          speed: 1.2
    audio:
      narration_lufs: -20.0
      clip_audio_lufs: -25.0
      background_music_lufs: -30.0
      ducking_db: -10.0
      sentence_pause_ms: 400
      segment_pause_ms: 600
      music_fade_sec: 2.0
      output_sample_rate: 44100
      output_channels: 2
    video:
      target_duration_min: 300
      target_duration_max: 600
      target_clips: 8
      clip_duration_min: 15
      clip_duration_max: 60
      resolution: "1280x720"
      fps: 24
      codec: "libx265"
      crf: 23
      preset: "fast"
      audio_codec: "aac"
      audio_bitrate: "128k"
      pixel_format: "yuv420p"
      transition_duration: 0.3
      fade_duration: 0.3
      max_source_duration_seconds: 1800
      clip_extraction_methods_priority:
        - "transcript"
        - "scene_detection"
      shorts_count_per_video: 1
      shorts_duration_min: 10
      shorts_duration_max: 30
    discovery:
      lookback_hours: 12
      max_candidates_per_niche: 20
      min_views: 5000
      min_viral_score: 0.5
      youtube_daily_quota_limit: 5000
      reddit_subreddits:
        tech: ["technology", "programming"]
      reddit_min_score: 50
      scoring_weight_view_velocity: 0.3
      scoring_weight_reddit: 0.2
      scoring_weight_like_ratio: 0.2
      scoring_weight_comment_velocity: 0.2
      scoring_weight_recency: 0.1
    channels:
      - name: "Gaming"
        niche: "gaming"
        enabled: true
        youtube_category_id: 20
        youtube_credentials_file: "path/to/creds.json"
        schedule_times_utc: ["12:00", "18:00"]
        voice: "voice1"
        hashtags: ["#gaming", "#fun"]
        standard_tags: ["gameplay", "fun"]
        youtube_search_queries: ["best games", "top gaming moments"]
    telegram:
      bot_token: "test-bot-token"
      authorized_user_ids: [123456789, 987654321]
      review_timeout_hours: 3
      reminder_after_hours: 1.5
      quiet_hours_start: 22
      quiet_hours_end: 6
    youtube_upload:
      chunk_size_bytes: 5242880
      max_retries: 5
      default_privacy: "public"
      default_language: "en"
    scheduler:
      max_concurrent_pipelines: 3
      max_concurrent_downloads: 5
      max_concurrent_renders: 2
      job_store_path: "data/test_scheduler_jobs.sqlite"
    branding:
      channel_display_name: "TEST CHANNEL"
      font_path: "assets/fonts/test.ttf"
      title_font_size: 64
      label_font_size: 100
      lower_third_font_size: 32
      primary_color: "#FF0000"
      secondary_color: "#00FF00"
      background_color: "#0000FF"
      watermark_path: "path/to/watermark.png"
      watermark_opacity: 0.5
    """
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        temp_file.write(config_data.encode())
        temp_file_path = temp_file.name

    try:
        config = load_config(temp_file_path)
        assert isinstance(config, AppConfig)
        assert config.general.project_name == "Test Project"
        assert config.llm.primary.name == "test-llm"
        assert config.audio.narration_lufs == -20.0
        assert config.video.target_duration_min == 300
        assert config.discovery.scoring_weight_view_velocity == 0.3
    finally:
        os.remove(temp_file_path)


def test_missing_required_fields():
    """Test that missing required fields raise ValidationError."""
    invalid_config = """
    general:
      project_name: "Test Project"
    """
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        temp_file.write(invalid_config.encode())
        temp_file_path = temp_file.name

    try:
        with pytest.raises(ValidationError):
            load_config(temp_file_path)
    finally:
        os.remove(temp_file_path)


def test_environment_variable_substitution():
    """Test environment variable substitution in configuration."""
    config_data = """
    general:
      project_name: "${PROJECT_NAME}"
    """
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        temp_file.write(config_data.encode())
        temp_file_path = temp_file.name

    with patch.dict(os.environ, {"PROJECT_NAME": "Env Project"}):
        try:
            config = load_config(temp_file_path)
            assert config.general.project_name == "Env Project"
        finally:
            os.remove(temp_file_path)


def test_missing_environment_variable():
    """Test that missing environment variables keep the placeholder and log a warning."""
    config_data = """
    general:
      project_name: "${PROJECT_NAME}"
    """
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        temp_file.write(config_data.encode())
        temp_file_path = temp_file.name

    try:
        with patch("src.config.logger.warning") as mock_warning:
            config = load_config(temp_file_path)
            assert config.general.project_name == "${PROJECT_NAME}"
            mock_warning.assert_called_once_with(
                "Environment variable %s is not set. Using placeholder value.", "PROJECT_NAME"
            )
    finally:
        os.remove(temp_file_path)


def test_default_values():
    """Test that default values are applied when fields are omitted."""
    config_data = """
    general:
      project_name: "Default Test"
    """
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        temp_file.write(config_data.encode())
        temp_file_path = temp_file.name

    try:
        config = load_config(temp_file_path)
        assert config.general.log_level == "INFO"
        assert config.general.timezone == "UTC"
    finally:
        os.remove(temp_file_path)


def test_scoring_weights_validation():
    """Test that scoring weights must sum to approximately 1.0."""
    invalid_config = """
    discovery:
      scoring_weight_view_velocity: 0.5
      scoring_weight_reddit: 0.5
      scoring_weight_like_ratio: 0.2
      scoring_weight_comment_velocity: 0.2
      scoring_weight_recency: 0.2
    """
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        temp_file.write(invalid_config.encode())
        temp_file_path = temp_file.name

    try:
        with pytest.raises(ValidationError, match="Scoring weights must sum to approximately 1.0"):
            load_config(temp_file_path)
    finally:
        os.remove(temp_file_path)


def test_schedule_times_validation():
    """Test that invalid schedule times raise ValidationError."""
    invalid_config = """
    channels:
      - name: "Invalid Channel"
        niche: "test"
        youtube_category_id: 10
        schedule_times_utc: ["25:00", "12:60"]
        voice: "test-voice"
        hashtags: ["#test"]
        standard_tags: ["test"]
        youtube_search_queries: ["test query"]
    """
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        temp_file.write(invalid_config.encode())
        temp_file_path = temp_file.name

    try:
        with pytest.raises(ValidationError):
            load_config(temp_file_path)
    finally:
        os.remove(temp_file_path)