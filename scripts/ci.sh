#!/usr/bin/env bash
set -euo pipefail

echo "Installing dependencies..."
bun install

echo "Running tests..."
bun test

echo "Running type check..."
bun run typecheck

echo "Running lint..."
bun run lint

echo "Checking format..."
bun run format:check

# Verify MCP server starts without import/initialization errors
# The server will hang waiting for stdio input, so we timeout after 2 seconds.
# If there are any errors, they appear on stderr.
echo "Testing MCP server startup..."
if stderr=$(timeout 2 bun run src/index.ts 2>&1 >/dev/null) || [ $? -eq 124 ]; then
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

echo ""
echo "CI passed!"
