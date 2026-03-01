## Problem Statement
The goal is to build a Reddit API client that discovers viral YouTube content by analyzing posts on specific subreddits. This will enable the "Last SiX Hours" pipeline to identify trending videos for compilation.

## Functional Requirements
1. FR-1: Implement `RedditSource` class initialized with config parameters (client_id, client_secret, user_agent).
2. FR-2: Implement `get_viral_youtube_links` method that:
   - Accepts list of subreddits, min_score, and max_age_hours.
   - Scans hot + rising posts from specified subreddits.
   - Extracts YouTube video IDs from various URL formats.
3. FR-3: Support extraction of YouTube video IDs from URLs in these formats:
   - `youtube.com/watch?v=`
   - `youtu.be/`
   - `youtube.com/shorts/`
4. FR-4: Filter posts based on:
   - Minimum score threshold
   - Maximum age (in hours)
5. FR-5: Return list of dictionaries containing these fields for each qualifying post:
   - reddit_post_id
   - youtube_video_id
   - youtube_url
   - post_title
   - subreddit
   - score
   - num_comments
   - created_utc
   - upvote_ratio

## Non-Functional Requirements
1. Performance: Handle up to 1000 posts per hour without exceeding Reddit's rate limits.
2. Reliability: Implement retry logic with exponential backoff for API errors.
3. Security: Use environment variables for credentials, avoid hardcoding.
4. Logging: Use structured logging with correlation IDs.
5. Maintainability: Follow PEP 8, use type hints, comprehensive docstrings.

## Constraints
1. Must use PRAW (Python Reddit API Wrapper) for Reddit API access.
2. Read-only access only - no posting, voting, or other write operations.
3. No emojis allowed in log messages.
4. Only handle YouTube URLs as specified - ignore other video platforms.
5. Dependencies: praw, requests

## Success Criteria
- [ ] `RedditSource` class is implemented with proper initialization
- [ ] `get_viral_youtube_links` method correctly scans and filters posts
- [ ] URL extraction handles all required formats
- [ ] Posts without YouTube links are skipped silently
- [ ] Rate limiting is handled gracefully
- [ ] Comprehensive test coverage including edge cases

## Out of Scope
1. Processing video content (handled by other modules)
2. Non-YouTube links (e.g., Twitch, Vimeo)
3. Video download or processing
4. User authentication flows beyond initial config
5. Caching or persistence of Reddit data

## Open Questions
1. What subreddits should be the default list?
2. How to handle posts that have multiple YouTube URLs?
3. Should we track seen posts to avoid duplicates?