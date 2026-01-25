# Parity Validation Runbook

This runbook provides step-by-step instructions for validating that the TypeScript
MCP server produces identical responses to the Python FastMCP server for all tools.

## Prerequisites

- macOS with Shortcuts app and at least one shortcut installed
- Bun runtime installed (`bun --version`)
- Python environment set up (`uv sync --all-extras --dev`)

## Overview

Both servers use stdio transport. We send JSON-RPC requests via stdin and compare
outputs. The validation covers:

1. Server initialization handshake
2. Tool discovery (tools/list)
3. Each tool invocation with representative inputs
4. Error handling parity

## Starting the Servers

### Python Server

```bash
uv run shortcuts-mcp
```

### TypeScript Server

```bash
bun run src/ts/index.ts
```

## JSON-RPC Message Format

All requests follow MCP's JSON-RPC 2.0 format:

```json
{"jsonrpc":"2.0","id":1,"method":"<method>","params":{...}}
```

Responses are newline-delimited JSON.

## Validation Steps

### Step 1: Initialize Handshake

Send the initialize request to establish the session:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | timeout 5 <server-command> 2>/dev/null | head -1
```

**Expected:** Both servers respond with a result containing `protocolVersion`, `capabilities`, and `serverInfo`.

**Parity check:** Server names may differ ("Shortcuts MCP" for both), versions may differ (not critical).

### Step 2: List Tools

After initialization, send tools/list to verify both servers expose the same tools:

```bash
echo -e '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":3,"method":"tools/list"}' | timeout 5 <server-command> 2>/dev/null
```

**Expected tools:**
- `list_shortcuts`
- `get_shortcut`
- `search_shortcuts`
- `get_folders`
- `get_available_actions`
- `run_shortcut`

**Parity check:** Tool names must match exactly. Input schemas must have the same required/optional fields.

### Step 3: Validate list_shortcuts

#### 3a. Default parameters

```bash
echo -e '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_shortcuts","arguments":{}}}' | timeout 10 <server-command> 2>/dev/null
```

**Expected response shape:**
```json
{
  "shortcuts": [
    {
      "name": "<string>",
      "id": "<string|null>",
      "folder": "<string|null>",
      "action_count": "<number|null>",
      "last_modified": "<string|null>",
      "action_types": null
    }
  ]
}
```

**Parity check:**
- Same shortcut names returned
- Same field names (snake_case)
- `action_types` is null when `include_actions` is false/omitted

#### 3b. With include_actions=true

```bash
echo -e '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_shortcuts","arguments":{"include_actions":true}}}' | timeout 30 <server-command> 2>/dev/null
```

**Parity check:** `action_types` should be an array of strings (action identifiers) for each shortcut.

### Step 4: Validate get_shortcut

Replace `<SHORTCUT_NAME>` with an actual shortcut name from your system.

#### 4a. Existing shortcut

```bash
echo -e '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_shortcut","arguments":{"name":"<SHORTCUT_NAME>"}}}' | timeout 10 <server-command> 2>/dev/null
```

**Expected response shape:**
```json
{
  "name": "<string>",
  "id": "<string|null>",
  "folder": "<string|null>",
  "action_count": "<number|null>",
  "last_modified": "<string|null>",
  "actions": [{"identifier": "<string>", "parameters": {...}}],
  "input_types": ["<string>", ...]
}
```

**Parity check:**
- Same actions array contents
- Same input_types array

#### 4b. Non-existent shortcut (error case)

```bash
echo -e '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_shortcut","arguments":{"name":"NonExistentShortcut12345"}}}' | timeout 10 <server-command> 2>/dev/null
```

**Parity check:** Both should return an error with message containing "Shortcut not found".

### Step 5: Validate search_shortcuts

#### 5a. Search by name

```bash
echo -e '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_shortcuts","arguments":{"query":"<PARTIAL_NAME>"}}}' | timeout 10 <server-command> 2>/dev/null
```

**Parity check:** Same shortcuts returned for the same query.

#### 5b. Search in actions

```bash
echo -e '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_shortcuts","arguments":{"query":"clipboard","search_in":"actions"}}}' | timeout 30 <server-command> 2>/dev/null
```

**Parity check:** Same shortcuts returned when searching action content.

### Step 6: Validate get_folders

```bash
echo -e '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_folders","arguments":{}}}' | timeout 10 <server-command> 2>/dev/null
```

**Expected response shape:**
```json
{
  "folders": [
    {"name": "<string>", "shortcut_count": 0}
  ]
}
```

**Parity check:** Same folder names returned. Note: `shortcut_count` is always 0 in both implementations.

### Step 7: Validate get_available_actions

#### 7a. Default parameters

```bash
echo -e '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_available_actions","arguments":{}}}' | timeout 30 <server-command> 2>/dev/null
```

**Expected response shape:**
```json
{
  "actions": [...],
  "categories": ["<string>", ...],
  "sources": {"system": 0, "apps": 0, "library": 0, "curated": 0},
  "cached": false
}
```

**Parity check:**
- Same action identifiers returned
- Same categories
- Source counts similar (may vary slightly based on system state)

#### 7b. With source filter

```bash
echo -e '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_available_actions","arguments":{"source":"curated"}}}' | timeout 30 <server-command> 2>/dev/null
```

**Parity check:** Only actions with source "curated" returned.

### Step 8: Validate run_shortcut

**WARNING:** This step actually executes shortcuts. Use a safe shortcut for testing.

#### 8a. Synchronous execution (wait_for_result=true)

```bash
echo -e '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"run_shortcut","arguments":{"name":"<SAFE_SHORTCUT_NAME>"}}}' | timeout 60 <server-command> 2>/dev/null
```

**Expected response shape:**
```json
{
  "success": true,
  "output": "<string|null>",
  "execution_time_ms": "<number|null>"
}
```

#### 8b. Asynchronous execution (wait_for_result=false)

```bash
echo -e '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"run_shortcut","arguments":{"name":"<SAFE_SHORTCUT_NAME>","wait_for_result":false}}}' | timeout 10 <server-command> 2>/dev/null
```

**Expected response shape:**
```json
{
  "success": true,
  "output": null,
  "execution_time_ms": null
}
```

## Quick Parity Comparison Script

Save this as `scripts/parity-check.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

PYTHON_CMD="uv run shortcuts-mcp"
TS_CMD="bun run src/ts/index.ts"

INIT='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
NOTIF='{"jsonrpc":"2.0","id":2,"method":"notifications/initialized"}'

compare_tool() {
    local name=$1
    local args=$2
    local request=$(echo -e "${INIT}\n${NOTIF}\n{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"${name}\",\"arguments\":${args}}}")

    echo "Testing ${name}..."

    py_out=$(echo "$request" | timeout 30 $PYTHON_CMD 2>/dev/null | tail -1)
    ts_out=$(echo "$request" | timeout 30 $TS_CMD 2>/dev/null | tail -1)

    if [ "$py_out" = "$ts_out" ]; then
        echo "  PASS: Outputs match"
    else
        echo "  DIFF: Outputs differ"
        echo "  Python: $py_out"
        echo "  TypeScript: $ts_out"
    fi
}

# Test each tool with default/minimal arguments
compare_tool "list_shortcuts" "{}"
compare_tool "get_folders" "{}"
compare_tool "search_shortcuts" '{"query":"test"}'

echo "Done. Manual review recommended for complex tools."
```

## Parity Checklist

Use this checklist to track validation progress:

| Tool | Inputs Tested | Outputs Match | Errors Match | Status |
|------|---------------|---------------|--------------|--------|
| list_shortcuts | default, folder, include_actions | [ ] | N/A | [ ] |
| get_shortcut | existing, include_actions=false | [ ] | [ ] not found | [ ] |
| search_shortcuts | name, actions, both | [ ] | N/A | [ ] |
| get_folders | default | [ ] | N/A | [ ] |
| get_available_actions | default, source, category, search | [ ] | N/A | [ ] |
| run_shortcut | sync, async, timeout | [ ] | [ ] timeout | [ ] |

## Known Differences

Document any acceptable differences here:

- Server version strings may differ
- Timestamps may have minor precision differences
- Action order within arrays may vary (use set comparison)
- `cached` field in get_available_actions may differ based on prior calls

## Troubleshooting

### Server hangs on input

Both servers wait for stdin. Ensure you're piping input or use `timeout`.

### JSON parse errors

Ensure each JSON message is on a single line with no trailing whitespace.

### Permission errors

The database at `~/Library/Shortcuts/Shortcuts.sqlite` requires read access.
Full Disk Access may be required in System Preferences > Privacy & Security.
