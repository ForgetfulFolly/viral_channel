# FFmpeg Utility Wrapper Design Document

## Architecture Overview

```
ffmpeg_utils
├── ffmpeg.py
│   ├── extract_clip()
│   ├── normalize_audio()
│   ├── get_media_info()
│   ├── extract_audio()
│   ├── concat_videos()
│   ├── overlay_text()
│   ├── overlay_image()
│   ├── scene_detect()
│   ├── create_silent_audio()
│   ├── mix_audio_tracks()
│   └── render_video()
└── tests/
    └── test_ffmpeg.py
```

## Components

- **ffmpeg_utils (src/utils/ffmpeg.py)**
  - Purpose: Central utility module for FFmpeg operations
  - Dependencies:
    - subprocess.run
    - pathlib.Path
    - json
    - typing
  - Functions:
    - extract_clip()
    - normalize_audio()
    - get_media_info()
    - extract_audio()
    - concat_videos()
    - overlay_text()
    - overlay_image()
    - scene_detect()
    - create_silent_audio()
    - mix_audio_tracks()
    - render_video()

## Interface Definitions

```python
from typing import Dict, List, Optional
from pathlib import Path

def extract_clip(
    input_path: Path,
    output_path: Path,
    start_sec: float,
    end_sec: float,
    fade_sec: float = 0.5,
    timeout: int = 600
) -> Path:
    """Extract video clip with optional fade effects."""
    ...

def normalize_audio(
    input_path: Path,
    output_path: Path,
    target_lufs: float = -16,
    timeout: int = 600
) -> Path:
    """Normalize audio to specified LUFS level."""
    ...

def get_media_info(path: Path) -> Dict[str, any]:
    """Get media metadata using ffprobe."""
    ...

def extract_audio(
    input_path: Path,
    output_path: Path,
    format: str = 'wav',
    timeout: int = 600
) -> Path:
    """Extract audio from video file."""
    ...
```

## Data Models

```python
from dataclasses import dataclass

@dataclass
class MediaInfo:
    duration: float
    resolution: tuple[int, int]
    codec: str
    fps: float
    audio_channels: int
```

## File Changes

| Action | Path                          | Description                                   |
|--------|-------------------------------|-----------------------------------------------|
| CREATE | src/utils/ffmpeg.py           | FFmpeg utility wrapper implementation         |
| CREATE | tests/test_ffmpeg.py          | Test cases for ffmpeg utilities               |

## Test Strategy

1. Unit Tests (tests/test_ffmpeg.py)
   - Mock subprocess.run to test command construction
   - Validate error handling with mocked exceptions
   - Test input validation
   - Verify return types and values

2. Integration Tests
   - Run against sample media files
   - Validate output file existence and format
   - Check audio/video properties using ffprobe

## Implementation Order

1. Create ffmpeg.py skeleton
2. Implement core functions (extract_clip, normalize_audio)
3. Add get_media_info with ffprobe parsing
4. Implement remaining utility functions
5. Write test cases
6. Integrate tests into CI/CD pipeline

## Risk Analysis

- **Risk:** Incorrect FFmpeg command syntax
  - Mitigation: Thorough testing of command construction
                Use subprocess.run with proper argument formatting

- **Risk:** Security vulnerabilities
  - Mitigation: Validate all input paths
                Use environment variables for sensitive data
                Avoid shell=True in subprocess calls

- **Risk:** Performance issues
  - Mitigation: Set timeouts per function
                Monitor resource usage during CI/CD tests
```