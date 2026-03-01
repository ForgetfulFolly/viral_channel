import os
import re
from datetime import datetime, timedelta
from typing import List, Dict

import praw
from praw.models import Submission
from pydantic import BaseModel

from src.config import DiscoveryConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)

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
        subreddits: List[str],
        min_score: int,
        max_age_hours: int
    ) -> List[Dict]:
        """Scan subreddits for viral YouTube links.

        Args:
            subreddits (List[str]): List of subreddit names to scan.
            min_score (int): Minimum score threshold for posts.
            max_age_hours (int): Maximum age in hours for posts.

        Returns:
            List[Dict]: List of dictionaries containing post data with YouTube links.
        """
        posts = []
        max_age = datetime.utcnow() - timedelta(hours=max_age_hours)

        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                for submission in subreddit.hot(limit=100):
                    if await self._is_valid_post(submission, min_score, max_age):
                        youtube_url = submission.url
                        youtube_video_id = self._extract_youtube_id(youtube_url)
                        posts.append({
                            'reddit_post_id': submission.id,
                            'youtube_video_id': youtube_video_id,
                            'youtube_url': youtube_url,
                            'post_title': submission.title,
                            'subreddit': subreddit_name,
                            'score': submission.score,
                            'num_comments': submission.num_comments,
                            'created_utc': submission.created_utc,
                            'upvote_ratio': submission.upvote_ratio
                        })
                for submission in subreddit.rising(limit=100):
                    if await self._is_valid_post(submission, min_score, max_age):
                        youtube_url = submission.url
                        youtube_video_id = self._extract_youtube_id(youtube_url)
                        posts.append({
                            'reddit_post_id': submission.id,
                            'youtube_video_id': youtube_video_id,
                            'youtube_url': youtube_url,
                            'post_title': submission.title,
                            'subreddit': subreddit_name,
                            'score': submission.score,
                            'num_comments': submission.num_comments,
                            'created_utc': submission.created_utc,
                            'upvote_ratio': submission.upvote_ratio
                        })
            except praw.exceptions.PRAWException as e:
                logger.error(f"Error accessing subreddit {subreddit_name}: {e}")

        return posts

    async def _is_valid_post(
        self,
        submission: Submission,
        min_score: int,
        max_age: datetime
    ) -> bool:
        """Check if a post is valid based on score and age.

        Args:
            submission (Submission): PRAW Submission object.
            min_score (int): Minimum score threshold.
            max_age (datetime): Maximum age for posts.

        Returns:
            bool: True if the post is valid, False otherwise.
        """
        created_utc = datetime.utcfromtimestamp(submission.created_utc)
        return (submission.score >= min_score and
                created_utc >= max_age and
                self._has_youtube_url(submission.url))

    @staticmethod
    def _has_youtube_url(url: str) -> bool:
        """Check if URL contains a YouTube video.

        Args:
            url (str): URL to check.

        Returns:
            bool: True if the URL is a YouTube link, False otherwise.
        """
        youtube_patterns = [
            r'^https?://(?:www\.)?youtube\.com/watch\?v=',
            r'^https?://youtu\.be/',
            r'^https?://(?:www\.)?youtube\.com/shorts/'
        ]
        return any(re.match(pattern, url) for pattern in youtube_patterns)

    @staticmethod
    def _extract_youtube_id(url: str) -> str:
        """Extract YouTube video ID from URL.

        Args:
            url (str): URL containing the YouTube link.

        Returns:
            str: YouTube video ID.

        Raises:
            ValueError: If the URL format is unsupported.
        """
        if 'v=' in url:
            return url.split('v=')[1].split('&')[0]
        elif '/be/' in url or '/shorts/' in url:
            return url.split('/')[-1].split('?')[0]
        else:
            raise ValueError("Unsupported YouTube URL format")