import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional

import praw
from praw.models.reddit.subreddit import Subreddit

from config import DiscoveryConfig

logger = logging.getLogger(__name__)


class RedditSource:
    """A class to interact with the Reddit API and discover viral YouTube content.

    Attributes:
        reddit: PRAW instance configured with provided credentials.
    """

    def __init__(self, config: DiscoveryConfig) -> None:
        """Initialize RedditSource with PRAW instance using configuration.

        Args:
            config: Configuration containing Reddit API credentials and settings.
        """
        self.reddit = praw.Reddit(
            client_id=config.reddit_client_id,
            client_secret=config.reddit_client_secret,
            user_agent=config.user_agent
        )
        logger.info("Initialized RedditSource with user agent %s", config.user_agent)

    async def get_viral_youtube_links(
        self,
        subreddits: List[str],
        min_score: int,
        max_age_hours: int
    ) -> List[Dict]:
        """Scan specified subreddits for viral YouTube links.

        Args:
            subreddits: List of subreddits to scan.
            min_score: Minimum score a post must have to be considered.
            max_age_hours: Maximum age in hours for posts to be included.

        Returns:
            List of dictionaries containing details of qualifying posts.

        Raises:
            ValueError: If URL format is unsupported or extraction fails.
        """
        posts = []
        current_time = datetime.now(timezone.utc)

        for subreddit_name in subreddits:
            subreddit = await self.reddit.subreddit(subreddit_name)
            logger.info("Scanning subreddit %s", subreddit_name)

            async for submission in subreddit.hot():
                if await self._should_include_post(
                    submission, min_score, max_age_hours, current_time
                ):
                    try:
                        youtube_id = self._extract_youtube_id(submission.url)
                        post_data = {
                            'reddit_post_id': submission.id,
                            'youtube_video_id': youtube_id,
                            'youtube_url': submission.url,
                            'post_title': submission.title,
                            'subreddit': subreddit_name,
                            'score': submission.score,
                            'num_comments': submission.num_comments,
                            'created_utc': datetime.utcfromtimestamp(submission.created_utc),
                            'upvote_ratio': submission.upvote_ratio
                        }
                        posts.append(post_data)
                    except ValueError as e:
                        logger.warning("Unsupported YouTube URL format: %s", submission.url)
                        continue

            async for submission in subreddit.rising():
                if await self._should_include_post(
                    submission, min_score, max_age_hours, current_time
                ):
                    try:
                        youtube_id = self._extract_youtube_id(submission.url)
                        post_data = {
                            'reddit_post_id': submission.id,
                            'youtube_video_id': youtube_id,
                            'youtube_url': submission.url,
                            'post_title': submission.title,
                            'subreddit': subreddit_name,
                            'score': submission.score,
                            'num_comments': submission.num_comments,
                            'created_utc': datetime.utcfromtimestamp(submission.created_utc),
                            'upvote_ratio': submission.upvote_ratio
                        }
                        posts.append(post_data)
                    except ValueError as e:
                        logger.warning("Unsupported YouTube URL format: %s", submission.url)
                        continue

        return posts

    async def _should_include_post(
        self,
        submission,
        min_score: int,
        max_age_hours: int,
        current_time: datetime
    ) -> bool:
        """Determine if a post should be included based on criteria.

        Args:
            submission: Reddit submission to evaluate.
            min_score: Minimum score required.
            max_age_hours: Maximum allowed age in hours.
            current_time: Current UTC time for age calculation.

        Returns:
            Boolean indicating whether the post meets all criteria.
        """
        if submission.score < min_score:
            return False

        submission_time = datetime.utcfromtimestamp(submission.created_utc)
        age = (current_time - submission_time).total_seconds() / 3600
        if age > max_age_hours:
            return False

        if not self._has_youtube_url(submission.url):
            return False

        return True

    @staticmethod
    def _has_youtube_url(url: str) -> bool:
        """Check if the URL is a YouTube video link.

        Args:
            url: URL to check.

        Returns:
            Boolean indicating whether the URL is a YouTube video.
        """
        patterns = [
            r'^https?://(?:www\.)?youtube\.com/watch\?v=',
            r'^https?://youtu\.be/',
            r'^https?://(?:www\.)?youtube\.com/shorts/'
        ]
        return any(re.match(pattern, url) for pattern in patterns)

    @staticmethod
    def _extract_youtube_id(url: str) -> str:
        """Extract YouTube video ID from URL.

        Args:
            url: URL containing the YouTube video.

        Returns:
            Extracted YouTube video ID.

        Raises:
            ValueError: If URL format is unsupported or extraction fails.
        """
        if 'v=' in url:
            return url.split('v=')[1].split('&')[0]
        elif '/be/' in url or '/shorts/' in url:
            parts = url.split('/')
            video_id_part = parts[-1].split('?')[0]
            # Handle cases where the path might have additional segments
            if len(video_id_part) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', video_id_part):
                return video_id_part
            else:
                raise ValueError("Invalid YouTube ID format in URL")
        else:
            raise ValueError("Unsupported YouTube URL format")

    async def close(self) -> None:
        """Close the RedditSource instance and clean up resources."""
        # PRAW doesn't require explicit cleanup, but this method is provided for symmetry
        logger.info("Closing RedditSource instance")