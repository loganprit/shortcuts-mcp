# shortcuts-mcp

MCP server that lists, inspects, searches, and runs macOS Shortcuts.

## Setup

```bash
uv run shortcuts-mcp
```

## MCP Tools

- `list_shortcuts(folder?, include_actions?)`
- `get_shortcut(name, include_actions?)`
- `search_shortcuts(query, search_in?)`
- `get_folders()`
- `run_shortcut(name, input?, wait_for_result?, timeout?)`

## Environment Variables

```bash
SHORTCUTS_DB_PATH="~/Library/Shortcuts/Shortcuts.sqlite"
SHORTCUTS_DEFAULT_TIMEOUT=30
SHORTCUTS_LOG_LEVEL="INFO"
```

## Claude Code Integration

```json
{
  "mcpServers": {
    "shortcuts": {
      "command": "uv",
      "args": ["--directory", "/path/to/shortcuts-mcp", "run", "shortcuts-mcp"]
    }
  }
}
```
