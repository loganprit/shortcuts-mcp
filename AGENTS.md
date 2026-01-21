# Repository Guidelines

## Project Structure & Module Organization
- `src/shortcuts_mcp/`: core library and MCP server implementation.
  - `server.py`: MCP tool definitions and entrypoint.
  - `database.py`: read-only access to the Shortcuts SQLite DB.
  - `executor.py`: AppleScript + URL scheme execution helpers.
  - `parser.py`, `models.py`, `config.py`: parsing, schemas, config.
- `tests/`: pytest suite (currently `tests/test_parser.py`).
- `README.md` / `CLAUDE.md`: usage notes and local run commands.

## Build, Test, and Development Commands
- `uv run shortcuts-mcp`: runs the MCP server locally.
- `uv run pytest`: executes the test suite.

## Coding Style & Naming Conventions
- Python 3.10+ with type hints and async/await patterns.
- Follow PEP 8 conventions (4-space indentation, snake_case for functions and variables, PascalCase for classes).
- Keep public tool functions small and delegate logic to helpers in `database.py`, `executor.py`, and `parser.py`.

## Testing Guidelines
- Framework: `pytest` with `pytest-asyncio` (async tests supported).
- Place new tests in `tests/` and name files `test_*.py` with functions `test_*`.
- Prefer fast, deterministic unit tests; avoid requiring live Shortcuts data unless explicitly intended.

## Commit & Pull Request Guidelines
- This checkout has no git history available, so follow clear, imperative commit messages (e.g., "Add shortcut action parser tests").
- PRs should include a concise description, test results, and any config or environment changes required to run locally.

## Configuration & Environment Notes
- The server reads from the macOS Shortcuts SQLite database. Default path:
  - `SHORTCUTS_DB_PATH="~/Library/Shortcuts/Shortcuts.sqlite"`
- Additional env vars:
  - `SHORTCUTS_DEFAULT_TIMEOUT` (seconds), `SHORTCUTS_LOG_LEVEL`.
- This project is macOS-specific due to AppleScript/Shortcuts integration.
