# Task: Create structured logging utility

Priority: 2
State: queued
Created: 2026-02-28T01:03:00Z
Depends-On: agent/task-20260228010000-create-project-scaffolding
Scope: src/utils/logging.py, tests/test_logging.py

## Description

Create a logging utility module that provides structured logging for all pipeline
modules. The utility outputs human-readable logs to the console (stderr) and
machine-parsable JSON-lines logs to rotating files.

### Implementation in src/utils/logging.py:

**Functions:**

```python
def setup_logging(
    log_dir: str,
    log_level: str = "INFO",
    module_name: str = "viral_channel"
) -> logging.Logger:
    """
    Configure and return a Logger instance.

    Sets up two handlers:
    1. StreamHandler (stderr): Human-readable format for development
       Format: "{timestamp} [{level}] {module}: {message}"
       Example: "2026-02-28 12:05:33 [INFO] discovery: Found 24 candidate videos"

    2. RotatingFileHandler: JSON-lines format for machine parsing
       File: {log_dir}/{module_name}.log
       Max size: 10 MB per file
       Backup count: 5 rotated files
       Each line is a JSON object: {"timestamp": "...", "level": "...",
       "module": "...", "message": "...", "extra": {...}}
    """
```

**Custom Formatter Classes:**

```python
class ConsoleFormatter(logging.Formatter):
    """Human-readable log formatter for console output."""

class JsonFormatter(logging.Formatter):
    """JSON-lines formatter for file output."""
    # Each log record formatted as a single JSON line
    # Fields: timestamp (ISO 8601), level, module, message, extra
    # Extra data: any additional kwargs passed via logger.info("msg", extra={"key": "val"})
```

**Helper:**

```python
def get_logger(module_name: str) -> logging.Logger:
    """
    Get a child logger for a specific module.
    Usage: logger = get_logger("discovery.youtube")
    Returns a logger that inherits handlers from the root viral_channel logger.
    """
```

### Design Details:

1. The root logger name is "viral_channel"
2. Child loggers use dot notation: "viral_channel.discovery", "viral_channel.tts"
3. get_logger("discovery") returns logging.getLogger("viral_channel.discovery")
4. setup_logging should be called ONCE at application startup
5. Log directory is created if it does not exist (os.makedirs with exist_ok=True)
6. Console level can differ from file level (console shows INFO+, file shows DEBUG+)
7. JSON formatter handles extra fields from LogRecord properly
8. Timestamps are always UTC in ISO 8601 format

### tests/test_logging.py:

Write tests covering:
- setup_logging creates the log directory if it does not exist
- Console formatter produces correct human-readable format
- JSON formatter produces valid JSON on each line
- JSON output includes timestamp, level, module, message fields
- Extra fields appear in the JSON output under "extra" key
- RotatingFileHandler is configured with correct max_bytes and backup_count
- get_logger returns a child logger with the correct name
- Multiple calls to get_logger with same name return same logger instance

## Acceptance Criteria

- [ ] setup_logging returns a configured Logger with both console and file handlers
- [ ] Console output is human-readable (not JSON)
- [ ] File output is JSON-lines format (one JSON object per line)
- [ ] JSON lines include: timestamp, level, module, message, extra
- [ ] Log rotation configured: 10 MB max, 5 backups
- [ ] Log directory created automatically if missing
- [ ] get_logger returns child loggers under "viral_channel" namespace
- [ ] tests/test_logging.py has at least 6 test functions

## Critical Constraints

- Use Python standard logging module ONLY (no loguru, structlog, etc.)
- No emojis in any log output, format strings, or examples
- Timestamps are UTC, ISO 8601 format (e.g., "2026-02-28T12:05:33Z")
- Module name included in every log line (both console and file)
- File handler uses RotatingFileHandler (not TimedRotatingFileHandler)
- Do NOT import from any other src/ module (logging utility has no internal dependencies)
- The logging module file is src/utils/logging.py (using Python's logging under the hood)

## Reference Files

- SPEC.md (Section 12 -- Error Handling and Monitoring)
- DESIGN.md (Section 4, Task T04)
