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

    def __post_init__(self):
        """Validate fields after initialization."""
        if not self.reddit_post_id:
            raise ValueError("reddit_post_id cannot be empty")
        if not self.youtube_video_id:
            raise ValueError("youtube_video_id cannot be empty")
        if not self.youtube_url:
            raise ValueError("youtube_url cannot be empty")
        if not self.post_title:
            raise ValueError("post_title cannot be empty")
        if not self.subreddit:
            raise ValueError("subreddit cannot be empty")