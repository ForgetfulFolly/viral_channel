## Problem Statement

The project requires a consistent and reliable way to handle video and audio processing tasks using FFmpeg. Currently, these operations are performed directly via subprocess calls throughout the codebase, leading to repetitive code and potential inconsistencies in error handling and output formatting. This task aims to create a centralized utility module that wraps common FFmpeg operations, ensuring consistency, reducing redundancy, and improving maintainability.

## Functional Requirements

1. **FR-1**: Implement an `extract_clip` function that extracts a video clip from a given input file with optional fade-in/out effects.
2. **FR-2**: Implement a `normalize_audio` function to normalize the audio of a media file to a specified target LUFS level.
3. **FR-3**: Implement a `get_media_info` function that retrieves metadata (duration, resolution, codec, FPS, audio channels) from a media file using FFprobe and returns it as a dictionary.
4. **FR-4**: Implement an `extract_audio` function to extract the audio track from a video file into a specified format (e.g., WAV).
5. **FR-5**: Implement a `concat_videos` function that concatenates multiple video files with optional transition effects between clips.
6. **FR-6**: Implement an `overlay_text` function to overlay text on a video file at a specified position, font, size, and color.
7. **FR-7**: Implement an `overlay_image` function to overlay an image on a video file at a specified position and duration.
8. **FR-8**: Implement a `scene_detect` function that detects scene changes in a video file based on a specified threshold and returns timestamps of detected scenes.
9. **FR-9**: Implement a `create_silent_audio` function to generate a silent audio file of a specified duration and sample rate.
10. **FR-10**: Implement a `mix_audio_tracks` function that mixes multiple audio tracks with specified volumes and start times into a single output file.
11. **FR-11**: Implement a `render_video` function that assembles a video from multiple inputs using FFmpeg's filter graph capabilities, applying specified resolution, FPS, codec settings, etc.
12. **FR-12**: Ensure all functions validate input file existence before executing FFmpeg commands and raise clear exceptions on failure.

## Non-Functional Requirements

1. **Performance**: The utility must efficiently handle large video and audio files without significant performance degradation.
2. **Reliability**: Robust error handling with detailed logging of FFmpeg stderr output to aid in debugging.
3. **Maintainability**: All functions must include type hints and comprehensive docstrings for clarity and ease of maintenance.
4. **Security**: Avoid hardcoding any sensitive information; use environment variables where necessary.

## Constraints

1. Must use `subprocess.run` to execute FFmpeg commands, not Python bindings like `ffmpeg-python`.
2. Always include the `-y` flag to overwrite output files without prompts.
3. Use `-hide_banner -loglevel error` flags to clean up FFmpeg's output.
4. Default timeout is 600 seconds, configurable per function.
5. Input file existence must be validated before executing commands.
6. No emojis in error messages.

## Success Criteria

- [ ] All listed functions (FR-1 to FR-12) are implemented and tested.
- [ ] `get_media_info` correctly parses FFprobe JSON output into a dictionary.
- [ ] Error handling includes FFmpeg stderr in exception messages.
- [ ] All functions have type hints and docstrings.
- [ ] Comprehensive tests cover each function, including command construction mocks and error handling.

## Out of Scope

1. Implementing a user interface for the utility module.
2. Adding new FFmpeg features not listed in the functional requirements.
3. Supporting alternative video processing tools like `moviepy`.
4. Providing a GUI or CLI wrapper around the utility functions.

## Open Questions

1. Are there additional FFmpeg flags that should be configurable beyond the defaults?
2. Should any of the functions support parallel execution for performance optimization?