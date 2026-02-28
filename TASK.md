# Task: Fix tests/conftest.py imports to match actual module exports

Priority: 1
Status: design-in-progress
Created: 2026-02-28T02:01:00Z
Scope: tests/conftest.py

## Description
The tests/conftest.py file was created during project scaffolding with placeholder
imports that do not match the actual implementations from Phase 0.

Current conftest.py contents:
\\\python
import pytest
from src.config import Config
from src.database import Database

@pytest.fixture
def config():
    return Config()

@pytest.fixture
def database(config):
    return Database(config)
\\\

### Problems to fix:

1. \rom src.config import Config\ -- there is no \Config\ class.
   The actual class is \AppConfig\ and the loader function is \load_config()\.
   See src/config.py for the actual exports.

2. \rom src.database import Database\ -- there is no \Database\ class.
   The actual database module exports: \Base\, \init_db(db_path)\, \get_session(engine)\,
   and model classes (\DiscoveredVideo\, \PipelineRun\, \Clip\, etc.).
   See src/database.py for the actual exports.

3. The \config()\ fixture calls \Config()\ which does not exist. It should use
   \load_config()\ with a test config path, or create an \AppConfig\ with test defaults.

4. The \database(config)\ fixture calls \Database(config)\ which does not exist.
   It should use \init_db()\ with a temporary SQLite path (e.g., \:memory:\) and
   provide a \get_session(engine)\ based fixture. Consider yielding a session that
   rolls back after each test for isolation.

### What the fixed conftest.py should provide:

- A \config\ fixture that returns a valid AppConfig for testing (use a minimal
  config/config.yaml or construct AppConfig with test defaults)
- A \db_engine\ fixture that creates an in-memory SQLite database using \init_db( :memory:)\
- A \db_session\ fixture that provides a Session from the engine, with cleanup after test
- Proper imports matching actual module exports

## Acceptance Criteria
- [ ] conftest.py imports match actual exports from src/config.py and src/database.py
- [ ] config fixture returns a valid AppConfig instance
- [ ] db_engine fixture creates an in-memory SQLite database with all tables
- [ ] db_session fixture provides a Session with rollback cleanup
- [ ] Running \python -c import tests.conftest\ does not raise ImportError
- [ ] All existing tests in tests/test_config.py still pass

## Critical Constraints
- Only modify tests/conftest.py (do NOT modify src/config.py or src/database.py)
- Use :memory: SQLite for test database (no files left behind)
- Keep fixtures simple and reusable
- No emojis in any output

## Reference Files
- src/config.py (actual config module with AppConfig, load_config)
- src/database.py (actual database module with init_db, get_session, model classes)
