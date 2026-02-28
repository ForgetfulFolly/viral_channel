import os
import sys
import pytest
from sqlalchemy.orm import Session
from src.config import AppConfig, load_config
from src.database import init_db, get_session

# Add parent directory to sys.path to allow direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def config() -> AppConfig:
    """Fixture providing a test AppConfig instance."""
    return load_config('config/test_config.yaml')

@pytest.fixture
def db_engine():
    """Fixture providing an in-memory database engine."""
    engine = init_db(':memory:')
    return engine

@pytest.fixture
def db_session(db_engine) -> Session:
    """Fixture providing a database session with cleanup."""
    session = get_session(db_engine)
    try:
        yield session
        session.rollback()
    finally:
        session.close()