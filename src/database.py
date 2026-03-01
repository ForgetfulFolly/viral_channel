from sqlalchemy import (
    Column, Integer, String, Text, Float,
    DateTime, ForeignKey, Index, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .base import Base

class Clip(Base):
    __tablename__ = "clips"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pipeline_runs.id"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(512))
    duration_seconds: Mapped[float] = mapped_column(Float)
    start_time_seconds: Mapped[float] = mapped_column(Float)
    end_time_seconds: Mapped[float] = mapped_column(Float)

class Script(Base):
    __tablename__ = "scripts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pipeline_runs.id"), nullable=False
    )
    opening_text: Mapped[str | None] = mapped_column(Text)
    closing_text: Mapped[str | None] = mapped_column(Text)
    full_script_json: Mapped[str] = mapped_column(Text)
    total_char_count: Mapped[int] = mapped_column(Integer)
    estimated_duration_seconds: Mapped[float] = mapped_column(Float)
    llm_model_used: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.utc_timestamp()
    )

class TTSAudio(Base):
    __tablename__ = "tts_audio"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pipeline_runs.id"), nullable=False
    )
    engine_used: Mapped[str] = mapped_column(String(255))
    voice_profile: Mapped[str | None] = mapped_column(String(255))
    audio_file_path: Mapped[str | None] = mapped_column(String(512))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.utc_timestamp()
    )

class Short(Base):
    __tablename__ = "shorts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pipeline_runs.id"), nullable=False
    )
    clip_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("clips.id")
    )
    file_path: Mapped[str | None] = mapped_column(String(512))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    youtube_video_id: Mapped[str | None] = mapped_column(String(100))
    youtube_url: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(
        String(32), default="pending"
    )
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime)

class Analytics(Base):
    __tablename__ = "analytics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    youtube_video_id: Mapped[str] = mapped_column(String(100))
    measured_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.utc_timestamp()
    )
    view_count: Mapped[int | None] = mapped_column(Integer)
    like_count: Mapped[int | None] = mapped_column(Integer)
    comment_count: Mapped[int | None] = mapped_column(Integer)
    average_view_duration_seconds: Mapped[float | None] = mapped_column(Float)
    click_through_rate: Mapped[float | None] = mapped_column(Float)
    subscriber_gain: Mapped[int | None] = mapped_column(Integer)
    estimated_revenue_usd: Mapped[float | None] = mapped_column(Float)

Index("idx_analytics_video", Analytics.youtube_video_id, Analytics.measured_at)

class ReviewLog(Base):
    __tablename__ = "review_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pipeline_runs.id"), nullable=False
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.utc_timestamp()
    )
    responded_at: Mapped[datetime | None] = mapped_column(DateTime)
    action: Mapped[str | None] = mapped_column(String(255))
    response_detail: Mapped[str | None] = mapped_column(String(1024))
    auto_held: Mapped[int] = mapped_column(Integer, default=0)

class ConfigOverride(Base):
    __tablename__ = "config_overrides"
    
    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[str] = mapped_column(String(1024))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.utc_timestamp()
    )
    updated_by: Mapped[str] = mapped_column(
        String(64), default="system"
    )

class ErrorLog(Base):
    __tablename__ = "error_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_run_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pipeline_runs.id")
    )
    module: Mapped[str] = mapped_column(String(255))
    error_type: Mapped[str] = mapped_column(String(255))
    error_message: Mapped[str] = mapped_column(Text)
    stack_trace: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.utc_timestamp()
    )
    resolved: Mapped[int] = mapped_column(Integer, default=0)

Index("idx_error_log_module", ErrorLog.module, ErrorLog.occurred_at)

def init_db(engine):
    Base.metadata.create_all(bind=engine)

def get_session(engine):
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def get_pending_videos(session):
    return session.query(DiscoveredVideo).filter_by(processed=False).all()

def mark_video_processed(session, video_id):
    video = session.query(DiscoveredVideo).get(video_id)
    if video:
        video.processed = True
        session.commit()
    else:
        raise ValueError(f"Video with id {video_id} not found")

def log_error(session, module: str, error_type: str, error_message: str, stack_trace: str | None = None):
    error_log = ErrorLog(
        module=module,
        error_type=error_type,
        error_message=error_message,
        stack_trace=stack_trace
    )
    session.add(error_log)
    session.commit()