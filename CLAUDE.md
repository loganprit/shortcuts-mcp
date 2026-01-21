# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv run shortcuts-mcp          # Run the MCP server locally
uv run pytest                 # Run all tests
uv run pytest tests/test_parser.py -k test_parse_actions  # Run a single test
uv run basedpyright           # Type checking (strict mode)
uv run ruff check             # Lint code
uv run ruff format            # Format code
uv run ruff format --check    # Check formatting without modifying
scripts/ci.sh                 # Run full CI suite locally
```

## Architecture

Python MCP server for macOS Shortcuts with read-only database access and two execution modes.

### Module Layout

- **server.py** - FastMCP tool definitions and entrypoint (`main()`). Tools: `list_shortcuts`, `get_shortcut`, `search_shortcuts`, `get_folders`, `run_shortcut`
- **database.py** - Async SQLite queries via aiosqlite. Read-only connection to `~/Library/Shortcuts/Shortcuts.sqlite`. Handles Cocoa epoch timestamps and UUID normalization
- **executor.py** - Two execution strategies:
  - `run_via_applescript()` - Synchronous execution with output capture via osascript
  - `run_via_url_scheme()` - Fire-and-forget via `shortcuts://` URL scheme
- **parser.py** - Parses binary plist blobs (shortcut action data) using `plistlib`. Extracts `WFWorkflowActions` and `WFWorkflowInputContentItemClasses`
- **models.py** - Pydantic models for API responses (`ShortcutMetadata`, `ShortcutDetail`, `RunResult`, `ShortcutAction`)
- **config.py** - Environment variable handling for `SHORTCUTS_DB_PATH`, `SHORTCUTS_DEFAULT_TIMEOUT`, `SHORTCUTS_LOG_LEVEL`

### Data Flow

1. MCP tool receives request → 2. `database.py` queries SQLite → 3. `parser.py` deserializes action plist blobs → 4. `models.py` structures response → 5. (for `run_shortcut`) `executor.py` runs via AppleScript or URL scheme

## Environment Variables

```bash
SHORTCUTS_DB_PATH="~/Library/Shortcuts/Shortcuts.sqlite"  # Database location
SHORTCUTS_DEFAULT_TIMEOUT=30                              # AppleScript timeout in seconds
SHORTCUTS_LOG_LEVEL="INFO"
```

## Key Implementation Details

- Database connection is always read-only (`?mode=ro` URI parameter)
- Cocoa epoch (2001-01-01) used for timestamp conversion in database.py
- Shortcut UUIDs may be stored as 16-byte blobs or strings; `_normalize_uuid()` handles both
- Action data stored as binary plist in `ZSHORTCUTACTIONS.ZDATA` column
- Plist parsing handles two formats: direct list of actions OR dict-wrapped with `WFWorkflowActions` key
- Type checking is strict mode (`basedpyright` with `typeCheckingMode = "strict"`)
- Python 3.10+ required for type alias syntax and modern typing features
