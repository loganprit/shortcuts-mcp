# shortcuts-mcp

MCP server that lists, inspects, searches, and runs macOS Shortcuts.

Built with [Bun](https://bun.sh) and the [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk).

## Requirements

- macOS with Shortcuts app
- [Bun](https://bun.sh) runtime
- Full Disk Access permission (System Settings > Privacy & Security) for reading the Shortcuts database

## Setup

```bash
# Install dependencies
bun install

# Run the server (stdio transport)
bun run src/ts/index.ts
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `list_shortcuts` | List all shortcuts, optionally filtered by folder |
| `get_shortcut` | Get detailed info about a specific shortcut |
| `search_shortcuts` | Search shortcuts by name or action content |
| `get_folders` | List all shortcut folders |
| `get_available_actions` | Discover available Shortcuts actions from system, apps, and library |
| `run_shortcut` | Execute a shortcut with optional input |

### Tool Parameters

```
list_shortcuts(folder?, include_actions?)
get_shortcut(name, include_actions?)
search_shortcuts(query, search_in?: "name" | "actions" | "both")
get_folders()
get_available_actions(source?, category?, search?, include_parameters?, include_examples?, force_refresh?)
run_shortcut(name, input?, wait_for_result?, timeout?)
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SHORTCUTS_DB_PATH` | `~/Library/Shortcuts/Shortcuts.sqlite` | Path to Shortcuts database |
| `SHORTCUTS_DEFAULT_TIMEOUT` | `30` | Default timeout in seconds for shortcut execution |
| `SHORTCUTS_LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARN, ERROR) |

## Claude Code Integration

Add to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "shortcuts": {
      "command": "bun",
      "args": ["run", "/path/to/shortcuts-mcp/src/ts/index.ts"]
    }
  }
}
```

## Development

```bash
# Run tests
bun test

# Type check
bun run typecheck

# Lint
bun run lint

# Format
bun run format
```

## Architecture

```
src/ts/
├── index.ts          # Entrypoint (stdio transport)
├── server.ts         # MCP server setup
├── database.ts       # SQLite queries (read-only)
├── parser.ts         # Binary plist parsing
├── actions.ts        # Action catalog discovery
├── executor.ts       # Shortcut execution (AppleScript/URL scheme)
├── config.ts         # Environment configuration
├── types.ts          # Type definitions
└── tools/            # MCP tool implementations
    ├── list_shortcuts.ts
    ├── get_shortcut.ts
    ├── search_shortcuts.ts
    ├── get_folders.ts
    ├── get_available_actions.ts
    └── run_shortcut.ts
```
