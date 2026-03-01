# YouTube Data API v3 Client Wrapper Design

## Architecture Overview

```
Mermaid
graph TD
    A[youtube_source.py] --> B[google-api-python-client]
    C[youtube_uploader.py] --> D[google-auth-oauthlib]
    E[setup_youtube_oauth.py] --> D
    F[src/config.py] --> A
    F --> C
    F --> E
```

## Components

### youtube_source.py (Discovery)
- **Purpose**: Provide API key-based YouTube discovery methods.
- **Location**: src/discovery/youtube_source.py
- **Dependencies**:
  - google-api-python-client
  - src/config.py (YouTubeConfig)
- **Interfaces**:
  - `get_trending(region_code: str, category_id: Optional[str] = None) -> List[Dict]`
  - `search_recent(query: str, published_after: datetime, max_results: int = 50) -> List[Dict]`
  - `get_video_details(video_ids: List[str]) -> List[Dict]`
  - `get_most_replayed_heatmap(video_id: str) -> Optional[List[Dict]]`

### youtube_uploader.py (Upload)
- **Purpose**: Handle OAuth-based YouTube uploads and video management.
- **Location**: src/upload/youtube_uploader.py
- **Dependencies**:
  - google-api-python-client
  - google-auth-oauthlib
  - src/config.py (YouTubeUploadConfig)
- **Interfaces**:
  - `async upload_video(file_path: str, metadata: Dict, credentials_file: str) -> str`
  - `async set_thumbnail(video_id: str, thumbnail_path: str, credentials_file: str) -> bool`
  - `async update_video_status(video_id: str, privacy_status: str, credentials_file: str) -> bool`

### setup_youtube_oauth.py (OAuth Setup)
- **Purpose**: CLI script to run OAuth consent flow and save credentials.
- **Location**: scripts/setup_youtube_oauth.py
- **Dependencies**:
  - google-auth-oauthlib
  - src/config.py (ChannelConfig)

## Interface Definitions

```python
from typing import List, Optional, Dict
from datetime import datetime

class YouTubeSource:
    def __init__(self, config: YouTubeConfig):
        self.config = config
        self.quota_used = 0
        self.daily_limit = config.daily_quota_limit

    def get_trending(self, region_code: str, category_id: Optional[str] = None) -> List[Dict]:
        """Retrieve trending videos for the specified region and category."""
        pass

    def search_recent(self, query: str, published_after: datetime, max_results: int = 50) -> List[Dict]:
        """Search for recent videos matching the query."""
        pass

    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """Get detailed information about specified video IDs."""
        pass

    def get_most_replayed_heatmap(self, video_id: str) -> Optional[List[Dict]]:
        """Scrape and return most replayed heatmap data for a video."""
        pass
```

```python
from typing import Dict
import asyncio

class YouTubeUploader:
    async def upload_video(
        self,
        file_path: str,
        metadata: Dict,
        credentials_file: str
    ) -> str:
        """Upload a video file with specified metadata using resumable upload."""
        pass

    async def set_thumbnail(
        self,
        video_id: str,
        thumbnail_path: str,
        credentials_file: str
    ) -> bool:
        """Set the thumbnail for an uploaded video."""
        pass

    async def update_video_status(
        self,
        video_id: str,
        privacy_status: str,
        credentials_file: str
    ) -> bool:
        """Update the privacy status of a video."""
        pass
```

## Data Models

```python
from pydantic import BaseModel, Field
from datetime import datetime

class VideoMetadata(BaseModel):
    video_id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Video title")
    channel_name: str = Field(..., description="Channel name")
    channel_id: str = Field(..., description="Channel ID")
    view_count: int = Field(..., description="Total views")
    like_count: Optional[int] = Field(None, description="Likes count")
    comment_count: Optional[int] = Field(None, description="Comments count")
    published_at: datetime = Field(..., description="Publication timestamp")
    duration: str = Field(..., description="Video duration in ISO 8601 format")
    category_id: Optional[str] = Field(None, description="Category ID")
    url: str = Field(..., description="Watch URL")
```

## File Changes

| Action | Path | Description |
|--------|------|-------------|
| CREATE | src/discovery/youtube_source.py | Discovery methods using API key |
| CREATE | src/upload/youtube_uploader.py | Upload methods with OAuth support |
| CREATE | scripts/setup_youtube_oauth.py | CLI script for OAuth setup |
| MODIFY | tests/test_youtube.py | Add test cases for YouTube wrapper |

## Test Strategy

1. **Discovery Tests**:
   - Mock `googleapiclient.discovery.build` to simulate API responses.
   - Test normalization of video metadata across all discovery methods.
   - Verify quota tracking and warning logging.

2. **Upload Tests**:
   - Mock OAuth client and YouTube API for upload operations.
   - Test resumable upload flow with mocked file handling.
   - Validate token refresh behavior.

3. **OAuth Setup Tests**:
   - Test CLI script end-to-end with mocked OAuth consent flow.
   - Verify credentials are saved to the correct file path.

## Implementation Order

1. Implement `youtube_source.py` with discovery methods and quota tracking.
2. Create `setup_youtube_oauth.py` CLI script for OAuth setup.
3. Develop `youtube_uploader.py` with async upload functionality.
4. Update `src/config.py` to include YouTube configuration models.
5. Write comprehensive test suite in `tests/test_youtube.py`.

## Risk Analysis

### Risks
1. **API Key Exposure**:
   - **Mitigation**: Use environment variables and secure config files.
2. **Rate Limiting**:
   - **Mitigation**: Implement exponential backoff with max retries.
3. **OAuth Token Refresh**:
   - **Mitigation**: Use `google-auth-oauthlib` built-in refresh mechanism.
4. **Scraping Most Replayed Heatmap**:
   - **Mitigation**: Handle missing data gracefully and log errors.

### Mitigations
- All sensitive data is sourced from configuration files or environment variables.
- Comprehensive error handling with retries for API calls.
- Structured logging for quota usage, API errors, and OAuth flows.