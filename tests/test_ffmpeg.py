import sys
import os
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path
from typing import Dict, List
from src.utils.ffmpeg import (
    extract_clip,
    normalize_audio,
    get_media_info,
    extract_audio,
    concat_videos,
    overlay_text,
    overlay_image,
    scene_detect,
    create_silent_audio,
    mix_audio_tracks,
    render_video
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def mock_subprocess_run(*args, **kwargs):
    result = MagicMock()
    result.returncode = 0
    result.stderr = b""
    return result

def mock_ffprobe_output():
    return b'{"format": {"duration": "123.456", "tags": {}},"streams": [{"codec_type": "video", "width": 1920, "height": 1080, "avg_frame_rate": "60/1"}, {"codec_type": "audio", "channels": 2}]}'

@pytest.fixture
def mock_subprocess(monkeypatch):
    monkeypatch.setattr('subprocess.run', mock_subprocess_run)

@pytest.fixture
def mock_ffprobe(monkeypatch):
    def mock_ffprobe_command(*args, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stdout = mock_ffprobe_output()
        return result
    monkeypatch.setattr('subprocess.run', mock_ffprobe_command)

def test_get_media_info(mock_ffprobe):
    path = Path("test_video.mp4")
    info = get_media_info(path)
    assert isinstance(info, dict)
    assert info['duration'] == 123.456
    assert info['resolution'] == (1920, 1080)
    assert info['codec'] == 'h264'
    assert info['fps'] == 60.0
    assert info['audio_channels'] == 2

def test_extract_clip(mock_subprocess):
    input_path = Path("input.mp4")
    output_path = Path("output.mp4")
    result = extract_clip(input_path, output_path, start_sec=10, end_sec=20)
    assert result == output_path

def test_normalize_audio(mock_subprocess):
    input_path = Path("input.mp3")
    output_path = Path("output.mp3")
    result = normalize_audio(input_path, output_path, target_lufs=-16)
    assert result == output_path

def test_extract_audio(mock_subprocess):
    input_path = Path("input.mp4")
    output_path = Path("output.wav")
    result = extract_audio(input_path, output_path, format='wav')
    assert result == output_path

def test_concat_videos(mock_subprocess):
    input_paths = [Path("clip1.mp4"), Path("clip2.mp4")]
    output_path = Path("concatenated.mp4")
    result = concat_videos(input_paths, output_path)
    assert result == output_path

def test_overlay_text(mock_subprocess):
    input_path = Path("input.mp4")
    output_path = Path("output.mp4")
    result = overlay_text(
        input_path,
        output_path,
        text="Hello",
        position="(10, 10)",
        font_path="/path/to/font.ttf",
        font_size=24,
        color="white"
    )
    assert result == output_path

def test_overlay_image(mock_subprocess):
    input_path = Path("input.mp4")
    output_path = Path("output.mp4")
    image_path = Path("image.png")
    result = overlay_image(input_path, output_path, image_path, position="(10, 10)")
    assert result == output_path

def test_scene_detect(mock_subprocess):
    input_path = Path("input.mp4")
    timestamps = scene_detect(input_path)
    assert isinstance(timestamps, list)

def test_create_silent_audio(mock_subprocess):
    output_path = Path("silent.mp3")
    result = create_silent_audio(output_path, duration_sec=10)
    assert result == output_path

def test_mix_audio_tracks(mock_subprocess):
    tracks = [
        {"path": "track1.mp3", "volume_db": 0, "start_sec": 0},
        {"path": "track2.mp3", "volume_db": -5, "start_sec": 5}
    ]
    output_path = Path("mixed.mp3")
    result = mix_audio_tracks(tracks, output_path)
    assert result == output_path

def test_render_video(mock_subprocess):
    inputs = {
        "video": "input.mp4",
        "audio": "input.mp3"
    }
    output_path = Path("rendered.mp4")
    result = render_video(
        inputs,
        output_path,
        resolution="1920x1080",
        fps=60,
        codec="libx264",
        crf=23,
        audio_codec="aac",
        audio_bitrate="192k"
    )
    assert result == output_path

def test_error_handling(mock_subprocess):
    def mock_subprocess_run_with_error(*args, **kwargs):
        result = MagicMock()
        result.returncode = 1
        result.stderr = b"FFmpeg error message"
        return result

    monkeypatch.setattr('subprocess.run', mock_subprocess_run_with_error)
    input_path = Path("input.mp4")
    output_path = Path("output.mp4")

    with pytest.raises(Exception, match="FFmpeg error message"):
        extract_clip(input_path, output_path, start_sec=10, end_sec=20)