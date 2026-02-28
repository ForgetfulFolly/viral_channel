# Task: Build Reddit API client for viral content discovery

Priority: 3
Status: pending
Created: 2026-02-28T02:06:00Z
Depends-On: agent/task-20260228020100-fix-conftest-imports
Scope: src/discovery/reddit_source.py, tests/test_reddit.py

## Description
Create a Reddit viral content discovery module using PRAW.

Implement src/discovery/reddit_source.py:
- RedditSource class initialized with config (client_id, client_secret, user_agent)
- get_viral_youtube_links(subreddits: list[str], min_score: int, max_age_hours: int) -> list[dict]
  Scans subreddits for posts with YouTube links, filters by score and age.
  Returns list of dicts with: reddit_post_id, youtube_video_id, youtube_url,
  post_title, subreddit, score, num_comments, created_utc, upvote_ratio
- Extract YouTube video IDs from various URL formats:
  youtube.com/watch?v=, youtu.be/, youtube.com/shorts/

## Acceptance Criteria
- [ ] RedditSource initializes a PRAW Reddit instance
- [ ] get_viral_youtube_links scans hot+rising posts from given subreddits
- [ ] YouTube URL extraction handles all common formats (watch, youtu.be, shorts, embed)
- [ ] Posts without YouTube links are silently skipped
- [ ] Rate limiting is handled by PRAW internally
- [ ] tests/test_reddit.py mocks PRAW and tests: URL extraction for all formats,
      filtering by score/age, handling of non-YouTube posts

## Critical Constraints
- Use PRAW (Python Reddit API Wrapper)
- Credentials come from config (client_id, client_secret, user_agent)
- Read-only access (no posting, no voting)
- No emojis in log messages

## Reference Files
- SPEC.md (Section 4.1)
- src/config.py (DiscoveryConfig for reddit_client_id, reddit_client_secret, subreddits)
