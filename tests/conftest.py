import pytest
from src.config import Config
from src.database import Database

@pytest.fixture
def config():
    """Fixture providing base configuration"""
    return Config()

@pytest.fixture
def database(config):
    """Fixture providing database interface"""
    return Database(config)