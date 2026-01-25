# shortcuts-mcp

## Project Overview
`shortcuts-mcp` is a Model Context Protocol (MCP) server that enables AI agents to interact with macOS Shortcuts. It allows listing, inspecting, searching, and running shortcuts on a macOS system.

**Current Status:** The project is in active migration from a Python implementation to a TypeScript implementation using the Bun runtime.

## Architecture

### Python (Legacy/Reference)
*   **Runtime:** Python 3.10+
*   **Key Libraries:** `mcp`, `pydantic`, `aiosqlite`
*   **Entry Point:** `src/shortcuts_mcp/server.py`
*   **Package Manager:** `uv`

### TypeScript (Target)
*   **Runtime:** Bun
*   **Key Libraries:** `@modelcontextprotocol/sdk`, `zod`, `bplist-parser`, `plist`
*   **Entry Point:** `src/ts/index.ts`
*   **Package Manager:** `bun`

## Directory Structure

*   `src/shortcuts_mcp/`: Python source code (existing implementation).
*   `src/ts/`: TypeScript source code (new implementation).
*   `tests/`: Tests for both Python and TypeScript.
*   `specs/`: Documentation and specifications for the migration and tool parity.
    *   `migration-to-ts-sdk.md`: Detailed plan for the TypeScript migration.
    *   `tool-parity-checklist.md`: Feature parity tracking.
*   `scripts/`: Utility scripts (e.g., `ci.sh`).

## Development Workflow

### TypeScript (Bun) - Recommended for new work
*   **Install Dependencies:** `bun install`
*   **Run Server:** `bun run src/ts/index.ts`
*   **Run Tests:** `bun test`
*   **Typecheck:** `bun run typecheck`
*   **Lint:** `bun run lint`
*   **Format:** `bun run format`

### Python (uv) - Reference
*   **Run Server:** `uv run shortcuts-mcp`
*   **Run Tests:** `uv run pytest`
*   **Lint:** `uv run ruff check .`
*   **Typecheck:** `uv run basedpyright`

## Environment Variables
Both implementations respect the following environment variables:

*   `SHORTCUTS_DB_PATH`: Path to the Shortcuts SQLite database (default: `~/Library/Shortcuts/Shortcuts.sqlite`).
*   `SHORTCUTS_DEFAULT_TIMEOUT`: Timeout for shortcut execution in seconds (default: `30`).
*   `SHORTCUTS_LOG_LEVEL`: Logging level (default: `INFO`).

## MCP Tools
The server exposes the following tools to the MCP client:

1.  `list_shortcuts(folder?, include_actions?)`
2.  `get_shortcut(name, include_actions?)`
3.  `search_shortcuts(query, search_in?)`
4.  `get_folders()`
5.  `get_available_actions(source?, category?, search?, ...)`
6.  `run_shortcut(name, input?, wait_for_result?, timeout?)`

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
