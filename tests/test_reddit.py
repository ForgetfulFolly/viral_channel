import datetime
from unittest.mock import Mock, patch

import pytest

from src.config import DiscoveryConfig
from src.discovery.reddit_source import RedditSource


@pytest.fixture
def mock_config():
    return DiscoveryConfig(
        reddit_client_id="test_id",
        reddit_client_secret="test_secret",
        user_agent="test_agent",
        subreddits=["youtube", "shorts"],
    )


@pytest.fixture
def reddit_source(mock_config):
    with patch("praw.Reddit") as mock_reddit:
        yield RedditSource(mock_config)


class TestURLExtraction:
    def test_extract_youtube_id_watch_url(self):
        url = "https://www.youtube.com/watch?v=abc123&feature=emb Logo"
        expected = "abc123"
        assert RedditSource._extract_youtube_id(url) == expected

    def test_extract_youtube_id_shorts_url(self):
        url = "https://youtu.be/xyz789?t=10"
        expected = "xyz789"
        assert RedditSource._extract_youtube_id(url) == expected

    def test_extract_youtube_id_embed_url(self):
        url = "https://www.youtube.com/embed/def456"
        expected = "def456"
        assert RedditSource._extract_youtube_id(url) == expected

    def test_extract_youtube_id_invalid_format(self):
        url = "https://www.youtube.com/someotherpath"
        with pytest.raises(ValueError):
            RedditSource._extract_youtube_id(url)

    def test_has_youtube_url_watch(self):
        assert RedditSource._has_youtube_url("https://youtube.com/watch?v=123")

    def test_has_youtube_url_shorts(self):
        assert RedditSource._has_youtube_url("https://youtu.be/456")

    def test_has_youtube_url_embed(self):
        assert RedditSource._has_youtube_url("https://youtube.com/embed/789")

    def test_has_youtube_url_non_youtube(self):
        assert not RedditSource._has_youtube_url("https://example.com")


class TestFiltering:
    @pytest.mark.asyncio
    async def test_get_viral_links_filters_by_min_score(self, reddit_source):
        mock_submission = Mock()
        mock_submission.score = 500
        min_score = 600

        result = await reddit_source.get_viral_youtube_links(
            subreddits=["test"],
            min_score=min_score,
            max_age_hours=24,
        )

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_viral_links_filters_by_max_age(self, reddit_source):
        mock_submission = Mock()
        mock_submission.created_utc = datetime.datetime.utcnow().timestamp() - (25 * 3600)
        max_age = 24

        result = await reddit_source.get_viral_youtube_links(
            subreddits=["test"],
            min_score=1,
            max_age_hours=max_age,
        )

        assert len(result) == 0


class TestAPIInteractions:
    @pytest.mark.asyncio
    async def test_get_viral_links_fetches_hot_and_rising(self, reddit_source):
        mock_subreddit = Mock()
        mock_hot = [Mock(), Mock()]
        mock_rising = [Mock(), Mock()]

        with patch.object(reddit_source.reddit.subreddit.return_value, "hot", return_value=mock_hot) as mock_hot_method:
            with patch.object(
                reddit_source.reddit.subreddit.return_value,
                "rising",
                return_value=mock_rising,
            ) as mock_rising_method:

                await reddit_source.get_viral_youtube_links(
                    subreddits=["test"],
                    min_score=1,
                    max_age_hours=24,
                )

        mock_hot_method.assert_called_once()
        mock_rising_method.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_viral_links_skips_non_youtube_posts(self, reddit_source):
        mock_submission = Mock()
        mock_submission.url = "https://example.com"
        mock_submission.score = 1000

        with patch.object(reddit_source.reddit.subreddit.return_value.hot, "__aiter__", return_value=iter([mock_submission])):
            result = await reddit_source.get_viral_youtube_links(
                subreddits=["test"],
                min_score=500,
                max_age_hours=24,
            )

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_viral_links_returns_expected_fields(self, reddit_source):
        mock_submission = Mock()
        mock_submission.id = "123"
        mock_submission.url = "https://youtu.be/abc"
        mock_submission.title = "Test Title"
        mock_submission.score = 500
        mock_submission.num_comments = 10
        mock_submission.created_utc = datetime.datetime.utcnow().timestamp()
        mock_submission.upvote_ratio = 0.8

        with patch.object(reddit_source.reddit.subreddit.return_value.hot, "__aiter__", return_value=iter([mock_submission])):
            result = await reddit_source.get_viral_youtube_links(
                subreddits=["test"],
                min_score=1,
                max_age_hours=24,
            )

        assert len(result) == 1
        post = result[0]
        assert post["reddit_post_id"] == "123"
        assert post["youtube_video_id"] == "abc"
        assert post["post_title"] == "Test Title"