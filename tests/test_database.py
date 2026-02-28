from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from src.database import (
    Base,
    DiscoveredVideo,
    PipelineRun,
    Clip,
    init_db,
    get_session,
    get_pending_videos,
    mark_video_processed,
    log_error,
)
from datetime import datetime, timedelta
import pytest
import os


@pytest.fixture(scope="module")
def test_engine():
    """Fixture to create a temporary SQLite database for testing."""
    engine = init_db("sqlite:///:memory:")
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Fixture to create a new session for each test."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


def test_table_creation(test_engine):
    """Test that all tables are created in the database."""
    inspector = inspect(test_engine)
    tables = inspector.get_table_names()

    expected_tables = [
        "discovered_videos",
        "pipeline_runs",
        "clips",
        "scripts",
        "tts_audio",
        "shorts",
        "analytics",
        "review_log",
        "config_override",
        "error_log",
    ]

    for table in expected_tables:
        assert table in tables, f"Table {table} was not created."


def test_insert_and_query_discovered_video(db_session: Session):
    """Test inserting and querying a DiscoveredVideo."""
    video = DiscoveredVideo(
        video_id="abc123",
        title="Test Video",
        channel_name="Test Channel",
        channel_id="channel123",
        url="https://youtube.com/watch?v=abc123",
        niche="gaming",
        discovered_at=datetime.utcnow(),
    )
    db_session.add(video)
    db_session.commit()

    queried_video = db_session.query(DiscoveredVideo).filter_by(video_id="abc123").first()
    assert queried_video is not None
    assert queried_video.title == "Test Video"
    assert queried_video.processed == 0  # Default value


def test_foreign_key_relationships(db_session: Session):
    """Test foreign key relationships between Clip, PipelineRun, and DiscoveredVideo."""
    pipeline_run = PipelineRun(
        niche="gaming",
        cycle_start=datetime.utcnow(),
        cycle_end=datetime.utcnow() + timedelta(hours=1),
    )
    db_session.add(pipeline_run)
    db_session.commit()

    video = DiscoveredVideo(
        video_id="xyz789",
        title="Another Test Video",
        channel_name="Another Channel",
        channel_id="channel456",
        url="https://youtube.com/watch?v=xyz789",
        niche="gaming",
        discovered_at=datetime.utcnow(),
    )
    db_session.add(video)
    db_session.commit()

    clip = Clip(
        pipeline_run_id=pipeline_run.id,
        discovered_video_id=video.id,
        rank_position=1,
        start_time_seconds=0.0,
        end_time_seconds=10.0,
        clip_duration_seconds=10.0,
    )
    db_session.add(clip)
    db_session.commit()

    queried_clip = db_session.query(Clip).filter_by(id=clip.id).first()
    assert queried_clip is not None
    assert queried_clip.pipeline_run_id == pipeline_run.id
    assert queried_clip.discovered_video_id == video.id


def test_helper_get_pending_videos(db_session: Session):
    """Test the get_pending_videos helper function."""
    video1 = DiscoveredVideo(
        video_id="vid1",
        title="Pending Video 1",
        channel_name="Channel A",
        channel_id="chanA",
        url="https://youtube.com/watch?v=vid1",
        niche="sports",
        processed=0,
        discovered_at=datetime.utcnow(),
    )
    video2 = DiscoveredVideo(
        video_id="vid2",
        title="Pending Video 2",
        channel_name="Channel B",
        channel_id="chanB",
        url="https://youtube.com/watch?v=vid2",
        niche="sports",
        processed=1,
        discovered_at=datetime.utcnow(),
    )
    db_session.add_all([video1, video2])
    db_session.commit()

    pending_videos = get_pending_videos(db_session, "sports")
    assert len(pending_videos) == 1
    assert pending_videos[0].video_id == "vid1"


def test_helper_mark_video_processed(db_session: Session):
    """Test the mark_video_processed helper function."""
    video = DiscoveredVideo(
        video_id="vid3",
        title="Video to Process",
        channel_name="Channel C",
        channel_id="chanC",
        url="https://youtube.com/watch?v=vid3",
        niche="music",
        processed=0,
        discovered_at=datetime.utcnow(),
    )
    db_session.add(video)
    db_session.commit()

    mark_video_processed(db_session, "vid3", 1)
    updated_video = db_session.query(DiscoveredVideo).filter_by(video_id="vid3").first()
    assert updated_video is not None
    assert updated_video.processed == 1


def test_helper_log_error(db_session: Session):
    """Test the log_error helper function."""
    log_error(
        db_session,
        module="test_module",
        error_type="TestError",
        message="This is a test error.",
        pipeline_run_id=None,
        stack_trace="Traceback (most recent call last)...",
    )

    error = db_session.query(ErrorLog).filter_by(module="test_module").first()
    assert error is not None
    assert error.error_type == "TestError"
    assert error.error_message == "This is a test error."
    assert error.resolved == 0  # Default value


def test_index_existence(test_engine):
    """Test that all required indexes are created."""
    inspector = inspect(test_engine)
    indexes = {index["name"] for table in inspector.get_table_names() for index in inspector.get_indexes(table)}

    expected_indexes = {
        "idx_discovered_videos_niche",
        "idx_discovered_videos_processed",
        "idx_pipeline_runs_status",
        "idx_pipeline_runs_niche",
        "idx_clips_pipeline",
        "idx_analytics_video",
        "idx_error_log_module",
    }

    for index in expected_indexes:
        assert index in indexes, f"Index {index} was not created."