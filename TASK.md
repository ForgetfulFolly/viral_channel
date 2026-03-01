# Task: Create FFmpeg utility wrapper for video and audio operations

Priority: 2
Status: spec-in-progress
Created: 2026-02-28T02:04:00Z
Depends-On: agent/task-20260228020100-fix-conftest-imports
Scope: src/utils/ffmpeg.py, tests/test_ffmpeg.py

## Description
Create a utility module that wraps common FFmpeg operations used throughout
the pipeline. All video and audio processing goes through this module.

Implement these functions (all call ffmpeg via subprocess):
- extract_clip(input_path, output_path, start_sec, end_sec, fade_sec=0.5) -> Path
- normalize_audio(input_path, output_path, target_lufs=-16) -> Path
- get_media_info(path) -> dict  (duration, resolution, codec, fps, audio_channels)
- extract_audio(input_path, output_path, format= wav) -> Path
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
