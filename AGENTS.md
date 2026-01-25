# Repository Guidelines

This file is for agentic coding tools working in this repo.
Keep changes aligned with existing patterns and tooling.

## Project Overview
- Python MCP server for macOS Shortcuts with read-only DB access.
- Supports listing, running, and creating shortcuts.
- Two execution modes: AppleScript (sync) and URL scheme (async).
- Strict typing via basedpyright; linting/formatting via ruff.
## Project Structure
- `src/shortcuts_mcp/`: core library + MCP server.
- `src/shortcuts_mcp/server.py`: FastMCP tool definitions + `main()`.
- `src/shortcuts_mcp/database.py`: async SQLite queries and helpers.
- `src/shortcuts_mcp/executor.py`: AppleScript, URL scheme, signing, deletion.
- `src/shortcuts_mcp/parser.py`: plist parsing for shortcut actions.
- `src/shortcuts_mcp/models.py`: Pydantic response models.
- `src/shortcuts_mcp/actions.py`: action catalog discovery and caching.
- `src/shortcuts_mcp/builder.py`: plist building for shortcut creation.
- `src/shortcuts_mcp/references.py`: variable reference normalization.
- `src/shortcuts_mcp/types.py`: JSON type aliases.
- `tests/`: pytest suite.
- `scripts/ci.sh`: local CI run (sync + tests + lint + typecheck).
## Data Flow
- MCP tool receives request from `server.py`.
- `database.py` queries the Shortcuts SQLite DB with aiosqlite.
- `parser.py` deserializes `ZSHORTCUTACTIONS.ZDATA` plist blobs.
- `models.py` structures responses for return via `model_dump()`.
- `executor.py` handles execution and returns output/metadata.
- Shortcut creation: `references.py` -> `builder.py` -> `executor.py` signing/import.
## Execution Modes
- AppleScript (`osascript`) is the synchronous path with output capture.
- URL scheme (`shortcuts://run-shortcut`) is async fire-and-forget.
- `run_shortcut` defaults to waiting for result unless overridden.
- Timeout is derived from `SHORTCUTS_DEFAULT_TIMEOUT` when not passed.
- `run_via_url_scheme` raises `RuntimeError` on non-zero return codes.
- Keep execution logic isolated to `executor.py`.
- Shortcut creation uses signing/import helpers in `executor.py`.
## Response Shapes
- Tool handlers return plain dicts or `model_dump()` of Pydantic models.
- `ShortcutMetadata` and `ShortcutDetail` are the primary payload shapes.
- `RunResult` always includes `success` and optional output/elapsed time.
- Actions expose identifier + parameters, preserving raw key names.
- `ActionInfo` captures action catalog metadata.
## Dependencies
- Core runtime deps: `mcp`, `pydantic`, `aiosqlite`.
- Dev deps: `pytest`, `pytest-asyncio`, `basedpyright`, `ruff`.
- Avoid adding new deps without clear justification.
## Build, Run, and Dev Commands
- `uv run shortcuts-mcp`: run MCP server locally.
- `uv sync --all-extras --dev`: install dev dependencies (CI uses this).
- `scripts/ci.sh`: run full CI suite locally.
## Testing Commands
- `uv run pytest`: run all tests.
- `uv run pytest tests/test_parser.py`: run a specific file.
- `uv run pytest tests/test_parser.py -k test_parse_actions`: run a single test.
- `uv run pytest -k parse_actions`: run by keyword.
- `uv run pytest -q`: quieter output.
## Lint, Format, Typecheck
- `uv run basedpyright`: strict type checking.
- `uv run ruff check`: lint (E/F/I).
- `uv run ruff format`: format code.
- `uv run ruff format --check`: verify formatting.
## CI Behavior (scripts/ci.sh)
- Runs `uv sync --all-extras --dev`.
- Runs pytest, basedpyright, ruff check, ruff format --check.
- Starts the MCP server with a 2s timeout to detect startup errors.
## Environment Variables
- `SHORTCUTS_DB_PATH`: `~/Library/Shortcuts/Shortcuts.sqlite`.
- `SHORTCUTS_DEFAULT_TIMEOUT`: AppleScript timeout in seconds.
- `SHORTCUTS_LOG_LEVEL`: logging level (INFO, DEBUG).
## Code Style Guidelines
### Formatting
- Python 3.10+ syntax, `from __future__ import annotations` preferred.
- Ruff format with 88-char line length.
- Use 4-space indentation and keep docstrings concise.

### Imports
- Order: `__future__`, stdlib, third-party, local.
- Keep imports explicit; avoid unused imports (ruff E/F).
- Use relative imports within `shortcuts_mcp`.

### Typing
- basedpyright strict mode: avoid `Any`.
- Prefer concrete types (`dict[str, object]`, `list[str]`).
- Use `JsonValue` TypeAlias for recursive JSON data.
- Use `object` only when Pydantic schema limitations require it.
- Annotate async return types explicitly.

### Naming
- `snake_case` for functions/vars, `PascalCase` for classes.
- Constants are `UPPER_SNAKE_CASE`.
- Pydantic fields mirror API keys (`action_count`, `last_modified`).

### Error Handling
- Return `None` for not-found DB lookups; callers raise if needed.
- Use `ValueError` for user-facing invalid requests (e.g., missing shortcut).
- Parse failures should fail soft (empty list/None) rather than raise.
- Wrap external execution errors and return clear messages.
- When creating shortcuts, surface signing/import failures with context.

### Async + IO
- Database access is async; keep DB functions `async def`.
- Avoid blocking operations in async contexts; use executors when needed.
- Keep AppleScript execution in `executor.py` only.

### Models
- Pydantic models live in `models.py` and are the API contract.
- Use `model_dump()` when returning from tools.
- Default empty collections via `Field(default_factory=...)`.

### Parsing
- `parser.py` handles binary plist blobs with `plistlib`.
- Accept both list and dict-wrapped plist formats.
- Normalize plist keys to strings before processing.

### Database Access
- Always connect with read-only URI (`?mode=ro`).
- Use `aiosqlite.Row` and access by column names.
- Normalize UUIDs and Cocoa epoch timestamps via helpers.

### Tool Definitions
- MCP tools are defined in `server.py` using `@mcp.tool()`.
- Keep tools thin and delegate to database/executor/parser modules.
- Support optional args with defaults to keep schemas stable.
- For catalog/build tools, cache or reuse results in memory where possible.

## Testing Guidelines
- Use `pytest` + `pytest-asyncio` with `asyncio_mode = auto`.
- Name files `tests/test_*.py`, tests `test_*`.
- Prefer deterministic unit tests (no live Shortcuts DB).
- Build sample plist data with `plistlib.dumps`.

## Workflow Expectations
- Keep changes small and focused; update docs with code changes.
- Avoid new dependencies without reason; update `pyproject.toml` if needed.
- When adding new tools, update README + tool list.

## Cursor/Copilot Rules
- None found in `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md`.

## Git Hygiene
- Do not rewrite history or use destructive git commands.
- Keep commit messages short, imperative, and consistent with history.

## Useful References
- `CLAUDE.md`: local command list and architecture notes.
- `README.md`: tool list and environment variables.
