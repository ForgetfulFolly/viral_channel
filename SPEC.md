# Task: Fix tests/conftest.py imports to match actual module exports

## Problem Statement
The current `tests/conftest.py` contains placeholder imports that do not match the actual implementations in `src/config.py` and `src/database.py`. This mismatch causes import errors and incorrect fixture behavior. The goal is to update the imports and fixtures to reflect the actual module exports.

## Functional Requirements

1. **FR-1**: Update imports from `src.config.py` to use `AppConfig` and `load_config`.
2. **FR-2**: Update imports from `src.database.py` to use `init_db`, `get_session`, and model classes.
3. **FR-3**: Modify the `config()` fixture to return a valid `AppConfig` instance using test defaults or a minimal config file.
4. **FR-4**: Replace the `database(config)` fixture with:
   - `db_engine`: Creates an in-memory SQLite database using `init_db`.
   - `db_session`: Provides a session from the engine with rollback cleanup after tests.
5. **FR-5**: Ensure all imports are direct and avoid relative imports or __init__.py cascades.

## Non-Functional Requirements
1. **NFR-1**: Fixtures must be lightweight and not leave files behind (use :memory: SQLite).
2. **NFR-2**: Test isolation must be maintained via session rollback.
3. **NFR-3**: All code must adhere to PEP 8, use type hints, and include comprehensive docstrings.

## Constraints
1. Only modify `tests/conftest.py`.
2. Do not change any source files (`src/config.py`, `src/database.py`).
3. Use in-memory SQLite for testing.
4. Avoid relative imports; use direct imports with sys.path.insert if needed.

## Success Criteria

- [ ] All imports in conftest.py match actual exports from src modules
- [ ] config fixture returns a valid AppConfig instance
- [ ] db_engine fixture creates and initializes an in-memory database
- [ ] db_session fixture provides isolated sessions per test
- [ ] Running pytest does not raise ImportError
- [ ] All existing tests pass

## Out of Scope
1. Modifying any source files (src/config.py, src/database.py)
2. Adding new test cases or functionality
3. Implementing test cleanup beyond session rollback

## Open Questions
1. Should the config fixture use a real config file or construct AppConfig programmatically?
2. What is the minimal set of configuration values needed for testing?