## Architecture Overview

```
mermaid
graph TD
  A[RedditSource] --> B[PRAW Reddit API]
  A --> C[DiscoveryConfig]
  A --> D{get_viral_youtube_links}
  D --> E[URL extraction]
  D --> F[Filtering]
  D --> G[List of dicts]
```

## Components

1. **RedditSource Class**
   - Purpose: Initialize PRAW Reddit instance with config and provide method to fetch viral YouTube links
   - Location: src/discovery/reddit_source.py
   - Dependencies:
     - praw
     - config.DiscoveryConfig

2. **get_viral_youtube_links Method**
   - Purpose: Scan subreddits for posts containing YouTube links, filter by score/age, and return structured data
   - Location: src/discovery/reddit_source.py
   - Dependencies:
     - praw.models.reddit.subreddit.Subreddit
     - datetime for age calculation

3. **URL Extraction Helper**
   - Purpose: Extract YouTube video IDs from various URL formats
   - Location: src/discovery/reddit_source.py
   - Dependencies:
     - re (regular expressions)

4. **DiscoveryConfig**
   - Purpose: Configuration model for Reddit API credentials and settings
   - Location: src/config.py
   - Dependencies:
     - pydantic BaseModel

## Interface Definitions

```python
class RedditSource:
    def __init__(self, config: DiscoveryConfig) -> None:
        """Initialize RedditSource with PRAW instance."""
        self.reddit = praw.Reddit(
            client_id=config.reddit_client_id,
            client_secret=config.reddit_client_secret,
            user_agent=config.user_agent
        )

    async def get_viral_youtube_links(
        self,
        subreddits: list[str],
        min_score: int,
        max_age_hours: int
    ) -> list[dict]:
        """Scan subreddits for viral YouTube links."""
        posts = []
        
        for subreddit in subreddits:
            # Get hot and rising posts
            for post_type in ['hot', 'rising']:
                async for submission in getattr(self.reddit.subreddit(subreddit), post_type):
                    if (submission.score >= min_score 
                        and (datetime.utcnow() - datetime.utcfromtimestamp(submission.created_utc)).total_seconds() / 3600 <= max_age_hours
                        and self._has_youtube_url(submission.url)):
                        posts.append({
                            'reddit_post_id': submission.id,
                            'youtube_video_id': self._extract_youtube_id(submission.url),
                            'youtube_url': submission.url,
                            'post_title': submission.title,
                            'subreddit': subreddit,
                            'score': submission.score,
                            'num_comments': submission.num_comments,
                            'created_utc': submission.created_utc,
                            'upvote_ratio': submission.upvote_ratio
                        })
        
        return posts

    @staticmethod
    def _has_youtube_url(url: str) -> bool:
        """Check if URL contains YouTube video."""
        youtube_patterns = [
            r'^https?://(?:www\.)?youtube\.com/watch\?v=',
            r'^https?://youtu\.be/',
            r'^https?://(?:www\.)?youtube\.com/shorts/'
        ]
        
        return any(re.match(pattern, url) for pattern in youtube_patterns)

    @staticmethod
    def _extract_youtube_id(url: str) -> str:
        """Extract YouTube video ID from URL."""
        if 'v=' in url:
            return url.split('v=')[1].split('&')[0]
        elif '/be/' in url or '/shorts/' in url:
            return url.split('/')[-1].split('?')[0]
        else:
            raise ValueError("Unsupported YouTube URL format")
```

## Data Models

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class RedditPostData:
    """Data model for a Reddit post containing YouTube link."""
    reddit_post_id: str
    youtube_video_id: str
    youtube_url: str
    post_title: str
    subreddit: str
    score: int
    num_comments: int
    created_utc: datetime
    upvote_ratio: float
```

## File Changes

| Action | Path | Description |
|--------|------|-------------|
| CREATE | src/discovery/reddit_source.py | Implementation of RedditSource class and helper methods |
| CREATE | src/discovery/dataclasses.py | Data model for Reddit post data |
| MODIFY | tests/test_reddit.py | Unit tests for URL extraction, filtering, and API interactions |

## Test Strategy

1. **Unit Tests**
   - Mock PRAW responses to test:
     - URL extraction from various formats
     - Filtering by score/age
     - Skipping non-YouTube posts
     - Error handling for invalid URLs
   - Verify structured output matches expected schema

2. **Integration Tests**
   - Test against real Reddit API with test credentials
   - Validate rate limiting behavior
   - Ensure proper retry logic on API errors

## Implementation Order

1. Create src/discovery/dataclasses.py with RedditPostData
2. Implement src/discovery/reddit_source.py:
   - __init__ method
   - get_viral_youtube_links
   - _has_youtube_url
   - _extract_youtube_id
3. Write tests in tests/test_reddit.py
4. Add test fixtures for PRAW mock responses

## Risk Analysis

1. **Rate Limiting**
   - *Risk*: Exceed Reddit API rate limits
   - *Mitigation*: Use PRAW's built-in retry logic and exponential backoff

2. **URL Extraction Errors**
   - *Risk*: Incorrect YouTube ID extraction from URLs
   - *Mitigation*: Comprehensive regex patterns covering all URL formats

3. **Configuration Issues**
   - *Risk*: Missing or invalid credentials in config
   - *Mitigation*: Validate configuration at initialization time