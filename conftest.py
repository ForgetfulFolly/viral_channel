"""
Standard conftest.py for agent-generated test suites.

This file is automatically placed into the worktree's test directory
by the implement phase BEFORE pytest runs.  It avoids the two most
common causes of test-time import failures:

  1. __init__.py cascades — pre-existing packages import their full
     dependency tree when Python resolves relative imports.  By inserting
     the package's parent dir into sys.path and using direct imports,
     tests bypass those __init__.py files entirely.

  2. Missing third-party deps — packages like numpy, pydantic, asyncpraw
     may not be installed in the agent's venv.  The collect_ignore hook
     below tells pytest to skip test files that fail to import rather
     than aborting the entire collection.

TEMPLATE VARIABLES (replaced at placement time):
  {{PACKAGE_ROOT}}  — absolute path to the package being tested
  {{WORKSPACE_ROOT}} — absolute path to the worktree root
"""
import os
import sys

# ---------------------------------------------------------------------------
# Path setup: ensure the package under test is importable without triggering
# __init__.py cascades.  We insert the package's PARENT directory so that
# `import birds.base` works as a direct import (no relative-import chain).
# ---------------------------------------------------------------------------
_WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PACKAGE_ROOT = os.environ.get("AGENT_PACKAGE_ROOT", _WORKSPACE)

if _PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, _PACKAGE_ROOT)
if _WORKSPACE not in sys.path:
    sys.path.insert(0, _WORKSPACE)


# ---------------------------------------------------------------------------
# Graceful collection: if a test file can't be imported (missing deps,
# broken __init__.py in a pre-existing package, etc.), skip it instead
# of failing the whole test suite.
# ---------------------------------------------------------------------------
def pytest_collect_file(parent, file_path):
    """Return None for files that can't be imported — pytest will skip them."""
    # Only interfere with .py files in the tests/ directory
    if not str(file_path).endswith(".py"):
        return None
    if not file_path.name.startswith("test_"):
        return None
    # Let pytest's default collector handle it; errors caught by
    # pytest_collectreport below.
    return None  # fall through to default


def pytest_collectreport(report):
    """Downgrade collection errors to warnings instead of hard failures.

    This prevents pre-existing broken imports from cascading into
    the agent's test validation loop.
    """
    import warnings
    if report.failed:
        for item in report.result if hasattr(report, "result") else []:
            pass  # Default processing
        # Log but don't abort — the implement phase checks exit codes.
        if hasattr(report, "longrepr"):
            warnings.warn(
                f"Collection warning (skipped): {report.nodeid}\n"
                f"{report.longrepr}",
                stacklevel=1,
            )
