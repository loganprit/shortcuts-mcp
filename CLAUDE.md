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
  - `run_via_applescript()` - Synchronous execution with output capture and exit code via osascript
  - `run_via_url_scheme()` - Asynchronous execution via `shortcuts://` URL scheme with optional timeout
- **parser.py** - Parses binary plist blobs (shortcut action data) using `plistlib`. Extracts `WFWorkflowActions` and `WFWorkflowInputContentItemClasses`
- **models.py** - Pydantic models for API responses (`ShortcutMetadata`, `ShortcutDetail`, `RunResult`, `ShortcutAction`)
- **config.py** - Environment variable handling for `SHORTCUTS_DB_PATH`, `SHORTCUTS_DEFAULT_TIMEOUT`, `SHORTCUTS_LOG_LEVEL`
- **types.py** - Type aliases for JSON data structures (`JsonPrimitive`, `JsonValue`). Used throughout the codebase to avoid `Any` types

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

## btca

When you need up-to-date information about technologies used in this project, use btca to query source repositories directly.

**Available resources**: zod, typescript, bun, modelContextProtocol, pydantic, biome, pytest, gemini

### Usage

```bash
btca ask -r <resource> -q "<question>"
```

Use multiple `-r` flags to query multiple resources at once:

```bash
btca ask -r zod -r typescript -q "How do I use Zod with TypeScript for runtime validation?"
```

### Examples

```bash
# Query MCP Python SDK for implementation details
btca ask -r modelContextProtocol -q "How do I create a custom MCP tool with async handlers?"

# Query Gemini CLI for troubleshooting terminal output
btca ask -r gemini -q "Why aren't agent responses showing in terminal output?"

# Query multiple testing frameworks
btca ask -r pytest -r pydantic -q "How to validate async test fixtures with Pydantic models?"
```