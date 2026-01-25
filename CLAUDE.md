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

Python MCP server for macOS Shortcuts with read-only database access, two execution modes, and shortcut creation capabilities.

### Module Layout

- **server.py** - FastMCP tool definitions and entrypoint (`main()`). Tools: `list_shortcuts`, `get_shortcut`, `search_shortcuts`, `get_folders`, `get_available_actions`, `create_shortcut`, `run_shortcut`
- **database.py** - Async SQLite queries via aiosqlite. Read-only connection to `~/Library/Shortcuts/Shortcuts.sqlite`. Handles Cocoa epoch timestamps and UUID normalization
- **executor.py** - Execution strategies and file operations:
  - `run_via_applescript()` - Synchronous execution with output capture via osascript
  - `run_via_url_scheme()` - Async execution via `shortcuts://` URL scheme
  - `sign_shortcut_file()` - Signs .shortcut files for import
  - `delete_shortcut()` - Removes shortcuts via AppleScript
- **parser.py** - Parses binary plist blobs (shortcut action data) using `plistlib`. Extracts `WFWorkflowActions` and `WFWorkflowInputContentItemClasses`
- **models.py** - Pydantic models for API responses (`ShortcutMetadata`, `ShortcutDetail`, `RunResult`, `ShortcutAction`, `ActionInfo`)
- **actions.py** - `ActionCatalog` class that discovers available actions from system frameworks, apps, user library, and curated definitions. Caches results in memory
- **builder.py** - Constructs shortcut plist payloads from `ShortcutAction` lists. Handles client version detection and plist serialization
- **references.py** - Transforms simplified reference syntax (`$ref`, `$var`, `$input`, `$ask`, `$clipboard`) into proper Shortcuts plist format
- **config.py** - Environment variable handling
- **types.py** - Type aliases for JSON data structures (`JsonPrimitive`, `JsonValue`)

### Data Flow

**Reading shortcuts:**
1. MCP tool receives request → 2. `database.py` queries SQLite → 3. `parser.py` deserializes action plist blobs → 4. `models.py` structures response

**Running shortcuts:**
1. `run_shortcut` tool → 2. `executor.py` runs via AppleScript or URL scheme → 3. Returns `RunResult`

**Creating shortcuts:**
1. `create_shortcut` tool → 2. `references.py` transforms variable references → 3. `builder.py` generates plist → 4. `executor.py` signs and imports

## Variable Reference System

When creating shortcuts, use simplified syntax that gets transformed into proper plist format:

```python
{"$ref": "previous"}      # Output of previous action
{"$ref": "uuid:ABC123"}   # Output of action with specific UUID
{"$ref": "-1"}            # Relative index (same as "previous")
{"$var": "MyVariable"}    # Named variable
{"$input": True}          # Shortcut input
{"$ask": True}            # Ask user at runtime
{"$clipboard": True}      # Clipboard contents
```

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
- Action catalog scans `/System/Library/PrivateFrameworks/*/Metadata.appintents/extract.actionsdata` and `/Applications/*.app` for available actions
- Curated action definitions stored in `data/curated_actions.json` for classic `is.workflow.actions.*` identifiers
- Type checking is strict mode (`basedpyright` with `typeCheckingMode = "strict"`)
- Python 3.10+ required for type alias syntax and modern typing features
