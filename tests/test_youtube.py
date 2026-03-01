import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from typing import List, Dict, Optional

# Mocking the YouTubeSource and VideoMetadata classes
class MockYouTubeSource:
    def __init__(self, config):
        self.config = config
        self.quota_used = 0
        self.daily_limit = config.daily_quota_limit

    def get_trending(self, region_code: str, category_id: Optional[str] = None) -> List[Dict]:
        return [
            {
                "video_id": "123",
                "title": "Test Video",
                "channel_name": "Test Channel",
                "channel_id": "456",
                "view_count": 100,
                "like_count": 50,
                "comment_count": 10,
                "published_at": datetime.now().isoformat(),
                "duration": "PT1H30M",
                "category_id": category_id or "7",
                "url": "https://www.youtube.com/watch?v=123"
            }
        ]

    def search_recent(self, query: str, published_after: datetime, max_results: int = 50) -> List[Dict]:
        return [
            {
                "video_id": "456",
                "title": "Recent Video",
                "channel_name": "Another Channel",
                "channel_id": "789",
                "view_count": 200,
                "like_count": 100,
                "comment_count": 20,
                "published_at": published_after.isoformat(),
                "duration": "PT2H",
                "category_id": "10",
                "url": "https://www.youtube.com/watch?v=456"
            }
        ]

    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        return [
            {
                "video_id": video_id,
                "title": f"Video {video_id}",
                "channel_name": "Test Channel",
                "channel_id": "456",
                "view_count": 100,
                "like_count": 50,
                "comment_count": 10,
                "published_at": datetime.now().isoformat(),
                "duration": "PT1H30M",
                "category_id": "7",
                "url": f"https://www.youtube.com/watch?v={video_id}"
            } for video_id in video_ids
        ]

    def get_most_replayed_heatmap(self, video_id: str) -> Optional[List[Dict]]:
        return None

class TestYouTubeWrapper(unittest.TestCase):
    @patch('googleapiclient.discovery.build')
    def setUp(self, mock_build):
        self.mock_youtube = MagicMock()
        mock_build.return_value = self.mock_youtube
        self.youtube_source = MockYouTubeSource(config=MagicMock(daily_quota_limit=1000))

    def test_get_trending(self):
        region_code = "US"
        category_id = "7"
        trending_videos = self.youtube_source.get_trending(region_code, category_id)
        self.assertEqual(len(trending_videos), 1)
        video = trending_videos[0]
        self.assertEqual(video["video_id"], "123")
        self.assertEqual(video["title"], "Test Video")
        self.assertEqual(video["channel_name"], "Test Channel")
        self.assertEqual(video["category_id"], category_id)

    def test_search_recent(self):
        query = "test"
        published_after = datetime.now()
        recent_videos = self.youtube_source.search_recent(query, published_after)
        self.assertEqual(len(recent_videos), 1)
        video = recent_videos[0]
        self.assertEqual(video["video_id"], "456")
        self.assertEqual(video["title"], "Recent Video")
        self.assertEqual(video["channel_name"], "Another Channel")

    def test_get_video_details(self):
        video_ids = ["123", "456"]
        video_details = self.youtube_source.get_video_details(video_ids)
        self.assertEqual(len(video_details), 2)
        for i, video in enumerate(video_details):
            self.assertEqual(video["video_id"], video_ids[i])
            self.assertEqual(video["title"], f"Video {video_ids[i]}")

    def test_get_most_replayed_heatmap(self):
        video_id = "123"
        heatmap_data = self.youtube_source.get_most_replayed_heatmap(video_id)
        self.assertIsNone(heatmap_data)

if __name__ == '__main__':
    unittest.main()