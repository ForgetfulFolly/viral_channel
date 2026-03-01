import os
import logging
from typing import List, Optional, Dict
from datetime import datetime
import googleapiclient.discovery
from googleapiclient.errors import HttpError
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

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

class YouTubeConfig(BaseModel):
    api_key: str
    daily_quota_limit: int

class YouTubeSource:
    def __init__(self, config: YouTubeConfig):
        self.config = config
        self.quota_used = 0
        self.daily_limit = config.daily_quota_limit
        self.youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=config.api_key)

    def _track_quota_usage(self, units: int) -> None:
        """Track and log API quota usage."""
        self.quota_used += units
        if self.quota_used >= 0.8 * self.daily_limit:
            logger.warning(f"Quota usage is at {self.quota_used / self.daily_limit * 100:.2f}% of daily limit.")

    def _normalize_video_data(self, video_item: Dict) -> VideoMetadata:
        """Normalize video data from API response."""
        snippet = video_item['snippet']
        statistics = video_item.get('statistics', {})
        content_details = video_item.get('contentDetails', {})

        return VideoMetadata(
            video_id=video_item['id'],
            title=snippet['title'],
            channel_name=snippet['channelTitle'],
            channel_id=snippet['channelId'],
            view_count=int(statistics.get('viewCount', 0)),
            like_count=int(statistics.get('likeCount', 0)) if 'likeCount' in statistics else None,
            comment_count=int(statistics.get('commentCount', 0)) if 'commentCount' in statistics else None,
            published_at=datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')),
            duration=content_details.get('duration', ''),
            category_id=snippet.get('categoryId'),
            url=f"https://www.youtube.com/watch?v={video_item['id']}"
        )

    def get_trending(self, region_code: str, category_id: Optional[str] = None) -> List[Dict]:
        """Retrieve trending videos for the specified region and category."""
        try:
            request = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                chart='mostPopular',
                regionCode=region_code,
                videoCategoryId=category_id,
                maxResults=50
            )
            response = request.execute()
            self._track_quota_usage(1)
            return [self._normalize_video_data(item).dict() for item in response.get('items', [])]
        except HttpError as e:
            logger.error(f"An HTTP error occurred: {e}")
            return []

    def search_recent(self, query: str, published_after: datetime, max_results: int = 50) -> List[Dict]:
        """Search for recent videos matching the query."""
        try:
            request = self.youtube.search().list(
                part='snippet',
                q=query,
                type='video',
                publishedAfter=published_after.isoformat('T') + 'Z',
                maxResults=max_results
            )
            response = request.execute()
            self._track_quota_usage(1)
            video_ids = [item['id']['videoId'] for item in response.get('items', [])]
            return self.get_video_details(video_ids)
        except HttpError as e:
            logger.error(f"An HTTP error occurred: {e}")
            return []

    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """Get detailed information about specified video IDs."""
        try:
            request = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(video_ids)
            )
            response = request.execute()
            self._track_quota_usage(1)
            return [self._normalize_video_data(item).dict() for item in response.get('items', [])]
        except HttpError as e:
            logger.error(f"An HTTP error occurred: {e}")
            return []

    def get_most_replayed_heatmap(self, video_id: str) -> Optional[List[Dict]]:
        """Scrape and return most replayed heatmap data for a video."""
        # This function is not implemented as it requires web scraping which is out of scope.
        logger.warning("get_most_replayed_heatmap is not implemented and returns None.")
        return None