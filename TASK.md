# Task: Build YouTube Data API v3 client wrapper

Priority: 2
Status: implement-in-progress
Created: 2026-02-28T02:05:00Z
Depends-On: agent/task-20260228020100-fix-conftest-imports
Scope: src/discovery/youtube_source.py, src/upload/youtube_uploader.py, scripts/setup_youtube_oauth.py, tests/test_youtube.py

## Description
Create two YouTube API wrapper modules:

1. src/discovery/youtube_source.py -- Discovery (uses API key, no OAuth):
   - get_trending(region_code, category_id=None) -> list[dict]
   - search_recent(query, published_after, max_results=50) -> list[dict]
   - get_video_details(video_ids: list[str]) -> list[dict]
   - get_most_replayed_heatmap(video_id) -> list[dict] | None
     (scrapes the YouTube player page, not an API call)
   - Track quota usage internally (log warnings at 80% of daily limit)

2. src/upload/youtube_uploader.py -- Upload (uses OAuth):
   - async upload_video(file_path, metadata: dict, credentials_file: str) -> str
     (returns YouTube video ID, uses resumable upload)
   - async set_thumbnail(video_id, thumbnail_path, credentials_file) -> bool
   - async update_video_status(video_id, privacy_status, credentials_file) -> bool
   - Handle OAuth token refresh automatically

3. scripts/setup_youtube_oauth.py -- One-time setup:
   - CLI script that runs the OAuth consent flow
   - Saves credentials to the specified JSON file
   - Usage: python scripts/setup_youtube_oauth.py --output config/youtube_gaming_creds.json

## Acceptance Criteria
- [ ] Discovery functions return normalized dicts with: video_id, title, channel_name,
      channel_id, view_count, like_count, comment_count, published_at, duration, category_id, url
- [ ] Quota tracking logs a warning when 80% of daily_quota_limit is reached
- [ ] Upload uses resumable upload protocol with configurable chunk size
- [ ] OAuth token refresh is handled automatically (no manual re-auth)
- [ ] Most Replayed scraper handles videos without heatmap data (returns None)
- [ ] tests/test_youtube.py mocks google API client and tests: trending parsing,
      search result normalization, quota tracking, upload flow, token refresh

## Critical Constraints
- Use google-api-python-client and google-auth-oauthlib
- API key and quota limit come from config
- OAuth credentials file paths come from per-channel config
- No emojis in any metadata or log messages
- Handle API errors gracefully (rate limit -> retry with backoff, quota exceeded -> log and return empty)

## Reference Files
- SPEC.md (Sections 4.1, 4.8, 14.3)
- src/config.py (YouTubeUploadConfig, ChannelConfig for configuration)
