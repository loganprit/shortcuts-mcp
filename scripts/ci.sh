#!/usr/bin/env bash
set -euo pipefail

uv sync --all-extras --dev
uv run pytest
uv run basedpyright
uv run ruff check
uv run ruff format --check

# Verify MCP server starts without import/initialization errors
# The server will hang waiting for stdio input, so we timeout after 2 seconds.
# If there are any errors (like Pydantic schema issues), they appear on stderr.
echo "Testing MCP server startup..."
if stderr=$(timeout 2 uv run shortcuts-mcp 2>&1 >/dev/null) || [ $? -eq 124 ]; then
    # Exit code 124 means timeout (expected - server started successfully)
    # Any other success means unexpected early exit
    if [ -n "$stderr" ]; then
        echo "MCP server startup failed with errors:"
        echo "$stderr"
        exit 1
    fi
    echo "MCP server startup: OK"
else
    echo "MCP server startup failed:"
    echo "$stderr"
    exit 1
fi
