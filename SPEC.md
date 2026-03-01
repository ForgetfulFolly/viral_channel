## Problem Statement
The task is to build a YouTube Data API v3 client wrapper to enable integration with YouTube's API for both discovery (using an API key) and upload (using OAuth) functionalities. This will allow the application to discover trending videos, search for recent content, retrieve video details, scrape most replayed heatmap data, and perform video uploads with proper authentication handling.

## Functional Requirements
1. **FR-Discovery-01**: Implement `get_trending(region_code, category_id=None)` in `youtube_source.py` that returns a list of normalized dictionaries containing video metadata.
2. **FR-Discovery-02**: Implement `search_recent(query, published_after, max_results=50)` in `youtube_source.py` to search for recent videos based on the query and publication date.
3. **FR-Discovery-03**: Implement `get_video_details(video_ids: list[str])` in `youtube_source.py` to retrieve detailed information about specified video IDs.
4. **FR-Discovery-04**: Implement `get_most_replayed_heatmap(video_id)` in `youtube_source.py` that scrapes the YouTube player page for heatmap data and returns it or None if unavailable.
5. **FR-Discovery-05**: Track daily API quota usage and log warnings when 80% of the limit is reached.
6. **FR-Upload-01**: Implement `async upload_video(file_path, metadata: dict, credentials_file: str)` in `youtube_uploader.py` to upload a video file with specified metadata using resumable upload protocol.
7. **FR-Upload-02**: Implement `async set_thumbnail(video_id, thumbnail_path, credentials_file)` in `youtube_uploader.py` to set the thumbnail for an uploaded video.
8. **FR-Upload-03**: Implement `async update_video_status(video_id, privacy_status, credentials_file)` in `youtube_uploader.py` to update the privacy status of a video.
9. **FR-Upload-04**: Handle OAuth token refresh automatically without manual intervention.
10. **FR-OAuthSetup-01**: Create a CLI script `setup_youtube_oauth.py` that runs the OAuth consent flow and saves credentials to a specified JSON file.

## Non-Functional Requirements
1. **NFR-Performance-01**: Ensure upload operations use resumable upload protocol with configurable chunk sizes for efficient data transfer.
2. **NFR-Reliability-01**: Implement error handling for API rate limits, quota exceeded errors, and other common issues, including retries with backoff where appropriate.
3. **NFR-Security-01**: Never hardcode secrets; use environment variables or secure configuration files for storing API keys and OAuth credentials.
4. **NFR-Monitoring-01**: Implement structured logging with correlation IDs to facilitate tracking of API requests and responses across the system.
5. **NFR-Maintainability-01**: Use type hints on all function signatures and provide comprehensive docstrings for all public functions.

## Constraints
1. **C-Library-01**: Must use `google-api-python-client` and `google-auth-oauthlib` libraries for API interactions.
2. **C-Config-01**: API key and daily quota limit must be sourced from configuration files, not hardcoded.
3. **C-OAuth-01**: OAuth credentials file paths must be specified in per-channel configurations.
4. **C-NoEmojis-01**: No emojis are allowed in any metadata fields or log messages.
5. **C-ErrorHandling-01**: Handle API errors gracefully, including rate limits (retry with backoff) and quota exceeded errors (log and return empty results).

## Success Criteria
- [ ] Discovery functions (`get_trending`, `search_recent`, `get_video_details`, `get_most_replayed_heatmap`) return normalized dictionaries with specified fields.
- [ ] Quota tracking logs warnings at 80% of daily limit and handles quota exceeded errors gracefully.
- [ ] Upload operations use resumable upload protocol with configurable chunk sizes.
- [ ] OAuth token refresh is handled automatically without manual intervention.
- [ ] `get_most_replayed_heatmap` returns None when heatmap data is unavailable.
- [ ] Comprehensive test suite mocks Google API client and tests all core functionalities.

## Out of Scope
1. Implementing video scraping beyond the most replayed heatmap functionality.
2. Providing a UI for OAuth setup; only CLI script is required.
3. Supporting other APIs (e.g., Reddit, Twitter) as part of this task.
4. Handling video transcoding or processing before upload.

## Open Questions
1. Should exponential backoff be implemented for API retries? If yes, what parameters should be used?
2. How should chunk size be configured for resumable uploads? Should it be configurable via settings?
3. Are there specific regional considerations for the `get_trending` function beyond the provided region code?
4. How will quota usage be tracked across multiple API calls and instances?