import os
from sqlalchemy import (
    create_engine, String, Integer, Float, Text, DateTime, ForeignKey, Index, Column
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker
from sqlalchemy.engine import Engine
from datetime import datetime
from typing import Optional, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass

# Models
class DiscoveredVideo(Base):
    __tablename__ = "discovered_videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    channel_name: Mapped[str] = mapped_column(String, nullable=False)
    channel_id: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    view_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    like_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comment_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    view_velocity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    viral_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    niche: Mapped[str] = mapped_column(String, nullable=False)
    discovery_source: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    content_id_risk: Mapped[str] = mapped_column(String, default="unknown")

    __table_args__ = (
        Index("idx_discovered_videos_niche", "niche", "discovered_at"),
        Index("idx_discovered_videos_processed", "processed"),
    )

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    niche: Mapped[str] = mapped_column(String, nullable=False)
    cycle_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cycle_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    video_file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    video_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    video_file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    youtube_video_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    youtube_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        Index("idx_pipeline_runs_status", "status"),
        Index("idx_pipeline_runs_niche", "niche", "cycle_start"),
    )

class Clip(Base):
    __tablename__ = "clips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pipeline_run_id: Mapped[int] = mapped_column(ForeignKey("pipeline_runs.id"), nullable=False)
    discovered_video_id: Mapped[int] = mapped_column(ForeignKey("discovered_videos.id"), nullable=False)
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    clip_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    extraction_method: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    clip_file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content_id_risk: Mapped[str] = mapped_column(String, default="unknown")

    __table_args__ = (
        Index("idx_clips_pipeline", "pipeline_run_id"),
    )

# Helper Functions
def init_db(db_path: str) -> Engine:
    """
    Create SQLAlchemy engine, create all tables and indexes.
    Returns the Engine instance.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        Engine: SQLAlchemy Engine instance.
    """
    try:
        if not db_path:
            raise ValueError("Database path cannot be empty.")
        engine = create_engine(f"sqlite:///{db_path}", echo=False, future=True)
        Base.metadata.create_all(engine)
        logger.info("Database initialized successfully.")
        return engine
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def get_session(engine: Engine) -> Session:
    """
    Create and return a new Session bound to the engine.

    Args:
        engine (Engine): SQLAlchemy Engine instance.

    Returns:
        Session: SQLAlchemy Session instance.
    """
    try:
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        return SessionLocal()
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise

def get_pending_videos(session: Session, niche: str) -> List[DiscoveredVideo]:
    """
    Get all videos with processed=0 for the given niche.

    Args:
        session (Session): SQLAlchemy Session instance.
        niche (str): The niche to filter videos by.

    Returns:
        List[DiscoveredVideo]: List of pending videos for the given niche.
    """
    try:
        if not niche:
            raise ValueError("Niche cannot be empty.")
        return session.query(DiscoveredVideo).filter_by(niche=niche, processed=0).all()
    except Exception as e:
        logger.error(f"Failed to fetch pending videos for niche '{niche}': {e}")
        raise

def mark_video_processed(session: Session, video_id: str, status: int) -> None:
    """
    Update a video's processed status (1=used, 2=skipped, 3=rejected).

    Args:
        session (Session): SQLAlchemy Session instance.
        video_id (str): The ID of the video to update.
        status (int): The new processed status.

    Raises:
        ValueError: If the video ID is empty or the video is not found.
    """
    try:
        if not video_id:
            raise ValueError("Video ID cannot be empty.")
        video = session.query(DiscoveredVideo).filter_by(video_id=video_id).first()
        if not video:
            raise ValueError(f"Video with ID {video_id} not found.")
        video.processed = status
        session.commit()
        logger.info(f"Video {video_id} marked as processed with status {status}.")
    except Exception as e:
        logger.error(f"Failed to mark video {video_id} as processed: {e}")
        session.rollback()
        raise

def log_error(session: Session, module: str, error_type: str, message: str,
              pipeline_run_id: Optional[int] = None, stack_trace: Optional[str] = None) -> None:
    """
    Insert an error into the error_log table.

    Args:
        session (Session): SQLAlchemy Session instance.
        module (str): The module where the error occurred.
        error_type (str): The type of error.
        message (str): The error message.
        pipeline_run_id (Optional[int], optional): The pipeline run ID associated with the error. Defaults to None.
        stack_trace (Optional[str], optional): The stack trace of the error. Defaults to None.

    Raises:
        ValueError: If required fields are empty.
    """
    try:
        if not module or not error_type or not message:
            raise ValueError("Module, error type, and message cannot be empty.")
        error = ErrorLog(
            module=module,
            error_type=error_type,
            error_message=message,
            stack_trace=stack_trace,
            pipeline_run_id=pipeline_run_id,
            occurred_at=datetime.utcnow(),
            resolved=0
        )
        session.add(error)
        session.commit()
        logger.info(f"Error logged in module {module}: {message}")
    except Exception as e:
        logger.error(f"Failed to log error in module {module}: {e}")
        session.rollback()
        raise