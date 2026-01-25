# shortcuts-mcp

## Project Overview

`shortcuts-mcp` is a Model Context Protocol (MCP) server that provides access to macOS Shortcuts. It allows AI agents to list, inspect, search, and run Shortcuts on a macOS system.

**Key Technologies:**
- **Language:** Python 3.10+
- **Core Libraries:** `mcp` (Server SDK), `pydantic` (Data models), `aiosqlite` (Async DB access).
- **Package Manager:** `uv`
- **Architecture:**
    - **`src/shortcuts_mcp/server.py`**: Entry point and MCP tool definitions.
    - **`src/shortcuts_mcp/database.py`**: Read-only access to the Shortcuts SQLite database.
    - **`src/shortcuts_mcp/executor.py`**: Handles Shortcut execution via AppleScript (`osascript`) or URL scheme.
    - **`src/shortcuts_mcp/parser.py`**: Parses binary plist data to extract action details.
    - **`src/shortcuts_mcp/models.py`**: Pydantic models for API responses.

## Building and Running

The project uses `uv` for dependency management and execution.

### Installation
```bash
uv sync --all-extras --dev
```

### Running the Server
```bash
uv run shortcuts-mcp
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific tests
uv run pytest tests/test_parser.py
uv run pytest -k parse_actions
```

### CI/CD
The local CI script runs tests, type checking, and linting:
```bash
./scripts/ci.sh
```
This script executes:
1. `uv sync`
2. `pytest`
3. `basedpyright` (Strict type checking)
4. `ruff check` (Linting)
5. `ruff format --check` (Formatting verification)
6. A startup smoke test for the MCP server.

## Development Conventions

### Code Style
- **Formatting:** Adhere strictly to `ruff` formatting with an 88-character line length.
- **Typing:** Strict type checking via `basedpyright`. Avoid `Any`; use specific types or `JsonValue`.
- **Imports:** Sort imports using `ruff` (standard library -> third-party -> local).
- **Async:** Database operations must be async (`aiosqlite`). `executor.py` handles synchronous AppleScript execution appropriately.

### Architecture Patterns
- **Read-Only DB:** The server treats the Shortcuts database (`~/Library/Shortcuts/Shortcuts.sqlite`) as read-only.
- **Execution Modes:**
    - **AppleScript:** Synchronous, captures output (default for `run_shortcut`).
    - **URL Scheme:** Asynchronous, fire-and-forget.
- **Error Handling:** Return `ValueError` for user errors (e.g., shortcut not found). internal errors should be wrapped and returned as helpful messages where possible.

### Environment Variables
- `SHORTCUTS_DB_PATH`: Path to the Shortcuts database (Default: `~/Library/Shortcuts/Shortcuts.sqlite`).
- `SHORTCUTS_DEFAULT_TIMEOUT`: Timeout for AppleScript execution in seconds (Default: 30).
- `SHORTCUTS_LOG_LEVEL`: Logging level (Default: `INFO`).
